import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.utils import timezone

from apps.analytics.services.financial_math import (
    CashFlow,
    FinancialMathEngine,
    LotMatchingEngine,
    TaxLot,
    to_decimal,
)
from apps.assets.models.investment import Investment
from apps.assets.models.transactions import InvestmentTransaction
from apps.assets.models.valuations import InvestmentValuation
from apps.market_data.services.history_service import MARKET_TZ, MarketHistoryService
from apps.market_data.services.price_resolver import PriceResolver

logger = logging.getLogger(__name__)


@dataclass
class HoldingPoint:
    date: str
    quantity: Decimal
    cost_basis: Decimal
    market_price: Optional[Decimal]
    market_value: Optional[Decimal]
    unrealized_pnl: Optional[Decimal]
    realized_pnl: Decimal
    total_pnl: Optional[Decimal]
    is_price_available: bool = True
    valuation_source: str = 'MARKET'


@dataclass
class InvestmentPerformanceResult:
    investment_id: str
    currency: str
    current_quantity: Decimal
    initial_invested_capital: Decimal
    net_invested_capital: Decimal
    current_cost_basis: Decimal
    current_market_price: Optional[Decimal]
    current_market_value: Optional[Decimal]
    realized_pnl: Decimal
    unrealized_pnl: Optional[Decimal]
    total_pnl: Optional[Decimal]
    absolute_return_pct: Optional[Decimal]
    cagr_pct: Optional[Decimal]
    xirr_pct: Optional[Decimal]
    xirr_status: str
    first_transaction_date: Optional[str]
    latest_transaction_date: Optional[str]
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    history: List[HoldingPoint] = field(default_factory=list)
    data_completeness: Dict[str, Any] = field(default_factory=dict)


