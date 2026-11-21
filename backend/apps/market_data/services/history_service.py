from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
import uuid
from decimal import Decimal
from typing import List, Optional
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone as dj_timezone

from apps.market_data.models.observation import ObservationStatus, PriceObservation
from apps.market_data.models.coverage import InstrumentCoverage
from apps.market_data.models.series import MarketDataSeries

MARKET_TZ = ZoneInfo('Asia/Kolkata')
PERIOD_DAYS_MAP = {
    '1D': 1, '1W': 7, '1M': 30, '3M': 90,
    '6M': 180, '1Y': 365, 'ALL': 365 * 5,
}


@dataclass
class HistoryPoint:
    timestamp: datetime
    date: str
    price: Decimal
    currency: str
    unit: str
    source: str
    is_synthetic: bool = False
    trust_class: str = 'UNVERIFIED'
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
    trust_class: str = 'UNVERIFIED'
    series_id: Optional[str] = None
    data_version: Optional[int] = None
    last_published_at: Optional[datetime] = None


class MarketHistoryService:
    """Reads one exact, published PriceObservation series; never falls back to legacy stores/providers."""

    @classmethod
    def get_history(
        cls,
        instrument,
        period: str = '1M',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        interval: str = '1D',
        price_type: Optional[str] = None,
        series_id: Optional[str] = None,
    ) -> HistoryResult:
        period_upper = (period or '1M').upper()
        interval_upper = (interval or '1D').upper()
        if period_upper not in PERIOD_DAYS_MAP:
            raise ValidationError(f'Unsupported period: {period_upper}.')
        # The storage is daily. Do not label daily points as weekly/monthly/yearly.
        if interval_upper != '1D':
            raise ValidationError('Only 1D frequency is currently supported; weekly/monthly aggregation is not implemented.')

        today = dj_timezone.now().astimezone(MARKET_TZ).date()
        resolved_end = min(end_date or today, today)
        if period_upper == 'ALL' and not start_date:
            resolved_start = resolved_end - timedelta(days=PERIOD_DAYS_MAP['ALL'])
        else:
            resolved_start = start_date or (resolved_end - timedelta(days=PERIOD_DAYS_MAP[period_upper]))
        if resolved_start > resolved_end:
            raise ValidationError('start_date cannot be greater than end_date.')
        if (resolved_end - resolved_start).days > 365 * 5:
            raise ValidationError('History range cannot exceed five years.')

        series_qs = MarketDataSeries.objects.using('market_data').filter(
            instrument_id=instrument.id, is_active=True
        )
        if price_type:
            series_qs = series_qs.filter(price_type=price_type)
        if series_id:
            try:
                series_uuid = uuid.UUID(str(series_id))
            except (ValueError, TypeError, AttributeError):
                raise ValidationError('series_id must be a valid UUID.')
            series_qs = series_qs.filter(pk=series_uuid)
        series_list = list(series_qs.order_by('id')[:2])
        if len(series_list) > 1 and not series_id:
            coverage = InstrumentCoverage.objects.using('market_data').filter(instrument_id=instrument.id).first()
            if coverage and coverage.preferred_source:
                preferred = list(series_qs.filter(source=coverage.preferred_source).order_by('id')[:2])
                if len(preferred) == 1:
                    series_list = preferred
        if not series_list:
            return HistoryResult(
                supported=True, points=[], period=period_upper,
                start_date=resolved_start.isoformat(), end_date=resolved_end.isoformat(),
                currency=instrument.currency, message='No active market-data series exists for this instrument.',
            )
        if len(series_list) > 1:
            raise ValidationError('Multiple active price series match this instrument. Supply an exact series_id.')
        series = series_list[0]

        # Market dates are interpreted in Asia/Kolkata, then converted to UTC for storage queries.
        start_dt = datetime.combine(resolved_start, time.min, tzinfo=MARKET_TZ).astimezone(ZoneInfo('UTC'))
        end_dt = datetime.combine(resolved_end + timedelta(days=1), time.min, tzinfo=MARKET_TZ).astimezone(ZoneInfo('UTC'))
        observations_qs = PriceObservation.objects.using('market_data').filter(
            instrument_id=instrument.id,
            series_id=series.id,
            price_type=series.price_type,
            status=ObservationStatus.PUBLISHED,
            effective_at__gte=start_dt,
            effective_at__lt=end_dt,
        )
        if getattr(settings, 'MARKET_DATA_PROVIDER_MODE', 'DEMO') != 'DEMO':
            observations_qs = observations_qs.filter(
                is_synthetic=False,
                trust_class__in=['VERIFIED_OFFICIAL', 'VERIFIED_PERMITTED_SECONDARY', 'MANUAL_VERIFIED', 'CORRECTED'],
            )
        observations = list(
            observations_qs.exclude(corrections__status=ObservationStatus.PUBLISHED)
            .order_by('effective_at', 'published_at', 'created_at')
        )

        # For a given market date, latest approved publication wins, without mixing series.
        by_market_date = {}
        for obs in observations:
            market_date = obs.effective_at.astimezone(MARKET_TZ).date()
            by_market_date[market_date] = obs
        ordered = [by_market_date[key] for key in sorted(by_market_date)]
        points = [
            HistoryPoint(
                timestamp=obs.effective_at,
                date=obs.effective_at.astimezone(MARKET_TZ).date().isoformat(),
                price=obs.value, currency=obs.currency, unit=obs.unit,
                source=obs.source, is_synthetic=obs.is_synthetic,
                trust_class=obs.trust_class, open_price=obs.open_price,
                high_price=obs.high_price, low_price=obs.low_price,
                volume=obs.volume, price_type=obs.price_type,
                published_at=obs.published_at,
            ) for obs in ordered
        ]
        return HistoryResult(
            supported=True, points=points, period=period_upper,
            start_date=resolved_start.isoformat(), end_date=resolved_end.isoformat(),
            currency=series.currency, unit=series.unit,
            message=f'Retrieved {len(points)} observations from exact series {series.id}.',
            trust_class=(points[-1].trust_class if points else 'UNVERIFIED'),
            series_id=str(series.id), data_version=series.data_version,
            last_published_at=series.last_published_at,
        )
