import os

from .base import *

DEBUG = False
TESTING = True

# If running in CI with a dedicated CI PostgreSQL service container
if os.getenv('CI_TEST_DATABASE_URL'):
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(
            os.environ['CI_TEST_DATABASE_URL'],
            conn_max_age=0,
        )
    }
else:
    # Isolated in-memory SQLite for local test runs
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/minute',
        'user': '1000/minute',
        'auth': '1000/minute',
    },
}
