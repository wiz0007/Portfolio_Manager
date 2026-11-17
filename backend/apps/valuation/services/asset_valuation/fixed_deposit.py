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
    calculate_ear,
    quantize_currency,
    quantize_rate,
    to_decimal,
)

FREQUENCY_MAP = {
    'MONTHLY': 12,
    'QUARTERLY': 4,
    'HALF_YEARLY': 2,
    'SEMI_ANNUALLY': 2,
    'ANNUAL': 1,
    'ANNUALLY': 1,
    'YEARLY': 1,
    'AT_MATURITY': 0,
    'SIMPLE': 0,
}


class FixedDepositValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates Fixed Deposits by compounding interest up to the valuation date.
    Maintains strict distinction between Cumulative (compounded) and Non-Cumulative (periodic payout) FDs.
    Never compounds past maturity date unless explicit renewal recorded.
    """

    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        details = investment.details or {}
        obs_dt = as_of or datetime.now(timezone.utc)
        obs_date = obs_dt.date() if isinstance(obs_dt, datetime) else obs_dt

        principal_raw = details.get('deposit_amount') or details.get('principal_amount')
        if principal_raw is None:
            principal_raw = investment.initial_value or investment.invested_amount

        if principal_raw is None:
            return ValuationResult(
                current_value=None,
                valuation_method='CONTRACTUAL',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing principal amount for fixed deposit.',
            )

        principal = to_decimal(principal_raw)
        if principal <= Decimal('0'):
            return ValuationResult(
                current_value=None,
                valuation_method='CONTRACTUAL',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                notes='Fixed deposit principal must be greater than zero.',
            )

        principal = quantize_currency(principal)

        rate_raw = details.get('interest_rate') or details.get('interest_rate_pct', '0.00')
        annual_rate = to_decimal(rate_raw)
        freq_str = str(details.get('compounding_frequency', 'QUARTERLY')).upper()
        comp_freq = FREQUENCY_MAP.get(freq_str, 4)

        payout_type = str(details.get('payout_type', details.get('payout_frequency', 'CUMULATIVE'))).upper()
        is_cumulative = payout_type in ('CUMULATIVE', 'AT_MATURITY')

        # Parse start and maturity dates
        start_date_raw = details.get('deposit_date') or details.get('start_date')
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

        # Effective calculation date cannot exceed maturity date (do not compound beyond maturity)
        is_matured = bool(mat_date and obs_date >= mat_date)
        calc_date = min(obs_date, mat_date) if mat_date else obs_date
        elapsed_days = max(0, (calc_date - start_date).days)

        if elapsed_days <= 0 or annual_rate <= Decimal('0'):
            current_value = principal
            accrued_interest = Decimal('0.00')
            distributed_interest = Decimal('0.00')
        else:
            t_years = Decimal(str(elapsed_days)) / Decimal('365')
            r = annual_rate / Decimal('100')

            if is_cumulative:
                # Cumulative FD: interest accumulates and compounds
                if is_matured and details.get('maturity_amount'):
                    current_value = to_decimal(details['maturity_amount'])
                    accrued_interest = current_value - principal
                    distributed_interest = Decimal('0.00')
                else:
                    if comp_freq <= 0:
                        accrued_interest = principal * r * t_years
                        current_value = principal + accrued_interest
                    else:
                        periodic_rate = r / Decimal(str(comp_freq))
                        total_periods = Decimal(str(comp_freq)) * t_years
                        factor = (Decimal('1') + periodic_rate) ** total_periods
                        current_value = principal * factor
                        accrued_interest = current_value - principal
                    distributed_interest = Decimal('0.00')
            else:
                # Non-Cumulative FD: interest is periodically paid out; only unpaid accrued in cycle remains
                payout_interval_days = 91 if comp_freq == 4 else (30 if comp_freq == 12 else 182)
                days_in_current_cycle = elapsed_days % payout_interval_days
                completed_cycles = elapsed_days // payout_interval_days

                cycle_interest_rate = (r / Decimal(str(comp_freq if comp_freq > 0 else 4)))
                distributed_interest = principal * cycle_interest_rate * Decimal(str(completed_cycles))
                accrued_interest = principal * (r * Decimal(str(days_in_current_cycle)) / Decimal('365'))
                # Non-cumulative current value is principal + accrued unpaid interest
                current_value = principal + accrued_interest

        ear_pct = calculate_ear(annual_rate, comp_freq if comp_freq > 0 else 1)

        return ValuationResult(
            current_value=quantize_currency(current_value),
            valuation_method='CONTRACTUAL',
            source='CONTRACTUAL_CALCULATION',
            source_reference=f"FD-{details.get('institution_name', details.get('bank_name', 'CONTRACT'))}",
            observed_at=obs_dt,
            currency=investment.currency,
            status=ValuationStatus.SUCCESS,
            metadata={
                'principal': str(principal),
                'annual_rate_percent': str(quantize_rate(annual_rate, 2)),
                'compounding_frequency': freq_str,
                'payout_type': payout_type,
                'effective_annual_rate_percent': str(ear_pct),
                'elapsed_days': elapsed_days,
                'is_matured': is_matured,
                'accrued_interest': str(quantize_currency(accrued_interest)),
                'distributed_interest': str(quantize_currency(distributed_interest)),
                'start_date': start_date.isoformat(),
                'maturity_date': mat_date.isoformat() if mat_date else None,
            },
        )
