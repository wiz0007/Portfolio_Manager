import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from apps.assets.models.investment import Investment
from apps.market_data.services.market_data_service import MarketDataService
from apps.valuation.services.asset_valuation.base import (
    BaseAssetValuationStrategy,
    ValuationResult,
    ValuationStatus,
)
from apps.valuation.services.calculation.decimal_utils import (
    quantize_currency,
    quantize_units,
    to_decimal,
)

logger = logging.getLogger(__name__)


class MutualFundValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates mutual fund holdings using official daily Net Asset Value (NAV).
    Units * Latest NAV.
    """

    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        details = investment.details or {}
        obs_dt = as_of or datetime.now(timezone.utc)

        units_raw = investment.quantity or details.get('units') or details.get('quantity')
        if units_raw is None:
            return ValuationResult(
                current_value=None,
                valuation_method='NAV',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing units for mutual fund holding; cannot default to 1.0.',
            )

        units = to_decimal(units_raw)
        if units <= Decimal('0'):
            return ValuationResult(
                current_value=None,
                valuation_method='NAV',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                notes='Mutual fund units must be greater than zero.',
            )

        units = quantize_units(units)

        nav_price = None
        source_name = 'MANUAL'
        source_ref = ''
        is_synthetic = False
        quote_ts = obs_dt

        # 1. Check instrument link for AMFI / provider NAV
        if investment.instrument:
            try:
                quote = MarketDataService.get_latest_quote(investment.instrument)
                if quote and quote.price:
                    nav_price = quote.price
                    source_name = quote.provider or 'AMFI'
                    source_ref = investment.instrument.symbol or investment.instrument.isin
                    is_synthetic = quote.is_synthetic
                    if quote.timestamp:
                        quote_ts = quote.timestamp
            except Exception as e:
                logger.warning(
                    f"Failed to fetch NAV for mutual fund instrument {investment.instrument_id}: {e}"
                )

        # 2. Fallback to details nav
        if nav_price is None:
            raw_nav = details.get('nav') or details.get('current_nav') or details.get('purchase_nav') or details.get('average_purchase_nav')
            if raw_nav is not None:
                nav_price = to_decimal(raw_nav)
                source_name = 'USER_INPUT'
            else:
                return ValuationResult(
                    current_value=None,
                    valuation_method='NAV',
                    source='NONE',
                    observed_at=quote_ts,
                    status=ValuationStatus.MARKET_DATA_UNAVAILABLE,
                    notes='Mutual fund NAV unavailable.',
                )

        nav_price = to_decimal(nav_price)
        total_value = quantize_currency(units * nav_price)

        return ValuationResult(
            current_value=total_value,
            valuation_method='NAV',
            source=source_name,
            source_reference=source_ref or details.get('scheme_code', ''),
            observed_at=quote_ts,
            currency=investment.currency,
            status=ValuationStatus.SUCCESS,
            is_synthetic=is_synthetic,
            metadata={
                'units': str(units),
                'nav': str(nav_price),
                'is_synthetic': is_synthetic,
                'source': source_name,
                'scheme_name': details.get('scheme_name', ''),
            },
        )
