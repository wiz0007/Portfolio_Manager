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
def user_a():
    return User.objects.create_user(
        email='user_a@example.com',
        password='Password123!',
        full_name='Alpha User',
    )


@pytest.fixture
def user_b():
    return User.objects.create_user(
        email='user_b@example.com',
        password='Password123!',
        full_name='Beta User',
    )


@pytest.mark.django_db
class TestDashboardOverviewAPI:
    def test_unauthenticated_overview_rejected(self, api_client):
        url = reverse('dashboard_api_v1:dashboard-overview')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_receives_valid_overview(self, api_client, user_a):
        url = reverse('dashboard_api_v1:dashboard-overview')
        api_client.force_authenticate(user=user_a)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert 'user' in data
        assert data['user']['id'] == str(user_a.id)
        assert data['user']['full_name'] == 'Alpha User'
        assert data['user']['email'] == 'user_a@example.com'
        assert data['portfolio_count'] == 0
        assert data['recent_portfolios'] == []

    def test_dashboard_user_isolation(self, api_client, user_a, user_b):
        url = reverse('dashboard_api_v1:dashboard-overview')

        api_client.force_authenticate(user=user_a)
        res_a = api_client.get(url)
        assert res_a.status_code == status.HTTP_200_OK
        assert res_a.data['user']['email'] == user_a.email

        api_client.force_authenticate(user=user_b)
        res_b = api_client.get(url)
        assert res_b.status_code == status.HTTP_200_OK
        assert res_b.data['user']['email'] == user_b.email
        assert res_b.data['user']['email'] != res_a.data['user']['email']
