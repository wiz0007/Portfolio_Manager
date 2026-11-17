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

        if investment.instrument:
            try:
                quote = MarketDataService.get_latest_quote(investment.instrument)
                if quote and quote.price:
                    market_price = quote.price
                    source_name = quote.provider or 'MARKET_FEED'
                    source_ref = investment.instrument.symbol
                    is_synthetic = quote.is_synthetic
                    if quote.timestamp:
                        obs_dt = quote.timestamp
            except Exception:
                pass

        if market_price is None:
            raw_p = details.get('current_price') or details.get('purchase_price_per_token') or details.get('buy_price')
            if raw_p is not None:
                market_price = to_decimal(raw_p)
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
            status=ValuationStatus.SUCCESS,
            is_synthetic=is_synthetic,
            metadata={
                'quantity': str(quantity),
                'market_price': str(market_price),
                'symbol': source_ref,
                'is_synthetic': is_synthetic,
            },
        )
