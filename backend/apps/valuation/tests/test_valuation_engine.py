from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models.investment import Investment
from apps.market_data.models.instrument import Instrument
from apps.market_data.models.market_data_point import MarketDataPoint
from apps.portfolios.models.portfolio import Portfolio
from apps.users.models.user import User
from apps.valuation.services.asset_valuation.cash import CashValuationStrategy
from apps.valuation.services.asset_valuation.fixed_deposit import FixedDepositValuationStrategy
from apps.valuation.services.asset_valuation.recurring_deposit import (
    RecurringDepositValuationStrategy,
)
from apps.valuation.services.calculation.decimal_utils import calculate_ear
from apps.valuation.services.valuation_orchestrator import ValuationOrchestrator


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        email="valuation_user@example.com",
        password="SecurePassword123!",
        full_name="Valuation Tester",
    )


@pytest.fixture
def test_portfolio(db, test_user):
    return Portfolio.objects.create(
        user=test_user,
        name="Wealth Growth Portfolio",
        base_currency="INR",
    )


@pytest.fixture
def cash_investment(db, test_user, test_portfolio):
    from apps.assets.models import CashAccountDetail
    inv = Investment.objects.create(
        user=test_user,
        portfolio=test_portfolio,
        category="cash",
        asset_type="savings_account",
        display_name="HDFC Primary Savings",
        currency="INR",
        initial_value=Decimal("50000.00"),
        current_value=Decimal("50000.00"),
        valuation_method="BANK_BALANCE",
    )
    CashAccountDetail.objects.create(
        investment=inv,
        bank_name="HDFC Bank",
        current_balance=Decimal("55000.00"),
        balance_date=date(2026, 1, 1),
        account_type="SAVINGS",
    )
    return inv


@pytest.fixture
def fd_investment(db, test_user, test_portfolio):
    from apps.assets.models import DepositDetail
    inv = Investment.objects.create(
        user=test_user,
        portfolio=test_portfolio,
        category="fixed_income",
        asset_type="fixed_deposit",
        display_name="SBI 1-Year FD",
        currency="INR",
        initial_value=Decimal("100000.00"),
        current_value=Decimal("100000.00"),
        valuation_method="CONTRACTUAL",
    )
    DepositDetail.objects.create(
        investment=inv,
        institution_name="State Bank of India",
        principal_amount=Decimal("100000.00"),
        interest_rate_pct=Decimal("7.50"),
        compounding_frequency="QUARTERLY",
        start_date=date(2026, 1, 1),
        maturity_date=date(2027, 1, 1),
        tenure_value=Decimal("1"),
        tenure_unit="YEARS",
        deposit_type="FIXED_DEPOSIT",
    )
    return inv


@pytest.fixture
def equity_investment(db, test_user, test_portfolio):
    from apps.assets.models import EquityDetail
    instrument = Instrument.objects.create(
        symbol="INFY",
        name="Infosys Limited",
        asset_class="EQUITY",
        exchange="NSE",
        currency="INR",
        is_active=True,
    )
    # Persist a recent quote
    MarketDataPoint.objects.create(
        instrument=instrument,
        price=Decimal("1650.00"),
        timestamp=datetime.now(timezone.utc),
        interval="1D",
        provider="DEMO_SYNTHETIC",
        is_synthetic=True,
    )
    inv = Investment.objects.create(
        user=test_user,
        portfolio=test_portfolio,
        instrument=instrument,
        category="equity",
        asset_type="listed_stock",
        display_name="Infosys Holding",
        currency="INR",
        initial_value=Decimal("150000.00"),
        current_value=Decimal("150000.00"),
        valuation_method="MARKET_PRICE",
    )
    EquityDetail.objects.create(
        investment=inv,
        company_name="Infosys Limited",
        symbol="INFY",
        exchange="NSE",
        quantity=Decimal("100.0000"),
        average_buy_price=Decimal("1500.00"),
        purchase_date=date(2026, 1, 15),
    )
    return inv


