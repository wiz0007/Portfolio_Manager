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


class DigitalGoldValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates Digital Gold holdings based on provider weight balance and provider buyback price.
    Separate from physical gold jewellery/coins.
    """

    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        details = investment.details or {}
        obs_dt = as_of or datetime.now(timezone.utc)

        weight_raw = details.get('weight_grams') or details.get('weight') or investment.quantity
        if weight_raw is None:
            return ValuationResult(
                current_value=None,
                valuation_method='DIGITAL_GOLD_PROVIDER',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing weight in grams for Digital Gold; cannot default to 1.0.',
            )

        weight = to_decimal(weight_raw)
        if weight <= Decimal('0'):
            return ValuationResult(
                current_value=None,
                valuation_method='DIGITAL_GOLD_PROVIDER',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                notes='Digital Gold weight must be positive.',
            )

        weight = quantize_units(weight)

        rate_per_gram = None
        provider = details.get('provider', 'DIGITAL_GOLD_PROVIDER')
        source_name = 'PROVIDER_QUOTE'
        source_ref = str(provider)
        is_synthetic = False
        val_status = ValuationStatus.SUCCESS

        # 1. Check instrument link via canonical PriceResolver
        if investment.instrument:
            try:
                resolved = PriceResolver.resolve_price(investment.instrument, as_of=obs_dt)
                if resolved.price is not None and resolved.status in (
                    ResolutionStatus.AVAILABLE,
                    ResolutionStatus.STALE,
                    ResolutionStatus.SYNTHETIC,
                ):
                    rate_per_gram = resolved.price
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
        if rate_per_gram is None:
            raw_p = details.get('current_price_per_gram') or details.get('provider_sell_price') or details.get('user_estimate')
            if raw_p is not None:
                rate_per_gram = to_decimal(raw_p)
                source_name = 'USER_ESTIMATE'
                val_status = ValuationStatus.ESTIMATED
            else:
                return ValuationResult(
                    current_value=None,
                    valuation_method='DIGITAL_GOLD_PROVIDER',
                    source='NONE',
                    observed_at=obs_dt,
                    status=ValuationStatus.MARKET_DATA_UNAVAILABLE,
                    notes=f"Provider price unavailable for {provider}.",
                )

        current_val = quantize_currency(weight * rate_per_gram)

        return ValuationResult(
            current_value=current_val,
            valuation_method='DIGITAL_GOLD_PROVIDER',
            source=source_name,
            source_reference=source_ref,
            observed_at=obs_dt,
            currency=investment.currency,
            status=val_status,
            is_synthetic=is_synthetic,
            metadata={
                'provider': provider,
                'weight_grams': str(weight),
                'rate_per_gram': str(rate_per_gram),
            },
        )
