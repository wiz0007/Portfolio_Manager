import pytest

from apps.assets.models.investment import Investment
from apps.portfolios.models.portfolio import Portfolio
from apps.users.models.user import User
from apps.valuation.services.asset_valuation import (
    BondValuationStrategy,
    CashValuationStrategy,
    CryptoValuationStrategy,
    EquityValuationStrategy,
    FixedDepositValuationStrategy,
    GoldValuationStrategy,
    MutualFundValuationStrategy,
    RealEstateValuationStrategy,
    RecurringDepositValuationStrategy,
    SovereignGoldBondValuationStrategy,
    UnsupportedStrategyError,
    get_strategy_for_investment,
)


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="registry_test@example.com",
        password="Password123!",
        full_name="Registry Tester",
    )


@pytest.fixture
def portfolio(db, user):
    return Portfolio.objects.create(
        user=user,
        name="Registry Portfolio",
        base_currency="INR",
    )


@pytest.mark.django_db
class TestValuationStrategyRegistry:
    """
    Registry mapping tests verifying explicit product-type mapping,
    absence of ambiguous fallbacks, and strict error handling (VAL-001 to VAL-006).
    """

    def test_val_001_explicit_product_type_resolution(self, portfolio, user):
        """Every supported product type resolves to its exact, authoritative strategy."""
        expected_resolutions = [
            ("equity", "listed_stock", EquityValuationStrategy),
            ("mutual_funds", "mutual_fund", MutualFundValuationStrategy),
            ("fixed_income", "fixed_deposit", FixedDepositValuationStrategy),
            ("fixed_income", "recurring_deposit", RecurringDepositValuationStrategy),
            ("fixed_income", "corporate_bond", BondValuationStrategy),
            ("fixed_income", "government_bond", BondValuationStrategy),
            ("cash", "savings_account", CashValuationStrategy),
            ("cash", "current_account", CashValuationStrategy),
            ("commodities", "physical_gold", GoldValuationStrategy),
            ("commodities", "sovereign_gold_bond", SovereignGoldBondValuationStrategy),
            ("real_estate", "residential_property", RealEstateValuationStrategy),
            ("real_estate", "commercial_property", RealEstateValuationStrategy),
            ("real_estate", "agricultural_land", RealEstateValuationStrategy),
            ("crypto", "crypto_token", CryptoValuationStrategy),
        ]

        for category, asset_type, expected_class in expected_resolutions:
            inv = Investment(
                user=user,
                portfolio=portfolio,
                category=category,
                asset_type=asset_type,
                display_name=f"Test {asset_type}",
            )
            strategy = get_strategy_for_investment(inv)
            assert isinstance(strategy, expected_class), (
                f"Expected {expected_class.__name__} for {category}/{asset_type}, got {type(strategy).__name__}"
            )

    def test_val_002_sgb_separate_from_physical_gold(self, portfolio, user):
        """Sovereign Gold Bonds must use SovereignGoldBondValuationStrategy, not physical gold."""
        sgb = Investment(
            user=user,
            portfolio=portfolio,
            category="commodities",
            asset_type="sovereign_gold_bond",
            display_name="SGB 2029 Series",
        )
        physical = Investment(
            user=user,
            portfolio=portfolio,
            category="commodities",
            asset_type="physical_gold",
            display_name="24K Gold Bar",
        )

        sgb_strategy = get_strategy_for_investment(sgb)
        phys_strategy = get_strategy_for_investment(physical)

        assert isinstance(sgb_strategy, SovereignGoldBondValuationStrategy)
        assert isinstance(phys_strategy, GoldValuationStrategy)
        assert type(sgb_strategy) is not type(phys_strategy)

    def test_val_003_bond_separate_from_fixed_deposit(self, portfolio, user):
        """Bonds must use BondValuationStrategy and never fall back to FixedDeposit."""
        bond = Investment(
            user=user,
            portfolio=portfolio,
            category="fixed_income",
            asset_type="corporate_bond",
            display_name="Tata Motors 8.5% NCD",
        )
        fd = Investment(
            user=user,
            portfolio=portfolio,
            category="fixed_income",
            asset_type="fixed_deposit",
            display_name="HDFC 1-Year FD",
        )

        bond_strategy = get_strategy_for_investment(bond)
        fd_strategy = get_strategy_for_investment(fd)

        assert isinstance(bond_strategy, BondValuationStrategy)
        assert isinstance(fd_strategy, FixedDepositValuationStrategy)
        assert type(bond_strategy) is not type(fd_strategy)

    def test_val_004_unsupported_product_type_raises_error(self, portfolio, user):
        """Unknown or unsupported asset_type must raise UnsupportedStrategyError."""
        unknown_inv = Investment(
            user=user,
            portfolio=portfolio,
            category="equity",
            asset_type="binary_option",
            display_name="Exotic Binary Option",
        )
        with pytest.raises(UnsupportedStrategyError) as exc_info:
            get_strategy_for_investment(unknown_inv)

        assert "binary_option" in str(exc_info.value)

    def test_val_005_incompatible_category_and_product_raises_error(self, portfolio, user):
        """Mismatched category and product type must raise UnsupportedStrategyError."""
        mismatched_inv = Investment(
            user=user,
            portfolio=portfolio,
            category="crypto",
            asset_type="listed_stock",
            display_name="Mismatched Stock in Crypto",
        )
        with pytest.raises(UnsupportedStrategyError) as exc_info:
            get_strategy_for_investment(mismatched_inv)

        assert "Incompatible category 'crypto'" in str(exc_info.value)

    def test_val_006_no_silent_fallback_to_cash(self, portfolio, user):
        """A missing or corrupt investment asset_type must fail loudly, never default to Cash."""
        blank_inv = Investment(
            user=user,
            portfolio=portfolio,
            category="equity",
            asset_type="",
            display_name="Empty Asset Type",
        )
        with pytest.raises(UnsupportedStrategyError):
            get_strategy_for_investment(blank_inv)
