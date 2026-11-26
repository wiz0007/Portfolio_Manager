import logging
from typing import Any, Dict, List

from django.db import models
from django.utils import timezone

from apps.assets.models.investment import Investment
from apps.market_data.models.instrument import Instrument
from apps.market_data.models.publication_event import (
    MarketDataPublicationEvent,
    PublicationEventStatus,
)
from apps.valuation.services.valuation_orchestrator import ValuationOrchestrator

logger = logging.getLogger(__name__)


class ValuationRefreshService:
    """Refresh instrument holdings from the durable market-data publication outbox."""

    MAX_EVENTS_PER_INSTRUMENT_BATCH = 5000

    @classmethod
    def refresh_holdings_for_instrument(cls, instrument: Instrument, event_id: str | None = None) -> Dict[str, Any]:
        """
        Finds all investments linked to the instrument, recalculates valuation using the authoritative
        asset valuation strategy, and records snapshots on Primary Database ('default').
        """
        investments = Investment.objects.using('default').filter(
            instrument=instrument
        ).select_related('portfolio', 'user').order_by('id')
        total = investments.count()
        refreshed = 0
        failed = 0
        errors: List[str] = []

        for inv in investments.iterator(chunk_size=100):
            try:
                snapshot = ValuationOrchestrator.calculate_and_record(
                    inv, user=inv.user, idempotency_key=event_id
                )
                if snapshot:
                    refreshed += 1
                else:
                    failed += 1
                    err_msg = (
                        f'No valuation snapshot was produced for investment {inv.id}; '
                        'market data may be missing, stale, synthetic, unverified or incompatible.'
                    )
                    logger.warning(err_msg)
                    errors.append(err_msg)
            except Exception as e:
                failed += 1
                err_msg = f"Failed to refresh investment {inv.id} for user {inv.user_id}: {e!s}"
                logger.exception(err_msg)
                errors.append(err_msg)

        logger.info(
            "Valuation refresh for instrument %s completed: %d/%d updated, %d failed.",
            instrument.symbol,
            refreshed,
            total,
            failed,
        )

        return {
            'total_holdings': total,
            'refreshed_count': refreshed,
            'failed_count': failed,
            'errors': errors,
        }

    @classmethod
    def process_pending_publication_events(cls, limit: int = 50) -> Dict[str, int]:
        """Process publication events in bounded per-instrument batches.

        Historical backfills can publish thousands of observations for one
        instrument. Recalculating every holding once per observation is both
        wasteful and operationally dangerous. This worker coalesces the events
        selected for one instrument into one current-valuation refresh.

        The oldest selected event is the stable idempotency key for the batch.
        Events are acknowledged together only after every affected holding has
        refreshed successfully. If the primary-database writes succeed but the
        secondary-database acknowledgement fails, replaying the same oldest event
        key makes already-created valuation snapshots idempotent.
        """
        from django.db import transaction

        if limit < 1:
            raise ValueError('limit must be a positive integer')

        candidate_events = list(
            MarketDataPublicationEvent.objects.using('market_data')
            .filter(status__in=[PublicationEventStatus.PENDING, PublicationEventStatus.FAILED])
            .order_by('created_at', 'id')
            .values_list('id', 'instrument_id')[:limit]
        )
        candidate_instrument_ids = list(dict.fromkeys(
            instrument_id for _event_id, instrument_id in candidate_events
        ))

        processed = failed = 0
        for instrument_id in candidate_instrument_ids:
            event_ids = []
            try:
                with transaction.atomic(using='market_data'):
                    events = list(
                        MarketDataPublicationEvent.objects.using('market_data')
                        .select_for_update()
                        .filter(
                            instrument_id=instrument_id,
                            status__in=[PublicationEventStatus.PENDING, PublicationEventStatus.FAILED],
                        )
                        .order_by('created_at', 'id')[:cls.MAX_EVENTS_PER_INSTRUMENT_BATCH]
                    )
                    if not events:
                        continue

                    event_ids = [event.id for event in events]
                    # The oldest event remains pending until the whole batch is
                    # acknowledged, so it remains stable across failed retries.
                    batch_idempotency_key = str(events[0].id)
                    instrument = Instrument.objects.using('default').filter(id=instrument_id).first()
                    if instrument is None:
                        raise RuntimeError(
                            f'Canonical instrument {instrument_id} is missing; publication events cannot be applied.'
                        )

                    stats = cls.refresh_holdings_for_instrument(
                        instrument, event_id=batch_idempotency_key
                    )
                    if stats['failed_count']:
                        raise RuntimeError(
                            f"{stats['failed_count']} of {stats['total_holdings']} holding refreshes failed: "
                            + '; '.join(stats.get('errors', [])[:5])
                        )

                    MarketDataPublicationEvent.objects.using('market_data').filter(
                        id__in=event_ids,
                        status__in=[PublicationEventStatus.PENDING, PublicationEventStatus.FAILED],
                    ).update(
                        status=PublicationEventStatus.PROCESSED,
                        processed_at=timezone.now(),
                        last_error='',
                        attempts=models.F('attempts') + 1,
                    )
                processed += len(event_ids)
            except Exception as exc:
                if event_ids:
                    MarketDataPublicationEvent.objects.using('market_data').filter(
                        id__in=event_ids,
                        status__in=[PublicationEventStatus.PENDING, PublicationEventStatus.FAILED],
                    ).update(
                        status=PublicationEventStatus.FAILED,
                        attempts=models.F('attempts') + 1,
                        last_error=str(exc)[:4000],
                    )
                logger.exception(
                    'Publication event batch for instrument %s failed and will be retried',
                    instrument_id,
                )
                failed += len(event_ids) if event_ids else 1

        return {'processed': processed, 'failed': failed}
