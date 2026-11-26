import logging
from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.market_data.adapters import (
    BaseHistoricalAdapter,
    CommodityAdapter,
    EquityIndexAdapter,
    MutualFundAdapter,
    NormalizedObservation,
)
from apps.market_data.models.instrument import Instrument
from apps.market_data.models.coverage import InstrumentCoverage
from apps.market_data.models.observation import ObservationStatus, PriceObservation
from apps.market_data.models.series import MarketDataSeries

logger = logging.getLogger(__name__)


class HistoricalBackfillService:
    """
    Controlled, idempotent backfill pipeline for Indian financial instruments.
    Orchestrates discovery, planning, acquisition, validation, and atomic staging.
    """

    def __init__(self, publisher=None):
        User = get_user_model()
        self.publisher = publisher
        if self.publisher is None:
            self.publisher = User.objects.filter(is_active=True).filter(
                Q(is_superuser=True) | Q(is_staff=True) | Q(groups__name='MarketDataPublisher')
            ).distinct().order_by('-is_superuser', '-is_staff', 'date_joined').first()
        self.adapters: List[BaseHistoricalAdapter] = [
            EquityIndexAdapter(),
            MutualFundAdapter(),
            CommodityAdapter(),
        ]

    def _select_adapter(self, instrument: Instrument) -> Optional[BaseHistoricalAdapter]:
        for adapter in self.adapters:
            if adapter.supports(instrument):
                return adapter
        return None

    @staticmethod
    def _is_authorized_publisher(user) -> bool:
        if user is None or not getattr(user, 'is_active', False):
            return False
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return True
        return user.groups.filter(name='MarketDataPublisher').exists()

    def plan_coverage(self, instrument: Instrument, target_days: int = 1825) -> Tuple[date, date, bool]:
        """
        Determines if backfill is required and the missing date range.
        Defaults to 5-year coverage window (1825 days).
        Returns (start_date, end_date, needs_backfill).
        """
        today = timezone.localtime(timezone.now(), ZoneInfo('Asia/Kolkata')).date()
        target_start = today - timedelta(days=target_days)
        # A row-count threshold cannot prove calendar coverage. Re-run the bounded,
        # idempotent acquisition and let exact observation uniqueness suppress duplicates.
        # A real exchange calendar can later optimize this without weakening correctness.
        return target_start, today, True

    def validate_observation(self, obs: NormalizedObservation) -> bool:
        """Validate financial values and interpret naive timestamps as market-local."""
        if obs.value is None or not obs.value.is_finite() or obs.value <= Decimal('0'):
            return False
        if obs.high_price is not None and obs.low_price is not None:
            if obs.high_price < obs.low_price:
                return False
        effective_at = obs.effective_at
        if effective_at is None:
            return False
        if timezone.is_naive(effective_at):
            effective_at = timezone.make_aware(effective_at, ZoneInfo('Asia/Kolkata'))
        market_date = effective_at.astimezone(ZoneInfo('Asia/Kolkata')).date()
        today = timezone.localtime(timezone.now(), ZoneInfo('Asia/Kolkata')).date()
        return market_date <= today

    def backfill_instrument(
        self,
        instrument: Instrument,
        target_days: int = 1825,
    ) -> Dict[str, any]:
        """
        Acquires, validates, and commits historical observations for a single instrument.
        """
        if not self._is_authorized_publisher(self.publisher):
            return {
                'instrument_id': str(instrument.id),
                'symbol': instrument.symbol,
                'status': 'PUBLISHER_REQUIRED',
                'reason': 'An active MarketDataPublisher, staff user or superuser is required before backfill.',
                'points_added': 0,
            }

        start_date, end_date, needs_backfill = self.plan_coverage(instrument, target_days)
        if not needs_backfill:
            return {
                'instrument_id': str(instrument.id),
                'symbol': instrument.symbol,
                'status': 'SKIPPED',
                'reason': 'Sufficient historical coverage already exists',
                'points_added': 0,
            }

        adapter = self._select_adapter(instrument)
        if not adapter:
            return {
                'instrument_id': str(instrument.id),
                'symbol': instrument.symbol,
                'status': 'UNSUPPORTED',
                'reason': f"No historical adapter for asset class {instrument.asset_class}",
                'points_added': 0,
            }

        raw_observations = adapter.fetch_history(instrument, start_date, end_date)
        if not raw_observations:
            return {
                'instrument_id': str(instrument.id),
                'symbol': instrument.symbol,
                'status': 'NO_DATA',
                'reason': 'Source returned no records for requested date range',
                'points_added': 0,
            }

        # Validate
        valid_observations = [obs for obs in raw_observations if self.validate_observation(obs)]
        market_tz = ZoneInfo('Asia/Kolkata')
        valid_observations.sort(key=lambda obs: (
            obs.effective_at.replace(tzinfo=market_tz)
            if timezone.is_naive(obs.effective_at) else obs.effective_at
        ).timestamp())
        if not valid_observations:
            return {
                'instrument_id': str(instrument.id),
                'symbol': instrument.symbol,
                'status': 'VALIDATION_FAILED',
                'reason': 'All retrieved observations failed validation checks',
                'points_added': 0,
            }

        # One backfill invocation owns one exact series. Reject mixed provider
        # payloads rather than accidentally attaching observations with different
        # price type, currency, unit or provenance to the first observation's series.
        first_obs = valid_observations[0]
        expected_identity = (first_obs.source, first_obs.price_type, first_obs.currency, first_obs.unit)
        if any(
            (obs.source, obs.price_type, obs.currency, obs.unit) != expected_identity
            for obs in valid_observations
        ):
            return {
                'instrument_id': str(instrument.id),
                'symbol': instrument.symbol,
                'status': 'INCOMPATIBLE_PROVIDER_RESPONSE',
                'reason': 'Provider returned observations with mixed source, price type, currency or quotation unit.',
                'points_added': 0,
            }

        # Resolve or create exact series on Market Data Storage
        series, _ = MarketDataSeries.objects.using('market_data').get_or_create(
            instrument_id=instrument.id,
            exchange=instrument.exchange or '',
            source=first_obs.source,
            price_type=first_obs.price_type,
            currency=first_obs.currency,
            unit=first_obs.unit,
            pricing_methodology='HISTORICAL_DAILY',
            adjustment_methodology='RAW',
            defaults={
                'description': f"Authoritative historical series for {instrument.symbol}",
                'data_version': 1,
            },
        )

        InstrumentCoverage.objects.using('market_data').update_or_create(
            instrument_id=instrument.id,
            defaults={
                'price_type': first_obs.price_type,
                'cadence': 'WEEKLY',
                'freshness_hours': 168,
                'grace_period_hours': 48,
                'currency': first_obs.currency,
                'unit': first_obs.unit,
                'preferred_source': first_obs.source,
            },
        )

        inserted = 0
        skipped = 0
        normalized_dates = []
        for obs in valid_observations:
            effective_at = obs.effective_at
            if timezone.is_naive(effective_at):
                effective_at = timezone.make_aware(effective_at, market_tz)
            normalized_dates.append((obs, effective_at, effective_at.astimezone(market_tz).date()))

        first_market_date = min(item[2] for item in normalized_dates)
        last_market_date = max(item[2] for item in normalized_dates)
        range_start = datetime.combine(first_market_date, time.min, tzinfo=market_tz).astimezone(dt_timezone.utc)
        range_end = datetime.combine(last_market_date + timedelta(days=1), time.min, tzinfo=market_tz).astimezone(dt_timezone.utc)
        existing_market_dates = {
            effective_at.astimezone(market_tz).date()
            for effective_at in PriceObservation.objects.using('market_data').filter(
                instrument_id=instrument.id,
                series_id=series.id,
                effective_at__gte=range_start,
                effective_at__lt=range_end,
                price_type=first_obs.price_type,
                source=first_obs.source,
                status=ObservationStatus.PUBLISHED,
            ).values_list('effective_at', flat=True)
        }

        # Duplicate detection is batched; publication still uses the validated
        # lifecycle so provenance, versions and durable events cannot be bypassed.
        with transaction.atomic(using='market_data'):
            for obs, eff_dt, market_date in normalized_dates:
                if market_date in existing_market_dates:
                    skipped += 1
                    continue
                existing_market_dates.add(market_date)
                observation = PriceObservation(
                    instrument_id=instrument.id,
                    series=series,
                    effective_at=eff_dt,
                    price_type=obs.price_type,
                    value=obs.value,
                    open_price=obs.open_price,
                    high_price=obs.high_price,
                    low_price=obs.low_price,
                    volume=obs.volume,
                    currency=obs.currency,
                    unit=obs.unit,
                    source=obs.source,
                    source_reference=obs.source_reference,
                    status=ObservationStatus.DRAFT,
                    trust_class=obs.trust_class,
                    is_synthetic=False,
                    recorded_by_id=getattr(self.publisher, 'id', None),
                )
                observation.save(using='market_data')
                observation.status = ObservationStatus.PENDING_REVIEW
                observation.save(using='market_data', update_fields=['status', 'updated_at'])
                observation.publish(self.publisher)
                inserted += 1

        return {
            'instrument_id': str(instrument.id),
            'symbol': instrument.symbol,
            'status': 'SUCCESS',
            'points_added': inserted,
            'points_skipped_as_duplicates': skipped,
            'start_date': first_market_date.isoformat(),
            'end_date': last_market_date.isoformat(),
        }
