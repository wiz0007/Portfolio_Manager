from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.assets.models import (
    CashAccountDetail,
    CryptoDetail,
    DepositDetail,
    EquityDetail,
    GoldDetail,
    RealEstateDetail,
)
from apps.assets.models.investment import Investment
from apps.portfolios.models.portfolio import Portfolio
from apps.users.models.user import User
from apps.valuation.services.asset_valuation import (
    CashValuationStrategy,
    CryptoValuationStrategy,
    EquityValuationStrategy,
    FixedDepositValuationStrategy,
    GoldValuationStrategy,
    RealEstateValuationStrategy,
    SovereignGoldBondValuationStrategy,
)
from apps.valuation.services.asset_valuation.base import ValuationStatus


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="strategies_test@example.com",
        password="Password123!",
        full_name="Strategy Tester",
    )


@pytest.fixture
def portfolio(db, user):
    return Portfolio.objects.create(
        user=user,
        name="Strategy Portfolio",
        base_currency="INR",
    )


@pytest.mark.django_db
class TestAssetValuationStrategies:
    """
    Detailed strategy-level tests verifying mathematical correctness,
    edge-case handling, and ValuationStatus reporting (VAL-010 to VAL-030).
    """

    def test_val_010_gold_purity_conversion_24k_vs_22k(self, portfolio, user):
        """24K vs 22K purity conversion basis: fine_weight = grams * (purity / 24)."""
        from datetime import datetime, timezone

        from apps.market_data.models import Instrument, MarketDataPoint

        gold_inst = Instrument.objects.create(
            symbol="GOLD_24K_REF",
            name="Gold 24K Benchmark",
            asset_class="COMMODITIES",
            exchange="MCX",
            currency="INR",
            is_active=True,
        )
        MarketDataPoint.objects.create(
            instrument=gold_inst,
            price=Decimal("7000.00"),
            timestamp=datetime.now(timezone.utc),
            interval="1D",
            provider="DEMO_SYNTHETIC",
            is_synthetic=True,
        )

        strategy = GoldValuationStrategy()

        inv_24k = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            instrument=gold_inst,
            category="commodities",
            asset_type="physical_gold",
            display_name="24K Gold Bar",
            initial_value=Decimal("100000.00"),
        )
        GoldDetail.objects.create(
            investment=inv_24k,
            item_name="24K Gold Bar",
            gold_type="PHYSICAL",
            purity_karat=Decimal("24.00"),
            weight_grams=Decimal("10.0000"),
            purchase_price=Decimal("70000.00"),
            purchase_date=date.today(),
        )

        inv_22k = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            instrument=gold_inst,
            category="commodities",
            asset_type="physical_gold",
            display_name="22K Gold Coin",
            initial_value=Decimal("100000.00"),
        )
        GoldDetail.objects.create(
            investment=inv_22k,
            item_name="22K Gold Coin",
            gold_type="PHYSICAL",
            purity_karat=Decimal("22.00"),
            weight_grams=Decimal("10.0000"),
            purchase_price=Decimal("65000.00"),
            purchase_date=date.today(),
        )

        res_24k = strategy.evaluate(inv_24k)
        res_22k = strategy.evaluate(inv_22k)

        assert res_24k.status == ValuationStatus.SUCCESS
        assert res_22k.status == ValuationStatus.SUCCESS

        # 22K value is fine grams (quantized to 4 decimal places) multiplied by 24K rate
        fine_weight = Decimal(res_22k.metadata['fine_weight_24k_grams'])
        expected_22k = (fine_weight * Decimal("7000.00")).quantize(Decimal("0.01"))
        assert res_22k.current_value == expected_22k
        assert abs(res_22k.current_value - (res_24k.current_value * Decimal("22") / Decimal("24"))) < Decimal("1.00")

    def test_val_011_gold_missing_quantity_returns_incomplete_input(self, portfolio, user):
        """Missing weight_grams must return INCOMPLETE_INPUT, never manufacture 1.0g."""
        strategy = GoldValuationStrategy()
        inv = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            category="commodities",
            asset_type="physical_gold",
            display_name="Gold with No Weight",
            initial_value=Decimal("50000.00"),
        )
        GoldDetail.objects.create(
            investment=inv,
            item_name="Gold Ring",
            gold_type="PHYSICAL",
            purity_karat=Decimal("22.00"),
            weight_grams=None,
            purchase_price=Decimal("6000.00"),
            purchase_date=date.today(),
        )

        res = strategy.evaluate(inv)
        assert res.status in (ValuationStatus.INCOMPLETE_INPUT, ValuationStatus.INVALID_FINANCIAL_INPUT)
        assert res.current_value is None

    def test_val_012_sgb_market_price_and_accrued_coupon(self, portfolio, user):
        """SGB valuation reflects unit market price plus semi-annual accrued coupon (2.5% p.a.)."""
        strategy = SovereignGoldBondValuationStrategy()
        inv = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            category="commodities",
            asset_type="sovereign_gold_bond",
            display_name="SGB 2028-29",
            initial_value=Decimal("50000.00"),
        )
        GoldDetail.objects.create(
            investment=inv,
            item_name="SGB 2028-29 Series IV",
            gold_type="SGB",
            purity_karat=Decimal("24.00"),
            weight_grams=Decimal("10.0000"),
            purchase_price=Decimal("50000.00"),
            purchase_date=date.today() - timedelta(days=90),
            coupon_rate_pct=Decimal("2.50"),
        )

        res = strategy.evaluate(inv)
        assert res.status == ValuationStatus.SUCCESS
        assert res.current_value is not None
        assert "accrued_coupon" in res.metadata

    def test_val_013_equity_missing_units_returns_incomplete_input(self, portfolio, user):
        """Equity with zero or missing units returns INCOMPLETE_INPUT, never defaults to 1.0."""
        strategy = EquityValuationStrategy()
        inv = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            category="equity",
            asset_type="listed_stock",
            display_name="Empty Stock",
            initial_value=Decimal("1000.00"),
        )
        EquityDetail.objects.create(
            investment=inv,
            company_name="Reliance Industries",
            symbol="RELIANCE",
            exchange="NSE",
            quantity=Decimal("0.0000"),
            average_buy_price=Decimal("2500.00"),
            purchase_date=date.today(),
        )

        res = strategy.evaluate(inv)
        assert res.status in (ValuationStatus.INCOMPLETE_INPUT, ValuationStatus.INVALID_FINANCIAL_INPUT)
        assert res.current_value is None

    def test_val_014_fixed_deposit_cumulative_vs_non_cumulative(self, portfolio, user):
        """
        Non-cumulative FD (payout) should never compound distributed interest into principal.
        Cumulative FD must compound interest.
        """
        strategy = FixedDepositValuationStrategy()
        start = date.today() - timedelta(days=180)
        maturity = date.today() + timedelta(days=185)

        # Cumulative FD (quarterly compounding)
        inv_cum = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            category="fixed_income",
            asset_type="fixed_deposit",
            display_name="Cumulative FD",
            initial_value=Decimal("100000.00"),
        )
        DepositDetail.objects.create(
            investment=inv_cum,
            institution_name="HDFC Bank",
            deposit_type="FIXED_DEPOSIT",
            principal_amount=Decimal("100000.00"),
            interest_rate_pct=Decimal("8.00"),
            compounding_frequency="QUARTERLY",
            payout_type="CUMULATIVE",
            start_date=start,
            maturity_date=maturity,
            tenure_value=Decimal("1"),
            tenure_unit="YEARS",
        )

        # Non-cumulative FD (monthly interest payout)
        inv_non_cum = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            category="fixed_income",
            asset_type="fixed_deposit",
            display_name="Non-Cumulative FD",
            initial_value=Decimal("100000.00"),
        )
        DepositDetail.objects.create(
            investment=inv_non_cum,
            institution_name="HDFC Bank",
            deposit_type="FIXED_DEPOSIT",
            principal_amount=Decimal("100000.00"),
            interest_rate_pct=Decimal("8.00"),
            compounding_frequency="SIMPLE",
            payout_type="NON_CUMULATIVE",
            start_date=start,
            maturity_date=maturity,
            tenure_value=Decimal("1"),
            tenure_unit="YEARS",
        )

        res_cum = strategy.evaluate(inv_cum)
        res_non_cum = strategy.evaluate(inv_non_cum)

        assert res_cum.status == ValuationStatus.SUCCESS
        assert res_non_cum.status == ValuationStatus.SUCCESS

        # Cumulative FD must grow above principal
        assert res_cum.current_value > Decimal("100000.00")
        # Non-cumulative FD pays out periodically, so current value is strictly less than cumulative
        assert res_non_cum.current_value < res_cum.current_value
        assert res_non_cum.metadata["payout_type"] == "NON_CUMULATIVE"

    def test_val_015_fixed_deposit_past_maturity_stops_compounding(self, portfolio, user):
        """FD ceases compounding past maturity date."""
        strategy = FixedDepositValuationStrategy()
        start = date.today() - timedelta(days=730)
        maturity = date.today() - timedelta(days=365)  # Matured 1 year ago

        inv = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            category="fixed_income",
            asset_type="fixed_deposit",
            display_name="Matured FD",
            initial_value=Decimal("100000.00"),
        )
        DepositDetail.objects.create(
            investment=inv,
            institution_name="State Bank of India",
            deposit_type="FIXED_DEPOSIT",
            principal_amount=Decimal("100000.00"),
            interest_rate_pct=Decimal("7.00"),
            compounding_frequency="ANNUAL",
            payout_type="CUMULATIVE",
            start_date=start,
            maturity_date=maturity,
            tenure_value=Decimal("1"),
            tenure_unit="YEARS",
        )

        res = strategy.evaluate(inv)
        assert res.status == ValuationStatus.SUCCESS
        # Exactly 1 year of compounding: 100,000 * 1.07 = 107,000.00
        assert res.current_value == Decimal("107000.00")
        assert res.metadata["is_matured"] is True

    def test_val_016_real_estate_ownership_percentage(self, portfolio, user):
        """Real estate current value must strictly scale by (ownership_percentage / 100)."""
        strategy = RealEstateValuationStrategy()
        inv = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            category="real_estate",
            asset_type="residential_property",
            display_name="Shared Apartment",
            initial_value=Decimal("5000000.00"),
        )
        RealEstateDetail.objects.create(
            investment=inv,
            property_type="RESIDENTIAL",
            state="Maharashtra",
            ownership_percentage=Decimal("50.00"),
            purchase_price=Decimal("10000000.00"),
            estimated_current_value=Decimal("12000000.00"),
            acquisition_date=date.today(),
        )

        res = strategy.evaluate(inv)
        assert res.status == ValuationStatus.SUCCESS
        # 12,000,000 * 50% = 6,000,000.00
        assert res.current_value == Decimal("6000000.00")
        assert res.metadata["ownership_percentage"] == "50.00"

    def test_val_017_cash_balance_date_metadata(self, portfolio, user):
        """Cash account valuation reflects stated balance and includes balance_date metadata."""
        strategy = CashValuationStrategy()
        bal_date = date.today() - timedelta(days=5)

        inv = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            category="cash",
            asset_type="savings_account",
            display_name="HDFC Savings",
            initial_value=Decimal("25000.00"),
        )
        CashAccountDetail.objects.create(
            investment=inv,
            bank_name="HDFC Bank",
            account_type="SAVINGS",
            current_balance=Decimal("25000.00"),
            balance_date=bal_date,
        )

        res = strategy.evaluate(inv)
        assert res.status == ValuationStatus.SUCCESS
        assert res.current_value == Decimal("25000.00")
        assert res.metadata["balance_date"] == bal_date.isoformat()

    def test_val_018_crypto_token_quantity_validation(self, portfolio, user):
        """Crypto valuation returns INCOMPLETE_INPUT if quantity is missing/zero."""
        strategy = CryptoValuationStrategy()
        inv = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            category="crypto",
            asset_type="crypto_token",
            display_name="Zero BTC",
            initial_value=Decimal("0.00"),
        )
        CryptoDetail.objects.create(
            investment=inv,
            token_name="Bitcoin",
            symbol="BTC",
            network="Bitcoin",
            quantity=Decimal("0.00000000"),
            purchase_price_per_token=Decimal("5000000.00"),
            purchase_date=date.today(),
        )

        res = strategy.evaluate(inv)
        assert res.status in (ValuationStatus.INCOMPLETE_INPUT, ValuationStatus.INVALID_FINANCIAL_INPUT)
        assert res.current_value is None
