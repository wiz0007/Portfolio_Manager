import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def valid_google_payload():
    return {
        "iss": "https://accounts.google.com",
        "sub": "google-user-123456",
        "aud": "361966023924-7q9t65dlt4ogcs0kisal3csibp52ega0.apps.googleusercontent.com",
        "email": "alex.investor@example.com",
        "email_verified": True,
        "name": "Alex Investor",
        "given_name": "Alex",
        "family_name": "Investor",
        "picture": "https://lh3.googleusercontent.com/photo.jpg",
    }


def make_mock_urlopen_response(payload: dict, status_code: int = 200):
    content = json.dumps(payload).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.status = status_code
    mock_resp.read.return_value = content
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None
    return mock_resp


@pytest.mark.django_db
class TestGoogleAuthAPI:
    """API integration tests for Google OAuth authentication."""

    def test_google_auth_new_user_registration_success(self, api_client, valid_google_payload, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = valid_google_payload["aud"]
        url = reverse("users_api_v1:auth-google")

        with patch("urllib.request.urlopen", return_value=make_mock_urlopen_response(valid_google_payload)):
            response = api_client.post(url, {"credential": "valid.google.id.token"}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["message"] == "Account created and authenticated via Google successfully."
        assert response.data["user"]["email"] == "alex.investor@example.com"
        assert response.data["user"]["full_name"] == "Alex Investor"
        assert response.data["user"]["is_email_verified"] is True

        user = User.objects.get(email="alex.investor@example.com")
        assert user.has_usable_password() is False
        assert user.is_email_verified is True
        assert user.is_active is True

        # Session cookie verified
        me_url = reverse("users_api_v1:auth-me")
        me_resp = api_client.get(me_url)
        assert me_resp.status_code == status.HTTP_200_OK
        assert me_resp.data["email"] == "alex.investor@example.com"

    def test_google_auth_existing_user_login_success(self, api_client, valid_google_payload, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = valid_google_payload["aud"]
        existing_user = User.objects.create_user(
            email=valid_google_payload["email"],
            password="OriginalPassword123!",
            full_name="Alex Existing",
        )
        assert existing_user.email_verified_at is None

        url = reverse("users_api_v1:auth-google")
        with patch("urllib.request.urlopen", return_value=make_mock_urlopen_response(valid_google_payload)):
            response = api_client.post(url, {"credential": "valid.google.id.token"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Google authentication successful."
        assert response.data["user"]["email"] == valid_google_payload["email"]

        existing_user.refresh_from_db()
        assert existing_user.is_email_verified is True
        assert existing_user.check_password("OriginalPassword123!") is True

    def test_google_auth_with_id_token_parameter_alias(self, api_client, valid_google_payload, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = valid_google_payload["aud"]
        url = reverse("users_api_v1:auth-google")

        with patch("urllib.request.urlopen", return_value=make_mock_urlopen_response(valid_google_payload)):
            response = api_client.post(url, {"id_token": "valid.google.id.token"}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"]["email"] == valid_google_payload["email"]

    def test_google_auth_missing_credentials_rejected(self, api_client):
        url = reverse("users_api_v1:auth-google")
        response = api_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "credential" in response.data

    def test_google_auth_empty_token_rejected(self, api_client):
        url = reverse("users_api_v1:auth-google")
        response = api_client.post(url, {"credential": "   "}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_google_auth_inactive_user_rejected(self, api_client, valid_google_payload, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = valid_google_payload["aud"]
        User.objects.create_user(
            email=valid_google_payload["email"],
            password="OriginalPassword123!",
            full_name="Inactive User",
            is_active=False,
        )

        url = reverse("users_api_v1:auth-google")
        with patch("urllib.request.urlopen", return_value=make_mock_urlopen_response(valid_google_payload)):
            response = api_client.post(url, {"credential": "valid.token"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "This account is inactive." in str(response.data)

    def test_google_auth_invalid_token_rejected(self, api_client):
        url = reverse("users_api_v1:auth-google")
        http_error = urllib.error.HTTPError(
            url="https://oauth2.googleapis.com/tokeninfo",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=io.BytesIO(b'{"error": "invalid_token"}'),
        )

        with patch("urllib.request.urlopen", side_effect=http_error):
            response = api_client.post(url, {"credential": "invalid.token"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "credential" in response.data
        assert "Invalid or expired Google token." in str(response.data["credential"])

    def test_google_auth_audience_mismatch_rejected(self, api_client, valid_google_payload, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = "different-client-id.apps.googleusercontent.com"
        url = reverse("users_api_v1:auth-google")

        with patch("urllib.request.urlopen", return_value=make_mock_urlopen_response(valid_google_payload)):
            response = api_client.post(url, {"credential": "valid.token"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "credential" in response.data
        assert "audience does not match" in str(response.data["credential"])

    def test_google_auth_untrusted_issuer_rejected(self, api_client, valid_google_payload, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = valid_google_payload["aud"]
        payload = dict(valid_google_payload)
        payload["iss"] = "https://evil.hacker.com"

        url = reverse("users_api_v1:auth-google")
        with patch("urllib.request.urlopen", return_value=make_mock_urlopen_response(payload)):
            response = api_client.post(url, {"credential": "token.with.fake.issuer"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "credential" in response.data
        assert "Token was not issued by Google." in str(response.data["credential"])

    def test_google_auth_unverified_google_email_rejected(self, api_client, valid_google_payload, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = valid_google_payload["aud"]
        payload = dict(valid_google_payload)
        payload["email_verified"] = False

        url = reverse("users_api_v1:auth-google")
        with patch("urllib.request.urlopen", return_value=make_mock_urlopen_response(payload)):
            response = api_client.post(url, {"credential": "unverified.token"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Your Google email address is not verified." in str(response.data)

    def test_google_auth_network_timeout_returns_service_error(self, api_client):
        url = reverse("users_api_v1:auth-google")
        with patch("urllib.request.urlopen", side_effect=TimeoutError("Connection timed out")):
            response = api_client.post(url, {"credential": "token"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unable to verify token with Google service" in str(response.data)

    def test_google_auth_with_access_token_success(self, api_client, valid_google_payload, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = valid_google_payload["aud"]
        tokeninfo_payload = {
            "aud": valid_google_payload["aud"],
            "email": "oauth.user@example.com",
            "email_verified": "true",
            "sub": "google-sub-987654",
        }
        userinfo_payload = {
            "sub": "google-sub-987654",
            "name": "OAuth User",
            "email": "oauth.user@example.com",
            "email_verified": True,
        }

        url = reverse("users_api_v1:auth-google")
        mock_tokeninfo = make_mock_urlopen_response(tokeninfo_payload)
        mock_userinfo = make_mock_urlopen_response(userinfo_payload)

        with patch("urllib.request.urlopen", side_effect=[mock_tokeninfo, mock_userinfo]):
            response = api_client.post(url, {"access_token": "ya29.sample_oauth2_access_token"}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"]["email"] == "oauth.user@example.com"
        assert response.data["user"]["full_name"] == "OAuth User"
        assert User.objects.filter(email="oauth.user@example.com").exists()


