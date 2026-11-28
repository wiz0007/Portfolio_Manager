import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.utils import timezone

from apps.analytics.services.financial_math import (
    CashFlow,
    FinancialMathEngine,
    quantize_currency,
)
from apps.analytics.services.fx_service import FXConversionService
from apps.analytics.services.investment_performance_service import (
    InvestmentPerformanceResult,
    InvestmentPerformanceService,
)
from apps.assets.models.investment import Investment
from apps.market_data.services.history_service import MARKET_TZ
from apps.portfolios.models import Portfolio

logger = logging.getLogger(__name__)


@dataclass
class PortfolioTimeSeriesPoint:
    date: str
    market_value: Decimal
    invested_capital: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    net_cash_flow_on_date: Decimal
    twr_cumulative_pct: Optional[Decimal] = None


@dataclass
class PortfolioPerformanceResult:
    portfolio_id: str
    portfolio_name: str
    currency: str
    current_value: Decimal
    total_invested_capital: Decimal
    current_cost_basis: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    absolute_return_pct: Optional[Decimal]
    cagr_pct: Optional[Decimal]
    xirr_pct: Optional[Decimal]
    xirr_status: str
    twr_pct: Optional[Decimal]
    active_holdings_count: int
    closed_holdings_count: int
    history: List[PortfolioTimeSeriesPoint] = field(default_factory=list)
    holdings_summary: List[Dict[str, Any]] = field(default_factory=list)
    data_completeness: Dict[str, Any] = field(default_factory=dict)


