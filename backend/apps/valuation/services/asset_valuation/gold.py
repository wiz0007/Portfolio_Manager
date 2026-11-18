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


class GoldValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates physical gold holdings using fine gold purity basis:
    Fine grams = gross weight * (purity_karats / 24.0)
    Current value = fine grams * rate_per_gram_24k.
    """

    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        details = investment.details or {}
        obs_dt = as_of or datetime.now(timezone.utc)

        grams_raw = details.get('weight_grams') or details.get('gross_weight_grams') or details.get('weight_in_grams') or details.get('grams') or investment.quantity
        if grams_raw is None:
            return ValuationResult(
                current_value=None,
                valuation_method='PHYSICAL_GOLD_PURITY',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing gold weight/quantity; cannot default to 1.0.',
            )

        grams = to_decimal(grams_raw)
        if grams <= Decimal('0'):
            return ValuationResult(
                current_value=None,
                valuation_method='PHYSICAL_GOLD_PURITY',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                notes='Gold weight must be greater than zero.',
            )

        grams = quantize_units(grams)

        # Karat purity conversion (basis: 24K) - never silently default invalid purity to 24K
        purity_raw = details.get('purity_karat') or details.get('purity_karats') or details.get('purity')
        if purity_raw is not None:
            raw_str = str(purity_raw).strip().upper()
            if raw_str.endswith('K'):
                raw_str = raw_str[:-1]
            try:
                purity_karats = to_decimal(raw_str)
            except Exception:
                return ValuationResult(
                    current_value=None,
                    valuation_method='PHYSICAL_GOLD_PURITY',
                    source='NONE',
                    observed_at=obs_dt,
                    status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                    notes=f"Invalid gold purity '{purity_raw}'. Expected karats between 1.00 and 24.00.",
                )
            if purity_karats <= Decimal('0') or purity_karats > Decimal('24.0'):
                return ValuationResult(
                    current_value=None,
                    valuation_method='PHYSICAL_GOLD_PURITY',
                    source='NONE',
                    observed_at=obs_dt,
                    status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                    notes="Gold purity must be between 1.00 and 24.00 karats; cannot default to 24K.",
                )
        else:
            purity_karats = Decimal('24.0')

        fine_grams = quantize_units(grams * (purity_karats / Decimal('24.0')))

        rate_24k = None
        source_name = 'USER_INPUT'
        source_ref = ''
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
                    rate_24k = resolved.price
                    source_name = resolved.source or 'MANUAL_VERIFIED'
                    source_ref = resolved.source_reference or investment.instrument.symbol
                    is_synthetic = resolved.is_synthetic
                    if resolved.effective_at:
                        obs_dt = resolved.effective_at
                    if resolved.status == ResolutionStatus.STALE:
                        val_status = ValuationStatus.STALE_DATA
            except Exception:
                pass

        if rate_24k is None:
            raw_p = details.get('current_price_per_gram') or details.get('user_estimate')
            if raw_p is not None:
                rate_24k = to_decimal(raw_p)
                source_name = 'USER_ESTIMATE'
                val_status = ValuationStatus.ESTIMATED
            elif details.get('purchase_price_per_gram'):
                rate_24k = to_decimal(details['purchase_price_per_gram'])
                source_name = 'PURCHASE_PRICE_FALLBACK'
                val_status = ValuationStatus.ESTIMATED
            else:
                raw_total = details.get('purchase_price')
                if raw_total is not None and fine_grams > 0:
                    rate_24k = to_decimal(raw_total) / fine_grams
                    source_name = 'ACQUISITION_AVERAGE'
                    val_status = ValuationStatus.ESTIMATED
                else:
                    return ValuationResult(
                        current_value=None,
                        valuation_method='PHYSICAL_GOLD_PURITY',
                        source='NONE',
                        observed_at=obs_dt,
                        status=ValuationStatus.MARKET_DATA_UNAVAILABLE,
                        notes='Market rate per gram unavailable.',
                    )

        rate_24k = to_decimal(rate_24k)
        total_value = quantize_currency(fine_grams * rate_24k)

        return ValuationResult(
            current_value=total_value,
            valuation_method='PHYSICAL_GOLD_PURITY',
            source=source_name,
            source_reference=source_ref or 'GOLD-24K-REFERENCE',
            observed_at=obs_dt,
            is_synthetic=is_synthetic,
            currency=investment.currency,
            status=val_status,
            metadata={
                'gross_weight_grams': str(grams),
                'purity_karats': str(purity_karats),
                'fine_weight_24k_grams': str(fine_grams),
                'rate_per_gram_24k': str(rate_24k),
                'is_synthetic': is_synthetic,
            },
        )
