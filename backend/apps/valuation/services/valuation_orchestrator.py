from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from django.db import transaction

from apps.assets.models.investment import Investment
from apps.assets.models.valuations import InvestmentValuation
from apps.valuation.services.asset_valuation import (
    ValuationStatus,
    get_valuation_strategy,
)
from apps.valuation.services.calculation.decimal_utils import (
    quantize_currency,
    quantize_rate,
    to_decimal,
)


class ValuationOrchestrator:
    """
    Coordinates asset-specific valuation calculations, atomic snapshot persistence,
    and portfolio synchronization.
    Strictly guarantees that historical snapshots never overwrite newer current values.
    """

    @classmethod
    @transaction.atomic
    def calculate_and_record(
        cls,
        investment: Investment,
        user=None,
        as_of: Optional[datetime] = None,
    ) -> Optional[InvestmentValuation]:
        """
        Executes the asset's deterministic valuation strategy and atomically persists
        an immutable valuation snapshot while updating Investment.current_value only
        if the snapshot date is >= latest recorded valuation date.
        """
        strategy = get_valuation_strategy(investment.category, investment.asset_type)
        val_result = strategy.evaluate(investment, as_of=as_of)

        effective_date = (as_of or datetime.now(timezone.utc)).date()

        # Failed or incomplete inputs must not destroy existing current value (VAL-044)
        if val_result.status != ValuationStatus.SUCCESS or val_result.current_value is None:
            return None

        # Lock investment row for update concurrency safety (VAL-043)
        locked_inv = Investment.objects.select_for_update().get(id=investment.id)
        latest_existing = locked_inv.valuations.order_by('-valuation_date', '-created_at').first()

        snapshot = InvestmentValuation.objects.create(
            investment=locked_inv,
            valuation_date=effective_date,
            amount=val_result.current_value,
            currency=val_result.currency,
            valuation_method=val_result.valuation_method,
            source=val_result.source,
            source_reference=val_result.source_reference,
            observed_at=val_result.observed_at,
            metadata={
                **val_result.metadata,
                'is_synthetic': val_result.is_synthetic,
                'status': val_result.status,
            },
            created_by=user,
        )

        # VAL-041 & VAL-042: Prevent historical snapshots from overwriting newer current values
        should_update = False
        if not latest_existing:
            should_update = True
        elif effective_date >= latest_existing.valuation_date:
            should_update = True

        if should_update:
            locked_inv.current_value = val_result.current_value
            locked_inv.save(update_fields=['current_value', 'updated_at'])
            investment.current_value = locked_inv.current_value

        return snapshot

    @classmethod
    @transaction.atomic
    def record_manual_valuation(
        cls,
        investment: Investment,
        amount: Decimal,
        valuation_date: date,
        user=None,
        notes: str = '',
        valuation_method: str = 'MANUAL',
    ) -> InvestmentValuation:
        """
        Records a user-specified valuation snapshot and updates Investment.current_value
        only if valuation_date is >= latest recorded valuation date.
        """
        dec_amount = quantize_currency(to_decimal(amount))

        locked_inv = Investment.objects.select_for_update().get(id=investment.id)
        latest_existing = locked_inv.valuations.order_by('-valuation_date', '-created_at').first()

        snapshot = InvestmentValuation.objects.create(
            investment=locked_inv,
            valuation_date=valuation_date,
            amount=dec_amount,
            currency=locked_inv.currency,
            valuation_method=valuation_method or 'MANUAL',
            source='MANUAL',
            source_reference='User Recorded Valuation',
            observed_at=datetime.now(timezone.utc),
            notes=notes,
            created_by=user,
        )

        should_update = False
        if not latest_existing:
            should_update = True
        elif valuation_date >= latest_existing.valuation_date:
            should_update = True

        if should_update:
            locked_inv.current_value = dec_amount
            locked_inv.save(update_fields=['current_value', 'updated_at'])
            investment.current_value = locked_inv.current_value

        return snapshot

    @classmethod
    def get_performance_metrics(cls, investment: Investment) -> Dict[str, Any]:
        """
        Computes financial performance metrics against acquisition cost.
        Returns unavailable percentage if invested amount is zero (VAL-046).
        Never mutates the investment.
        """
        invested_raw = investment.initial_value or investment.invested_amount or Decimal('0.00')
        invested = quantize_currency(to_decimal(invested_raw))

        # Distinguish 0.00 current value from None (VAL-045)
        if investment.current_value is not None:
            current = quantize_currency(to_decimal(investment.current_value))
        else:
            current = invested

        gain_loss_abs = current - invested
        if invested > Decimal('0.00'):
            gain_loss_pct = quantize_rate((gain_loss_abs / invested) * Decimal('100'), places=2)
            pct_val = str(gain_loss_pct)
        else:
            gain_loss_pct = None
            pct_val = 'unavailable'

        latest_snapshot = investment.valuations.order_by('-valuation_date', '-created_at').first()
        is_synthetic = False
        if latest_snapshot and isinstance(latest_snapshot.metadata, dict):
            is_synthetic = bool(latest_snapshot.metadata.get('is_synthetic', False))

        return {
            'investment_id': str(investment.id),
            'display_name': investment.display_name,
            'category': investment.category,
            'asset_type': investment.asset_type,
            'currency': investment.currency,
            'invested_amount': str(invested),
            'current_value': str(current),
            'absolute_gain_loss': str(gain_loss_abs),
            'percentage_gain_loss': pct_val,
            'is_gain': bool(gain_loss_abs >= Decimal('0.00')),
            'last_valuation_date': latest_snapshot.valuation_date.isoformat() if latest_snapshot else None,
            'valuation_method': latest_snapshot.valuation_method if latest_snapshot else investment.valuation_method,
            'source': latest_snapshot.source if latest_snapshot else 'ACQUISITION',
            'is_synthetic': is_synthetic,
        }
