from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.assets.models import EquityDetail
from apps.assets.models.investment import Investment
from apps.assets.models.valuations import InvestmentValuation
from apps.portfolios.models.portfolio import Portfolio
from apps.users.models.user import User
from apps.valuation.services.valuation_orchestrator import ValuationOrchestrator


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="history_test@example.com",
        password="Password123!",
        full_name="History Tester",
    )


@pytest.fixture
def portfolio(db, user):
    return Portfolio.objects.create(
        user=user,
        name="History Portfolio",
        base_currency="INR",
    )


@pytest.fixture
def test_stock(db, user, portfolio):
    inv = Investment.objects.create(
        user=user,
        portfolio=portfolio,
        category="equity",
        asset_type="listed_stock",
        display_name="Infosys Ltd",
        currency="INR",
        initial_value=Decimal("150000.00"),
        current_value=Decimal("180000.00"),
        valuation_method="MARKET_PRICE",
    )
    EquityDetail.objects.create(
        investment=inv,
        company_name="Infosys Limited",
        symbol="INFY",
        exchange="NSE",
        quantity=Decimal("100.0000"),
        average_buy_price=Decimal("1500.00"),
        purchase_date=date.today() - timedelta(days=60),
    )
    return inv


@pytest.mark.django_db
class TestValuationHistoryAndIntegrity:
    """
    Tests for snapshot integrity, non-regression of current_value by older snapshots,
    zero-value preservation, and zero-cost performance metrics (VAL-040 to VAL-049).
    """

    def test_val_040_older_snapshot_never_overwrites_newer_current_value(self, test_stock, user):
        """
        If current_value is recorded for today (e.g. 180,000.00), recording an older
        historical snapshot for 30 days ago (e.g. 140,000.00) must save to history
        WITHOUT regressing investment.current_value.
        """
        # First record today's snapshot
        today = date.today()
        ValuationOrchestrator.record_manual_valuation(
            investment=test_stock,
            user=user,
            amount=Decimal("180000.00"),
            valuation_date=today,
            valuation_method="MANUAL",
            notes="Today's current snapshot",
        )
        test_stock.refresh_from_db()
        assert test_stock.current_value == Decimal("180000.00")

        # Now record an older snapshot for 30 days ago
        older_date = today - timedelta(days=30)
        ValuationOrchestrator.record_manual_valuation(
            investment=test_stock,
            user=user,
            amount=Decimal("140000.00"),
            valuation_date=older_date,
            valuation_method="MANUAL",
            notes="Older historical snapshot",
        )

        test_stock.refresh_from_db()
        # Older snapshot is recorded in history
        assert InvestmentValuation.objects.filter(investment=test_stock, valuation_date=older_date).exists()
        # BUT current_value remains at the latest (180,000.00)
        assert test_stock.current_value == Decimal("180000.00")

    def test_val_041_newer_snapshot_updates_current_value(self, test_stock, user):
        """Recording a newer snapshot properly updates investment.current_value."""
        past_date = date.today() - timedelta(days=10)
        ValuationOrchestrator.record_manual_valuation(
            investment=test_stock,
            user=user,
            amount=Decimal("160000.00"),
            valuation_date=past_date,
        )

        today = date.today()
        ValuationOrchestrator.record_manual_valuation(
            investment=test_stock,
            user=user,
            amount=Decimal("195000.00"),
            valuation_date=today,
        )

        test_stock.refresh_from_db()
        assert test_stock.current_value == Decimal("195000.00")

    def test_val_042_failed_calculation_preserves_current_value(self, test_stock):
        """
        When calculate_and_record fails (e.g. MARKET_DATA_UNAVAILABLE or INCOMPLETE_INPUT),
        existing investment.current_value must NOT be destroyed or set to None.
        """
        initial_val = test_stock.current_value

        # Make equity details incomplete to force INCOMPLETE_INPUT
        test_stock.equity_detail.quantity = Decimal("0.0000")
        test_stock.equity_detail.save()

        result = ValuationOrchestrator.calculate_and_record(test_stock)
        assert result is None

        test_stock.refresh_from_db()
        # Existing value must be strictly preserved
        assert test_stock.current_value == initial_val

    def test_val_043_zero_cost_basis_returns_unavailable_percentage(self, portfolio, user):
        """
        When invested_amount is zero (e.g. gifted asset or air-dropped token),
        percentage_gain_loss must return 'unavailable' without raising ZeroDivisionError.
        """
        inv_zero_cost = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            category="crypto",
            asset_type="crypto_token",
            display_name="Gifted Token",
            currency="INR",
            initial_value=Decimal("0.00"),
            current_value=Decimal("5000.00"),
            valuation_method="MARKET_PRICE",
        )

        metrics = ValuationOrchestrator.get_performance_metrics(inv_zero_cost)
        assert metrics["invested_amount"] == "0.00"
        assert metrics["current_value"] == "5000.00"
        assert metrics["absolute_gain_loss"] == "5000.00"
        assert metrics["percentage_gain_loss"] == "unavailable"
        assert metrics["is_gain"] is True

    def test_val_044_zero_valuation_preserved(self, test_stock, user):
        """
        A legitimate zero valuation (e.g. bankrupt stock or total loss) must be
        preserved in the database as Decimal('0.00'), not treated as missing.
        """
        today = date.today()
        ValuationOrchestrator.record_manual_valuation(
            investment=test_stock,
            user=user,
            amount=Decimal("0.00"),
            valuation_date=today,
            notes="Asset written off",
        )

        test_stock.refresh_from_db()
        assert test_stock.current_value == Decimal("0.00")
        metrics = ValuationOrchestrator.get_performance_metrics(test_stock)
        assert metrics["current_value"] == "0.00"
        assert metrics["percentage_gain_loss"] == "-100.00"
        assert metrics["is_gain"] is False
