from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from apps.assets.models.investment import Investment
from apps.valuation.services.asset_valuation.base import (
    BaseAssetValuationStrategy,
    ValuationResult,
    ValuationStatus,
)
from apps.valuation.services.calculation.decimal_utils import (
    quantize_currency,
    quantize_rate,
    to_decimal,
)


class RecurringDepositValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates Recurring Deposits by compounding individual monthly installments
    accrued between start date and calculation date using quarterly compounding convention.
    """

    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        details = investment.details or {}
        obs_dt = as_of or datetime.now(timezone.utc)
        obs_date = obs_dt.date() if isinstance(obs_dt, datetime) else obs_dt

        installment_raw = details.get('monthly_installment') or details.get('installment_amount') or details.get('deposit_amount')
        if installment_raw is None:
            return ValuationResult(
                current_value=None,
                valuation_method='CONTRACTUAL',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing monthly installment amount for recurring deposit.',
            )

        installment = to_decimal(installment_raw)
        if installment <= Decimal('0'):
            return ValuationResult(
                current_value=None,
                valuation_method='CONTRACTUAL',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                notes='Monthly installment amount must be greater than zero.',
            )

        installment = quantize_currency(installment)

        rate_raw = details.get('interest_rate') or details.get('interest_rate_pct', '0.00')
        annual_rate = to_decimal(rate_raw)

        start_date_raw = details.get('start_date') or details.get('deposit_date')
        if start_date_raw:
            if isinstance(start_date_raw, str):
                start_date = date.fromisoformat(start_date_raw)
            elif isinstance(start_date_raw, datetime):
                start_date = start_date_raw.date()
            else:
                start_date = start_date_raw
        else:
            start_date = investment.created_at.date()

        mat_date_raw = details.get('maturity_date')
        mat_date = None
        if mat_date_raw:
            if isinstance(mat_date_raw, str):
                mat_date = date.fromisoformat(mat_date_raw)
            elif isinstance(mat_date_raw, datetime):
                mat_date = mat_date_raw.date()
            else:
                mat_date = mat_date_raw
        elif details.get('tenure_months') or details.get('tenure_value'):
            t_val = int(details.get('tenure_months') or details.get('tenure_value', 12))
            u = str(details.get('tenure_unit', 'MONTHS')).upper()
            months = t_val * 12 if 'YEAR' in u else t_val
            # Approximate maturity date from tenure months
            end_year = start_date.year + (start_date.month + months - 1) // 12
            end_month = (start_date.month + months - 1) % 12 + 1
            mat_date = date(end_year, end_month, min(start_date.day, 28))

        # Effective calculation date cannot exceed maturity date
        calc_date = min(obs_date, mat_date) if mat_date else obs_date

        if obs_date < start_date:
            months_elapsed = 0
        else:
            months_diff = (calc_date.year - start_date.year) * 12 + (calc_date.month - start_date.month) + 1
            months_elapsed = max(0, months_diff)

        user_installments = details.get('installments_paid')
        is_estimated = False
        if user_installments is not None:
            installments_count = max(0, int(user_installments))
        else:
            installments_count = months_elapsed
            is_estimated = True

        total_principal = installment * Decimal(str(installments_count))

        r = annual_rate / Decimal('100')
        n = 4  # Standard quarterly compounding for Indian bank RDs

        total_value = Decimal('0.00')
        if installments_count == 0:
            total_value = Decimal('0.00')
            accrued_interest = Decimal('0.00')
        elif annual_rate <= Decimal('0'):
            total_value = total_principal
            accrued_interest = Decimal('0.00')
        else:
            for k in range(installments_count):
                remaining_months = max(0, installments_count - k)
                t_years = Decimal(str(remaining_months)) / Decimal('12')
                total_periods = Decimal(str(n)) * t_years
                factor = (Decimal('1') + (r / Decimal(str(n)))) ** total_periods
                total_value += installment * factor
            accrued_interest = total_value - total_principal

        val_status = ValuationStatus.ESTIMATED if is_estimated else ValuationStatus.SUCCESS
        notes = "Installment history estimated based on calendar elapsed months." if is_estimated else ""

        return ValuationResult(
            current_value=quantize_currency(total_value),
            valuation_method='CONTRACTUAL',
            source='CONTRACTUAL_CALCULATION',
            source_reference=f"RD-{details.get('institution_name', details.get('bank_name', 'CONTRACT'))}",
            observed_at=obs_dt,
            currency=investment.currency,
            status=val_status,
            notes=notes,
            metadata={
                'monthly_installment': str(installment),
                'annual_rate_percent': str(quantize_rate(annual_rate, 2)),
                'installments_paid': installments_count,
                'total_principal_paid': str(quantize_currency(total_principal)),
                'accrued_interest': str(quantize_currency(accrued_interest)),
                'compounding_frequency': 'QUARTERLY',
                'start_date': start_date.isoformat(),
                'maturity_date': mat_date.isoformat() if mat_date else None,
            },
        )
