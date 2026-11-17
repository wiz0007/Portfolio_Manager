from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from apps.assets.models.investment import Investment
from apps.market_data.services.market_data_service import MarketDataService
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


class SovereignGoldBondValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates Sovereign Gold Bond (SGB) holdings:
    Units (grams) * SGB Market Quote + Accrued Semi-Annual Coupon (2.50% p.a.).
    """

    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        details = investment.details or {}
        obs_dt = as_of or datetime.now(timezone.utc)
        calc_date = obs_dt.date() if isinstance(obs_dt, datetime) else obs_dt

        units_raw = details.get('units') or details.get('quantity') or investment.quantity or details.get('weight_grams')
        if units_raw is None and details.get('purchase_price') and details.get('purchase_price_per_gram'):
            try:
                units_raw = to_decimal(details['purchase_price']) / to_decimal(details['purchase_price_per_gram'])
            except Exception:
                units_raw = None

        if units_raw is None:
            return ValuationResult(
                current_value=None,
                valuation_method='SGB_VALUATION',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing units for Sovereign Gold Bond; cannot default to 1.0.',
            )

        units = to_decimal(units_raw)
        if units <= Decimal('0'):
            return ValuationResult(
                current_value=None,
                valuation_method='SGB_VALUATION',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                notes='SGB units must be greater than zero.',
            )

        units = quantize_units(units)

        unit_price = None
        source_name = 'USER_INPUT'
        source_ref = details.get('sgb_series', '')
        is_synthetic = False

        if investment.instrument:
            try:
                quote = MarketDataService.get_latest_quote(investment.instrument)
                if quote and quote.price:
                    unit_price = quote.price
                    source_name = quote.provider or 'MARKET_FEED'
                    source_ref = investment.instrument.symbol
                    is_synthetic = quote.is_synthetic
                    if quote.timestamp:
                        obs_dt = quote.timestamp
            except Exception:
                pass

        if unit_price is None:
            raw_p = details.get('current_price') or details.get('purchase_price_per_gram')
            if raw_p is not None:
                unit_price = to_decimal(raw_p)
            elif details.get('purchase_price'):
                unit_price = to_decimal(details['purchase_price']) / units
            else:
                unit_price = investment.invested_amount / units if units > 0 else Decimal('0.00')

        unit_price = to_decimal(unit_price)
        base_value = units * unit_price

        # Accrued coupon calculation (RBI standard: 2.50% p.a. paid semi-annually on face/issue value)
        coupon_pct = to_decimal(details.get('coupon_rate_pct', '2.50'))
        accrued_coupon = Decimal('0.00')

        p_date_raw = details.get('purchase_date')
        if p_date_raw:
            if isinstance(p_date_raw, str):
                p_date = date.fromisoformat(p_date_raw)
            else:
                p_date = p_date_raw

            if calc_date > p_date:
                days_held = (calc_date - p_date).days
                # Days into current half-year cycle (182.5 days)
                days_in_cycle = days_held % 182
                accrued_coupon = quantize_currency(
                    base_value * (coupon_pct / Decimal('100.0')) * (Decimal(days_in_cycle) / Decimal('365.0'))
                )

        total_value = quantize_currency(base_value + accrued_coupon)

        return ValuationResult(
            current_value=total_value,
            valuation_method='SGB_VALUATION',
            source=source_name,
            source_reference=source_ref or 'SGB-SERIES',
            observed_at=obs_dt,
            is_synthetic=is_synthetic,
            currency=investment.currency,
            status=ValuationStatus.SUCCESS,
            metadata={
                'units': str(units),
                'unit_price': str(unit_price),
                'accrued_coupon': str(accrued_coupon),
                'coupon_rate_pct': str(coupon_pct),
                'sgb_series': source_ref,
                'is_synthetic': is_synthetic,
            },
        )