@pytest.mark.django_db
class TestValuationEngineStrategies:
    """
    Unit tests for deterministic asset valuation strategies (VAL-001 to VAL-004).
    """

    def test_val_001_cash_valuation_reads_stated_balance(self, cash_investment):
        strategy = CashValuationStrategy()
        result = strategy.evaluate(cash_investment)
        assert result.current_value == Decimal("55000.00")
        assert result.valuation_method == "BANK_BALANCE"
        assert result.currency == "INR"

    def test_val_002_fixed_deposit_ear_and_compounding(self, fd_investment):
        # 1. Verify EAR formula: ((1 + 0.075 / 4)^4 - 1) * 100 = 7.7136%
        ear = calculate_ear(Decimal("7.50"), 4)
        assert round(float(ear), 2) == 7.71

        # 2. Evaluate FD after 6 months (~182.5 days)
        eval_dt = datetime(2026, 7, 2, tzinfo=timezone.utc)
        strategy = FixedDepositValuationStrategy()
        result = strategy.evaluate(fd_investment, as_of=eval_dt)

        assert result.current_value > Decimal("100000.00")
        assert result.valuation_method == "CONTRACTUAL"
        assert "accrued_interest" in result.metadata

    def test_val_003_recurring_deposit_compounding(self, test_user, test_portfolio):
        from apps.assets.models import DepositDetail
        rd_inv = Investment.objects.create(
            user=test_user,
            portfolio=test_portfolio,
            category="fixed_income",
            asset_type="recurring_deposit",
            display_name="Monthly RD",
            currency="INR",
            initial_value=Decimal("30000.00"),
            current_value=Decimal("30000.00"),
            valuation_method="CONTRACTUAL",
        )
        DepositDetail.objects.create(
            investment=rd_inv,
            institution_name="State Bank of India",
            principal_amount=Decimal("30000.00"),
            monthly_installment=Decimal("5000.00"),
            interest_rate_pct=Decimal("7.00"),
            compounding_frequency="QUARTERLY",
            start_date=date(2026, 1, 1),
            tenure_value=Decimal("1"),
            tenure_unit="YEARS",
            deposit_type="RECURRING_DEPOSIT",
        )
        strategy = RecurringDepositValuationStrategy()
        result = strategy.evaluate(rd_inv)
        assert result.current_value >= Decimal("30000.00")
        assert result.valuation_method == "CONTRACTUAL"

    def test_val_004_equity_evaluates_from_instrument_latest_quote(self, equity_investment):
        from apps.valuation.services.asset_valuation.equity import EquityValuationStrategy
        strategy = EquityValuationStrategy()
        result = strategy.evaluate(equity_investment)
        # 100 shares * 1650.00 = 165,000.00
        assert result.current_value == Decimal("165000.00")
        assert result.valuation_method == "MARKET_PRICE"


@pytest.mark.django_db
class TestValuationOrchestratorAndAPIs:
    """
    Tests for ValuationOrchestrator and REST API lifecycle (VAL-005 to VAL-008).
    """

    def test_val_005_orchestrator_calculate_and_record_creates_snapshot(self, equity_investment, test_user):
        snapshot = ValuationOrchestrator.calculate_and_record(equity_investment, user=test_user)
        assert snapshot.amount == Decimal("165000.00")
        assert snapshot.valuation_method == "MARKET_PRICE"
        equity_investment.refresh_from_db()
        assert equity_investment.current_value == Decimal("165000.00")

    def test_val_006_record_manual_valuation_updates_current_value(self, cash_investment, test_user):
        snapshot = ValuationOrchestrator.record_manual_valuation(
            investment=cash_investment,
            amount=Decimal("60000.00"),
            valuation_date=date(2026, 5, 1),
            user=test_user,
            notes="Bank statement reconciled",
        )
        assert snapshot.amount == Decimal("60000.00")
        assert snapshot.notes == "Bank statement reconciled"
        cash_investment.refresh_from_db()
        assert cash_investment.current_value == Decimal("60000.00")

    def test_val_007_performance_metrics_calculation(self, equity_investment):
        # Invested: 150,000.00, Current: 150,000.00 initially
        equity_investment.current_value = Decimal("180000.00")
        equity_investment.save()

        metrics = ValuationOrchestrator.get_performance_metrics(equity_investment)
        assert metrics["invested_amount"] == "150000.00"
        assert metrics["current_value"] == "180000.00"
        assert metrics["absolute_gain_loss"] == "30000.00"
        assert metrics["percentage_gain_loss"] == "20.00"
        assert metrics["is_gain"] is True

    def test_val_008_api_calculate_and_history_lifecycle(self, api_client, test_user, equity_investment):
        api_client.force_authenticate(user=test_user)

        # 1. POST /calculate/
        calc_url = reverse(
            "valuation_api_v1:investment-valuation-calculate",
            kwargs={"investment_id": equity_investment.id},
        )
        calc_resp = api_client.post(calc_url, format="json")
        assert calc_resp.status_code == status.HTTP_201_CREATED
        assert Decimal(calc_resp.data["amount"]) == Decimal("165000.00")

        # 2. GET /valuations/ (history)
        list_url = reverse(
            "valuation_api_v1:investment-valuation-list-create",
            kwargs={"investment_id": equity_investment.id},
        )
        list_resp = api_client.get(list_url)
        assert list_resp.status_code == status.HTTP_200_OK
        assert len(list_resp.data) >= 1

        # 3. GET /performance/
        perf_url = reverse(
            "valuation_api_v1:investment-performance",
            kwargs={"investment_id": equity_investment.id},
        )
        perf_resp = api_client.get(perf_url)
        assert perf_resp.status_code == status.HTTP_200_OK
        assert perf_resp.data["current_value"] == "165000.00"
