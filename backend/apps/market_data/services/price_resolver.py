import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Sequence

from django.utils import timezone as dj_timezone

from apps.market_data.models.instrument import Instrument
from apps.market_data.models.market_data_point import MarketDataPoint
from apps.market_data.models.observation import ObservationStatus, PriceObservation


class ResolutionStatus:
    AVAILABLE = 'AVAILABLE'
    STALE = 'STALE'
    MISSING = 'MISSING'
    SYNTHETIC = 'SYNTHETIC'
    AWAITING_VERIFICATION = 'AWAITING_VERIFICATION'
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
    published_at: Optional[datetime] = None
    price_type: Optional[str] = None
    is_synthetic: bool = False
    notes: str = ''
    age_seconds: Optional[int] = None


class PriceResolver:
    """
    Central authoritative resolver for market prices across all asset classes.
    Prioritizes verified published PriceObservations over fallback demo data.
    Enforces historical as_of bounds, freshness policies, currency/unit consistency,
    and excludes superseded observations.
    """

    @classmethod
    def resolve_price(
        cls,
        instrument: Instrument,
        as_of: Optional[datetime] = None,
        price_type: Optional[str] = None,
    ) -> ResolvedPrice:
        obs_dt = as_of or dj_timezone.now()
        cov = getattr(instrument, 'coverage', None)
        target_price_type = price_type or (cov.price_type if cov else None)

        # 1. Check for verified published PriceObservation (excluding superseded ones)
        obs_qs = PriceObservation.objects.filter(
            instrument=instrument,
            status=ObservationStatus.PUBLISHED,
            effective_at__lte=obs_dt,
        ).exclude(corrections__status=ObservationStatus.PUBLISHED)

        if target_price_type:
            obs_qs = obs_qs.filter(price_type=target_price_type)

        latest_obs = obs_qs.order_by('-effective_at', '-published_at', '-created_at').first()

        if latest_obs:
            # Currency & unit integrity check against coverage policy
            if cov:
                if cov.currency and latest_obs.currency != cov.currency:
                    return ResolvedPrice(
                        price=None,
                        status=ResolutionStatus.UNSUPPORTED,
                        source=latest_obs.source,
                        source_reference=instrument.symbol,
                        effective_at=None,
                        published_at=None,
                        price_type=latest_obs.price_type,
                        currency=instrument.currency,
                        unit=cov.unit if cov else latest_obs.unit,
                        notes=f"Currency mismatch: observation in {latest_obs.currency}, coverage requires {cov.currency}.",
                    )

            # Check freshness against instrument coverage policy
            is_stale = False
            notes = latest_obs.notes or ''
            age_sec = None

            if latest_obs.published_at:
                age_sec = max(0, int((dj_timezone.now() - latest_obs.published_at).total_seconds()))

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
                published_at=latest_obs.published_at,
                price_type=latest_obs.price_type,
                currency=latest_obs.currency,
                unit=latest_obs.unit,
                is_synthetic=latest_obs.is_synthetic,
                notes=notes,
                age_seconds=age_sec,
            )

        # 2. Check if a relevant observation is in PENDING_REVIEW (awaiting verification)
        has_pending = PriceObservation.objects.filter(
            instrument=instrument,
            status=ObservationStatus.PENDING_REVIEW,
            effective_at__lte=obs_dt,
        ).exists()

        if has_pending:
            return ResolvedPrice(
                price=None,
                status=ResolutionStatus.AWAITING_VERIFICATION,
                source='MANUAL_OPERATOR',
                source_reference=instrument.symbol,
                effective_at=None,
                published_at=None,
                price_type=target_price_type,
                currency=instrument.currency,
                unit=cov.unit if cov else 'UNITS',
                is_synthetic=False,
                notes='Price observation has been drafted and is awaiting verification by publisher.',
            )

        # 3. Check for MarketDataPoint (demo/synthetic provider data in development)
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
                published_at=latest_point.created_at if hasattr(latest_point, 'created_at') else latest_point.timestamp,
                price_type=target_price_type or 'LTP',
                currency=instrument.currency,
                unit='UNITS',
                is_synthetic=latest_point.is_synthetic,
                notes='Resolved from market feed data point.',
            )

        # 4. Price unavailable: missing prices must have price=None, effective_at=None, published_at=None
        return ResolvedPrice(
            price=None,
            status=ResolutionStatus.MISSING,
            source='NONE',
            source_reference=instrument.symbol,
            effective_at=None,
            published_at=None,
            price_type=target_price_type,
            currency=instrument.currency,
            unit=cov.unit if cov else 'UNITS',
            is_synthetic=False,
            notes=f"No published price observation or quote available on or before {obs_dt.isoformat()}.",
        )

    @classmethod
    def resolve_prices_bulk(
        cls,
        instruments: Sequence[Instrument],
        as_of: Optional[datetime] = None,
    ) -> Dict[uuid.UUID, ResolvedPrice]:
        """
        High-performance bulk price resolver for batches of instruments.
        Eliminates N+1 queries in dashboard and watchlist operations.
        """
        if not instruments:
            return {}

        obs_dt = as_of or dj_timezone.now()
        unique_insts = {inst.id: inst for inst in instruments}
        inst_ids = list(unique_insts.keys())

        # 1. Batch query latest published observations (excluding superseded)
        published_qs = (
            PriceObservation.objects.filter(
                instrument_id__in=inst_ids,
                status=ObservationStatus.PUBLISHED,
                effective_at__lte=obs_dt,
            )
            .exclude(corrections__status=ObservationStatus.PUBLISHED)
            .select_related('instrument', 'instrument__coverage')
            .order_by('instrument_id', '-effective_at', '-published_at', '-created_at')
        )

        latest_by_inst: Dict[uuid.UUID, PriceObservation] = {}
        for obs in published_qs:
            if obs.instrument_id not in latest_by_inst:
                latest_by_inst[obs.instrument_id] = obs

        # 2. Check pending review observations in bulk for remaining instruments
        missing_ids = [iid for iid in inst_ids if iid not in latest_by_inst]
        pending_set = set(
            PriceObservation.objects.filter(
                instrument_id__in=missing_ids,
                status=ObservationStatus.PENDING_REVIEW,
                effective_at__lte=obs_dt,
            ).values_list('instrument_id', flat=True)
        )

        # 3. Check MarketDataPoints for remaining
        remaining_ids = [iid for iid in missing_ids if iid not in pending_set]
        points_qs = (
            MarketDataPoint.objects.filter(
                instrument_id__in=remaining_ids,
                timestamp__lte=obs_dt,
            )
            .order_by('instrument_id', '-timestamp')
        )
        point_by_inst: Dict[uuid.UUID, MarketDataPoint] = {}
        for pt in points_qs:
            if pt.instrument_id not in point_by_inst:
                point_by_inst[pt.instrument_id] = pt

        results: Dict[uuid.UUID, ResolvedPrice] = {}
        now = dj_timezone.now()

        for inst_id, inst in unique_insts.items():
            cov = getattr(inst, 'coverage', None)

            if inst_id in latest_by_inst:
                latest_obs = latest_by_inst[inst_id]

                # Currency validation
                if cov and cov.currency and latest_obs.currency != cov.currency:
                    results[inst_id] = ResolvedPrice(
                        price=None,
                        status=ResolutionStatus.UNSUPPORTED,
                        source=latest_obs.source,
                        source_reference=inst.symbol,
                        effective_at=None,
                        published_at=None,
                        price_type=latest_obs.price_type,
                        currency=inst.currency,
                        unit=cov.unit if cov else latest_obs.unit,
                        notes=f"Currency mismatch: {latest_obs.currency} vs {cov.currency}.",
                    )
                    continue

                is_stale = False
                notes = latest_obs.notes or ''
                age_sec = None
                if latest_obs.published_at:
                    age_sec = max(0, int((now - latest_obs.published_at).total_seconds()))

                if cov and cov.freshness_hours:
                    if not as_of or (now - obs_dt).total_seconds() < 300:
                        age_hours = (now - latest_obs.effective_at).total_seconds() / 3600.0
                        if age_hours > cov.freshness_hours:
                            is_stale = True
                            notes = f"Observation is {int(age_hours)} hours old (threshold: {cov.freshness_hours}h)."

                results[inst_id] = ResolvedPrice(
                    price=latest_obs.value,
                    status=ResolutionStatus.STALE if is_stale else ResolutionStatus.AVAILABLE,
                    source=latest_obs.source,
                    source_reference=latest_obs.source_reference or inst.symbol,
                    effective_at=latest_obs.effective_at,
                    published_at=latest_obs.published_at,
                    price_type=latest_obs.price_type,
                    currency=latest_obs.currency,
                    unit=latest_obs.unit,
                    is_synthetic=latest_obs.is_synthetic,
                    notes=notes,
                    age_seconds=age_sec,
                )

            elif inst_id in pending_set:
                results[inst_id] = ResolvedPrice(
                    price=None,
                    status=ResolutionStatus.AWAITING_VERIFICATION,
                    source='MANUAL_OPERATOR',
                    source_reference=inst.symbol,
                    effective_at=None,
                    published_at=None,
                    price_type=cov.price_type if cov else None,
                    currency=inst.currency,
                    unit=cov.unit if cov else 'UNITS',
                    is_synthetic=False,
                    notes='Awaiting verification by publisher.',
                )

            elif inst_id in point_by_inst and point_by_inst[inst_id].price:
                pt = point_by_inst[inst_id]
                results[inst_id] = ResolvedPrice(
                    price=pt.price,
                    status=ResolutionStatus.SYNTHETIC if pt.is_synthetic else ResolutionStatus.AVAILABLE,
                    source=pt.provider or 'MARKET_FEED',
                    source_reference=inst.symbol,
                    effective_at=pt.timestamp,
                    published_at=pt.timestamp,
                    price_type=cov.price_type if cov else 'LTP',
                    currency=inst.currency,
                    unit='UNITS',
                    is_synthetic=pt.is_synthetic,
                    notes='Resolved from market feed data point.',
                )

            else:
                results[inst_id] = ResolvedPrice(
                    price=None,
                    status=ResolutionStatus.MISSING,
                    source='NONE',
                    source_reference=inst.symbol,
                    effective_at=None,
                    published_at=None,
                    price_type=cov.price_type if cov else None,
                    currency=inst.currency,
                    unit=cov.unit if cov else 'UNITS',
                    is_synthetic=False,
                    notes=f"No published price observation on or before {obs_dt.isoformat()}.",
                )

        return results
