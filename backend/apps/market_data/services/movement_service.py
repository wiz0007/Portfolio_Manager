from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from django.db.models import F, Window
from django.db.models.functions import RowNumber
from django.utils import timezone as dj_timezone

from apps.market_data.models.instrument import Instrument
from apps.market_data.models.observation import ObservationStatus, PriceObservation, TrustClass


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
    def calculate_movements_bulk(cls, resolved_map):
        """Resolve previous observations for many exact series in one bounded query."""
        eligible = {
            key: value for key, value in resolved_map.items()
            if value and value.price is not None and value.series_id and value.effective_at
        }
        if not eligible:
            return {}
        series_ids = list({value.series_id for value in eligible.values()})
        ranked = (
            PriceObservation.objects.using('market_data').filter(
                series_id__in=series_ids,
                status=ObservationStatus.PUBLISHED,
                is_synthetic=False,
                trust_class__in=[TrustClass.VERIFIED_OFFICIAL, TrustClass.VERIFIED_PERMITTED_SECONDARY,
                                 TrustClass.MANUAL_VERIFIED, TrustClass.CORRECTED],
            )
            .exclude(corrections__status=ObservationStatus.PUBLISHED)
            .annotate(row_number=Window(
                expression=RowNumber(), partition_by=[F('series_id')],
                order_by=[F('effective_at').desc(), F('published_at').desc(), F('created_at').desc()],
            ))
            .filter(row_number__lte=2)
            .order_by('series_id', '-effective_at', '-published_at', '-created_at')
        )
        previous_by_series = {}
        for observation in ranked:
            previous_by_series.setdefault(str(observation.series_id), []).append(observation)

        results = {}
        for key, current in eligible.items():
            candidates = previous_by_series.get(current.series_id, [])
            previous = next((obs for obs in candidates if obs.effective_at < current.effective_at), None)
            if previous is None:
                results[key] = PriceMovement(None, None, None, None, MovementStatus.UNAVAILABLE,
                                             'No eligible prior observation exists in this exact series.')
            elif previous.currency != current.currency or previous.unit != current.unit or previous.price_type != current.price_type:
                results[key] = PriceMovement(None, None, previous.value, previous.effective_at,
                                             MovementStatus.INCOMPATIBLE,
                                             'Previous observation has incompatible currency, unit or price type.')
            elif previous.value <= Decimal('0'):
                results[key] = PriceMovement(None, None, previous.value, previous.effective_at,
                                             MovementStatus.ZERO_BASE, 'Previous price is zero.')
            else:
                change = current.price - previous.value
                percent = (change / previous.value * Decimal('100')).quantize(Decimal('0.0001'))
                results[key] = PriceMovement(change, percent, previous.value, previous.effective_at,
                                             MovementStatus.CALCULATED,
                                             'Calculated from the same published price series.')
        return results

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
                trust_class__in=[TrustClass.VERIFIED_OFFICIAL, TrustClass.VERIFIED_PERMITTED_SECONDARY, TrustClass.MANUAL_VERIFIED, TrustClass.CORRECTED],
            )
            .exclude(corrections__status=ObservationStatus.PUBLISHED)
        )
        if series_id:
            obs_qs = obs_qs.filter(series_id=series_id, is_synthetic=False)
        if price_type:
            obs_qs = obs_qs.filter(price_type=price_type)
        if unit:
            obs_qs = obs_qs.filter(unit=unit)

        prev_obs = obs_qs.order_by('-effective_at', '-published_at', '-created_at').first()

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
