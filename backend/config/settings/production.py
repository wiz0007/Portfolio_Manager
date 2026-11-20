import os

from django.core.exceptions import ImproperlyConfigured

from .base import *
from .base import _parse_database_url

DEBUG = False

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '').split(',') if h.strip()]

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Production Database Configuration - Fail Fast
database_url = os.getenv('DATABASE_URL', '').strip()
if not database_url:
    raise ImproperlyConfigured(
        "DATABASE_URL environment variable is required in production. "
        "Production must never fall back to SQLite."
    )

if not (database_url.startswith('postgres://') or database_url.startswith('postgresql://')):
    raise ImproperlyConfigured(
        "DATABASE_URL must be a valid PostgreSQL connection URL in production."
    )

if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    raise ImproperlyConfigured(
        "Production primary database cannot use SQLite engine."
    )

# Production Security & Secret Key
if os.getenv('ENVIRONMENT', '').lower() == 'production' or os.getenv('DJANGO_ENV', '').lower() == 'production':
    secret_key = os.getenv('SECRET_KEY', '').strip()
    if not secret_key or secret_key.startswith('django-insecure') or 'dev-insecure' in secret_key:
        raise ImproperlyConfigured(
            "A secure, non-default SECRET_KEY environment variable is required in production."
        )

# Secondary Market Data Storage Database URL
storage_database_url = (
    os.getenv('NEON_STORAGE_DATABASE_URL', '').strip()
    or os.getenv('MARKET_DATA_STORAGE_DATABASE_URL', '').strip()
    or os.getenv('NEON_STORAGE_URL', '').strip()
    or os.getenv('MARKET_DATA_DATABASE_URL', '').strip()
)
if storage_database_url:
    if not (storage_database_url.startswith('postgres://') or storage_database_url.startswith('postgresql://')):
        raise ImproperlyConfigured(
            "NEON_STORAGE_DATABASE_URL must be a valid PostgreSQL connection URL in production."
        )
    DATABASES['market_data'] = _parse_database_url(storage_database_url)
elif 'market_data' not in DATABASES and database_url:
    DATABASES['market_data'] = _parse_database_url(database_url)

if 'market_data' in DATABASES and DATABASES['market_data']['ENGINE'] == 'django.db.backends.sqlite3':
    raise ImproperlyConfigured(
        "Production secondary market data database cannot use SQLite engine."
    )

# Prohibit silent demo provider fallback in production
provider_mode = os.getenv('MARKET_DATA_PROVIDER_MODE', 'PRODUCTION').upper()
if provider_mode == 'DEMO':
    raise ImproperlyConfigured(
        "MARKET_DATA_PROVIDER_MODE cannot be DEMO in production. "
        "Synthetic prices must never update production portfolios."
    )
