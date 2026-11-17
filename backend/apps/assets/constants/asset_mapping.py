"""
Authoritative compatibility mapping between asset categories and supported product types.
Used across investment validation, valuation strategy selection, and projections.
"""

from typing import Dict, Set

CATEGORY_PRODUCT_COMPATIBILITY_MAP: Dict[str, Set[str]] = {
    'cash': {
        'savings_account',
        'current_account',
        'salary_account',
        'cash_balance',
        'savings',
        'current',
        'wallet',
        'physical_cash',
        'overdraft',
        'cash_account',
    },
    'fixed_income': {
        'fixed_deposit',
        'recurring_deposit',
        'corporate_bond',
        'government_bond',
        'sovereign_bond',
        'bond',
        'bond_holding',
        'public_provident_fund',
        'ppf',
    },
    'equity': {
        'listed_stock',
        'stock',
        'large_cap_equity',
        'mid_cap_equity',
        'small_cap_equity',
        'equity_share',
        'us_equity',
    },
    'mutual_funds': {
        'mutual_fund',
        'equity_mutual_fund',
        'debt_mutual_fund',
        'hybrid_mutual_fund',
        'index_fund',
        'elss',
    },
    'gold': {
        'physical_gold',
        'sovereign_gold_bond',
        'digital_gold',
        'gold_etf',
        'sgb',
    },
    'commodities': {
        'physical_gold',
        'sovereign_gold_bond',
        'digital_gold',
        'gold_etf',
        'silver',
    },
    'real_estate': {
        'agricultural_land',
        'residential_property',
        'commercial_property',
        'reit',
        'real_estate',
        'land',
        'land_plot',
        'commercial',
        'residential',
    },
    'crypto': {
        'cryptocurrency',
        'bitcoin',
        'ethereum',
        'altcoin',
        'crypto_token',
    },
    'alternative': {
        'private_equity',
        'startup_equity',
        'art',
        'collectible',
        'other',
    },
}


def is_category_product_compatible(category: str, asset_type: str) -> bool:
    """
    Validates whether an asset category and product type combination is supported.
    """
    if not category or not asset_type:
        return False
    cat_lower = category.lower().strip()
    type_lower = asset_type.lower().strip()

    allowed = CATEGORY_PRODUCT_COMPATIBILITY_MAP.get(cat_lower)
    if not allowed:
        return False
    return type_lower in allowed
