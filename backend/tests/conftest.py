import os
import sys
from pathlib import Path
import mongomock
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['AI_PROVIDER'] = 'none'
import django
django.setup()
from django.test import Client
from api import db


@pytest.fixture(autouse=True)
def mongo(monkeypatch):
    db.database.cache_clear()
    client = mongomock.MongoClient(tz_aware=True)
    monkeypatch.setattr(db, 'MongoClient', lambda *a, **kw: client)
    monkeypatch.setenv('AI_PROVIDER', 'none')
    for key in ['ALL_PROXY', 'all_proxy', 'HTTP_PROXY', 'http_proxy', 'HTTPS_PROXY', 'https_proxy']:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv('JUDGE0_URL', raising=False)
    yield db.database()
    db.database.cache_clear()


def register(client, email='candidate@example.com', opt=True):
    token = client.get('/api/auth/csrf').json()['csrfToken']
    r = client.post('/api/auth/register', {'full_name': 'Test Candidate', 'email': email,
        'password': 'Bright!Sky927#', 'confirm_password': 'Bright!Sky927#', 'leaderboard_opt_in': opt},
        content_type='application/json', HTTP_X_CSRFTOKEN=token)
    assert r.status_code == 200, r.content
    client.defaults['HTTP_X_CSRFTOKEN'] = r.json()['csrfToken']
    return client


@pytest.fixture
def client():
    return register(Client(enforce_csrf_checks=True))
