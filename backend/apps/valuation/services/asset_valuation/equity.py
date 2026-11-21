import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from apps.assets.models.investment import Investment
from apps.market_data.services.price_resolver import PriceResolver, ResolutionStatus
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


class EquityValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates listed equity holdings using live/stored market data feeds.
    Quantity * Latest Market Price.
    """

    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        details = investment.details or {}
        obs_dt = as_of or datetime.now(timezone.utc)

        qty_raw = investment.quantity or details.get('quantity') or details.get('shares')
        if qty_raw is None:
            return ValuationResult(
                current_value=None,
                valuation_method='MARKET_PRICE',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing quantity for equity holding; cannot default to 1.0.',
            )

        quantity = to_decimal(qty_raw)
        if quantity <= Decimal('0'):
            return ValuationResult(
                current_value=None,
                valuation_method='MARKET_PRICE',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                notes='Equity shares quantity must be greater than zero.',
            )

        quantity = quantize_units(quantity)

        market_price = None
        source_name = 'MANUAL'
        source_ref = ''
        market_data_provenance = {}
        is_synthetic = False
        quote_ts = obs_dt
        val_status = ValuationStatus.SUCCESS

        # 1. Check instrument link via canonical PriceResolver
        if investment.instrument:
            try:
                resolved = PriceResolver.resolve_price(investment.instrument, as_of=obs_dt)
                if resolved.price is not None and resolved.status in (
                    ResolutionStatus.AVAILABLE,
                    ResolutionStatus.STALE,
                ):
                    market_price = resolved.price
                    source_name = resolved.source or 'MANUAL_VERIFIED'
                    source_ref = resolved.source_reference or investment.instrument.symbol
                    market_data_provenance = {
                        'series_id': resolved.series_id,
                        'observation_id': resolved.observation_id,
                        'series_data_version': resolved.data_version,
                        'price_type': resolved.price_type,
                    }
                    is_synthetic = resolved.is_synthetic
                    if resolved.effective_at:
                        quote_ts = resolved.effective_at
                    if resolved.status == ResolutionStatus.STALE:
                        val_status = ValuationStatus.STALE_DATA
            except Exception as e:
                logger.warning(
                    f"Failed to fetch market price for instrument {investment.instrument_id}: {e}"
                )



        # 2. If market price is unavailable, check for user explicit estimate
        if market_price is None:
            raw_estimate = details.get('current_price') or details.get('user_estimate')
            if raw_estimate is not None:
                market_price = to_decimal(raw_estimate)
                source_name = 'USER_ESTIMATE'
                val_status = ValuationStatus.ESTIMATED
            else:
                return ValuationResult(
                    current_value=None,
                    valuation_method='MARKET_PRICE',
                    source='NONE',
                    observed_at=quote_ts,
                    status=ValuationStatus.MARKET_DATA_UNAVAILABLE,
                    notes='Market price unavailable for equity holding.',
                )

        market_price = to_decimal(market_price)
        total_value = quantize_currency(quantity * market_price)

        return ValuationResult(
            current_value=total_value,
            valuation_method='MARKET_PRICE',
            source=source_name,
            source_reference=source_ref or details.get('symbol', ''),
            observed_at=quote_ts,
            currency=investment.currency,
            status=val_status,
            is_synthetic=is_synthetic,
            metadata={
                'quantity': str(quantity),
                'market_price': str(market_price),
                'is_synthetic': is_synthetic,
                'source': source_name,
                'symbol': source_ref or details.get('symbol', ''),
                **market_data_provenance,
            },
        )
