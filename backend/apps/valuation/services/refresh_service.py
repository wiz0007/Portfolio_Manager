import logging
from typing import Any, Dict, List

from django.utils import timezone
from django.db import models

from apps.assets.models.investment import Investment
from apps.market_data.models.instrument import Instrument
from apps.market_data.models.publication_event import (
    MarketDataPublicationEvent,
    PublicationEventStatus,
)
from apps.valuation.services.valuation_orchestrator import ValuationOrchestrator

logger = logging.getLogger(__name__)


class ValuationRefreshService:
    """
    Orchestrates batch valuation recalculations across all user portfolios holding an instrument
    upon publication of a new market price observation.
    Guarantees failure isolation: an error on one holding does not rollback other holdings or the publication.
    Integrates with durable MarketDataPublicationEvent outbox.
    """

    @classmethod
    def refresh_holdings_for_instrument(cls, instrument: Instrument, event_id: str = None) -> Dict[str, Any]:
        """
        Finds all investments linked to the instrument, recalculates valuation using the authoritative
        asset valuation strategy, and records snapshots on Primary Database ('default').
        """
        investments = list(Investment.objects.using('default').filter(instrument=instrument).select_related('portfolio', 'user'))
        total = len(investments)
        refreshed = 0
        failed = 0
        errors: List[str] = []

        for inv in investments:
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
        """Process publication events with retry-safe, per-event idempotency.

        A partially failed holding refresh is NOT acknowledged. Successful holding
        snapshots carry the event UUID as an idempotency key, so retrying the event
        does not create duplicate snapshots for already-refreshed holdings.
        """
        from django.db import transaction

        event_ids = list(
            MarketDataPublicationEvent.objects.using('market_data')
            .filter(status__in=[PublicationEventStatus.PENDING, PublicationEventStatus.FAILED])
            .order_by('created_at').values_list('id', flat=True)[:limit]
        )
        processed = failed = 0
        for event_id in event_ids:
            try:
                with transaction.atomic(using='market_data'):
                    event = (
                        MarketDataPublicationEvent.objects.using('market_data')
                        .select_for_update().get(pk=event_id)
                    )
                    if event.status == PublicationEventStatus.PROCESSED:
                        continue
                    event.attempts += 1
                    instrument = Instrument.objects.using('default').filter(id=event.instrument_id).first()
                    if instrument is None:
                        raise RuntimeError(
                            f'Canonical instrument {event.instrument_id} is missing; publication event cannot be applied.'
                        )
                    stats = cls.refresh_holdings_for_instrument(instrument, event_id=str(event.id))
                    if stats['failed_count']:
                        raise RuntimeError(
                            f"{stats['failed_count']} of {stats['total_holdings']} holding refreshes failed: "
                            + '; '.join(stats.get('errors', [])[:5])
                        )
                    event.status = PublicationEventStatus.PROCESSED
                    event.processed_at = timezone.now()
                    event.last_error = ''
                    event.save(using='market_data', update_fields=[
                        'status', 'processed_at', 'last_error', 'attempts'
                    ])
                processed += 1
            except Exception as exc:
                MarketDataPublicationEvent.objects.using('market_data').filter(pk=event_id).update(
                    status=PublicationEventStatus.FAILED,
                    attempts=models.F('attempts') + 1,
                    last_error=str(exc)[:4000],
                )
                logger.exception('Publication event %s failed and will be retried', event_id)
                failed += 1
        return {'processed': processed, 'failed': failed}
