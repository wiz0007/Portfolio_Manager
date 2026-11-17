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

        if investment.instrument:
            try:
                quote = MarketDataService.get_latest_quote(investment.instrument)
                if quote and quote.price is not None:
                    rate_24k = quote.price
                    source_name = quote.provider or 'MARKET_FEED'
                    source_ref = investment.instrument.symbol
                    is_synthetic = quote.is_synthetic
                    if quote.timestamp:
                        obs_dt = quote.timestamp
            except Exception:
                pass

        if rate_24k is None:
            raw_p = details.get('current_price_per_gram') or details.get('purchase_price_per_gram')
            if raw_p is not None:
                rate_24k = to_decimal(raw_p)
                source_name = 'USER_INPUT'
            else:
                raw_total = details.get('purchase_price')
                if raw_total is not None and fine_grams > 0:
                    rate_24k = to_decimal(raw_total) / fine_grams
                    source_name = 'ACQUISITION_AVERAGE'
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
            status=ValuationStatus.SUCCESS,
            metadata={
                'gross_weight_grams': str(grams),
                'purity_karats': str(purity_karats),
                'fine_weight_24k_grams': str(fine_grams),
                'rate_per_gram_24k': str(rate_24k),
                'is_synthetic': is_synthetic,
            },
        )
