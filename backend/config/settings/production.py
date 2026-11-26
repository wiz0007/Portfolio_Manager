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
secret_key = os.getenv('SECRET_KEY', '').strip()
if not secret_key or secret_key.startswith('django-insecure') or 'dev-insecure' in secret_key:
    raise ImproperlyConfigured(
        "A secure, non-default SECRET_KEY environment variable is required when production settings are loaded."
    )
if not ALLOWED_HOSTS or any(host in ('localhost', '127.0.0.1', 'testserver') for host in ALLOWED_HOSTS):
    raise ImproperlyConfigured('ALLOWED_HOSTS must contain production hostnames and no local development hosts.')

# Secondary Market Data Storage Database URL. Production must have two
# independently configured PostgreSQL databases; never silently alias them.
storage_database_url = (
    os.getenv('NEON_STORAGE_DATABASE_URL', '').strip()
    or os.getenv('MARKET_DATA_STORAGE_DATABASE_URL', '').strip()
    or os.getenv('NEON_STORAGE_URL', '').strip()
    or os.getenv('MARKET_DATA_DATABASE_URL', '').strip()
)
if not storage_database_url:
    raise ImproperlyConfigured(
        "NEON_STORAGE_DATABASE_URL (or a supported compatibility alias) is required in production. "
        "The market_data database must never silently reuse DATABASE_URL."
    )
if not (storage_database_url.startswith('postgres://') or storage_database_url.startswith('postgresql://')):
    raise ImproperlyConfigured("The secondary market-data database URL must be PostgreSQL.")

primary_config = DATABASES['default']
secondary_config = _parse_database_url(storage_database_url)
if secondary_config['ENGINE'] == 'django.db.backends.sqlite3':
    raise ImproperlyConfigured("Production secondary market data database cannot use SQLite.")

# Reject identical physical database targets, even when different aliases/URLs
# are used. Compare normalized connection identity, not credentials.
def _database_identity(config):
    return (
        config.get('HOST', '').lower(),
        str(config.get('PORT', '')),
        config.get('NAME', ''),
    )

if _database_identity(primary_config) == _database_identity(secondary_config):
    raise ImproperlyConfigured(
        "DATABASE_URL and NEON_STORAGE_DATABASE_URL resolve to the same database. "
        "Two physically independent PostgreSQL databases are required."
    )
DATABASES['market_data'] = secondary_config

# Prohibit silent demo provider fallback in production
provider_mode = os.getenv('MARKET_DATA_PROVIDER_MODE', 'PRODUCTION').strip().upper()
if provider_mode != 'PRODUCTION':
    raise ImproperlyConfigured(
        "MARKET_DATA_PROVIDER_MODE must be PRODUCTION in production. "
        "Synthetic providers are disabled for production portfolio data."
    )

# Set the effective Django setting, not only a local validation variable.
MARKET_DATA_PROVIDER_MODE = 'PRODUCTION'

# Authenticated application APIs require verified email in production.
REQUIRE_VERIFIED_EMAIL_FOR_API = True

# Production email and browser-origin configuration must be real, not development defaults.
if EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
    raise ImproperlyConfigured('A real production EMAIL_BACKEND is required; console email is development-only.')
if not DEFAULT_FROM_EMAIL or DEFAULT_FROM_EMAIL.endswith('.local'):
    raise ImproperlyConfigured('Set a valid production DEFAULT_FROM_EMAIL address.')
if not FRONTEND_BASE_URL.startswith('https://'):
    raise ImproperlyConfigured('FRONTEND_BASE_URL must be an HTTPS origin in production.')
if not CORS_ALLOWED_ORIGINS or not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured('Production CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS must be configured.')
if any('localhost' in origin or '127.0.0.1' in origin for origin in CORS_ALLOWED_ORIGINS + CSRF_TRUSTED_ORIGINS):
    raise ImproperlyConfigured('Production CORS/CSRF origins must not contain localhost entries.')

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
