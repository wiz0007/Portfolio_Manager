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


class PublicProvidentFundValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates Public Provident Fund (PPF) holdings:
    Annual compounding based on sovereign PPF interest rate (7.10% p.a. convention).
    Strictly distinct from commercial bank Fixed Deposits.
    """

    DEFAULT_PPF_RATE = Decimal('7.10')

    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        details = investment.details or {}
        obs_dt = as_of or datetime.now(timezone.utc)
        obs_date = obs_dt.date() if isinstance(obs_dt, datetime) else obs_dt

        balance_raw = details.get('current_balance') or details.get('principal_amount') or investment.initial_value or investment.invested_amount
        if balance_raw is None:
            return ValuationResult(
                current_value=None,
                valuation_method='PPF_SOVEREIGN_CONTRACTUAL',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing balance for Public Provident Fund.',
            )

        balance = to_decimal(balance_raw)
        if balance < Decimal('0'):
            return ValuationResult(
                current_value=None,
                valuation_method='PPF_SOVEREIGN_CONTRACTUAL',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                notes='PPF balance cannot be negative.',
            )

        balance = quantize_currency(balance)
        rate_raw = details.get('interest_rate_pct') or details.get('interest_rate')
        rate = to_decimal(rate_raw) if rate_raw is not None else self.DEFAULT_PPF_RATE

        start_date_raw = details.get('start_date') or details.get('opening_date')
        if start_date_raw:
            if isinstance(start_date_raw, str):
                start_date = date.fromisoformat(start_date_raw)
            elif isinstance(start_date_raw, datetime):
                start_date = start_date_raw.date()
            else:
                start_date = start_date_raw
        else:
            start_date = investment.created_at.date()

        elapsed_days = max(0, (obs_date - start_date).days)
        t_years = Decimal(str(elapsed_days)) / Decimal('365')
        r = rate / Decimal('100')

        if elapsed_days > 0 and r > Decimal('0'):
            factor = (Decimal('1') + r) ** t_years
            current_value = quantize_currency(balance * factor)
            accrued = current_value - balance
        else:
            current_value = balance
            accrued = Decimal('0.00')

        return ValuationResult(
            current_value=current_value,
            valuation_method='PPF_SOVEREIGN_CONTRACTUAL',
            source='GOVERNMENT_OF_INDIA_REFERENCE',
            source_reference='PPF-SCHEME',
            observed_at=obs_dt,
            currency=investment.currency,
            status=ValuationStatus.SUCCESS,
            metadata={
                'principal_balance': str(balance),
                'annual_interest_rate_percent': str(quantize_rate(rate, 2)),
                'compounding_frequency': 'ANNUAL',
                'accrued_interest': str(quantize_currency(accrued)),
                'start_date': start_date.isoformat(),
            },
        )
