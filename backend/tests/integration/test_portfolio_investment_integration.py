import pytest
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import create_test_user


@pytest.fixture
def user(db):
    return create_test_user(email="integ_user@example.com", full_name="Integration User")


@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.mark.django_db
class TestPortfolioInvestmentIntegration:
    """
    Integration tests verifying relationships and lifecycle coordination
    between Users, Portfolios, Investments, and Dashboard services.
    """

    def test_complete_portfolio_investment_lifecycle(self, client, user):
        # 1. Create Portfolio
        port_res = client.post(
            '/api/v1/portfolios/',
            {"name": "Comprehensive Retirement Portfolio", "base_currency": "INR"},
            format='json',
        )
        assert port_res.status_code == status.HTTP_201_CREATED
        portfolio_id = port_res.json()["id"]

        # 2. Add Fixed Deposit
        fd_res = client.post(
            f'/api/v1/portfolios/{portfolio_id}/investments/',
            {
                "category": "fixed_income",
                "asset_type": "fixed_deposit",
                "display_name": "SBI 5-Year FD",
                "details": {
                    "institution_name": "SBI",
                    "principal_amount": 200000.00,
                    "tenure_value": 5,
                    "tenure_unit": "YEARS",
                    "interest_rate_pct": 7.0,
                },
            },
            format='json',
        )
        assert fd_res.status_code == status.HTTP_201_CREATED

        # 3. Add Agricultural Land Plot
        land_res = client.post(
            f'/api/v1/portfolios/{portfolio_id}/investments/',
            {
                "category": "real_estate",
                "asset_type": "land_plot",
                "display_name": "Dehradun Farm Plot",
                "details": {
                    "property_type": "AGRICULTURAL",
                    "state": "Uttarakhand",
                    "district": "Dehradun",
                    "survey_or_plot_number": "Khasra 44",
                    "land_area": 1.5,
                    "area_unit": "ACRE",
                    "purchase_price": 3000000.00,
                    "acquisition_date": "2026-04-10",
                    "estimated_current_value": 3500000.00,
                    "valuation_date": "2026-11-01",
                },
            },
            format='json',
        )
        assert land_res.status_code == status.HTTP_201_CREATED

        # 4. Add Listed Stock
        stock_res = client.post(
            f'/api/v1/portfolios/{portfolio_id}/investments/',
            {
                "category": "equity",
                "asset_type": "listed_stock",
                "details": {
                    "company_name": "Reliance Industries",
                    "symbol": "RELIANCE",
                    "quantity": 40,
                    "average_buy_price": 2500.00,
                },
            },
            format='json',
        )
        assert stock_res.status_code == status.HTTP_201_CREATED

        # 5. List Portfolio Holdings
        list_res = client.get(f'/api/v1/portfolios/{portfolio_id}/investments/')
        assert list_res.status_code == status.HTTP_200_OK
        holdings = list_res.json()
        assert len(holdings) == 3

        # Verify category grouping in portfolio
        categories = {h["category"] for h in holdings}
        assert categories == {"fixed_income", "real_estate", "equity"}

        # 6. Verify Dashboard overview reflects created portfolio
        dash_res = client.get('/api/v1/dashboard/overview/')
        assert dash_res.status_code == status.HTTP_200_OK
        dash_data = dash_res.json()
        assert dash_data["portfolio_count"] >= 1
        assert "recent_portfolios" in dash_data

        # 7. Delete one holding and confirm portfolio listing shrinks
        stock_id = stock_res.json()["id"]
        del_res = client.delete(f'/api/v1/portfolios/{portfolio_id}/investments/{stock_id}/')
        assert del_res.status_code == status.HTTP_204_NO_CONTENT

        after_del_res = client.get(f'/api/v1/portfolios/{portfolio_id}/investments/')
        assert len(after_del_res.json()) == 2
        assert not any(h["id"] == stock_id for h in after_del_res.json())
