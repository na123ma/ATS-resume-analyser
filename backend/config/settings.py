import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'development-only-change-before-deployment')
if not DEBUG and (len(SECRET_KEY) < 40 or SECRET_KEY.startswith('development-')):
    raise RuntimeError('Set a random DJANGO_SECRET_KEY of at least 40 characters.')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,backend,testserver,https://ats-resume-analyser-1.onrender.com').split(',')
INSTALLED_APPS = ['api']
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'api.security.ResponseHeadersMiddleware',
]
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
# All domain data and sessions live in MongoDB through PyMongo. No SQL database.
DATABASES = {'default': {'ENGINE': 'django.db.backends.dummy'}}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
TIME_ZONE = 'UTC'
APPEND_SLASH = False
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
CSRF_FAILURE_VIEW = 'api.security.csrf_failure'
CSRF_COOKIE_HTTPONLY = False  # JS sends this as X-CSRFToken; session is HttpOnly.
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
CSRF_TRUSTED_ORIGINS = [
    s.strip()
    for s in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "http://localhost:5173,http://localhost:8080,https://ats-resume-analyser-1.onrender.com"
    ).split(",")
    if s.strip()
]

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if SESSION_COOKIE_SECURE else 0
PASSWORD_HASHERS = ['django.contrib.auth.hashers.PBKDF2PasswordHasher']
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB = os.getenv('MONGO_DB', 'skillentra')
SESSION_DAYS = 7
EXAM_SECONDS = 600
MAX_EXAM_EVENTS = 3
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
