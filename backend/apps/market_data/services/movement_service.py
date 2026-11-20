from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from django.utils import timezone as dj_timezone

from apps.market_data.models.instrument import Instrument
from apps.market_data.models.observation import ObservationStatus, PriceObservation


class MovementStatus:
    CALCULATED = 'CALCULATED'
    UNAVAILABLE = 'UNAVAILABLE'
    ZERO_BASE = 'ZERO_BASE'
    INCOMPATIBLE = 'INCOMPATIBLE'


@dataclass
class PriceMovement:
    change_amount: Optional[Decimal]
    change_percent: Optional[Decimal]
    previous_price: Optional[Decimal]
    previous_effective_at: Optional[datetime]
    status: str
    notes: str = ''


class PriceMovementService:
    """
    Authoritative service for calculating price movement across trading sessions.
    Strictly uses decimal-safe arithmetic, enforces unit/currency compatibility,
    and returns explicit UNAVAILABLE states when prior data is missing or zero.
    """

    @classmethod
    def calculate_movement(
        cls,
        instrument: Instrument,
        current_price: Optional[Decimal],
        current_dt: Optional[datetime] = None,
        price_type: Optional[str] = None,
        currency: Optional[str] = None,
        unit: Optional[str] = None,
        series_id: Optional[str] = None,
    ) -> PriceMovement:
        if current_price is None or current_price <= Decimal('0'):
            return PriceMovement(
                change_amount=None,
                change_percent=None,
                previous_price=None,
                previous_effective_at=None,
                status=MovementStatus.UNAVAILABLE,
                notes='Current price is unavailable or non-positive.',
            )

        ref_dt = current_dt or dj_timezone.now()
        expected_currency = currency or instrument.currency

        # Look for previous published PriceObservation strictly before ref_dt (excluding superseded)
        obs_qs = (
            PriceObservation.objects.using('market_data').filter(
                instrument=instrument,
                status=ObservationStatus.PUBLISHED,
                effective_at__lt=ref_dt,
            )
            .exclude(corrections__status=ObservationStatus.PUBLISHED)
        )
        if series_id:
            obs_qs = obs_qs.filter(series_id=series_id)
        if price_type:
            obs_qs = obs_qs.filter(price_type=price_type)
        if unit:
            obs_qs = obs_qs.filter(unit=unit)

        prev_obs = obs_qs.order_by('-effective_at').first()

        if prev_obs:
            if prev_obs.currency != expected_currency:
                return PriceMovement(
                    change_amount=None,
                    change_percent=None,
                    previous_price=None,
                    previous_effective_at=prev_obs.effective_at,
                    status=MovementStatus.INCOMPATIBLE,
                    notes=f"Currency mismatch: current {expected_currency} vs previous {prev_obs.currency}.",
                )

            if prev_obs.value <= Decimal('0'):
                return PriceMovement(
                    change_amount=None,
                    change_percent=None,
                    previous_price=prev_obs.value,
                    previous_effective_at=prev_obs.effective_at,
                    status=MovementStatus.ZERO_BASE,
                    notes='Previous price is zero; percentage change cannot be computed.',
                )

            change_amount = current_price - prev_obs.value
            pct_raw = (change_amount / prev_obs.value) * Decimal('100')
            change_percent = pct_raw.quantize(Decimal('0.0001'))

            return PriceMovement(
                change_amount=change_amount,
                change_percent=change_percent,
                previous_price=prev_obs.value,
                previous_effective_at=prev_obs.effective_at,
                status=MovementStatus.CALCULATED,
                notes='Calculated from authoritative published observations.',
            )

        # No previous authoritative observation found
        return PriceMovement(
            change_amount=None,
            change_percent=None,
            previous_price=None,
            previous_effective_at=None,
            status=MovementStatus.UNAVAILABLE,
            notes='No eligible prior price observation exists for comparison in this series.',
        )
