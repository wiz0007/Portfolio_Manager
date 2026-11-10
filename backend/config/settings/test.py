import os
from urllib.parse import unquote

import dj_database_url

from .base import *

DEBUG = False
TESTING = True

test_db_url = os.getenv('CI_TEST_DATABASE_URL')
if test_db_url:
    ssl_require = 'neon.tech' in test_db_url or 'sslmode=require' in test_db_url
    parsed = dj_database_url.parse(test_db_url, conn_max_age=0, ssl_require=ssl_require)
    if parsed.get('PASSWORD'):
        parsed['PASSWORD'] = unquote(parsed['PASSWORD'])
    DATABASES = {
        'default': parsed
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
