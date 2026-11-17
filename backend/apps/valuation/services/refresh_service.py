import logging
from typing import Any, Dict, List

from apps.assets.models.investment import Investment
from apps.market_data.models.instrument import Instrument
from apps.valuation.services.valuation_orchestrator import ValuationOrchestrator

logger = logging.getLogger(__name__)


class ValuationRefreshService:
    """
    Orchestrates batch valuation recalculations across all user portfolios holding an instrument
    upon publication of a new market price observation.
    Guarantees failure isolation: an error on one holding does not rollback other holdings or the publication.
    """

    @classmethod
    def refresh_holdings_for_instrument(cls, instrument: Instrument) -> Dict[str, Any]:
        """
        Finds all investments linked to the instrument, recalculates valuation using the authoritative
        asset valuation strategy, and records snapshots.
        """
        investments = list(Investment.objects.filter(instrument=instrument).select_related('portfolio', 'user'))
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
                    logger.info(f"Valuation recalculation returned no snapshot for investment {inv.id}")
            except Exception as e:
                failed += 1
                err_msg = f"Failed to refresh investment {inv.id} for user {inv.user_id}: {e!s}"
                logger.exception(err_msg)
                errors.append(err_msg)

        logger.info(
            f"Valuation refresh for instrument {instrument.symbol} completed: {refreshed}/{total} updated, {failed} failed."
        )

        return {
            'total_holdings': total,
            'refreshed_count': refreshed,
            'failed_count': failed,
            'errors': errors,
        }
