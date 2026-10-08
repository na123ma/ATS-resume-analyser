from datetime import datetime, timezone
from functools import lru_cache
from uuid import uuid4
from django.conf import settings
from pymongo import MongoClient


def now():
    return datetime.now(timezone.utc)


def uid():
    return uuid4().hex


@lru_cache(maxsize=1)
def database():
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=4000, tz_aware=True)
    db = client[settings.MONGO_DB]
    ensure_indexes(db)
    return db


def ensure_indexes(db):
    db.users.create_index('email', unique=True)
    db.sessions.create_index('token_hash', unique=True)
    db.sessions.create_index('expires_at', expireAfterSeconds=0)
    db.limits.create_index('expires_at', expireAfterSeconds=0)
    for name in ['reports', 'drafts', 'interviews', 'exams', 'coding', 'submissions']:
        db[name].create_index([('user_id', 1), ('created_at', -1)])
    db.exams.create_index([('user_id', 1)], unique=True, partialFilterExpression={'status': 'active'}, name='one_active_exam')
    db.exams.create_index([('rank_key', 1)], unique=True, partialFilterExpression={'mode': 'ranked'}, name='daily_ranked_attempt')
    db.exams.create_index([('technology', 1), ('status', 1), ('score', -1)])


def public(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [public(x) for x in value]
    if isinstance(value, dict):
        return {('id' if k == '_id' else k): public(v) for k, v in value.items()}
    return value
