import hashlib
import json
from datetime import timedelta
from functools import wraps
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from pydantic import ValidationError
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError
from .db import database, now, public


class APIError(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status
        super().__init__(message)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def csrf_failure(request, reason=''):
    return JsonResponse({'error': 'Your session needs a refresh. Reload the page and try again.'}, status=403)


def rate_limit(key, maximum=60, seconds=60):
    db = database()
    slot = int(now().timestamp()) // seconds
    entry = db.limits.find_one_and_update(
        {'_id': digest(f'{key}:{slot}')},
        {'$inc': {'count': 1}, '$setOnInsert': {'expires_at': now() + timedelta(seconds=seconds * 2)}},
        upsert=True, return_document=ReturnDocument.AFTER,
    )
    if entry['count'] > maximum:
        raise APIError('Too many requests. Please try again shortly.', 429)


def api(methods=('GET',), authenticated=True, limit=90):
    def decorate(fn):
        @wraps(fn)
        def wrapped(request, *args, **kwargs):
            try:
                if request.method not in methods:
                    return JsonResponse({'error': 'Method not allowed.'}, status=405)
                request.user_doc = None
                if authenticated:
                    token = request.COOKIES.get('skillentra_session', '')
                    session = database().sessions.find_one({'token_hash': digest(token), 'expires_at': {'$gt': now()}}) if token else None
                    request.user_doc = database().users.find_one({'_id': session['user_id']}) if session else None
                    if not request.user_doc:
                        raise APIError('Please sign in to continue.', 401)
                key = request.user_doc['_id'] if request.user_doc else request.META.get('REMOTE_ADDR', 'unknown')
                if limit:
                    rate_limit(f'{fn.__name__}:{key}', limit)
                request.data = {}
                if request.content_type == 'application/json':
                    try:
                        request.data = json.loads(request.body or b'{}')
                    except (ValueError, UnicodeDecodeError):
                        raise APIError('Send valid JSON.')
                    if not isinstance(request.data, dict):
                        raise APIError('Send a JSON object.')
                result = fn(request, *args, **kwargs)
                if isinstance(result, HttpResponse):
                    return result
                return JsonResponse(public(result), safe=not isinstance(result, list))
            except APIError as exc:
                return JsonResponse({'error': exc.message}, status=exc.status)
            except ValidationError as exc:
                errors = ['.'.join(map(str, e['loc'])) + ': ' + e['msg'] for e in exc.errors()]
                return JsonResponse({'error': 'Please check the form.', 'details': errors}, status=400)
            except PyMongoError:
                return JsonResponse({'error': 'Database unavailable. Check the MongoDB connection and try again.'}, status=503)
        return wrapped
    return decorate


def owned(collection, resource_id, request):
    doc = database()[collection].find_one({'_id': resource_id, 'user_id': request.user_doc['_id']})
    if not doc:
        raise APIError('This item was not found.', 404)
    return doc


class ResponseHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['Referrer-Policy'] = 'same-origin'
        response['X-Frame-Options'] = 'DENY'
        if request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-store'
        return response
