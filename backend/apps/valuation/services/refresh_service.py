import logging
from typing import Any, Dict, List

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
    """
    Orchestrates batch valuation recalculations across all user portfolios holding an instrument
    upon publication of a new market price observation.
    Guarantees failure isolation: an error on one holding does not rollback other holdings or the publication.
    Integrates with durable MarketDataPublicationEvent outbox.
    """

    @classmethod
    def refresh_holdings_for_instrument(cls, instrument: Instrument) -> Dict[str, Any]:
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
                snapshot = ValuationOrchestrator.calculate_and_record(inv, user=inv.user)
                if snapshot:
                    refreshed += 1
                else:
                    logger.info("Valuation recalculation returned no snapshot for investment %s", inv.id)
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
        """
        Processes pending publication outbox events from the Market Data Storage Database,
        recalculating valuations on the Primary Database idempotently.
        """
        events = list(
            MarketDataPublicationEvent.objects.using('market_data')
            .filter(status__in=[PublicationEventStatus.PENDING, PublicationEventStatus.FAILED])
            .order_by('created_at')[:limit]
        )
        processed = 0
        failed = 0

        for event in events:
            try:
                event.attempts += 1
                inst = Instrument.objects.using('default').filter(id=event.instrument_id).first()
                if inst:
                    cls.refresh_holdings_for_instrument(inst)
                event.status = PublicationEventStatus.PROCESSED
                event.processed_at = timezone.now()
                event.save(using='market_data', update_fields=['status', 'processed_at', 'attempts'])
                processed += 1
            except Exception as e:
                event.status = PublicationEventStatus.FAILED
                event.last_error = str(e)
                event.save(using='market_data', update_fields=['status', 'last_error', 'attempts'])
                failed += 1

        return {'processed': processed, 'failed': failed}
