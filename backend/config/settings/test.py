import os
from urllib.parse import unquote

import dj_database_url

from .base import *

DEBUG = False
TESTING = True

test_db_url = os.getenv('CI_TEST_DATABASE_URL')
test_market_db_url = os.getenv('CI_TEST_MARKET_DATA_DATABASE_URL') or os.getenv('NEON_STORAGE_DATABASE_URL')

if test_db_url:
    ssl_require = 'neon.tech' in test_db_url or 'sslmode=require' in test_db_url
    parsed_default = dj_database_url.parse(test_db_url, conn_max_age=0, ssl_require=ssl_require)
    if parsed_default.get('PASSWORD'):
        parsed_default['PASSWORD'] = unquote(parsed_default['PASSWORD'])
    parsed_default['ENGINE'] = DATABASE_ENGINE

    DATABASES = {
        'default': parsed_default,
    }

    if test_market_db_url:
        ssl_market = 'neon.tech' in test_market_db_url or 'sslmode=require' in test_market_db_url
        parsed_market = dj_database_url.parse(test_market_db_url, conn_max_age=0, ssl_require=ssl_market)
        if parsed_market.get('PASSWORD'):
            parsed_market['PASSWORD'] = unquote(parsed_market['PASSWORD'])
        parsed_market['ENGINE'] = DATABASE_ENGINE
        DATABASES['market_data'] = parsed_market
    else:
        # If secondary URL not provided in CI, create separate test database on default connection
        market_clone = dict(parsed_default)
        market_clone['TEST'] = {'NAME': 'test_market_data_db'}
        DATABASES['market_data'] = market_clone
else:
    # Isolated in-memory SQLite for local test runs across both databases
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        },
        'market_data': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        },
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