class InvestmentPerformanceService:
    """Reconstructs historical holdings, cost basis, realized/unrealized gains,
    and performance time-series from immutable transaction records using single-pass
    chronological event-stream processing.
    """

    @classmethod
    def get_investment_performance(
        cls,
        investment: Investment,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> InvestmentPerformanceResult:
        today = timezone.now().astimezone(MARKET_TZ).date()
        resolved_end = min(end_date or today, today)

        # 1. Fetch eligible transactions effective on or before resolved_end
        # Filter out future transactions per ERD Section 6.1
        tx_list = list(
            InvestmentTransaction.objects.filter(
                investment=investment,
                transaction_date__lte=resolved_end,
            ).select_related('reversal_of').order_by('transaction_date', 'created_at')
        )

        open_lots: List[TaxLot] = []
        disposal_matches: Dict[str, Any] = {}
        cumulative_realized_pnl = Decimal('0.0000')
        total_invested_gross = Decimal('0.0000')
        total_fees = Decimal('0.0000')
        total_taxes = Decimal('0.0000')

        timeline_entries: List[Dict[str, Any]] = []
        cash_flows: List[CashFlow] = []

        first_tx_date: Optional[date] = None
        latest_tx_date: Optional[date] = None

        # Build transaction indexed by date for chronological streaming
        txs_by_date: Dict[date, List[InvestmentTransaction]] = {}
        for tx in tx_list:
            d = tx.transaction_date
            txs_by_date.setdefault(d, []).append(tx)

            if first_tx_date is None or d < first_tx_date:
                first_tx_date = d
            if latest_tx_date is None or d > latest_tx_date:
                latest_tx_date = d

            tx_type = tx.transaction_type.upper()
            gross = to_decimal(tx.gross_amount or tx.amount)
            f = to_decimal(tx.fees)
            t = to_decimal(tx.taxes)
            u = to_decimal(tx.units)
            p = to_decimal(tx.price_per_unit)

            total_fees += f
            total_taxes += t

            if tx_type in ('INITIAL_PURCHASE', 'BUY', 'DEPOSIT'):
                lot_cost = gross + f + t
                total_invested_gross += lot_cost
                lot = TaxLot(
                    lot_id=str(tx.id),
                    acquisition_date=d,
                    units=u,
                    price_per_unit=p,
                    acquisition_cost=lot_cost,
                    remaining_units=u,
                    remaining_cost=lot_cost,
                )
                open_lots.append(lot)
                cash_flows.append(CashFlow(d, -lot_cost))

                timeline_entries.append({
                    'id': str(tx.id),
                    'date': d.isoformat(),
                    'type': tx_type,
                    'units': str(u),
                    'price_per_unit': str(p),
                    'gross_amount': str(gross),
                    'fees': str(f),
                    'taxes': str(t),
                    'net_cash_flow': str(-lot_cost),
                    'notes': tx.notes,
                })

            elif tx_type in ('SELL', 'WITHDRAWAL'):
                match = LotMatchingEngine.match_fifo(
                    open_lots=open_lots,
                    sell_units=u,
                    sell_price_per_unit=p,
                    sell_fees=f,
                    sell_taxes=t,
                )
                disposal_matches[str(tx.id)] = match
                cumulative_realized_pnl += match.realized_gain_loss
                cash_flows.append(CashFlow(d, match.net_proceeds))

                timeline_entries.append({
                    'id': str(tx.id),
                    'date': d.isoformat(),
                    'type': tx_type,
                    'units': str(u),
                    'price_per_unit': str(p),
                    'gross_amount': str(match.gross_proceeds),
                    'allocated_cost_basis': str(match.allocated_cost_basis),
                    'realized_gain_loss': str(match.realized_gain_loss),
                    'fees': str(f),
                    'taxes': str(t),
                    'net_cash_flow': str(match.net_proceeds),
                    'notes': tx.notes,
                })

            elif tx_type in ('DIVIDEND', 'INTEREST'):
                net_payout = gross - f - t
                cumulative_realized_pnl += net_payout
                cash_flows.append(CashFlow(d, net_payout))
                timeline_entries.append({
                    'id': str(tx.id),
                    'date': d.isoformat(),
                    'type': tx_type,
                    'units': '0',
                    'price_per_unit': '0',
                    'gross_amount': str(gross),
                    'fees': str(f),
                    'taxes': str(t),
                    'net_cash_flow': str(net_payout),
                    'notes': tx.notes,
                })

            elif tx_type == 'REVERSAL' and tx.reversal_of:
                orig_tx = tx.reversal_of
                orig_type = orig_tx.transaction_type.upper()
                orig_id = str(orig_tx.id)

                if orig_type in ('INITIAL_PURCHASE', 'BUY', 'DEPOSIT'):
                    orig_gross = to_decimal(orig_tx.gross_amount or orig_tx.amount)
                    orig_f = to_decimal(orig_tx.fees)
                    orig_t = to_decimal(orig_tx.taxes)
                    orig_cost = orig_gross + orig_f + orig_t
                    total_invested_gross = max(Decimal('0'), total_invested_gross - orig_cost)
                    cash_flows.append(CashFlow(d, orig_cost))  # Refund / cash inflow

                    # Remove the lot or reduce remaining units
                    for lot in open_lots:
                        if lot.lot_id == orig_id:
                            lot.remaining_units = Decimal('0')
                            lot.remaining_cost = Decimal('0')
                            break

                elif orig_type in ('SELL', 'WITHDRAWAL'):
                    orig_match = disposal_matches.get(orig_id)
                    if orig_match:
                        # Restore exact tax lots from previous match
                        for lot, units_sold, cost_alloc in orig_match.matched_lots:
                            lot.remaining_units = (lot.remaining_units + units_sold).quantize(Decimal('0.0001'))
                            lot.remaining_cost = (lot.remaining_cost + cost_alloc).quantize(Decimal('0.0001'))
                        cumulative_realized_pnl -= orig_match.realized_gain_loss
                        cash_flows.append(CashFlow(d, -orig_match.net_proceeds))  # Undo sale proceeds
                    else:
                        # Fallback lot restoration
                        restored_lot = TaxLot(
                            lot_id=f"restored_{orig_id}",
                            acquisition_date=orig_tx.transaction_date,
                            units=u,
                            price_per_unit=p,
                            acquisition_cost=gross,
                            remaining_units=u,
                            remaining_cost=gross,
                        )
                        open_lots.append(restored_lot)
                        cash_flows.append(CashFlow(d, -gross))

                elif orig_type in ('DIVIDEND', 'INTEREST'):
                    orig_gross = to_decimal(orig_tx.gross_amount or orig_tx.amount)
                    orig_payout = orig_gross - to_decimal(orig_tx.fees) - to_decimal(orig_tx.taxes)
                    cumulative_realized_pnl -= orig_payout
                    cash_flows.append(CashFlow(d, -orig_payout))

                timeline_entries.append({
                    'id': str(tx.id),
                    'date': d.isoformat(),
                    'type': 'REVERSAL',
                    'reversal_of_id': orig_id,
                    'units': str(u),
                    'price_per_unit': str(p),
                    'gross_amount': str(gross),
                    'fees': str(f),
                    'taxes': str(t),
                    'net_cash_flow': str(tx.net_cash_flow or Decimal('0')),
                    'notes': tx.notes or f"Reversed transaction {orig_id}",
                })

        # Calculate current remaining state
        current_remaining_units = sum(lot.remaining_units for lot in open_lots)
        current_remaining_cost = sum(lot.remaining_cost for lot in open_lots)

        # Resolve current market price / value
        current_market_price: Optional[Decimal] = None
        current_market_val: Optional[Decimal] = None
        unrealized_pnl: Optional[Decimal] = None
        total_pnl: Optional[Decimal] = None

        if investment.instrument:
            res = PriceResolver.resolve_price(investment.instrument)
            if res and res.price is not None:
                current_market_price = res.price
                current_market_val = (current_remaining_units * current_market_price).quantize(Decimal('0.01'))
        elif to_decimal(investment.current_value) > Decimal('0'):
            current_market_val = to_decimal(investment.current_value)
        else:
            # Check latest InvestmentValuation snapshot
            latest_val = InvestmentValuation.objects.filter(
                investment=investment,
                valuation_date__lte=resolved_end,
            ).order_by('-valuation_date', '-created_at').first()
            if latest_val:
                current_market_val = latest_val.amount

        if current_market_val is not None:
            unrealized_pnl = current_market_val - current_remaining_cost
            total_pnl = cumulative_realized_pnl + unrealized_pnl
            if current_market_val > Decimal('0') or current_remaining_units > Decimal('0'):
                cash_flows.append(CashFlow(resolved_end, current_market_val))

        # Performance metrics
        _, abs_pct = (None, None)
        if current_market_val is not None:
            _, abs_pct = FinancialMathEngine.calculate_absolute_return(
                current_value=current_market_val,
                cost_basis=current_remaining_cost if current_remaining_cost > 0 else total_invested_gross,
            )

        cagr_pct: Optional[Decimal] = None
        if first_tx_date and current_market_val is not None:
            cagr_pct = FinancialMathEngine.calculate_cagr(
                start_value=total_invested_gross,
                end_value=current_market_val,
                start_date=first_tx_date,
                end_date=resolved_end,
            )

        xirr_pct, xirr_status = FinancialMathEngine.calculate_xirr(cash_flows)

        # Reconstruct historical daily curve in bounded range
        history_points: List[HoldingPoint] = []
        resolved_start = start_date or (first_tx_date or (resolved_end - timedelta(days=365)))
        if resolved_start < (resolved_end - timedelta(days=365 * 5)):
            resolved_start = resolved_end - timedelta(days=365 * 5)

        # 2. Fetch market observations in one bounded batch
        market_price_by_date: Dict[str, Decimal] = {}
        if investment.instrument:
            try:
                hist = MarketHistoryService.get_history(
                    investment.instrument,
                    period='ALL',
                    start_date=resolved_start,
                    end_date=resolved_end,
                )
                if hist and hist.points:
                    for pt in hist.points:
                        market_price_by_date[pt.date] = pt.price
            except Exception as e:
                logger.warning("MarketHistoryService error for %s: %s", investment.display_name, e)

        # 3. Fetch non-market InvestmentValuation snapshots in one bounded batch
        valuations_by_date: Dict[str, Decimal] = {}
        val_snaps = InvestmentValuation.objects.filter(
            investment=investment,
            valuation_date__gte=resolved_start,
            valuation_date__lte=resolved_end,
        ).order_by('valuation_date', 'created_at')
        for v in val_snaps:
            valuations_by_date[v.valuation_date.isoformat()] = v.amount

        # 4. Chronological single-pass stream processing (no replaying from day 0)
        # Pre-accumulate state up to resolved_start
        running_lots: List[TaxLot] = []
        running_realized = Decimal('0.0000')

        pre_txs = [t for t in tx_list if t.transaction_date < resolved_start]
        for t in pre_txs:
            t_type = t.transaction_type.upper()
            g = to_decimal(t.gross_amount or t.amount)
            fees = to_decimal(t.fees)
            taxes = to_decimal(t.taxes)
            units = to_decimal(t.units)
            price = to_decimal(t.price_per_unit)
            if t_type in ('INITIAL_PURCHASE', 'BUY', 'DEPOSIT'):
                cost = g + fees + taxes
                running_lots.append(TaxLot(str(t.id), t.transaction_date, units, price, cost, units, cost))
            elif t_type in ('SELL', 'WITHDRAWAL'):
                try:
                    m = LotMatchingEngine.match_fifo(running_lots, units, price, fees, taxes)
                    running_realized += m.realized_gain_loss
                except ValueError:
                    pass
            elif t_type in ('DIVIDEND', 'INTEREST'):
                running_realized += (g - fees - taxes)

        # Now advance day-by-day in single pass
        last_known_market_price: Optional[Decimal] = None
        last_known_valuation_amount: Optional[Decimal] = None
        curr_d = resolved_start

        while curr_d <= resolved_end:
            d_str = curr_d.isoformat()
            days_txs = txs_by_date.get(curr_d, [])
            for t in days_txs:
                t_type = t.transaction_type.upper()
                g = to_decimal(t.gross_amount or t.amount)
                fees = to_decimal(t.fees)
                taxes = to_decimal(t.taxes)
                units = to_decimal(t.units)
                price = to_decimal(t.price_per_unit)
                if t_type in ('INITIAL_PURCHASE', 'BUY', 'DEPOSIT'):
                    cost = g + fees + taxes
                    running_lots.append(TaxLot(str(t.id), t.transaction_date, units, price, cost, units, cost))
                elif t_type in ('SELL', 'WITHDRAWAL'):
                    try:
                        m = LotMatchingEngine.match_fifo(running_lots, units, price, fees, taxes)
                        running_realized += m.realized_gain_loss
                    except ValueError:
                        pass
                elif t_type in ('DIVIDEND', 'INTEREST'):
                    running_realized += (g - fees - taxes)

            h_units = sum(lot_item.remaining_units for lot_item in running_lots)
            h_cost = sum(lot_item.remaining_cost for lot_item in running_lots)

            # Price carry-forward for market-traded assets (weekends / holidays)
            m_price = market_price_by_date.get(d_str)
            if m_price is not None:
                last_known_market_price = m_price
            effective_price = m_price or last_known_market_price

            # Check snapshot valuation for non-market assets
            v_amount = valuations_by_date.get(d_str)
            if v_amount is not None:
                last_known_valuation_amount = v_amount
            effective_valuation = v_amount or last_known_valuation_amount

            m_val: Optional[Decimal] = None
            val_source = 'NONE'
            if effective_price is not None and h_units > Decimal('0'):
                m_val = (h_units * effective_price).quantize(Decimal('0.01'))
                val_source = 'MARKET'
            elif effective_valuation is not None:
                m_val = effective_valuation
                val_source = 'VALUATION_SNAPSHOT'

            u_pnl = (m_val - h_cost) if m_val is not None else None
            tot_pnl = (running_realized + u_pnl) if u_pnl is not None else None

            history_points.append(HoldingPoint(
                date=d_str,
                quantity=h_units,
                cost_basis=h_cost,
                market_price=effective_price,
                market_value=m_val,
                unrealized_pnl=u_pnl,
                realized_pnl=running_realized,
                total_pnl=tot_pnl,
                is_price_available=(m_val is not None),
                valuation_source=val_source,
            ))
            curr_d += timedelta(days=1)

        reconciled = True
        discrepancy_notes = []
        if tx_list and investment.initial_value and investment.initial_value > Decimal('0'):
            diff = abs(total_invested_gross - investment.initial_value)
            if diff > Decimal('1.00'):  # Allow minor rounding tolerance
                reconciled = False
                discrepancy_notes.append(
                    f"Stored initial value ({investment.initial_value}) differs from transaction ledger cost basis ({total_invested_gross}) by {diff}."
                )

        return InvestmentPerformanceResult(
            investment_id=str(investment.id),
            currency=investment.currency or 'INR',
            current_quantity=current_remaining_units,
            initial_invested_capital=total_invested_gross,
            net_invested_capital=current_remaining_cost,
            current_cost_basis=current_remaining_cost,
            current_market_price=current_market_price,
            current_market_value=current_market_val,
            realized_pnl=cumulative_realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_pnl=total_pnl,
            absolute_return_pct=abs_pct,
            cagr_pct=cagr_pct,
            xirr_pct=xirr_pct,
            xirr_status=xirr_status,
            first_transaction_date=first_tx_date.isoformat() if first_tx_date else None,
            latest_transaction_date=latest_tx_date.isoformat() if latest_tx_date else None,
            timeline=timeline_entries,
            history=history_points,
            data_completeness={
                'total_days': len(history_points),
                'days_with_price': sum(1 for p in history_points if p.is_price_available),
                'has_transactions': bool(tx_list),
                'reconciliation_status': 'RECONCILED' if reconciled else 'DISCREPANCY',
                'reconciliation_notes': discrepancy_notes,
            },
        )
