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


class CryptoValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates crypto currency holdings:
    Quantity * Latest Market Price.
    """

    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        details = investment.details or {}
        obs_dt = as_of or datetime.now(timezone.utc)

        qty_raw = investment.quantity or details.get('quantity')
        if qty_raw is None:
            return ValuationResult(
                current_value=None,
                valuation_method='MARKET_PRICE',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing quantity for crypto holding; cannot default to 1.0.',
            )

        quantity = to_decimal(qty_raw)
        if quantity <= Decimal('0'):
            return ValuationResult(
                current_value=None,
                valuation_method='MARKET_PRICE',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                notes='Crypto token quantity must be greater than zero.',
            )

        quantity = quantize_units(quantity, places=8)

        market_price = None
        source_name = 'USER_INPUT'
        source_ref = details.get('symbol', 'CRYPTO')
        is_synthetic = False
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
                    is_synthetic = resolved.is_synthetic
                    if resolved.effective_at:
                        obs_dt = resolved.effective_at
                    if resolved.status == ResolutionStatus.STALE:
                        val_status = ValuationStatus.STALE_DATA
            except Exception:
                pass

        # 2. Check for user explicit estimate
        if market_price is None:
            raw_p = details.get('current_price') or details.get('user_estimate')
            if raw_p is not None:
                market_price = to_decimal(raw_p)
                source_name = 'USER_ESTIMATE'
                val_status = ValuationStatus.ESTIMATED
            else:
                return ValuationResult(
                    current_value=None,
                    valuation_method='MARKET_PRICE',
                    source='NONE',
                    observed_at=obs_dt,
                    status=ValuationStatus.MARKET_DATA_UNAVAILABLE,
                    notes='Market price unavailable for crypto token.',
                )

        market_price = to_decimal(market_price)
        total_value = quantize_currency(quantity * market_price)

        return ValuationResult(
            current_value=total_value,
            valuation_method='MARKET_PRICE',
            source=source_name,
            source_reference=source_ref,
            observed_at=obs_dt,
            currency=investment.currency,
            status=val_status,
            is_synthetic=is_synthetic,
            metadata={
                'quantity': str(quantity),
                'market_price': str(market_price),
                'symbol': source_ref,
                'is_synthetic': is_synthetic,
            },
        )
