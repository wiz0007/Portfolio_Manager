from typing import Dict, Type

from apps.valuation.services.asset_valuation.base import (
    BaseAssetValuationStrategy,
    UnsupportedStrategyError,
    ValuationResult,
    ValuationStatus,
)
from apps.valuation.services.asset_valuation.bond import BondValuationStrategy
from apps.valuation.services.asset_valuation.cash import CashValuationStrategy
from apps.valuation.services.asset_valuation.crypto import CryptoValuationStrategy
from apps.valuation.services.asset_valuation.digital_gold import DigitalGoldValuationStrategy
from apps.valuation.services.asset_valuation.equity import EquityValuationStrategy
from apps.valuation.services.asset_valuation.fixed_deposit import FixedDepositValuationStrategy
from apps.valuation.services.asset_valuation.gold import GoldValuationStrategy
from apps.valuation.services.asset_valuation.gold_etf import GoldEtfValuationStrategy
from apps.valuation.services.asset_valuation.mutual_fund import MutualFundValuationStrategy
from apps.valuation.services.asset_valuation.ppf import PublicProvidentFundValuationStrategy
from apps.valuation.services.asset_valuation.real_estate import RealEstateValuationStrategy
from apps.valuation.services.asset_valuation.recurring_deposit import (
    RecurringDepositValuationStrategy,
)
from apps.valuation.services.asset_valuation.reit import (
    RealEstateInvestmentTrustValuationStrategy,
)
from apps.valuation.services.asset_valuation.sgb import SovereignGoldBondValuationStrategy

# Authoritative product-type to strategy mapping
EXPLICIT_PRODUCT_STRATEGY_MAP: Dict[str, Type[BaseAssetValuationStrategy]] = {
    # Cash / Liquid
    'SAVINGS_ACCOUNT': CashValuationStrategy,
    'CURRENT_ACCOUNT': CashValuationStrategy,
    'SALARY_ACCOUNT': CashValuationStrategy,
    'CASH_ACCOUNT': CashValuationStrategy,
    'CASH_BALANCE': CashValuationStrategy,
    'WALLET': CashValuationStrategy,
    'PHYSICAL_CASH': CashValuationStrategy,
    'OVERDRAFT': CashValuationStrategy,
    'CASH': CashValuationStrategy,

    # Fixed Income / Deposits
    'FIXED_DEPOSIT': FixedDepositValuationStrategy,
    'PUBLIC_PROVIDENT_FUND': PublicProvidentFundValuationStrategy,
    'PPF': PublicProvidentFundValuationStrategy,
    'RECURRING_DEPOSIT': RecurringDepositValuationStrategy,

    # Fixed Income / Bonds
    'BOND': BondValuationStrategy,
    'BOND_HOLDING': BondValuationStrategy,
    'CORPORATE_BOND': BondValuationStrategy,
    'GOVERNMENT_BOND': BondValuationStrategy,
    'SOVEREIGN_BOND': BondValuationStrategy,

    # Equities
    'LISTED_STOCK': EquityValuationStrategy,
    'STOCK': EquityValuationStrategy,
    'LARGE_CAP_EQUITY': EquityValuationStrategy,
    'MID_CAP_EQUITY': EquityValuationStrategy,
    'SMALL_CAP_EQUITY': EquityValuationStrategy,
    'EQUITY_SHARE': EquityValuationStrategy,
    'US_EQUITY': EquityValuationStrategy,
    'EQUITY': EquityValuationStrategy,

    # Mutual Funds
    'MUTUAL_FUND': MutualFundValuationStrategy,
    'EQUITY_MUTUAL_FUND': MutualFundValuationStrategy,
    'DEBT_MUTUAL_FUND': MutualFundValuationStrategy,
    'HYBRID_MUTUAL_FUND': MutualFundValuationStrategy,
    'INDEX_FUND': MutualFundValuationStrategy,
    'ELSS': MutualFundValuationStrategy,
    'MUTUAL_FUNDS': MutualFundValuationStrategy,

    # Gold / Commodities
    'PHYSICAL_GOLD': GoldValuationStrategy,
    'DIGITAL_GOLD': DigitalGoldValuationStrategy,
    'GOLD_ETF': GoldEtfValuationStrategy,
    'GOLD': GoldValuationStrategy,
    'COMMODITIES': GoldValuationStrategy,

    # Sovereign Gold Bonds
    'SOVEREIGN_GOLD_BOND': SovereignGoldBondValuationStrategy,
    'SGB': SovereignGoldBondValuationStrategy,

    # Real Estate
    'REAL_ESTATE': RealEstateValuationStrategy,
    'AGRICULTURAL_LAND': RealEstateValuationStrategy,
    'LAND_PLOT': RealEstateValuationStrategy,
    'RESIDENTIAL_PROPERTY': RealEstateValuationStrategy,
    'COMMERCIAL_PROPERTY': RealEstateValuationStrategy,
    'REIT': RealEstateInvestmentTrustValuationStrategy,

    # Crypto
    'CRYPTOCURRENCY': CryptoValuationStrategy,
    'BITCOIN': CryptoValuationStrategy,
    'ETHEREUM': CryptoValuationStrategy,
    'CRYPTO_TOKEN': CryptoValuationStrategy,
    'ALTCOIN': CryptoValuationStrategy,
    'CRYPTO': CryptoValuationStrategy,
}


def get_valuation_strategy(category: str, asset_type: str = '') -> BaseAssetValuationStrategy:
    """
    Returns an instantiated strategy for the given asset category and product type.
    Strictly prevents silent fallbacks to unrelated strategies.
    Raises UnsupportedStrategyError if product type is unsupported or incompatible.
    """
    cat_clean = (category or '').strip()
    type_clean = (asset_type or '').strip()

    if not type_clean:
        raise UnsupportedStrategyError(
            f"Asset type is required to resolve a valuation strategy. Given category: '{category}'."
        )

    from apps.assets.constants.asset_mapping import is_category_product_compatible
    if cat_clean and not is_category_product_compatible(cat_clean, type_clean):
        raise UnsupportedStrategyError(
            f"Incompatible category '{category}' and product type '{asset_type}'."
        )

    cls = EXPLICIT_PRODUCT_STRATEGY_MAP.get(type_clean.upper())
    if not cls:
        raise UnsupportedStrategyError(
            f"No valuation strategy registered for product type '{asset_type}' in category '{category}'."
        )

    return cls()


def get_strategy_for_investment(investment) -> BaseAssetValuationStrategy:
    """
    Resolves the canonical valuation strategy for a given Investment model instance.
    """
    category = getattr(investment, 'category', '')
    asset_type = getattr(investment, 'asset_type', '')
    return get_valuation_strategy(category=category, asset_type=asset_type)


__all__ = [
    'EXPLICIT_PRODUCT_STRATEGY_MAP',
    'BaseAssetValuationStrategy',
    'BondValuationStrategy',
    'CashValuationStrategy',
    'CryptoValuationStrategy',
    'DigitalGoldValuationStrategy',
    'EquityValuationStrategy',
    'FixedDepositValuationStrategy',
    'GoldDetailSerializer',
    'GoldEtfValuationStrategy',
    'GoldValuationStrategy',
    'MutualFundValuationStrategy',
    'PublicProvidentFundValuationStrategy',
    'RealEstateInvestmentTrustValuationStrategy',
    'RealEstateValuationStrategy',
    'RecurringDepositValuationStrategy',
    'SovereignGoldBondValuationStrategy',
    'UnsupportedStrategyError',
    'ValuationResult',
    'ValuationStatus',
    'get_strategy_for_investment',
    'get_valuation_strategy',
]
