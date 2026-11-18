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
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    volume: Optional[int] = None


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

        # 1. Query verified published PriceObservation records
        obs_qs = PriceObservation.objects.filter(
            instrument=instrument,
            status=ObservationStatus.PUBLISHED,
            effective_at__gte=start_dt,
            effective_at__lte=end_dt,
        )
        if price_type:
            obs_qs = obs_qs.filter(price_type=price_type)

        published_obs = list(obs_qs.order_by('effective_at'))

        if published_obs:
            points = [
                HistoryPoint(
                    timestamp=obs.effective_at,
                    date=obs.effective_at.date().isoformat(),
                    price=obs.value,
                    currency=obs.currency,
                    unit=obs.unit,
                    source=obs.source,
                    is_synthetic=obs.is_synthetic,
                )
                for obs in published_obs
            ]
            first_obs = published_obs[0]
            return HistoryResult(
                supported=True,
                points=points,
                period=period_upper,
                start_date=resolved_start.isoformat(),
                end_date=resolved_end.isoformat(),
                currency=first_obs.currency,
                unit=first_obs.unit,
                message=f"Retrieved {len(points)} verified published observations.",
            )

        # 2. Check Provider capabilities
        provider = provider_registry.get_provider_for_instrument(instrument)
        if not getattr(provider.capabilities, 'historical', False):
            return HistoryResult(
                supported=False,
                points=[],
                period=period_upper,
                start_date=resolved_start.isoformat(),
                end_date=resolved_end.isoformat(),
                currency=instrument.currency,
                unit='UNITS',
                message='Historical market observations are not supported by the provider for this instrument.',
            )

        # 3. Query or populate MarketDataPoints
        db_points = list(
            MarketDataPoint.objects.filter(
                instrument=instrument,
                interval=interval,
                timestamp__gte=start_dt,
                timestamp__lte=end_dt,
            ).order_by('timestamp')
        )

        # If data is sparse, fetch from provider
        if len(db_points) < 2 and getattr(provider, 'get_history', None):
            try:
                fetched = provider.get_history(instrument, resolved_start, resolved_end, interval)
                for p in fetched:
                    # Ignore any future points
                    if p.timestamp.date() > today:
                        continue
                    MarketDataPoint.objects.update_or_create(
                        instrument=instrument,
                        timestamp=p.timestamp,
                        interval=interval,
                        provider=provider.provider_name,
                        defaults={
                            'price': p.price,
                            'open_price': p.open_price,
                            'high_price': p.high_price,
                            'low_price': p.low_price,
                            'close_price': p.close_price,
                            'volume': p.volume,
                            'change_amount': p.change_amount,
                            'change_percent': p.change_percent,
                            'is_synthetic': getattr(provider, 'provider_name', '') == 'DEMO',
                        },
                    )
                db_points = list(
                    MarketDataPoint.objects.filter(
                        instrument=instrument,
                        interval=interval,
                        timestamp__gte=start_dt,
                        timestamp__lte=end_dt,
                    ).order_by('timestamp')
                )
            except Exception:
                # Provider fetch failure handled gracefully
                pass

        points = [
            HistoryPoint(
                timestamp=p.timestamp,
                date=p.timestamp.date().isoformat(),
                price=p.price,
                currency=instrument.currency,
                unit='UNITS',
                source=p.provider or 'FEED',
                is_synthetic=p.is_synthetic,
                open_price=p.open_price,
                high_price=p.high_price,
                low_price=p.low_price,
                volume=p.volume,
            )
            for p in db_points
            if p.timestamp.date() <= today  # Enforce past or today only
        ]

        return HistoryResult(
            supported=True,
            points=points,
            period=period_upper,
            start_date=resolved_start.isoformat(),
            end_date=resolved_end.isoformat(),
            currency=instrument.currency,
            unit='UNITS',
            message=f"Retrieved {len(points)} market feed data points.",
        )
