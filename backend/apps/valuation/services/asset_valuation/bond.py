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
    quantize_units,
    to_decimal,
)


class BondValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates bond holdings using clean market price plus accrued coupon interest,
    or contractual face value plus accrued interest.
    """

    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        details = investment.details or {}
        obs_dt = as_of or datetime.now(timezone.utc)
        calc_date = obs_dt.date() if isinstance(obs_dt, datetime) else obs_dt

        units_raw = investment.quantity or details.get('units') or details.get('quantity')
        if units_raw is None:
            return ValuationResult(
                current_value=None,
                valuation_method='BOND_VALUATION',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing bond units/quantity; cannot default to 1.0.',
            )

        units = to_decimal(units_raw)
        if units <= Decimal('0'):
            return ValuationResult(
                current_value=None,
                valuation_method='BOND_VALUATION',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                notes='Bond quantity must be positive.',
            )

        units = quantize_units(units)

        face_raw = details.get('face_value')
        market_price = details.get('market_price') or details.get('current_price') or details.get('purchase_price')

        if market_price is not None:
            clean_price = to_decimal(market_price)
            valuation_method = 'MARKET_PRICE'
        elif face_raw is not None:
            clean_price = to_decimal(face_raw)
            valuation_method = 'CONTRACTUAL'
        else:
            return ValuationResult(
                current_value=None,
                valuation_method='BOND_VALUATION',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing face value and market price for bond valuation.',
            )

        # Accrued coupon interest calculation
        coupon_pct = to_decimal(details.get('coupon_rate_pct') or details.get('coupon_rate') or '0.00')
        accrued = to_decimal(details.get('accrued_interest', '0.00'))

        p_date_raw = details.get('purchase_date')
        if accrued == Decimal('0.00') and coupon_pct > Decimal('0.00') and p_date_raw:
            if isinstance(p_date_raw, str):
                p_date = date.fromisoformat(p_date_raw)
            else:
                p_date = p_date_raw
            if calc_date > p_date:
                days_held = (calc_date - p_date).days
                # Annual coupon cycle convention
                days_in_cycle = days_held % 365
                accrued = clean_price * (coupon_pct / Decimal('100.0')) * (Decimal(days_in_cycle) / Decimal('365.0'))

        total_unit_price = clean_price + accrued
        total_value = quantize_currency(units * total_unit_price)

        return ValuationResult(
            current_value=total_value,
            valuation_method=valuation_method,
            source='CONTRACTUAL_CALCULATION',
            source_reference=details.get('isin', details.get('bond_name', '')),
            observed_at=obs_dt,
            currency=investment.currency,
            status=ValuationStatus.SUCCESS,
            metadata={
                'units': str(units),
                'clean_price': str(clean_price),
                'accrued_interest': str(accrued),
                'face_value': str(face_raw or clean_price),
                'coupon_rate_pct': str(coupon_pct),
            },
        )
