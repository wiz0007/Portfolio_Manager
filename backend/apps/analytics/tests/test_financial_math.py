from datetime import date
from decimal import Decimal

import pytest

from apps.analytics.services.financial_math import (
    CashFlow,
    FinancialMathEngine,
    LotMatchingEngine,
    TaxLot,
)


class TestLotMatchingEngine:
    def test_single_purchase_full_sale(self):
        lot = TaxLot(
            lot_id='lot-1',
            acquisition_date=date(2026, 1, 1),
            units=Decimal('10.0000'),
            price_per_unit=Decimal('100.0000'),
            acquisition_cost=Decimal('1000.0000'),
            remaining_units=Decimal('10.0000'),
            remaining_cost=Decimal('1000.0000'),
        )
        match = LotMatchingEngine.match_fifo(
            open_lots=[lot],
            sell_units=Decimal('10.0000'),
            sell_price_per_unit=Decimal('120.0000'),
            sell_fees=Decimal('20.0000'),
        )
        assert match.sold_units == Decimal('10.0000')
        assert match.gross_proceeds == Decimal('1200.0000')
        assert match.allocated_cost_basis == Decimal('1000.0000')
        assert match.net_proceeds == Decimal('1180.0000')
        assert match.realized_gain_loss == Decimal('180.0000')
        assert lot.remaining_units == Decimal('0.0000')
        assert lot.remaining_cost == Decimal('0.0000')

    def test_multiple_purchases_partial_sale_fifo(self):
        lot1 = TaxLot(
            lot_id='lot-1',
            acquisition_date=date(2026, 1, 1),
            units=Decimal('10.0000'),
            price_per_unit=Decimal('100.0000'),
            acquisition_cost=Decimal('1000.0000'),
            remaining_units=Decimal('10.0000'),
            remaining_cost=Decimal('1000.0000'),
        )
        lot2 = TaxLot(
            lot_id='lot-2',
            acquisition_date=date(2026, 2, 1),
            units=Decimal('10.0000'),
            price_per_unit=Decimal('120.0000'),
            acquisition_cost=Decimal('1200.0000'),
            remaining_units=Decimal('10.0000'),
            remaining_cost=Decimal('1200.0000'),
        )
        # Sell 15 units (all of lot 1 + 5 of lot 2)
        match = LotMatchingEngine.match_fifo(
            open_lots=[lot1, lot2],
            sell_units=Decimal('15.0000'),
            sell_price_per_unit=Decimal('150.0000'),
            sell_fees=Decimal('0.0000'),
        )
        assert match.sold_units == Decimal('15.0000')
        assert match.gross_proceeds == Decimal('2250.0000')
        # Lot 1: 10 * 100 = 1000, Lot 2: 5 * 120 = 600 => Total cost basis = 1600
        assert match.allocated_cost_basis == Decimal('1600.0000')
        assert match.realized_gain_loss == Decimal('650.0000')

        # Remaining state
        assert lot1.remaining_units == Decimal('0.0000')
        assert lot1.remaining_cost == Decimal('0.0000')
        assert lot2.remaining_units == Decimal('5.0000')
        assert lot2.remaining_cost == Decimal('600.0000')

    def test_sell_more_than_available_raises(self):
        lot = TaxLot(
            lot_id='lot-1',
            acquisition_date=date(2026, 1, 1),
            units=Decimal('5.0000'),
            price_per_unit=Decimal('100.0000'),
            acquisition_cost=Decimal('500.0000'),
            remaining_units=Decimal('5.0000'),
            remaining_cost=Decimal('500.0000'),
        )
        with pytest.raises(ValueError, match=r"Cannot sell 10\.0000 units"):
            LotMatchingEngine.match_fifo(
                open_lots=[lot],
                sell_units=Decimal('10.0000'),
                sell_price_per_unit=Decimal('100.0000'),
            )


class TestFinancialMathEngine:
    def test_absolute_return(self):
        pnl, pct = FinancialMathEngine.calculate_absolute_return(
            current_value=Decimal('15000.00'),
            cost_basis=Decimal('10000.00'),
        )
        assert pnl == Decimal('5000.00')
        assert pct == Decimal('50.0000')

    def test_cagr_exact(self):
        cagr = FinancialMathEngine.calculate_cagr(
            start_value=Decimal('10000.00'),
            end_value=Decimal('14400.00'),  # 20% per year for 2 years (1.2^2 = 1.44)
            start_date=date(2024, 1, 1),
            end_date=date(2026, 1, 1),
        )
        assert cagr is not None
        # approx 20%
        assert Decimal('19.9') < cagr < Decimal('20.1')

    def test_cagr_under_one_year_returns_none(self):
        cagr = FinancialMathEngine.calculate_cagr(
            start_value=Decimal('10000.00'),
            end_value=Decimal('12000.00'),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 1),
        )
        assert cagr is None

    def test_xirr_standard_investment(self):
        # Invest 10,000 on 2025-01-01, terminal value 11,000 on 2026-01-01 -> approx 10%
        flows = [
            CashFlow(date(2025, 1, 1), Decimal('-10000.00')),
            CashFlow(date(2026, 1, 1), Decimal('11000.00')),
        ]
        rate, status = FinancialMathEngine.calculate_xirr(flows)
        assert status == 'SUCCESS'
        assert rate is not None
        assert Decimal('9.9') < rate < Decimal('10.1')

    def test_xirr_insufficient_or_no_sign_change(self):
        flows = [CashFlow(date(2025, 1, 1), Decimal('-10000.00'))]
        rate, status = FinancialMathEngine.calculate_xirr(flows)
        assert status == 'INSUFFICIENT_CASH_FLOWS'
        assert rate is None

        flows_no_pos = [
            CashFlow(date(2025, 1, 1), Decimal('-10000.00')),
            CashFlow(date(2025, 6, 1), Decimal('-5000.00')),
        ]
        rate, status = FinancialMathEngine.calculate_xirr(flows_no_pos)
        assert status == 'NO_SIGN_CHANGE'
        assert rate is None
