import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.portfolios.models import Portfolio
from apps.users.models import User


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        email="user_a@example.com",
        password="ValidPassword123!",
        full_name="User Alpha",
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        email="user_b@example.com",
        password="ValidPassword123!",
        full_name="User Beta",
    )


@pytest.fixture
def client_a(user_a):
    client = APIClient()
    client.force_authenticate(user=user_a)
    return client


@pytest.fixture
def client_b(user_b):
    client = APIClient()
    client.force_authenticate(user=user_b)
    return client


@pytest.fixture
def unauthenticated_client():
    return APIClient()


@pytest.mark.django_db
class TestPortfolioAPI:

    def test_unauthenticated_requests_rejected(self, unauthenticated_client):
        """Unauthenticated requests must receive 401 Unauthorized."""
        response = unauthenticated_client.get('/api/v1/portfolios/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = unauthenticated_client.post('/api/v1/portfolios/', {"name": "Test"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_portfolios_empty(self, client_a):
        """User with no portfolios receives an empty list."""
        response = client_a.get('/api/v1/portfolios/')
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_create_portfolio_with_defaults(self, client_a, user_a):
        """Creating a portfolio sets user ownership and defaults base_currency to INR."""
        payload = {
            "name": "Retirement Fund",
            "description": "Long term index fund allocations",
        }
        response = client_a.post('/api/v1/portfolios/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Retirement Fund"
        assert data["description"] == "Long term index fund allocations"
        assert data["base_currency"] == "INR"
        assert "id" in data
        assert "created_at" in data

        # Check DB
        portfolio = Portfolio.objects.get(id=data["id"])
        assert portfolio.user == user_a

    def test_create_portfolio_with_custom_currency(self, client_a, user_a):
        """Creating a portfolio with a supported custom currency succeeds."""
        payload = {
            "name": "US Tech Growth",
            "description": "NASDAQ & S&P500 holdings",
            "base_currency": "USD",
        }
        response = client_a.post('/api/v1/portfolios/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["base_currency"] == "USD"

    def test_create_portfolio_validation_errors(self, client_a):
        """Rejects empty name, oversized name, and unsupported currency."""
        # Blank name
        res = client_a.post('/api/v1/portfolios/', {"name": "   "}, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST

        # Oversized name (>100 chars)
        res = client_a.post('/api/v1/portfolios/', {"name": "A" * 101}, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST

        # Unsupported currency
        res = client_a.post('/api/v1/portfolios/', {"name": "Crypto", "base_currency": "BTC"}, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unsupported currency" in str(res.json())

    def test_retrieve_portfolio(self, client_a, user_a):
        """Owner can retrieve their own portfolio by UUID."""
        portfolio = Portfolio.objects.create(
            user=user_a,
            name="Tactical Trading",
            base_currency="EUR",
        )
        response = client_a.get(f'/api/v1/portfolios/{portfolio.id}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(portfolio.id)
        assert data["name"] == "Tactical Trading"
        assert data["base_currency"] == "EUR"

    def test_update_portfolio(self, client_a, user_a):
        """Owner can update portfolio attributes."""
        portfolio = Portfolio.objects.create(
            user=user_a,
            name="Initial Name",
            description="Initial Desc",
            base_currency="INR",
        )
        payload = {
            "name": "Updated Portfolio Name",
            "description": "Updated Description",
            "base_currency": "GBP",
        }
        response = client_a.patch(f'/api/v1/portfolios/{portfolio.id}/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Portfolio Name"
        assert data["description"] == "Updated Description"
        assert data["base_currency"] == "GBP"

        portfolio.refresh_from_db()
        assert portfolio.name == "Updated Portfolio Name"

    def test_delete_portfolio(self, client_a, user_a):
        """Owner can delete their portfolio."""
        portfolio = Portfolio.objects.create(
            user=user_a,
            name="To Be Deleted",
        )
        response = client_a.delete(f'/api/v1/portfolios/{portfolio.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Portfolio.objects.filter(id=portfolio.id).exists()

    def test_cross_user_isolation(self, client_a, client_b, user_a, user_b):
        """User B cannot see, retrieve, update, or delete User A's portfolio."""
        portfolio_a = Portfolio.objects.create(
            user=user_a,
            name="Alpha Confidential",
            base_currency="INR",
        )

        # User B listing must not contain User A's portfolio
        res = client_b.get('/api/v1/portfolios/')
        assert res.status_code == status.HTTP_200_OK
        assert res.json() == []

        # User B attempting to GET User A's portfolio receives 404
        res = client_b.get(f'/api/v1/portfolios/{portfolio_a.id}/')
        assert res.status_code == status.HTTP_404_NOT_FOUND

        # User B attempting to PATCH User A's portfolio receives 404
        res = client_b.patch(f'/api/v1/portfolios/{portfolio_a.id}/', {"name": "Hacked"}, format='json')
        assert res.status_code == status.HTTP_404_NOT_FOUND
        portfolio_a.refresh_from_db()
        assert portfolio_a.name == "Alpha Confidential"

        # User B attempting to DELETE User A's portfolio receives 404
        res = client_b.delete(f'/api/v1/portfolios/{portfolio_a.id}/')
        assert res.status_code == status.HTTP_404_NOT_FOUND
        assert Portfolio.objects.filter(id=portfolio_a.id).exists()

    def test_client_cannot_transfer_ownership(self, client_a, user_a, user_b):
        """Passing another user's ID during create/update cannot reassign ownership."""
        res = client_a.post('/api/v1/portfolios/', {
            "name": "Attempt Hijack",
            "user": str(user_b.id),
        }, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        portfolio = Portfolio.objects.get(id=res.json()["id"])
        assert portfolio.user == user_a
