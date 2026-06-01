"""
Django settings for Dota 2 Item Shop
"""
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# Production: set SECRET_KEY, DEBUG=false, ALLOWED_HOSTS (comma-separated)
SECRET_KEY = os.environ.get('SECRET_KEY', 'demo-dev-key-change-in-production-xyz123')
DEBUG = os.environ.get('DEBUG', 'true').lower() in ('1', 'true', 'yes')
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get('ALLOWED_HOSTS', '*').split(',') if h.strip()
]
if '*' in ALLOWED_HOSTS or not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['*']

# SPA frontend root (production).
# Priority:
#   1) SPA_ROOT env var (absolute path)
#   2) backend/static/spa (when frontend build was copied there)
_SPA_ROOT = (os.environ.get('SPA_ROOT') or '').strip()
if _SPA_ROOT:
    SPA_ROOT = Path(_SPA_ROOT).resolve()
else:
    default_spa = (BASE_DIR / 'static' / 'spa')
    SPA_ROOT = default_spa.resolve() if default_spa.exists() else None

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'shop',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # VULN(Clickjacking): XFrameOptionsMiddleware removed — site can be embedded in iframes
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# Database: default SQLite; set DATABASE_URL for PostgreSQL (postgres://user:pass@host/dbname)
_db_url = os.environ.get('DATABASE_URL', '').strip()
if _db_url and _db_url.startswith('postgres://'):
    import re
    _db_url = re.sub(r'^postgres://', 'postgresql://', _db_url)
if _db_url and _db_url.startswith('postgresql://'):
    try:
        import dj_database_url
        DATABASES = {'default': dj_database_url.parse(_db_url, conn_max_age=600)}
    except ImportError:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.environ.get('DB_PATH', str(BASE_DIR / 'db.sqlite3')),
            }
        }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.environ.get('DB_PATH', str(BASE_DIR / 'db.sqlite3')),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

# Media for uploaded images
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Production security (when DEBUG is False)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR.parent / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.app_urls',
            ],
        },
    },
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JWT settings for SPA (Vite frontend)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# DRF - JWT auth for API
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Dota 2 Item Shop API',
    'DESCRIPTION': 'REST API for the Dota 2 Item Shop — a web security demo application.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'TAGS': [
        {'name': 'Auth', 'description': 'Authentication & user management'},
        {'name': 'Items', 'description': 'Store item catalog & reviews'},
        {'name': 'Cart', 'description': 'Shopping cart operations'},
        {'name': 'Orders', 'description': 'Order management'},
        {'name': 'Wallet', 'description': 'Wallet balance & transactions'},
        {'name': 'Inventory', 'description': 'User inventory & trading'},
        {'name': 'Vouchers', 'description': 'Voucher redemption'},
        {'name': 'Tools', 'description': 'Developer / utility endpoints'},
    ],
    'COMPONENT_SPLIT_REQUEST': True,
}

# CORS - allow access from any origin (any IP/host)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Login URLs for Django template (cookie) auth
LOGIN_URL = '/shop/login/'
LOGIN_REDIRECT_URL = '/shop/items/'
LOGOUT_REDIRECT_URL = '/shop/'
