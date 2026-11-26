import importlib
import os
import sys
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured


def reload_settings_modules():
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith("config.settings."):
            del sys.modules[mod_name]


def test_production_settings_fails_fast_when_database_url_missing():
    """Verify production settings raises ImproperlyConfigured if DATABASE_URL is missing."""
    with mock.patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
        reload_settings_modules()
        with pytest.raises(ImproperlyConfigured) as exc_info:
            importlib.import_module("config.settings.production")
        assert "DATABASE_URL environment variable is required in production" in str(exc_info.value)


def test_production_settings_fails_fast_with_invalid_database_url():
    """Verify production settings raises ImproperlyConfigured if DATABASE_URL is not PostgreSQL."""
    with mock.patch.dict(os.environ, {"DATABASE_URL": "sqlite:///test.db"}, clear=False):
        reload_settings_modules()
        with pytest.raises(ImproperlyConfigured) as exc_info:
            importlib.import_module("config.settings.production")
        assert "must be a valid PostgreSQL connection URL" in str(exc_info.value)


def test_production_settings_succeeds_with_valid_postgres_url():
    """Verify production settings loads properly with valid PostgreSQL URL."""
    valid_pg_url = "postgresql://user:pass@localhost:5432/testdb"
    valid_storage_url = "postgresql://user:pass@remotehost:5432/storagedb"
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": valid_pg_url,
            "NEON_STORAGE_DATABASE_URL": valid_storage_url,
            "SECRET_KEY": "a-very-secure-production-secret-key-that-is-not-insecure",
            "ALLOWED_HOSTS": "api.portfolio.example.com",
            "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "DEFAULT_FROM_EMAIL": "notifications@portfolio.example.com",
            "FRONTEND_BASE_URL": "https://portfolio.example.com",
            "CORS_ALLOWED_ORIGINS": "https://portfolio.example.com",
            "CSRF_TRUSTED_ORIGINS": "https://portfolio.example.com",
        },
        clear=False,
    ):
        reload_settings_modules()
        mod = importlib.import_module("config.settings.production")
        assert mod.DEBUG is False
        assert mod.DATABASES["default"]["NAME"] == "testdb"
        assert mod.DATABASES["market_data"]["NAME"] == "storagedb"
