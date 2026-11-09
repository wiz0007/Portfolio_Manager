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
def test_user(db):
    return User.objects.create_user(
        email='existing@example.com',
        password='ValidPassword123!',
        full_name='Existing User'
    )

@pytest.mark.django_db
class TestAuthAPI:
    """API integration tests for authentication endpoints."""

    def test_csrf_cookie_endpoint(self, api_client):
        url = reverse('users_api_v1:auth-csrf')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'csrfToken' in response.data
        assert 'detail' in response.data

    def test_user_registration_success(self, api_client):
        url = reverse('users_api_v1:auth-register')
        payload = {
            'full_name': 'New Registered User',
            'email': 'newuser@example.com',
            'password': 'SecurePassword123!',
            'password_confirmation': 'SecurePassword123!',
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['message'] == 'User registered successfully.'
        assert response.data['user']['email'] == 'newuser@example.com'
        assert response.data['user']['full_name'] == 'New Registered User'
        assert 'password' not in response.data['user']

        # Verify user is created in database
        assert User.objects.filter(email='newuser@example.com').exists()

        # Session should be established
        me_url = reverse('users_api_v1:auth-me')
        me_response = api_client.get(me_url)
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.data['email'] == 'newuser@example.com'

    def test_user_registration_duplicate_email_rejected(self, api_client, test_user):
        url = reverse('users_api_v1:auth-register')
        payload = {
            'full_name': 'Duplicate User',
            'email': test_user.email,
            'password': 'Password123!',
            'password_confirmation': 'Password123!',
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_user_registration_password_mismatch_rejected(self, api_client):
        url = reverse('users_api_v1:auth-register')
        payload = {
            'full_name': 'Mismatch User',
            'email': 'mismatch@example.com',
            'password': 'Password123!',
            'password_confirmation': 'DifferentPassword123!',
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirmation' in response.data

    def test_user_registration_weak_password_rejected(self, api_client):
        url = reverse('users_api_v1:auth-register')
        payload = {
            'full_name': 'Weak User',
            'email': 'weak@example.com',
            'password': '123',  # Less than 8 chars
            'password_confirmation': '123',
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_user_registration_invalid_email_rejected(self, api_client):
        url = reverse('users_api_v1:auth-register')
        payload = {
            'full_name': 'Bad Email User',
            'email': 'not-an-email',
            'password': 'ValidPassword123!',
            'password_confirmation': 'ValidPassword123!',
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_login_success(self, api_client, test_user):
        url = reverse('users_api_v1:auth-login')
        payload = {
            'email': test_user.email,
            'password': 'ValidPassword123!',
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Login successful.'
        assert response.data['user']['email'] == test_user.email

        # Subsequent requests are authenticated via session
        me_url = reverse('users_api_v1:auth-me')
        me_response = api_client.get(me_url)
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.data['id'] == str(test_user.id)

    def test_login_invalid_password_rejected(self, api_client, test_user):
        url = reverse('users_api_v1:auth-login')
        payload = {
            'email': test_user.email,
            'password': 'IncorrectPassword!',
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detail' in response.data
        detail = response.data['detail']
        msg = detail[0] if isinstance(detail, list) else detail
        assert str(msg) == 'Invalid email or password.'

    def test_login_nonexistent_email_rejected(self, api_client):
        url = reverse('users_api_v1:auth-login')
        payload = {
            'email': 'doesnotexist@example.com',
            'password': 'SomePassword123!',
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detail' in response.data
        detail = response.data['detail']
        msg = detail[0] if isinstance(detail, list) else detail
        assert str(msg) == 'Invalid email or password.'

    def test_login_inactive_user_rejected(self, api_client):
        inactive_user = User.objects.create_user(
            email='inactive@example.com',
            password='ValidPassword123!',
            full_name='Inactive User',
            is_active=False
        )
        url = reverse('users_api_v1:auth-login')
        payload = {
            'email': inactive_user.email,
            'password': 'ValidPassword123!',
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        detail = response.data['detail']
        msg = detail[0] if isinstance(detail, list) else detail
        assert str(msg) == 'This account is inactive.'

    def test_current_user_unauthenticated_returns_401(self, api_client):
        url = reverse('users_api_v1:auth-me')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_invalidates_session(self, api_client, test_user):
        # First log in
        login_url = reverse('users_api_v1:auth-login')
        api_client.post(login_url, {'email': test_user.email, 'password': 'ValidPassword123!'}, format='json')

        # Check authenticated
        me_url = reverse('users_api_v1:auth-me')
        assert api_client.get(me_url).status_code == status.HTTP_200_OK

        # Call logout
        logout_url = reverse('users_api_v1:auth-logout')
        logout_response = api_client.post(logout_url)
        assert logout_response.status_code == status.HTTP_200_OK

        # Verify subsequent request is 401 Unauthorized
        after_logout_response = api_client.get(me_url)
        assert after_logout_response.status_code == status.HTTP_401_UNAUTHORIZED
