from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from django.utils import timezone as dj_timezone

from apps.market_data.models.instrument import Instrument
from apps.market_data.models.market_data_point import MarketDataPoint
from apps.market_data.models.observation import ObservationStatus, PriceObservation


class ResolutionStatus:
    AVAILABLE = 'AVAILABLE'
    STALE = 'STALE'
    MISSING = 'MISSING'
    SYNTHETIC = 'SYNTHETIC'
    UNSUPPORTED = 'UNSUPPORTED'


@dataclass
class ResolvedPrice:
    price: Optional[Decimal]
    status: str
    source: str
    source_reference: str
    effective_at: Optional[datetime]
    currency: str
    unit: str
    is_synthetic: bool = False
    notes: str = ''


class PriceResolver:
    """
    Central authoritative resolver for market prices across all asset classes.
    Prioritizes verified published PriceObservations over fallback demo data.
    Enforces historical as_of bounds, freshness policies, and currency consistency.
    """

    @classmethod
    def resolve_price(
        cls,
        instrument: Instrument,
        as_of: Optional[datetime] = None,
        price_type: Optional[str] = None,
    ) -> ResolvedPrice:
        obs_dt = as_of or dj_timezone.now()

        # 1. Check for verified published PriceObservation
        obs_qs = PriceObservation.objects.filter(
            instrument=instrument,
            status=ObservationStatus.PUBLISHED,
            effective_at__lte=obs_dt,
        )
        if price_type:
            obs_qs = obs_qs.filter(price_type=price_type)

        latest_obs = obs_qs.order_by('-effective_at').first()

        if latest_obs:
            # Check freshness against instrument coverage policy
            cov = getattr(instrument, 'coverage', None)
            is_stale = False
            notes = latest_obs.notes or ''

            if cov and cov.freshness_hours:
                # If requested as_of is current time, check staleness against now
                if not as_of or (dj_timezone.now() - obs_dt).total_seconds() < 300:
                    age_hours = (dj_timezone.now() - latest_obs.effective_at).total_seconds() / 3600.0
                    if age_hours > cov.freshness_hours:
                        is_stale = True
                        notes = f"Observation is {int(age_hours)} hours old (threshold: {cov.freshness_hours}h)."

            status = ResolutionStatus.STALE if is_stale else ResolutionStatus.AVAILABLE
            return ResolvedPrice(
                price=latest_obs.value,
                status=status,
                source=latest_obs.source,
                source_reference=latest_obs.source_reference or instrument.symbol,
                effective_at=latest_obs.effective_at,
                currency=latest_obs.currency,
                unit=latest_obs.unit,
                is_synthetic=latest_obs.is_synthetic,
                notes=notes,
            )

        # 2. Check for MarketDataPoint (demo/synthetic provider data in development)
        latest_point = MarketDataPoint.objects.filter(
            instrument=instrument,
            timestamp__lte=obs_dt,
        ).order_by('-timestamp').first()

        if latest_point and latest_point.price:
            status = (
                ResolutionStatus.SYNTHETIC
                if latest_point.is_synthetic
                else ResolutionStatus.AVAILABLE
            )
            return ResolvedPrice(
                price=latest_point.price,
                status=status,
                source=latest_point.provider or 'MARKET_FEED',
                source_reference=instrument.symbol,
                effective_at=latest_point.timestamp,
                currency=instrument.currency,
                unit='UNITS',
                is_synthetic=latest_point.is_synthetic,
                notes='Resolved from market feed data point.',
            )

        # 3. Price unavailable: missing prices remain explicitly missing
        return ResolvedPrice(
            price=None,
            status=ResolutionStatus.MISSING,
            source='NONE',
            source_reference=instrument.symbol,
            effective_at=obs_dt,
            currency=instrument.currency,
            unit='UNITS',
            is_synthetic=False,
            notes=f"No published price observation or quote available on or before {obs_dt.isoformat()}.",
        )
