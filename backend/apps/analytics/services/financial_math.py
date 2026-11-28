import math
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional, Tuple, Union

FOUR_PLACES = Decimal('0.0001')
TWO_PLACES = Decimal('0.01')
SIX_PLACES = Decimal('0.000001')


def to_decimal(val: Union[Decimal, float, int, str, None], default: str = '0.00') -> Decimal:
    if val is None or val == '':
        return Decimal(default)
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal(default)


def quantize_currency(amount: Union[Decimal, float, int, str], places: int = 2) -> Decimal:
    d = to_decimal(amount)
    fmt = Decimal('10') ** -places
    return d.quantize(fmt, rounding=ROUND_HALF_UP)


@dataclass
class CashFlow:
    """Dated cash flow for money-weighted return (XIRR).
    Outflows (investor deposits/buys) are negative.
    Inflows (sales/dividends/terminal value) are positive.
    """
    flow_date: date
    amount: Decimal  # Positive or negative Decimal


@dataclass
class TaxLot:
    """An open acquisition lot for FIFO tracking."""
    lot_id: str
    acquisition_date: date
    units: Decimal
    price_per_unit: Decimal
    acquisition_cost: Decimal  # gross + proportional fees/taxes
    remaining_units: Decimal
    remaining_cost: Decimal


@dataclass
class DisposalMatch:
    """Result of matching a sale transaction against open lots."""
    matched_lots: List[Tuple[TaxLot, Decimal, Decimal]]  # (lot, units_sold_from_lot, cost_allocated)
    sold_units: Decimal
    gross_proceeds: Decimal
    allocated_cost_basis: Decimal
    net_proceeds: Decimal
    realized_gain_loss: Decimal


class LotMatchingEngine:
    """Deterministic FIFO and Weighted Average lot matching engine."""

    @classmethod
    def match_fifo(
        cls,
        open_lots: List[TaxLot],
        sell_units: Decimal,
        sell_price_per_unit: Decimal,
        sell_fees: Decimal = Decimal('0'),
        sell_taxes: Decimal = Decimal('0'),
    ) -> DisposalMatch:
        """Matches a disposal against open acquisition lots in strict FIFO order.
        Raises ValueError if sell_units exceeds available quantity.
        """
        sell_units = to_decimal(sell_units)
        sell_price_per_unit = to_decimal(sell_price_per_unit)
        sell_fees = to_decimal(sell_fees)
        sell_taxes = to_decimal(sell_taxes)

        available_units = sum(lot.remaining_units for lot in open_lots)
        if sell_units > available_units:
            raise ValueError(
                f"Cannot sell {sell_units} units: only {available_units} units available in open lots."
            )

        matched_lots: List[Tuple[TaxLot, Decimal, Decimal]] = []
        remaining_to_sell = sell_units
        total_allocated_cost = Decimal('0')

        # Lots must be in chronological order
        sorted_lots = sorted(open_lots, key=lambda lot_obj: (lot_obj.acquisition_date, lot_obj.lot_id))

        for lot in sorted_lots:
            if remaining_to_sell <= Decimal('0'):
                break

            if lot.remaining_units <= Decimal('0'):
                continue

            units_from_lot = min(remaining_to_sell, lot.remaining_units)
            cost_ratio = units_from_lot / lot.remaining_units if lot.remaining_units > 0 else Decimal('0')
            allocated_cost_for_slice = (lot.remaining_cost * cost_ratio).quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)

            # Update lot
            lot.remaining_units = (lot.remaining_units - units_from_lot).quantize(FOUR_PLACES)
            lot.remaining_cost = max(Decimal('0'), lot.remaining_cost - allocated_cost_for_slice)

            matched_lots.append((lot, units_from_lot, allocated_cost_for_slice))
            total_allocated_cost += allocated_cost_for_slice
            remaining_to_sell -= units_from_lot

        gross_proceeds = (sell_units * sell_price_per_unit).quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)
        net_proceeds = gross_proceeds - sell_fees - sell_taxes
        realized_pnl = net_proceeds - total_allocated_cost

        return DisposalMatch(
            matched_lots=matched_lots,
            sold_units=sell_units,
            gross_proceeds=gross_proceeds,
            allocated_cost_basis=total_allocated_cost,
            net_proceeds=net_proceeds,
            realized_gain_loss=realized_pnl,
        )


