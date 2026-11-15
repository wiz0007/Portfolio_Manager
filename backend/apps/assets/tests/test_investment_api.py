import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models import (
    Investment,
    InvestmentTransaction,
    InvestmentValuation,
)
from apps.portfolios.models import Portfolio
from apps.users.models import User


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        email="investor_a@example.com",
        password="ValidPassword123!",
        full_name="Investor Alpha",
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        email="investor_b@example.com",
        password="ValidPassword123!",
        full_name="Investor Beta",
    )


@pytest.fixture
def portfolio_a(user_a):
    return Portfolio.objects.create(
        user=user_a,
        name="Alpha Portfolio",
        base_currency="INR",
    )


@pytest.fixture
def portfolio_b(user_b):
    return Portfolio.objects.create(
        user=user_b,
        name="Beta Portfolio",
        base_currency="INR",
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
class TestInvestmentAPI:

    def test_unauthenticated_requests_rejected(self, unauthenticated_client, portfolio_a):
        res = unauthenticated_client.get(f'/api/v1/portfolios/{portfolio_a.id}/investments/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        res = unauthenticated_client.post(
            f'/api/v1/portfolios/{portfolio_a.id}/investments/',
            {"category": "cash", "asset_type": "savings_account"},
            format='json',
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_savings_account_investment(self, client_a, user_a, portfolio_a):
        payload = {
            "category": "cash",
            "asset_type": "savings_account",
            "display_name": "Emergency SBI Account",
            "currency": "INR",
            "valuation_method": "BANK_BALANCE",
            "details": {
                "bank_name": "State Bank of India",
                "account_nickname": "Emergency SBI Account",
                "account_type": "SAVINGS",
                "masked_account_number": "XX4812",
                "current_balance": 150000.00,
                "balance_date": "2026-11-01",
                "interest_rate_pct": 3.0,
                "interest_credit_frequency": "QUARTERLY",
            },
        }

        res = client_a.post(
            f'/api/v1/portfolios/{portfolio_a.id}/investments/',
            payload,
            format='json',
        )
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["display_name"] == "Emergency SBI Account"
        assert data["category"] == "cash"
        assert data["asset_type"] == "savings_account"
        assert data["valuation_method"] == "BANK_BALANCE"
        assert float(data["current_value"]) == 150000.00
        assert data["details"]["bank_name"] == "State Bank of India"
        assert len(data["transactions"]) == 1
        assert float(data["transactions"][0]["amount"]) == 150000.00

        # DB assertion
        inv = Investment.objects.get(id=data["id"])
        assert inv.portfolio == portfolio_a
        assert inv.user == user_a
        assert inv.cash_detail.bank_name == "State Bank of India"
        assert InvestmentTransaction.objects.filter(investment=inv).exists()

    def test_create_agricultural_land_investment(self, client_a, user_a, portfolio_a):
        payload = {
            "category": "real_estate",
            "asset_type": "land_plot",
            "display_name": "Dehradun Mango Orchard",
            "currency": "INR",
            "details": {
                "property_name": "Dehradun Mango Orchard",
                "property_type": "AGRICULTURAL",
                "land_classification": "AGRICULTURAL",
                "state": "Uttarakhand",
                "district": "Dehradun",
                "tehsil": "Vikas Nagar",
                "village": "Sahaspur",
                "survey_or_plot_number": "Khasra 412/1",
                "land_area": 2.5,
                "area_unit": "ACRE",
                "ownership_percentage": 100,
                "acquisition_date": "2026-05-10",
                "purchase_price": 5000000.00,
                "stamp_duty": 250000.00,
                "registration_charges": 100000.00,
                "other_acquisition_costs": 50000.00,
                "estimated_current_value": 5800000.00,
                "valuation_date": "2026-11-01",
                "valuation_source": "Circle Rate Evaluation",
            },
        }

        res = client_a.post(
            f'/api/v1/portfolios/{portfolio_a.id}/investments/',
            payload,
            format='json',
        )
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["display_name"] == "Dehradun Mango Orchard"
        assert data["category"] == "real_estate"
        assert data["asset_type"] == "land_plot"
        assert float(data["initial_value"]) == 5400000.00  # 50L + 2.5L + 1L + 0.5L
        assert float(data["current_value"]) == 5800000.00
        assert data["details"]["district"] == "Dehradun"
        assert data["details"]["state"] == "Uttarakhand"
        assert len(data["valuations"]) == 1

        # Check DB
        inv = Investment.objects.get(id=data["id"])
        assert inv.real_estate_detail.survey_or_plot_number == "Khasra 412/1"
        assert InvestmentValuation.objects.filter(investment=inv).exists()

    def test_create_listed_stock_investment(self, client_a, user_a, portfolio_a):
        payload = {
            "category": "equity",
            "asset_type": "listed_stock",
            "currency": "INR",
            "details": {
                "company_name": "Tata Consultancy Services",
                "symbol": "TCS",
                "exchange": "NSE",
                "quantity": 50,
                "average_buy_price": 4000.00,
                "purchase_date": "2026-10-15",
                "brokerage_fees": 20.00,
                "statutory_taxes": 35.00,
            },
        }

        res = client_a.post(
            f'/api/v1/portfolios/{portfolio_a.id}/investments/',
            payload,
            format='json',
        )
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert "TCS" in data["display_name"]
        assert float(data["initial_value"]) == 200055.00  # (50 * 4000) + 20 + 35
        assert float(data["current_value"]) == 200000.00
        assert data["details"]["symbol"] == "TCS"

    def test_cross_user_isolation_returns_404(self, client_b, portfolio_a):
        """User B cannot create or view investments in User A's portfolio."""
        # List investments in user A's portfolio
        res = client_b.get(f'/api/v1/portfolios/{portfolio_a.id}/investments/')
        assert res.status_code == status.HTTP_404_NOT_FOUND

        # Post investment into user A's portfolio
        payload = {
            "category": "cash",
            "asset_type": "savings_account",
            "details": {"bank_name": "HDFC", "current_balance": 1000},
        }
        res = client_b.post(
            f'/api/v1/portfolios/{portfolio_a.id}/investments/',
            payload,
            format='json',
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_list_and_filter_investments(self, client_a, portfolio_a):
        # Create cash
        client_a.post(
            f'/api/v1/portfolios/{portfolio_a.id}/investments/',
            {
                "category": "cash",
                "asset_type": "savings_account",
                "display_name": "Account 1",
                "details": {"bank_name": "HDFC", "current_balance": 1000},
            },
            format='json',
        )
        # Create equity
        client_a.post(
            f'/api/v1/portfolios/{portfolio_a.id}/investments/',
            {
                "category": "equity",
                "asset_type": "listed_stock",
                "display_name": "Stock 1",
                "details": {"company_name": "Infosys", "symbol": "INFY", "quantity": 10, "average_buy_price": 1500},
            },
            format='json',
        )

        # List all
        res = client_a.get(f'/api/v1/portfolios/{portfolio_a.id}/investments/')
        assert res.status_code == status.HTTP_200_OK
        assert len(res.json()) == 2

        # Filter by category
        res = client_a.get(f'/api/v1/portfolios/{portfolio_a.id}/investments/?category=equity')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert len(data) == 1
        assert data[0]["category"] == "equity"

    def test_retrieve_and_patch_investment(self, client_a, portfolio_a):
        # Create investment
        create_res = client_a.post(
            f'/api/v1/portfolios/{portfolio_a.id}/investments/',
            {
                "category": "cash",
                "asset_type": "savings_account",
                "display_name": "My Primary Bank",
                "details": {"bank_name": "ICICI Bank", "current_balance": 25000},
            },
            format='json',
        )
        inv_id = create_res.json()["id"]

        # Retrieve
        get_res = client_a.get(f'/api/v1/portfolios/{portfolio_a.id}/investments/{inv_id}/')
        assert get_res.status_code == status.HTTP_200_OK
        assert get_res.json()["display_name"] == "My Primary Bank"
        assert get_res.json()["details"]["bank_name"] == "ICICI Bank"

        # Patch display name and notes
        patch_res = client_a.patch(
            f'/api/v1/portfolios/{portfolio_a.id}/investments/{inv_id}/',
            {"display_name": "ICICI Salary Account", "notes": "Primary payroll account"},
            format='json',
        )
        assert patch_res.status_code == status.HTTP_200_OK
        assert patch_res.json()["display_name"] == "ICICI Salary Account"
        assert patch_res.json()["notes"] == "Primary payroll account"

    def test_delete_investment(self, client_a, portfolio_a):
        create_res = client_a.post(
            f'/api/v1/portfolios/{portfolio_a.id}/investments/',
            {
                "category": "cash",
                "asset_type": "savings_account",
                "details": {"bank_name": "Axis Bank", "current_balance": 5000},
            },
            format='json',
        )
        inv_id = create_res.json()["id"]

        del_res = client_a.delete(f'/api/v1/portfolios/{portfolio_a.id}/investments/{inv_id}/')
        assert del_res.status_code == status.HTTP_204_NO_CONTENT

        # Confirm 404 now
        get_res = client_a.get(f'/api/v1/portfolios/{portfolio_a.id}/investments/{inv_id}/')
        assert get_res.status_code == status.HTTP_404_NOT_FOUND
        assert not Investment.objects.filter(id=inv_id).exists()
