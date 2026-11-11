import os

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '').split(',') if h.strip()]

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Production Database Configuration - Fail Fast (Sprint 3 requirement 3.1)
# Production must strictly require a valid PostgreSQL database URL and never fall back to SQLite.
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
        "Production database cannot use SQLite engine."
    )
