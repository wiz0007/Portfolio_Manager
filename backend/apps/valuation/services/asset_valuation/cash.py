from datetime import date, datetime, timezone
from typing import Optional

from apps.assets.models.investment import Investment
from apps.valuation.services.asset_valuation.base import (
    BaseAssetValuationStrategy,
    ValuationResult,
    ValuationStatus,
)
from apps.valuation.services.calculation.decimal_utils import quantize_currency, to_decimal


class CashValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates cash, savings, current, and wallet balances.
    Valuation is the stated account balance as of the recorded balance date.
    """

    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        details = investment.details or {}
        raw_val = details.get('current_balance')
        if raw_val is None:
            raw_val = investment.current_value or investment.initial_value or investment.invested_amount

        balance = quantize_currency(to_decimal(raw_val or '0.00'))
        bank_name = details.get('bank_name', '')
        account_type = details.get('account_type', 'SAVINGS')

        b_date_raw = details.get('balance_date')
        if b_date_raw:
            if isinstance(b_date_raw, str):
                b_date = date.fromisoformat(b_date_raw)
            else:
                b_date = b_date_raw
            obs_dt = datetime.combine(b_date, datetime.min.time(), tzinfo=timezone.utc)
        else:
            obs_dt = as_of or datetime.now(timezone.utc)

        return ValuationResult(
            current_value=balance,
            valuation_method='BANK_BALANCE',
            source='BANK_RECORD',
            source_reference=str(bank_name),
            observed_at=obs_dt,
            currency=investment.currency,
            status=ValuationStatus.SUCCESS,
            metadata={
                'bank_name': bank_name,
                'account_type': account_type,
                'current_balance': str(balance),
                'balance_date': b_date_raw.isoformat() if hasattr(b_date_raw, 'isoformat') else (str(b_date_raw) if b_date_raw else obs_dt.date().isoformat()),
            },
        )
