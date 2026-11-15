import pytest
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import create_test_portfolio, create_test_user


@pytest.fixture
def user(db):
    return create_test_user(email="contract_user@example.com")


@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.mark.django_db
class TestApiSchemaContracts:
    """
    Contract tests validating expected request payload acceptance,
    required response schema keys, data types, and status codes.
    """

    def test_health_check_contract(self):
        c = APIClient()
        res = c.get('/api/v1/health/')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data.get("status") == "healthy"
        assert data.get("database") == "connected"

    def test_auth_me_contract(self, client, user):
        res = client.get('/api/v1/auth/me/')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        required_fields = ["id", "email", "full_name", "is_email_verified", "date_joined"]
        for f in required_fields:
            assert f in data, f"Missing expected field '{f}' in /api/v1/auth/me/ contract"
        assert "password" not in data

    def test_portfolio_contract(self, client):
        # Create
        res = client.post(
            '/api/v1/portfolios/',
            {"name": "Contract Test Portfolio", "base_currency": "INR", "description": "Contract check"},
            format='json',
        )
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        for f in ["id", "name", "description", "base_currency", "created_at", "updated_at"]:
            assert f in data

        port_id = data["id"]

        # List
        list_res = client.get('/api/v1/portfolios/')
        assert list_res.status_code == status.HTTP_200_OK
        assert isinstance(list_res.json(), list)

        # Retrieve
        get_res = client.get(f'/api/v1/portfolios/{port_id}/')
        assert get_res.status_code == status.HTTP_200_OK
        assert get_res.json()["id"] == port_id

        # Delete
        del_res = client.delete(f'/api/v1/portfolios/{port_id}/')
        assert del_res.status_code == status.HTTP_204_NO_CONTENT

    def test_investment_contract(self, client, user):
        port = create_test_portfolio(user=user, name="Contract Holdings Port")

        # Create
        payload = {
            "category": "equity",
            "asset_type": "listed_stock",
            "display_name": "Contract Stock",
            "currency": "INR",
            "details": {
                "company_name": "Contract Corp",
                "symbol": "CC",
                "quantity": 10,
                "average_buy_price": 500.00,
            },
        }
        create_res = client.post(f'/api/v1/portfolios/{port.id}/investments/', payload, format='json')
        assert create_res.status_code == status.HTTP_201_CREATED
        data = create_res.json()
        required_inv_fields = [
            "id", "portfolio", "category", "asset_type", "display_name",
            "currency", "is_active", "valuation_method", "initial_value",
            "current_value", "details", "transactions", "valuations",
            "created_at", "updated_at",
        ]
        for f in required_inv_fields:
            assert f in data, f"Missing field '{f}' in investment detail contract"

        assert isinstance(data["details"], dict)
        assert isinstance(data["transactions"], list)
        assert isinstance(data["valuations"], list)
