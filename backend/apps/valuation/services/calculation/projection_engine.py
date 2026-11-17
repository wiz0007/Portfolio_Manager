from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from apps.assets.models.investment import Investment
from apps.valuation.services.calculation.decimal_utils import (
    compound_annuity_fv,
    compound_lump_sum,
    quantize_currency,
    quantize_rate,
    to_decimal,
)

CATEGORY_DEFAULT_RATES: Dict[str, Dict[str, Decimal]] = {
    'EQUITY': {
        'conservative': Decimal('8.00'),
        'base': Decimal('12.00'),
        'optimistic': Decimal('15.00'),
    },
    'MUTUAL_FUNDS': {
        'conservative': Decimal('8.00'),
        'base': Decimal('12.00'),
        'optimistic': Decimal('15.00'),
    },
    'FIXED_INCOME': {
        'conservative': Decimal('6.00'),
        'base': Decimal('7.25'),
        'optimistic': Decimal('8.50'),
    },
    'CASH': {
        'conservative': Decimal('3.50'),
        'base': Decimal('5.00'),
        'optimistic': Decimal('6.50'),
    },
    'COMMODITIES': {
        'conservative': Decimal('6.00'),
        'base': Decimal('9.00'),
        'optimistic': Decimal('12.00'),
    },
    'GOLD': {
        'conservative': Decimal('6.00'),
        'base': Decimal('9.00'),
        'optimistic': Decimal('12.00'),
    },
    'REAL_ESTATE': {
        'conservative': Decimal('5.00'),
        'base': Decimal('8.00'),
        'optimistic': Decimal('11.00'),
    },
    'CRYPTO': {
        'conservative': Decimal('0.00'),
        'base': Decimal('15.00'),
        'optimistic': Decimal('30.00'),
    },
}

DEFAULT_FALLBACK_RATES: Dict[str, Decimal] = {
    'conservative': Decimal('6.00'),
    'base': Decimal('10.00'),
    'optimistic': Decimal('14.00'),
}


class ProjectionEngine:
    """
    Financial calculation engine for deterministic future-value projections.
    Strictly non-mutating: zero database writes.
    """

    FORMULA_ID = 'ANNUITY_COMPOUND_FV_V1'
    ASSUMPTION_DISCLOSURES = (
        'Projections are deterministic mathematical estimates based on constant return assumptions '
        'and periodic compounding. They do not account for market volatility, inflation, tax liabilities, '
        'or variable cash flows, and are not guarantees of future returns.'
    )

    @classmethod
    def calculate_projection(
        cls,
        investment: Investment,
        time_horizon_years: Union[Decimal, float, int, str] = 5,
        monthly_contribution: Union[Decimal, float, int, str] = Decimal('0.00'),
        contribution_amount: Optional[Union[Decimal, float, int, str]] = None,
        contribution_timing: str = 'END_OF_PERIOD',
        compounding_frequency_per_year: int = 12,
        contribution_frequency_per_year: Optional[int] = None,
        custom_annual_rate: Optional[Decimal] = None,
        selected_scenarios: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates future value trajectories under different growth assumptions.
        Supports separate contribution frequency (k) vs compounding frequency (m)
        and fractional-year horizons.
        """
        raw_horizon = to_decimal(time_horizon_years, default='5')
        if raw_horizon <= Decimal('0'):
            horizon_dec = Decimal('1')
        elif raw_horizon > Decimal('50'):
            horizon_dec = Decimal('50')
        else:
            horizon_dec = raw_horizon

        m = max(1, int(compounding_frequency_per_year))
        k = max(1, int(contribution_frequency_per_year or 12))

        # Contribution amount priority
        amt_raw = contribution_amount if contribution_amount is not None else monthly_contribution
        pmt = quantize_currency(to_decimal(amt_raw))

        # Current starting principal
        initial_principal = quantize_currency(
            to_decimal(investment.current_value or investment.invested_amount)
        )

        cat = (investment.category or '').upper()
        default_rates = CATEGORY_DEFAULT_RATES.get(cat, DEFAULT_FALLBACK_RATES)

        scenarios_to_run: Dict[str, Decimal] = {}
        if custom_annual_rate is not None:
            scenarios_to_run['custom'] = to_decimal(custom_annual_rate)
        else:
            names = selected_scenarios or ['conservative', 'base', 'optimistic']
            for name in names:
                normalized = name.lower()
                rate = default_rates.get(normalized, DEFAULT_FALLBACK_RATES.get(normalized, Decimal('10.00')))
                scenarios_to_run[normalized] = rate

        scenario_results: Dict[str, Any] = {}

        # Build schedule points: full years + final fractional horizon if not integer
        int_years = int(horizon_dec)
        schedule_steps: List[Decimal] = [Decimal(str(y)) for y in range(1, int_years + 1)]
        if horizon_dec > Decimal(str(int_years)):
            schedule_steps.append(horizon_dec)

        for scenario_name, annual_rate_pct in scenarios_to_run.items():
            schedule: List[Dict[str, Any]] = []

            for step in schedule_steps:
                fv_lump = compound_lump_sum(initial_principal, annual_rate_pct, m, step)
                fv_annuity = compound_annuity_fv(
                    payment=pmt,
                    annual_rate_pct=annual_rate_pct,
                    compounding_frequency=m,
                    years=step,
                    contribution_frequency=k,
                    timing=contribution_timing,
                )
                fv_total = quantize_currency(fv_lump + fv_annuity)

                periods_count = int(Decimal(str(k)) * step)
                total_contributions = quantize_currency(initial_principal + (pmt * Decimal(str(periods_count))))
                growth = quantize_currency(fv_total - total_contributions)

                schedule.append({
                    'year': int(step) if step == int(step) else float(step),
                    'invested_capital': str(total_contributions),
                    'projected_future_value': str(fv_total),
                    'estimated_growth': str(growth),
                })

            final_entry = schedule[-1] if schedule else None
            scenario_results[scenario_name] = {
                'scenario_name': scenario_name,
                'annual_rate_percent': str(quantize_rate(annual_rate_pct, places=2)),
                'projected_future_value': final_entry['projected_future_value'] if final_entry else str(initial_principal),
                'total_invested_capital': final_entry['invested_capital'] if final_entry else str(initial_principal),
                'total_estimated_growth': final_entry['estimated_growth'] if final_entry else '0.00',
                'schedule': schedule,
            }

        return {
            'formula_id': cls.FORMULA_ID,
            'assumption_disclosures': cls.ASSUMPTION_DISCLOSURES,
            'investment_id': str(investment.id),
            'display_name': investment.display_name,
            'category': investment.category,
            'currency': investment.currency,
            'starting_value': str(initial_principal),
            'initial_principal': str(initial_principal),
            'monthly_contribution': str(pmt),
            'contribution_amount': str(pmt),
            'time_horizon_years': int(horizon_dec) if horizon_dec == int(horizon_dec) else float(horizon_dec),
            'horizon_years': str(horizon_dec),
            'contribution_timing': contribution_timing,
            'contribution_frequency_per_year': k,
            'compounding_frequency_per_year': m,
            'scenarios': scenario_results,
        }
