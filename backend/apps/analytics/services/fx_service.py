import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Tuple

from apps.analytics.models.fx import FXRate

logger = logging.getLogger(__name__)

FOUR_PLACES = Decimal('0.0001')
SIX_PLACES = Decimal('0.000001')
MAX_STALENESS_DAYS = 7


class FXConversionService:
    """
    Authoritative FX Conversion Engine supporting direct, inverse, and cross-currency rates
    with explicit staleness tracking and missing-rate detection.
    """

    @classmethod
    def get_rate(
        cls,
        from_currency: str,
        to_currency: str,
        as_of_date: date,
        max_staleness_days: int = MAX_STALENESS_DAYS,
    ) -> Tuple[Optional[Decimal], str]:
        """
        Resolves effective exchange rate to convert 1 unit of `from_currency` into `to_currency`.
        Returns (rate, status) where status is one of:
        - 'SAME_CURRENCY'
        - 'EXACT' (effective on as_of_date)
        - 'STALE' (effective earlier within max_staleness_days)
        - 'MISSING' (no rate found)
        """
        from_c = (from_currency or '').upper().strip()
        to_c = (to_currency or '').upper().strip()

        if not from_c or not to_c:
            return None, 'MISSING'

        if from_c == to_c:
            return Decimal('1.000000'), 'SAME_CURRENCY'

        # 1. Direct pair lookup: 1 from_c = rate to_c
        direct = FXRate.objects.filter(
            base_currency=from_c,
            quote_currency=to_c,
            effective_date__lte=as_of_date,
            is_published=True,
        ).order_by('-effective_date').first()

        if direct:
            age_days = (as_of_date - direct.effective_date).days
            if age_days <= max_staleness_days:
                status = 'EXACT' if age_days == 0 else 'STALE'
                return direct.rate.quantize(SIX_PLACES, rounding=ROUND_HALF_UP), status

        # 2. Inverse pair lookup: 1 to_c = inv_rate from_c => 1 from_c = (1 / inv_rate) to_c
        inverse = FXRate.objects.filter(
            base_currency=to_c,
            quote_currency=from_c,
            effective_date__lte=as_of_date,
            is_published=True,
        ).order_by('-effective_date').first()

        if inverse and inverse.rate > Decimal('0'):
            age_days = (as_of_date - inverse.effective_date).days
            if age_days <= max_staleness_days:
                status = 'EXACT' if age_days == 0 else 'STALE'
                rate = (Decimal('1') / inverse.rate).quantize(SIX_PLACES, rounding=ROUND_HALF_UP)
                return rate, status

        # 3. Triangulation via USD if neither currency is USD
        if from_c != 'USD' and to_c != 'USD':
            rate_from_usd, status_from = cls.get_rate(from_c, 'USD', as_of_date, max_staleness_days)
            rate_usd_to, status_to = cls.get_rate('USD', to_c, as_of_date, max_staleness_days)

            if rate_from_usd and rate_usd_to:
                combined_rate = (rate_from_usd * rate_usd_to).quantize(SIX_PLACES, rounding=ROUND_HALF_UP)
                status = 'EXACT' if (status_from == 'EXACT' and status_to == 'EXACT') else 'STALE'
                return combined_rate, status

        return None, 'MISSING'

    @classmethod
    def convert_amount(
        cls,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        as_of_date: date,
        max_staleness_days: int = MAX_STALENESS_DAYS,
    ) -> Tuple[Decimal, Optional[Decimal], str]:
        """
        Converts financial amount from `from_currency` to `to_currency` as of `as_of_date`.
        Returns:
            (converted_amount, rate_used, status)
        If status is 'MISSING', returns (original_amount, None, 'MISSING').
        """
        rate, status = cls.get_rate(from_currency, to_currency, as_of_date, max_staleness_days)
        if rate is None:
            return amount, None, 'MISSING'

        converted = (amount * rate).quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)
        return converted, rate, status