class PortfolioPerformanceService:
    """Aggregates multi-holding portfolio performance, reconstructing historical
    portfolio values, capital contributions, and money-weighted returns (XIRR).
    Ensures that unvalued holdings yield honest partial completeness metadata.
    """

    @classmethod
    def get_portfolio_performance(
        cls,
        portfolio: Portfolio,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> PortfolioPerformanceResult:
        today = timezone.now().astimezone(MARKET_TZ).date()
        resolved_end = min(end_date or today, today)

        # Retrieve all investments for this portfolio
        investments = list(
            Investment.objects.filter(portfolio=portfolio)
            .select_related('instrument')
        )

        holding_results: List[InvestmentPerformanceResult] = []
        for inv in investments:
            res = InvestmentPerformanceService.get_investment_performance(
                investment=inv,
                start_date=start_date,
                end_date=resolved_end,
            )
            holding_results.append(res)

        total_curr_val = Decimal('0.00')
        total_inv_capital = Decimal('0.00')
        total_cost_basis = Decimal('0.00')
        total_realized = Decimal('0.00')
        total_unrealized = Decimal('0.00')
        total_pnl = Decimal('0.00')

        active_count = 0
        closed_count = 0
        unvalued_count = 0

        portfolio_cash_flows: List[CashFlow] = []
        holdings_summary: List[Dict[str, Any]] = []
        earliest_start: Optional[date] = None
        fx_warnings: List[str] = []

        for hr in holding_results:
            is_active = hr.current_quantity > Decimal('0') or (hr.current_market_value or Decimal('0')) > Decimal('0')
            if is_active:
                active_count += 1
            else:
                closed_count += 1

            if is_active and hr.current_market_value is None:
                unvalued_count += 1

            # Convert holding amounts to portfolio base currency if currency differs
            raw_curr_val = hr.current_market_value or Decimal('0.00')
            raw_cost_basis = hr.current_cost_basis
            raw_realized = hr.realized_pnl
            raw_unrealized = hr.unrealized_pnl or Decimal('0.00')
            raw_total_pnl = hr.total_pnl or hr.realized_pnl
            raw_inv_capital = hr.initial_invested_capital

            c_val = raw_curr_val
            c_cost = raw_cost_basis
            c_realized = raw_realized
            c_unrealized = raw_unrealized
            c_total_pnl = raw_total_pnl
            c_inv_capital = raw_inv_capital

            if hr.currency != portfolio.base_currency:
                c_val, _, status_val = FXConversionService.convert_amount(
                    raw_curr_val, hr.currency, portfolio.base_currency, resolved_end
                )
                c_cost, _, _ = FXConversionService.convert_amount(
                    raw_cost_basis, hr.currency, portfolio.base_currency, resolved_end
                )
                c_realized, _, _ = FXConversionService.convert_amount(
                    raw_realized, hr.currency, portfolio.base_currency, resolved_end
                )
                c_unrealized, _, _ = FXConversionService.convert_amount(
                    raw_unrealized, hr.currency, portfolio.base_currency, resolved_end
                )
                c_total_pnl, _, _ = FXConversionService.convert_amount(
                    raw_total_pnl, hr.currency, portfolio.base_currency, resolved_end
                )
                c_inv_capital, _, _ = FXConversionService.convert_amount(
                    raw_inv_capital, hr.currency, portfolio.base_currency, resolved_end
                )
                if status_val == 'MISSING':
                    fx_warnings.append(f"Missing FX rate for {hr.currency} -> {portfolio.base_currency} as of {resolved_end}")

            total_curr_val += c_val
            total_inv_capital += c_inv_capital
            total_cost_basis += c_cost
            total_realized += c_realized
            total_unrealized += c_unrealized
            total_pnl += c_total_pnl

            # Collect timeline cash flows
            for entry in hr.timeline:
                flow_d = date.fromisoformat(entry['date'])
                if flow_d <= resolved_end:
                    if earliest_start is None or flow_d < earliest_start:
                        earliest_start = flow_d
                    net_cf = Decimal(entry['net_cash_flow'])
                    if hr.currency != portfolio.base_currency:
                        net_cf, _, _ = FXConversionService.convert_amount(
                            net_cf, hr.currency, portfolio.base_currency, flow_d
                        )
                    portfolio_cash_flows.append(CashFlow(flow_d, net_cf))

            holdings_summary.append({
                'investment_id': hr.investment_id,
                'current_quantity': str(hr.current_quantity),
                'cost_basis': str(quantize_currency(c_cost)),
                'market_value': str(quantize_currency(c_val)),
                'realized_pnl': str(quantize_currency(c_realized)),
                'unrealized_pnl': str(quantize_currency(c_unrealized)),
                'total_pnl': str(quantize_currency(c_total_pnl)),
                'absolute_return_pct': str(hr.absolute_return_pct) if hr.absolute_return_pct is not None else None,
                'xirr_pct': str(hr.xirr_pct) if hr.xirr_pct is not None else None,
                'is_active': is_active,
                'is_valued': hr.current_market_value is not None,
                'original_currency': hr.currency,
            })

        # Add terminal valuation flow for portfolio XIRR
        if total_curr_val > Decimal('0') or active_count > 0:
            portfolio_cash_flows.append(CashFlow(resolved_end, total_curr_val))

        _, p_abs_pct = FinancialMathEngine.calculate_absolute_return(
            current_value=total_curr_val,
            cost_basis=total_cost_basis if total_cost_basis > 0 else total_inv_capital,
        )

        p_cagr: Optional[Decimal] = None
        if earliest_start and total_curr_val > Decimal('0'):
            p_cagr = FinancialMathEngine.calculate_cagr(
                start_value=total_inv_capital,
                end_value=total_curr_val,
                start_date=earliest_start,
                end_date=resolved_end,
            )

        p_xirr, p_xirr_status = FinancialMathEngine.calculate_xirr(portfolio_cash_flows)

        # Merge daily time-series from all holdings
        history_map: Dict[str, Dict[str, Decimal]] = {}
        resolved_start = start_date or (earliest_start or (resolved_end - timedelta(days=365)))
        if resolved_start < (resolved_end - timedelta(days=365 * 5)):
            resolved_start = resolved_end - timedelta(days=365 * 5)

        curr_d = resolved_start
        while curr_d <= resolved_end:
            d_str = curr_d.isoformat()
            history_map[d_str] = {
                'market_value': Decimal('0.00'),
                'invested_capital': Decimal('0.00'),
                'realized_pnl': Decimal('0.00'),
                'unrealized_pnl': Decimal('0.00'),
                'total_pnl': Decimal('0.00'),
                'net_cash_flow_on_date': Decimal('0.00'),
            }
            curr_d += timedelta(days=1)

        for hr in holding_results:
            for pt in hr.history:
                if pt.date in history_map:
                    entry = history_map[pt.date]
                    val = pt.market_value if pt.market_value is not None else pt.cost_basis
                    entry['market_value'] += val
                    entry['invested_capital'] += pt.cost_basis
                    entry['realized_pnl'] += pt.realized_pnl
                    entry['unrealized_pnl'] += (pt.unrealized_pnl or Decimal('0.00'))
                    entry['total_pnl'] += (pt.total_pnl or pt.realized_pnl)

        for cf in portfolio_cash_flows:
            d_str = cf.flow_date.isoformat()
            if d_str in history_map and cf.flow_date != resolved_end:
                history_map[d_str]['net_cash_flow_on_date'] += cf.amount

        # Calculate daily TWR return linking across external flows
        # TWR = Product(1 + R_subperiod) - 1 where R_t = (V_t - Flow_t) / V_{t-1} - 1
        sorted_dates = sorted(history_map.keys())
        cum_twr = Decimal('1.0000')
        prev_val = Decimal('0.00')

        sorted_points: List[PortfolioTimeSeriesPoint] = []
        for d_str in sorted_dates:
            v = history_map[d_str]
            curr_val = v['market_value']
            flow = v['net_cash_flow_on_date']  # Positive inflow (investor withdrawal), negative (deposit)
            # External cash inflow into portfolio = -flow
            ext_deposit = -flow

            daily_twr = Decimal('0.0000')
            if prev_val > Decimal('0.00'):
                # Net return before today's external deposit
                sub_r = (curr_val - ext_deposit - prev_val) / prev_val
                cum_twr = cum_twr * (Decimal('1.0') + sub_r)
                daily_twr = ((cum_twr - Decimal('1.0')) * Decimal('100.0')).quantize(Decimal('0.01'))

            prev_val = curr_val

            sorted_points.append(
                PortfolioTimeSeriesPoint(
                    date=d_str,
                    market_value=quantize_currency(v['market_value']),
                    invested_capital=quantize_currency(v['invested_capital']),
                    realized_pnl=quantize_currency(v['realized_pnl']),
                    unrealized_pnl=quantize_currency(v['unrealized_pnl']),
                    total_pnl=quantize_currency(v['total_pnl']),
                    net_cash_flow_on_date=quantize_currency(v['net_cash_flow_on_date']),
                    twr_cumulative_pct=daily_twr,
                )
            )

        final_twr = sorted_points[-1].twr_cumulative_pct if sorted_points else None

        return PortfolioPerformanceResult(
            portfolio_id=str(portfolio.id),
            portfolio_name=portfolio.name,
            currency=portfolio.base_currency,
            current_value=quantize_currency(total_curr_val),
            total_invested_capital=quantize_currency(total_inv_capital),
            current_cost_basis=quantize_currency(total_cost_basis),
            realized_pnl=quantize_currency(total_realized),
            unrealized_pnl=quantize_currency(total_unrealized),
            total_pnl=quantize_currency(total_pnl),
            absolute_return_pct=p_abs_pct,
            cagr_pct=p_cagr,
            xirr_pct=p_xirr,
            xirr_status=p_xirr_status,
            twr_pct=final_twr,
            active_holdings_count=active_count,
            closed_holdings_count=closed_count,
            history=sorted_points,
            holdings_summary=holdings_summary,
            data_completeness={
                'total_holdings': len(investments),
                'active_holdings': active_count,
                'unvalued_holdings': unvalued_count,
                'is_complete': (unvalued_count == 0 and len(fx_warnings) == 0),
                'has_cash_flows': bool(portfolio_cash_flows),
                'fx_warnings': fx_warnings,
            },
        )
