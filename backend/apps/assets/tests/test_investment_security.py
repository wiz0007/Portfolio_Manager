from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models.investment import Investment
from apps.assets.models.valuations import InvestmentValuation
from apps.portfolios.models.portfolio import Portfolio
from apps.users.models.user import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        email="user_a@example.com",
        password="SecurePassword123!",
        full_name="User A",
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        email="user_b@example.com",
        password="SecurePassword123!",
        full_name="User B",
    )


@pytest.fixture
def portfolio_a(db, user_a):
    return Portfolio.objects.create(
        user=user_a,
        name="Portfolio A",
        base_currency="INR",
    )


@pytest.fixture
def portfolio_b(db, user_b):
    return Portfolio.objects.create(
        user=user_b,
        name="Portfolio B",
        base_currency="INR",
    )


@pytest.fixture
def investment_a(db, user_a, portfolio_a):
    from datetime import date

    from apps.assets.models import EquityDetail

    inv = Investment.objects.create(
        user=user_a,
        portfolio=portfolio_a,
        category="equity",
        asset_type="listed_stock",
        display_name="TCS Holding",
        currency="INR",
        initial_value=Decimal("35000.00"),
        current_value=Decimal("38000.00"),
        valuation_method="MARKET_PRICE",
    )
    EquityDetail.objects.create(
        investment=inv,
        company_name="Tata Consultancy Services",
        symbol="TCS",
        exchange="NSE",
        quantity=Decimal("10.0000"),
        average_buy_price=Decimal("3500.00"),
        purchase_date=date(2026, 1, 15),
    )
    return inv


@pytest.mark.django_db
class TestInvestmentSecurityHardening:
    """
    Workstream A security regression test suite.
    """

    def test_cross_user_investment_patch_rejected(self, api_client, user_b, portfolio_a, investment_a):
        """User B cannot PATCH or modify User A's investment."""
        api_client.force_authenticate(user=user_b)
        url = reverse(
            "assets_api_v1:portfolio-investment-detail",
            kwargs={"portfolio_id": portfolio_a.id, "id": investment_a.id},
        )
        response = api_client.patch(url, {"display_name": "Hacked Name"}, format="json")
        assert response.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN)
        investment_a.refresh_from_db()
        assert investment_a.display_name == "TCS Holding"

    def test_immutable_relationship_fields_rejected_on_patch(self, api_client, user_a, portfolio_a, investment_a, portfolio_b):
        """Attempting to reassign portfolio, id, or investment_id must raise 400 validation error."""
        api_client.force_authenticate(user=user_a)
        url = reverse(
            "assets_api_v1:portfolio-investment-detail",
            kwargs={"portfolio_id": portfolio_a.id, "id": investment_a.id},
        )

        # 1. Attempt to change portfolio
        response = api_client.patch(url, {"portfolio": str(portfolio_b.id)}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "portfolio" in response.data

        # 2. Attempt to pass immutable field in details
        response2 = api_client.patch(
            url,
            {"details": {"investment_id": str(portfolio_b.id), "symbol": "TCS"}},
            format="json",
        )
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

    def test_strict_category_detail_validation_rejects_negative_values(self, api_client, user_a, portfolio_a):
        """Creating an equity investment with negative quantity or price must fail."""
        api_client.force_authenticate(user=user_a)
        url = reverse(
            "assets_api_v1:portfolio-investment-list-create",
            kwargs={"portfolio_id": portfolio_a.id},
        )

        payload = {
            "category": "equity",
            "asset_type": "listed_stock",
            "details": {
                "symbol": "INFY",
                "quantity": -5,
                "purchase_price": "1400.00",
                "purchase_date": "2026-02-10",
            },
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "details" in response.data

    def test_strict_boolean_validation_rejects_ambiguous_strings(self, api_client, user_a, portfolio_a):
        """Passing invalid string booleans (like invalid tokens) must be rejected."""
        api_client.force_authenticate(user=user_a)
        url = reverse(
            "assets_api_v1:portfolio-investment-list-create",
            kwargs={"portfolio_id": portfolio_a.id},
        )

        payload = {
            "category": "cash",
            "asset_type": "savings_account",
            "details": {
                "bank_name": "HDFC Bank",
                "current_balance": "50000.00",
                "auto_sweep_enabled": "maybe",  # Invalid boolean
            },
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_current_value_records_valuation_snapshot_without_mutating_invested_cost(
        self, api_client, user_a, portfolio_a, investment_a
    ):
        """Updating current_value records an immutable snapshot and preserves acquisition cost."""
        api_client.force_authenticate(user=user_a)
        url = reverse(
            "assets_api_v1:portfolio-investment-detail",
            kwargs={"portfolio_id": portfolio_a.id, "id": investment_a.id},
        )

        initial_cost = investment_a.invested_amount
        response = api_client.patch(url, {"current_value": "42000.00"}, format="json")
        assert response.status_code == status.HTTP_200_OK

        investment_a.refresh_from_db()
        assert investment_a.current_value == Decimal("42000.00")
        assert investment_a.invested_amount == initial_cost  # Cost must NOT be overwritten!

        # Check snapshot was recorded
        latest_val = InvestmentValuation.objects.filter(investment=investment_a).order_by("-created_at").first()
        assert latest_val is not None
        assert latest_val.amount == Decimal("42000.00")
