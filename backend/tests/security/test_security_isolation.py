import uuid

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models import Investment
from apps.portfolios.models import Portfolio
from tests.factories import create_test_investment, create_test_portfolio, create_test_user


@pytest.fixture
def user_alpha(db):
    return create_test_user(email="alpha@security.test", full_name="Alpha Investor")


@pytest.fixture
def user_bravo(db):
    return create_test_user(email="bravo@security.test", full_name="Bravo Investor")


@pytest.fixture
def client_alpha(user_alpha):
    c = APIClient()
    c.force_authenticate(user=user_alpha)
    return c


@pytest.fixture
def client_bravo(user_bravo):
    c = APIClient()
    c.force_authenticate(user=user_bravo)
    return c


@pytest.fixture
def unauthenticated_client():
    return APIClient()


@pytest.mark.django_db
class TestSecurityIsolationAndIDOR:
    """
    Centralized security tests verifying authentication barriers,
    IDOR defenses, cross-user isolation, and non-disclosure guarantees.
    """

    def test_unauthenticated_access_strictly_rejected(self, unauthenticated_client):
        """All protected routes reject anonymous access with HTTP 401."""
        random_id = uuid.uuid4()
        endpoints = [
            ('GET', '/api/v1/auth/me/'),
            ('GET', '/api/v1/users/me/'),
            ('GET', '/api/v1/portfolios/'),
            ('POST', '/api/v1/portfolios/'),
            ('GET', f'/api/v1/portfolios/{random_id}/'),
            ('PATCH', f'/api/v1/portfolios/{random_id}/'),
            ('DELETE', f'/api/v1/portfolios/{random_id}/'),
            ('GET', f'/api/v1/portfolios/{random_id}/investments/'),
            ('POST', f'/api/v1/portfolios/{random_id}/investments/'),
            ('GET', f'/api/v1/portfolios/{random_id}/investments/{random_id}/'),
            ('PATCH', f'/api/v1/portfolios/{random_id}/investments/{random_id}/'),
            ('DELETE', f'/api/v1/portfolios/{random_id}/investments/{random_id}/'),
            ('GET', '/api/v1/dashboard/overview/'),
        ]

        for method, url in endpoints:
            if method == 'GET':
                res = unauthenticated_client.get(url)
            elif method == 'POST':
                res = unauthenticated_client.post(url, {}, format='json')
            elif method == 'PATCH':
                res = unauthenticated_client.patch(url, {}, format='json')
            elif method == 'DELETE':
                res = unauthenticated_client.delete(url)
            assert res.status_code == status.HTTP_401_UNAUTHORIZED, f"Failed 401 check on {method} {url}"

    def test_cross_user_portfolio_idor_protection(self, client_alpha, client_bravo, user_alpha):
        """User Bravo cannot read, modify, or delete User Alpha's portfolio."""
        port_alpha = create_test_portfolio(user=user_alpha, name="Alpha Private Wealth")

        # 1. GET returns 404
        assert client_bravo.get(f'/api/v1/portfolios/{port_alpha.id}/').status_code == status.HTTP_404_NOT_FOUND

        # 2. PATCH returns 404
        res = client_bravo.patch(
            f'/api/v1/portfolios/{port_alpha.id}/',
            {"name": "Compromised Name"},
            format='json',
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND
        port_alpha.refresh_from_db()
        assert port_alpha.name == "Alpha Private Wealth"

        # 3. DELETE returns 404
        assert client_bravo.delete(f'/api/v1/portfolios/{port_alpha.id}/').status_code == status.HTTP_404_NOT_FOUND
        assert Portfolio.objects.filter(id=port_alpha.id).exists()

    def test_cross_user_investment_idor_protection(self, client_alpha, client_bravo, user_alpha):
        """User Bravo cannot read, mutate, or delete User Alpha's holdings."""
        port_alpha = create_test_portfolio(user=user_alpha, name="Alpha Holdings")
        inv_alpha = create_test_investment(portfolio=port_alpha, user=user_alpha, display_name="Alpha Secret Stock")

        # 1. Listing Alpha's portfolio returns 404 to Bravo
        assert client_bravo.get(f'/api/v1/portfolios/{port_alpha.id}/investments/').status_code == status.HTTP_404_NOT_FOUND

        # 2. Detail of Alpha's investment returns 404 to Bravo
        assert client_bravo.get(f'/api/v1/portfolios/{port_alpha.id}/investments/{inv_alpha.id}/').status_code == status.HTTP_404_NOT_FOUND

        # 3. Post into Alpha's portfolio returns 404 to Bravo
        res = client_bravo.post(
            f'/api/v1/portfolios/{port_alpha.id}/investments/',
            {"category": "cash", "asset_type": "savings_account", "details": {"bank_name": "Bad", "current_balance": 100}},
            format='json',
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND

        # 4. Patch Alpha's investment returns 404 to Bravo
        res = client_bravo.patch(
            f'/api/v1/portfolios/{port_alpha.id}/investments/{inv_alpha.id}/',
            {"display_name": "Tampered"},
            format='json',
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND

        # 5. Delete Alpha's investment returns 404 to Bravo
        res = client_bravo.delete(f'/api/v1/portfolios/{port_alpha.id}/investments/{inv_alpha.id}/')
        assert res.status_code == status.HTTP_404_NOT_FOUND
        assert Investment.objects.filter(id=inv_alpha.id).exists()

    def test_random_uuid_manipulation_returns_404(self, client_alpha):
        """Random non-existent UUIDs return 404 without server exceptions."""
        non_existent = uuid.uuid4()
        assert client_alpha.get(f'/api/v1/portfolios/{non_existent}/').status_code == status.HTTP_404_NOT_FOUND
        assert client_alpha.get(f'/api/v1/portfolios/{non_existent}/investments/').status_code == status.HTTP_404_NOT_FOUND
