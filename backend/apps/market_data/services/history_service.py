from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from django.core.exceptions import ValidationError
from django.utils import timezone as dj_timezone

from apps.market_data.models.instrument import Instrument
from apps.market_data.models.market_data_point import MarketDataPoint
from apps.market_data.models.observation import ObservationStatus, PriceObservation
from apps.market_data.providers.registry import provider_registry


@dataclass
class HistoryPoint:
    timestamp: datetime
    date: str
    price: Decimal
    currency: str
    unit: str
    source: str
    is_synthetic: bool = False
    trust_class: str = 'VERIFIED_OFFICIAL'
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    volume: Optional[int] = None
    price_type: str = 'LTP'
    published_at: Optional[datetime] = None


@dataclass
class HistoryResult:
    supported: bool
    points: List[HistoryPoint] = field(default_factory=list)
    period: str = '1M'
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    currency: str = 'INR'
    unit: str = 'UNITS'
    message: str = ''
    trust_class: str = 'VERIFIED_OFFICIAL'


PERIOD_DAYS_MAP = {
    '1D': 1,
    '1W': 7,
    '1M': 30,
    '3M': 90,
    '6M': 180,
    '1Y': 365,
    'ALL': 365 * 5,  # 5 years max history lookup
}


class MarketHistoryService:
    """
    Authoritative service for historical price series retrieval.
    Enforces strict chronological ordering, rejects future bounds,
    and returns verified published observations before provider fallbacks.
    """

    @classmethod
    def get_history(
        cls,
        instrument: Instrument,
        period: str = '1M',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        interval: str = '1D',
        price_type: Optional[str] = None,
    ) -> HistoryResult:
        today = dj_timezone.now().date()
        period_upper = period.upper()

        if start_date or end_date:
            resolved_end = end_date or today
            resolved_start = start_date or (resolved_end - timedelta(days=30))
        elif period_upper == 'ALL':
            resolved_end = today
            # Dynamically determine earliest available observation date
            earliest_obs = (
                PriceObservation.objects.filter(
                    instrument=instrument,
                    status=ObservationStatus.PUBLISHED,
                    effective_at__lte=datetime.combine(resolved_end, datetime.max.time(), tzinfo=timezone.utc),
                )
                .exclude(corrections__status=ObservationStatus.PUBLISHED)
                .order_by('effective_at')
                .first()
            )
            if earliest_obs:
                resolved_start = earliest_obs.effective_at.date()
            else:
                earliest_mdp = (
                    MarketDataPoint.objects.filter(
                        instrument=instrument,
                        timestamp__lte=datetime.combine(resolved_end, datetime.max.time(), tzinfo=timezone.utc),
                    )
                    .order_by('timestamp')
                    .first()
                )
                if earliest_mdp:
                    resolved_start = earliest_mdp.timestamp.date()
                else:
                    resolved_start = today - timedelta(days=365 * 5)
        else:
            days = PERIOD_DAYS_MAP.get(period_upper, 30)
            resolved_end = today
            resolved_start = today - timedelta(days=days)

        # Bounds validation
        if resolved_end > today:
            resolved_end = today  # Capped strictly at today, no future observations

        if resolved_start > resolved_end:
            raise ValidationError('start_date cannot be greater than end_date.')

        start_dt = datetime.combine(resolved_start, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(resolved_end, datetime.max.time(), tzinfo=timezone.utc)

        # 1. Query verified published PriceObservation records (excluding superseded ones)
        obs_qs = (
            PriceObservation.objects.filter(
                instrument=instrument,
                status=ObservationStatus.PUBLISHED,
                effective_at__gte=start_dt,
                effective_at__lte=end_dt,
            )
            .exclude(corrections__status=ObservationStatus.PUBLISHED)
        )
        if price_type:
            obs_qs = obs_qs.filter(price_type=price_type)

        published_obs = list(obs_qs.order_by('effective_at', 'published_at'))

        if published_obs:
            # Deduplicate strictly to 1 observation per trading date (latest published wins)
            obs_by_date = {}
            for obs in published_obs:
                obs_by_date[obs.effective_at.date()] = obs
            deduped_obs = sorted(obs_by_date.values(), key=lambda o: o.effective_at)

            points = [
                HistoryPoint(
                    timestamp=obs.effective_at,
                    date=obs.effective_at.date().isoformat(),
                    price=obs.value,
                    currency=obs.currency,
                    unit=obs.unit,
                    source=obs.source,
                    is_synthetic=obs.is_synthetic,
                    trust_class=getattr(obs, 'trust_class', 'VERIFIED_OFFICIAL'),
                    open_price=obs.open_price,
                    high_price=obs.high_price,
                    low_price=obs.low_price,
                    volume=obs.volume,
                    price_type=obs.price_type,
                    published_at=obs.published_at,
                )
                for obs in deduped_obs
            ]
            first_obs = deduped_obs[0]
            trust = getattr(first_obs, 'trust_class', 'VERIFIED_OFFICIAL')
            return HistoryResult(
                supported=True,
                points=points,
                period=period_upper,
                start_date=resolved_start.isoformat(),
                end_date=resolved_end.isoformat(),
                currency=first_obs.currency,
                unit=first_obs.unit,
                message=f"Retrieved {len(points)} verified published observations.",
                trust_class=trust,
            )

        # 2. Check non-synthetic MarketDataPoints in database
        db_points = list(
            MarketDataPoint.objects.filter(
                instrument=instrument,
                interval=interval,
                timestamp__gte=start_dt,
                timestamp__lte=end_dt,
                is_synthetic=False,
            ).order_by('timestamp')
        )

        if db_points:
            points = [
                HistoryPoint(
                    timestamp=p.timestamp,
                    date=p.timestamp.date().isoformat(),
                    price=p.price,
                    currency=instrument.currency,
                    unit='UNITS',
                    source=p.provider or 'FEED',
                    is_synthetic=False,
                    trust_class='VERIFIED_OFFICIAL',
                    open_price=p.open_price,
                    high_price=p.high_price,
                    low_price=p.low_price,
                    volume=p.volume,
                )
                for p in db_points
                if p.timestamp.date() <= today
            ]
            return HistoryResult(
                supported=True,
                points=points,
                period=period_upper,
                start_date=resolved_start.isoformat(),
                end_date=resolved_end.isoformat(),
                currency=instrument.currency,
                unit='UNITS',
                message=f"Retrieved {len(points)} verified historical data points.",
                trust_class='VERIFIED_OFFICIAL',
            )

        # 3. For strictly demo instruments (explicitly flagged demo only)
        provider = provider_registry.get_provider_for_instrument(instrument)
        if getattr(provider, 'provider_name', '') == 'DEMO' and getattr(instrument, 'is_synthetic', False):
            fetched = provider.get_history(instrument, resolved_start, resolved_end, interval)
            points = [
                HistoryPoint(
                    timestamp=p.timestamp,
                    date=p.timestamp.date().isoformat(),
                    price=p.price,
                    currency=instrument.currency,
                    unit='UNITS',
                    source='DEMO',
                    is_synthetic=True,
                    trust_class='SYNTHETIC',
                    open_price=p.open_price,
                    high_price=p.high_price,
                    low_price=p.low_price,
                    volume=p.volume,
                )
                for p in fetched
                if p.timestamp.date() <= today
            ]
            return HistoryResult(
                supported=True,
                points=points,
                period=period_upper,
                start_date=resolved_start.isoformat(),
                end_date=resolved_end.isoformat(),
                currency=instrument.currency,
                unit='UNITS',
                message="Retrieved synthetic demonstration data points.",
                trust_class='SYNTHETIC',
            )

        # 4. If no verified history exists, return explicit empty/unsupported result without synthetic noise
        return HistoryResult(
            supported=True,
            points=[],
            period=period_upper,
            start_date=resolved_start.isoformat(),
            end_date=resolved_end.isoformat(),
            currency=instrument.currency,
            unit='UNITS',
            message='No verified historical market observations available for this instrument.',
            trust_class='UNVERIFIED',
        )
