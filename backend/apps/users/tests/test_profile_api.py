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
def user():
    return User.objects.create_user(
        email='profiletest@example.com',
        password='StrongPassword123!',
        full_name='Original Name',
    )


@pytest.mark.django_db
class TestUserProfileAPI:
    def test_unauthenticated_cannot_access_profile(self, api_client):
        response = api_client.get(reverse('users_profile_api_v1:user-me'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_cannot_patch_profile(self, api_client):
        response = api_client.patch(
            reverse('users_profile_api_v1:user-me'),
            {'full_name': 'New Name'},
            format='json',
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_can_retrieve_profile(self, api_client, user):
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse('users_profile_api_v1:user-me'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email
        assert response.data['full_name'] == 'Original Name'

    def test_authenticated_user_can_update_full_name(self, api_client, user):
        api_client.force_authenticate(user=user)
        response = api_client.patch(
            reverse('users_profile_api_v1:user-me'),
            {'full_name': 'Updated Name'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['full_name'] == 'Updated Name'
        user.refresh_from_db()
        assert user.full_name == 'Updated Name'

    def test_update_profile_validation_rejects_blank(self, api_client, user):
        api_client.force_authenticate(user=user)
        response = api_client.patch(
            reverse('users_profile_api_v1:user-me'),
            {'full_name': '   '},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.full_name == 'Original Name'

    def test_update_profile_validation_rejects_short_name(self, api_client, user):
        api_client.force_authenticate(user=user)
        response = api_client.patch(
            reverse('users_profile_api_v1:user-me'),
            {'full_name': 'A'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_modify_sensitive_fields_via_profile_patch(self, api_client, user):
        api_client.force_authenticate(user=user)
        response = api_client.patch(
            reverse('users_profile_api_v1:user-me'),
            {
                'full_name': 'Legit Name',
                'email': 'hacked@example.com',
                'is_staff': True,
                'is_superuser': True,
            },
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.full_name == 'Legit Name'
        assert user.email == 'profiletest@example.com'
        assert user.is_staff is False
        assert user.is_superuser is False
