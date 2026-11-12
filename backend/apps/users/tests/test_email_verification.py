from unittest import mock

import pytest
from django.core import mail
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User
from apps.users.services.email_verification import EmailVerificationService


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def unverified_user(db):
    return User.objects.create_user(
        email="unverified@example.com",
        password="ValidPassword123!",
        full_name="Unverified User",
    )


@pytest.fixture
def verified_user(db):
    user = User.objects.create_user(
        email="verified@example.com",
        password="ValidPassword123!",
        full_name="Verified User",
    )
    user.email_verified_at = timezone.now()
    user.save()
    return user


@pytest.mark.django_db
class TestEmailVerification:

    def test_registration_sends_verification_email_and_leaves_unverified(self, api_client):
        """Registering a new account leaves email_verified_at None and sends email."""
        mail.outbox.clear()
        payload = {
            "full_name": "Test Reg User",
            "email": "reguser@example.com",
            "password": "Password123!",
            "password_confirmation": "Password123!",
        }
        response = api_client.post('/api/v1/auth/register/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        user_data = response.json()["user"]
        assert user_data["is_email_verified"] is False
        assert user_data["email_verified_at"] is None

        user = User.objects.get(email="reguser@example.com")
        assert user.email_verified_at is None
        assert user.is_email_verified is False

        # Email was sent
        assert len(mail.outbox) == 1
        assert "reguser@example.com" in mail.outbox[0].to
        assert "Verify your Portfolio Manager email address" in mail.outbox[0].subject
        assert "/verify-email?token=" in mail.outbox[0].body

    def test_verify_with_valid_token(self, api_client, unverified_user):
        """Submitting a valid token verifies the user account."""
        token = EmailVerificationService.generate_token(unverified_user)
        response = api_client.post('/api/v1/auth/verify-email/', {"token": token}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "verified"

        unverified_user.refresh_from_db()
        assert unverified_user.is_email_verified is True
        assert unverified_user.email_verified_at is not None

    def test_verify_with_expired_token(self, api_client, unverified_user):
        """Tokens past EMAIL_VERIFICATION_TIMEOUT are rejected with expired code."""
        import time
        current_time = time.time()
        with mock.patch("time.time", return_value=current_time):
            token = EmailVerificationService.generate_token(unverified_user)

        # Fast forward time by 40 minutes (2400 seconds; timeout is 1800s)
        with mock.patch("time.time", return_value=current_time + 2400):
            response = api_client.post('/api/v1/auth/verify-email/', {"token": token}, format='json')
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.json()["code"] == "expired"

            unverified_user.refresh_from_db()
            assert unverified_user.is_email_verified is False

    def test_verify_with_tampered_token(self, api_client, unverified_user):
        """Altered token signatures are rejected with invalid code."""
        token = EmailVerificationService.generate_token(unverified_user)
        tampered_token = token + "xyz123"
        response = api_client.post('/api/v1/auth/verify-email/', {"token": tampered_token}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["code"] == "invalid"

    def test_verify_already_verified_user_is_idempotent(self, api_client, verified_user):
        """Re-verifying an already verified user returns status: already_verified safely."""
        token = EmailVerificationService.generate_token(verified_user)
        response = api_client.post('/api/v1/auth/verify-email/', {"token": token}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "already_verified"

    def test_verify_with_token_for_changed_email(self, api_client, unverified_user):
        """If user changes email after token generation, old token is invalid."""
        token = EmailVerificationService.generate_token(unverified_user)
        unverified_user.email = "newemail@example.com"
        unverified_user.save()

        response = api_client.post('/api/v1/auth/verify-email/', {"token": token}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["code"] == "invalid"

    def test_resend_verification_email(self, api_client, unverified_user):
        """Resend sends a fresh email to an unverified user."""
        mail.outbox.clear()
        response = api_client.post('/api/v1/auth/resend-verification/', {"email": unverified_user.email}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1
        assert unverified_user.email in mail.outbox[0].to

    def test_resend_verification_generic_response_for_nonexistent_email(self, api_client):
        """Resending for nonexistent email returns 200 without leaking user existence."""
        mail.outbox.clear()
        response = api_client.post('/api/v1/auth/resend-verification/', {"email": "nobody@example.com"}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 0

    def test_resend_verification_rate_limiting(self, api_client, unverified_user):
        """Resend endpoint allows up to 3 requests per hour, then rejects with 429."""
        for _ in range(3):
            res = api_client.post('/api/v1/auth/resend-verification/', {"email": unverified_user.email}, format='json')
            assert res.status_code == status.HTTP_200_OK

        # 4th request must be rate limited
        res = api_client.post('/api/v1/auth/resend-verification/', {"email": unverified_user.email}, format='json')
        assert res.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert res.json()["code"] == "rate_limited"
