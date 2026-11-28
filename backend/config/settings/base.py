import os
from pathlib import Path
from urllib.parse import unquote

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from backend/.env if present
ENV_FILE = BASE_DIR / '.env'
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-me-portfolio-manager-sprint1')

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
    if host.strip()
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'corsheaders',
    'drf_spectacular',

    # Domain Apps
    'apps.users',
    'apps.dashboard',
    'apps.portfolios',
    'apps.assets',
    'apps.transactions',
    'apps.market_data',
    'apps.valuation',
    'apps.analytics',
    'apps.ai_insights',
    'apps.watchlists',
    'apps.notifications',
    'apps.audit',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database Configuration
# Determines engine based on psycopg availability. In standard Linux / Docker / CI environments,
# django.db.backends.postgresql with psycopg 3 is used. If Windows Smart App Control blocks native
# binary C-extensions, django_pg8000 provides a 100% pure-Python PostgreSQL SSL driver.
DATABASE_ENGINE = 'django.db.backends.postgresql'
try:
    import psycopg  # noqa: F401
except ImportError:
    try:
        import psycopg2  # noqa: F401
    except ImportError:
        DATABASE_ENGINE = 'django_pg8000'

def _parse_database_url(url: str):
    if not url:
        return None
    ssl_require = 'neon.tech' in url or 'sslmode=require' in url
    parsed = dj_database_url.parse(url, conn_max_age=0, ssl_require=ssl_require)
    if parsed.get('PASSWORD'):
        parsed['PASSWORD'] = unquote(parsed['PASSWORD'])
    parsed['ENGINE'] = DATABASE_ENGINE
    if DATABASE_ENGINE == 'django_pg8000':
        import ssl
        options = parsed.setdefault('OPTIONS', {})
        options.pop('sslmode', None)
        options.pop('channel_binding', None)
        options['ssl_context'] = ssl.create_default_context()
    return parsed

DATABASE_URL = os.getenv('DATABASE_URL')
# Market Data Storage Database URL (Neon Storage)
NEON_STORAGE_DATABASE_URL = (
    os.getenv('NEON_STORAGE_DATABASE_URL')
    or os.getenv('MARKET_DATA_STORAGE_DATABASE_URL')
    or os.getenv('NEON_STORAGE_URL')
    or os.getenv('MARKET_DATA_DATABASE_URL')
)

DATABASES = {}

if DATABASE_URL:
    DATABASES['default'] = _parse_database_url(DATABASE_URL)
else:
    # Safe fallback when DATABASE_URL is not set (e.g. CI checks / test settings)
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

if NEON_STORAGE_DATABASE_URL:
    DATABASES['market_data'] = _parse_database_url(NEON_STORAGE_DATABASE_URL)

DATABASE_ROUTERS = ['config.database.routers.MarketDataRouter']

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'core.permissions.IsAuthenticatedAndEmailVerified',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'core.authentication.EnforcedSessionAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/minute',
        'user': '120/minute',
        'auth': '15/minute',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Cookie & Session Security
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True

CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False

# CORS and CSRF Origins
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
    if origin.strip()
]

# OpenAPI Spec
SPECTACULAR_SETTINGS = {
    'TITLE': 'Portfolio Manager API',
    'DESCRIPTION': 'Financial intelligence and portfolio management platform API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Email & Verification Configuration (Sprint 3)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@portfoliomanager.local')
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'http://localhost:5173')
EMAIL_VERIFICATION_TIMEOUT = int(os.getenv('EMAIL_VERIFICATION_TIMEOUT', '1800'))

# Email verification policy (production overrides to True).
REQUIRE_VERIFIED_EMAIL_FOR_API = os.getenv('REQUIRE_VERIFIED_EMAIL_FOR_API', 'False').lower() in ('true', '1', 't')

# Market Data Configuration (Sprint 3 & Sprint 7)
MARKET_DATA_PROVIDER_MODE = os.getenv('MARKET_DATA_PROVIDER_MODE', 'DEMO')  # 'DEMO' or 'PRODUCTION'
TRUEDATA_API_KEY = os.getenv('TRUEDATA_API_KEY', '')
TRUEDATA_USERNAME = os.getenv('TRUEDATA_USERNAME', '')
MARKET_DATA_CACHE_TIMEOUT = int(os.getenv('MARKET_DATA_CACHE_TIMEOUT', '900'))  # 15 mins default

# CoinGecko cryptocurrency provider
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', '')
COINGECKO_BASE_URL = os.getenv('COINGECKO_BASE_URL', 'https://api.coingecko.com/api/v3').rstrip('/')
COINGECKO_ENABLED = os.getenv('COINGECKO_ENABLED', 'True').lower() in ('true', '1', 't')
COINGECKO_REQUEST_TIMEOUT = int(os.getenv('COINGECKO_REQUEST_TIMEOUT', '20'))
COINGECKO_PRICE_SYNC_INTERVAL_MINUTES = int(os.getenv('COINGECKO_PRICE_SYNC_INTERVAL_MINUTES', '15'))
COINGECKO_HISTORY_SYNC_ENABLED = os.getenv('COINGECKO_HISTORY_SYNC_ENABLED', 'True').lower() in ('true', '1', 't')
COINGECKO_QUOTE_CURRENCY = os.getenv('COINGECKO_QUOTE_CURRENCY', 'INR').upper()

# MFAPI / Indian mutual funds provider
MFAPI_BASE_URL = os.getenv('MFAPI_BASE_URL', 'https://api.mfapi.in').rstrip('/')
MFAPI_ENABLED = os.getenv('MFAPI_ENABLED', 'True').lower() in ('true', '1', 't')
MFAPI_REQUEST_TIMEOUT = int(os.getenv('MFAPI_REQUEST_TIMEOUT', '20'))
MF_NAV_SYNC_ENABLED = os.getenv('MF_NAV_SYNC_ENABLED', 'True').lower() in ('true', '1', 't')
MF_NAV_SYNC_INTERVAL_HOURS = int(os.getenv('MF_NAV_SYNC_INTERVAL_HOURS', '24'))
MF_NAV_DEFAULT_CURRENCY = os.getenv('MF_NAV_DEFAULT_CURRENCY', 'INR').upper()

# OpenAI & AI Insights Configuration (Sprint 9)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
OPENAI_REQUEST_TIMEOUT = int(os.getenv('OPENAI_REQUEST_TIMEOUT', '30'))
OPENAI_MAX_OUTPUT_TOKENS = int(os.getenv('OPENAI_MAX_OUTPUT_TOKENS', '1000'))