class FinancialMathEngine:
    """Robust, purely functional financial return calculators."""

    @classmethod
    def calculate_absolute_return(
        cls,
        current_value: Decimal,
        cost_basis: Decimal,
    ) -> Tuple[Decimal, Optional[Decimal]]:
        """Returns (absolute_pnl, percentage_return).
        Returns None for percentage if cost_basis <= 0.
        """
        curr = to_decimal(current_value)
        cost = to_decimal(cost_basis)
        pnl = curr - cost
        if cost > Decimal('0'):
            pct = ((pnl / cost) * Decimal('100')).quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)
            return pnl, pct
        return pnl, None

    @classmethod
    def calculate_cagr(
        cls,
        start_value: Decimal,
        end_value: Decimal,
        start_date: date,
        end_date: date,
    ) -> Optional[Decimal]:
        """Calculates Compound Annual Growth Rate (CAGR).
        Only valid when holding duration >= 365 days and start_value > 0 and end_value >= 0.
        """
        v_start = to_decimal(start_value)
        v_end = to_decimal(end_value)
        if v_start <= Decimal('0') or v_end < Decimal('0'):
            return None

        days = (end_date - start_date).days
        if days < 365:
            # ERD requires CAGR only for periods >= 1 year to avoid misleading annualization
            return None

        years = float(days) / 365.25
        try:
            ratio = float(v_end / v_start)
            cagr_float = (ratio ** (1.0 / years)) - 1.0
            return (Decimal(str(cagr_float)) * Decimal('100')).quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)
        except Exception:
            return None

    @classmethod
    def calculate_xirr(
        cls,
        cash_flows: List[CashFlow],
        max_iterations: int = 100,
        tolerance: float = 1e-6,
    ) -> Tuple[Optional[Decimal], str]:
        """Calculates exact Extended Internal Rate of Return (XIRR).
        Returns (rate_percentage, status_str).
        Status is one of: 'SUCCESS', 'INSUFFICIENT_CASH_FLOWS', 'NO_SIGN_CHANGE', 'NON_CONVERGENT', 'INVALID_DATES'.
        """
        if len(cash_flows) < 2:
            return None, 'INSUFFICIENT_CASH_FLOWS'

        # Check for both positive and negative cash flows
        has_negative = any(cf.amount < Decimal('0') for cf in cash_flows)
        has_positive = any(cf.amount > Decimal('0') for cf in cash_flows)
        if not (has_negative and has_positive):
            return None, 'NO_SIGN_CHANGE'

        sorted_flows = sorted(cash_flows, key=lambda cf: cf.flow_date)
        d0 = sorted_flows[0].flow_date

        dates_and_amounts = [
            ((cf.flow_date - d0).days / 365.25, float(cf.amount))
            for cf in sorted_flows
        ]

        def npv(rate: float) -> float:
            if rate <= -1.0:
                return float('inf')
            val = 0.0
            for t, amt in dates_and_amounts:
                denom = (1.0 + rate) ** t
                if denom == 0:
                    return float('inf')
                val += amt / denom
            return val

        def npv_prime(rate: float) -> float:
            if rate <= -1.0:
                return float('-inf')
            val = 0.0
            for t, amt in dates_and_amounts:
                denom = (1.0 + rate) ** (t + 1.0)
                if denom == 0:
                    continue
                val -= (t * amt) / denom
            return val

        # Initial guess
        rate = 0.10

        # Newton-Raphson iteration
        for _ in range(max_iterations):
            val = npv(rate)
            if math.isnan(val) or math.isinf(val):
                break
            if abs(val) < tolerance:
                res_pct = (Decimal(str(rate)) * Decimal('100')).quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)
                return res_pct, 'SUCCESS'

            deriv = npv_prime(rate)
            if deriv == 0 or math.isnan(deriv) or math.isinf(deriv):
                break

            new_rate = rate - (val / deriv)
            if new_rate <= -0.9999 or new_rate > 100.0:  # Restrict bounds
                break
            if abs(new_rate - rate) < tolerance:
                res_pct = (Decimal(str(new_rate)) * Decimal('100')).quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)
                return res_pct, 'SUCCESS'
            rate = new_rate

        # Fallback to Bisection method if Newton-Raphson failed to converge
        low = -0.99
        high = 10.0  # 1000%
        val_low = npv(low)
        val_high = npv(high)

        if val_low * val_high <= 0:
            for _ in range(100):
                mid = (low + high) / 2.0
                val_mid = npv(mid)
                if abs(val_mid) < tolerance or (high - low) / 2.0 < tolerance:
                    res_pct = (Decimal(str(mid)) * Decimal('100')).quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)
                    return res_pct, 'SUCCESS'
                if val_mid * val_low <= 0:
                    high = mid
                    val_high = val_mid
                else:
                    low = mid
                    val_low = val_mid

        return None, 'NON_CONVERGENT'
