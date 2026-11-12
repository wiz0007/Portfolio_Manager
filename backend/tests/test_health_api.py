from unittest import mock

import pytest
from django.db import OperationalError
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_health_check_healthy(api_client):
    """Test health check returns 200 OK and connected status when database is reachable."""
    response = api_client.get('/api/v1/health/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "healthy",
        "database": "connected"
    }


def test_health_check_unhealthy(api_client):
    """Test health check returns 503 Service Unavailable when database fails, with no leaked details."""
    with mock.patch("django.db.connection.ensure_connection", side_effect=OperationalError("password authentication failed for user secret_user")):
        response = api_client.get('/api/v1/health/')
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data == {
            "status": "unhealthy",
            "database": "unavailable"
        }
        # Guarantee no leaked credentials or stack traces
        assert "password" not in str(data)
        assert "secret_user" not in str(data)
