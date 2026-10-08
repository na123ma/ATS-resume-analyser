import secrets
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import CommonPasswordValidator, NumericPasswordValidator
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.middleware.csrf import get_token, rotate_token
from pymongo.errors import DuplicateKeyError
from .db import database, now, uid, public
from .schemas import Register, Login
from .security import api, APIError, digest, rate_limit


def user_public(user):
    return {k: user[k] for k in ['_id', 'full_name', 'email', 'leaderboard_opt_in']}


def session_response(request, user):
    token = secrets.token_urlsafe(48)
    database().sessions.insert_one({'_id': uid(), 'token_hash': digest(token), 'user_id': user['_id'],
                                    'expires_at': now() + timedelta(days=settings.SESSION_DAYS)})
    rotate_token(request)
    response = JsonResponse({'user': public(user_public(user)), 'csrfToken': get_token(request)})
    response.set_cookie('skillentra_session', token, max_age=settings.SESSION_DAYS * 86400,
                        httponly=True, secure=settings.SESSION_COOKIE_SECURE, samesite='Lax', path='/')
    return response


@api(authenticated=False, limit=0)
def csrf(request):
    return {'csrfToken': get_token(request)}


@api(('POST',), authenticated=False, limit=8)
def register(request):
    form = Register.model_validate(request.data)
    email = form.email.casefold()
    try:
        validate_email(email)
        CommonPasswordValidator().validate(form.password)
        NumericPasswordValidator().validate(form.password)
    except ValidationError as e:
        raise APIError(' '.join(e.messages))
    if form.password != form.confirm_password:
        raise APIError('Passwords do not match.')
    if email.split('@')[0].casefold() in form.password.casefold():
        raise APIError('Your password should not contain your email username.')
    user = {'_id': uid(), 'full_name': form.full_name, 'email': email,
            'password_hash': make_password(form.password), 'leaderboard_opt_in': form.leaderboard_opt_in,
            'created_at': now()}
    try:
        database().users.insert_one(user)
    except DuplicateKeyError:
        raise APIError('An account with this email already exists.', 409)
    return session_response(request, user)


@api(('POST',), authenticated=False, limit=10)
def login(request):
    form = Login.model_validate(request.data)
    email = form.email.casefold()
    rate_limit('login-email:' + digest(email), 12, 900)
    user = database().users.find_one({'email': email})
    # Equalize work for nonexistent users without ever exposing password hashes.
    if not user:
        make_password(form.password)
        raise APIError('Email or password is incorrect.', 401)
    if not check_password(form.password, user['password_hash']):
        raise APIError('Email or password is incorrect.', 401)
    return session_response(request, user)


@api(('POST',))
def logout(request):
    database().sessions.delete_one({'token_hash': digest(request.COOKIES.get('skillentra_session', ''))})
    response = JsonResponse({'ok': True})
    response.delete_cookie('skillentra_session', path='/', samesite='Lax')
    return response


@api(('GET', 'PATCH', 'DELETE'))
def me(request):
    if request.method == 'PATCH':
        opt = request.data.get('leaderboard_opt_in')
        if not isinstance(opt, bool): raise APIError('Choose a leaderboard visibility setting.')
        database().users.update_one({'_id': request.user_doc['_id']}, {'$set': {'leaderboard_opt_in': opt}})
        request.user_doc['leaderboard_opt_in'] = opt
    if request.method == 'DELETE':
        password = request.data.get('password', '')
        if not isinstance(password, str) or not check_password(password, request.user_doc['password_hash']):
            raise APIError('Enter your password to delete your account.', 400)
        for collection in ['reports', 'drafts', 'interviews', 'exams', 'coding', 'submissions', 'sessions']:
            database()[collection].delete_many({'user_id': request.user_doc['_id']})
        database().users.delete_one({'_id': request.user_doc['_id']})
        response = JsonResponse({'ok': True})
        response.delete_cookie('skillentra_session', path='/', samesite='Lax')
        return response
    return {'user': user_public(request.user_doc)}
