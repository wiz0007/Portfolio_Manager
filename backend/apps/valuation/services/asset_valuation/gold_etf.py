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


class GoldEtfValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates Gold ETF holdings:
    ETF Units * Exchange Market Price.
    Never treats ETF units as physical grams of gold.
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
                valuation_method='ETF_MARKET_PRICE',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing ETF units/quantity; cannot default to 1.0.',
            )

        units = to_decimal(units_raw)
        if units <= Decimal('0'):
            return ValuationResult(
                current_value=None,
                valuation_method='ETF_MARKET_PRICE',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                notes='Gold ETF units must be greater than zero.',
            )

        units = quantize_units(units)

        market_price = None
        source_name = 'USER_INPUT'
        source_ref = details.get('symbol', 'GOLD_ETF')
        is_synthetic = False

        if investment.instrument:
            try:
                quote = MarketDataService.get_latest_quote(investment.instrument)
                if quote and quote.price is not None:
                    market_price = quote.price
                    source_name = quote.provider or 'MARKET_FEED'
                    source_ref = investment.instrument.symbol
                    is_synthetic = quote.is_synthetic
                    if quote.timestamp:
                        obs_dt = quote.timestamp
            except Exception:
                pass

        if market_price is None:
            raw_p = details.get('current_price') or details.get('market_price')
            if raw_p is not None:
                market_price = to_decimal(raw_p)
                source_name = 'USER_INPUT'
            else:
                return ValuationResult(
                    current_value=None,
                    valuation_method='ETF_MARKET_PRICE',
                    source='NONE',
                    observed_at=obs_dt,
                    status=ValuationStatus.UNAVAILABLE,
                    notes='Market price unavailable for Gold ETF.',
                )

        current_val = quantize_currency(units * market_price)

        return ValuationResult(
            current_value=current_val,
            valuation_method='ETF_MARKET_PRICE',
            source=source_name,
            source_reference=source_ref,
            observed_at=obs_dt,
            currency=investment.currency,
            status=ValuationStatus.SUCCESS,
            is_synthetic=is_synthetic,
            metadata={
                'units': str(units),
                'market_price': str(market_price),
                'symbol': source_ref,
            },
        )
