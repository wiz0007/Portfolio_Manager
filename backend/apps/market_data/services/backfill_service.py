import logging
from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db import transaction
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
        self.publisher = publisher or User.objects.filter(is_superuser=True).first() or User.objects.first()
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
        """Enforces financial validation rules."""
        if obs.value is None or obs.value <= Decimal('0'):
            return False
        if obs.high_price is not None and obs.low_price is not None:
            if obs.high_price < obs.low_price:
                return False
        if obs.effective_at.astimezone(ZoneInfo('Asia/Kolkata')).date() > timezone.localtime(timezone.now(), ZoneInfo('Asia/Kolkata')).date():
            return False
        return True

    def backfill_instrument(
        self,
        instrument: Instrument,
        target_days: int = 1825,
    ) -> Dict[str, any]:
        """
        Acquires, validates, and commits historical observations for a single instrument.
        """
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
        if not valid_observations:
            return {
                'instrument_id': str(instrument.id),
                'symbol': instrument.symbol,
                'status': 'VALIDATION_FAILED',
                'reason': 'All retrieved observations failed validation checks',
                'points_added': 0,
            }

        # Resolve or create exact series on Market Data Storage
        first_obs = valid_observations[0]
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
                'currency': first_obs.currency,
                'unit': first_obs.unit,
                'preferred_source': first_obs.source,
            },
        )

        if self.publisher is None:
            return {
                'instrument_id': str(instrument.id), 'symbol': instrument.symbol,
                'status': 'PUBLISHER_REQUIRED',
                'reason': 'A staff publisher account is required to publish backfilled observations.',
                'points_added': 0,
            }

        inserted = 0
        skipped = 0
        # Use the same publication lifecycle/outbox as manually approved observations.
        # This is intentionally slower than bulk_create, but prevents backfill from
        # bypassing provenance validation, version increments and downstream events.
        with transaction.atomic(using='market_data'):
            for obs in valid_observations:
                eff_dt = obs.effective_at
                if timezone.is_naive(eff_dt):
                    eff_dt = timezone.make_aware(eff_dt, timezone.get_current_timezone())
                market_date = eff_dt.astimezone(ZoneInfo('Asia/Kolkata')).date()
                day_start = datetime.combine(market_date, time.min, tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(dt_timezone.utc)
                day_end = datetime.combine(market_date + timedelta(days=1), time.min, tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(dt_timezone.utc)
                exists = PriceObservation.objects.using('market_data').filter(
                    instrument_id=instrument.id, series_id=series.id,
                    effective_at__gte=day_start, effective_at__lt=day_end,
                    price_type=obs.price_type, source=obs.source,
                    status=ObservationStatus.PUBLISHED,
                ).exists()
                if exists:
                    skipped += 1
                    continue
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
            'start_date': valid_observations[0].effective_at.date().isoformat(),
            'end_date': valid_observations[-1].effective_at.date().isoformat(),
        }
