import logging
from datetime import date
from typing import Any, Dict, List, Optional

from apps.analytics.services.allocation_service import AllocationAnalyticsService
from apps.analytics.services.investment_performance_service import (
    InvestmentPerformanceResult,
    InvestmentPerformanceService,
)
from apps.analytics.services.portfolio_performance_service import (
    PortfolioPerformanceResult,
    PortfolioPerformanceService,
)
from apps.assets.models.investment import Investment
from apps.portfolios.models import Portfolio

logger = logging.getLogger(__name__)

MAX_HOLDINGS_IN_CONTEXT = 20


class AIContextBuilder:
    """
    Constructs a minimized, typed, Decimal-safe, and PII-free snapshot of verified
    portfolio metrics, allocation, and holding details by consuming canonical domain services.
    Never calculates financial metrics independently and never routes through binary floats.
    """

    @classmethod
    def build_portfolio_context(
        cls,
        user: Any,
        portfolio: Portfolio,
        investment: Optional[Investment] = None,
        as_of_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Extracts bounded context snapshot from canonical analytics and allocation services.
        """
        # 1. Fetch canonical portfolio performance
        perf: PortfolioPerformanceResult = PortfolioPerformanceService.get_portfolio_performance(
            portfolio=portfolio,
            end_date=as_of_date,
        )

        # 2. Fetch canonical allocation
        alloc = AllocationAnalyticsService.get_allocation(user=user, portfolio=portfolio)

        # 3. Assemble bounded holdings summary
        bounded_holdings: List[Dict[str, Any]] = []
        for h in perf.holdings_summary[:MAX_HOLDINGS_IN_CONTEXT]:
            # Look up holding display name safely
            inv_obj = Investment.objects.filter(id=h['investment_id']).only('display_name', 'category', 'asset_type').first()
            bounded_holdings.append({
                'investment_id': str(h['investment_id']),
                'name': inv_obj.display_name if inv_obj else 'Holding',
                'category': inv_obj.category if inv_obj else 'Unknown',
                'asset_type': inv_obj.asset_type if inv_obj else 'Unknown',
                'current_quantity': str(h['current_quantity']),
                'cost_basis': str(h['cost_basis']),
                'market_value': str(h['market_value']),
                'realized_pnl': str(h['realized_pnl']),
                'unrealized_pnl': str(h['unrealized_pnl']),
                'total_pnl': str(h['total_pnl']),
                'xirr_pct': str(h['xirr_pct']) if h.get('xirr_pct') is not None else None,
                'is_active': bool(h['is_active']),
                'is_valued': bool(h['is_valued']),
            })

        # 4. Assemble category allocation breakdown
        alloc_breakdown: List[Dict[str, Any]] = []
        for cat in alloc.by_asset_category:
            alloc_breakdown.append({
                'category': cat.name,
                'market_value': str(cat.market_value),
                'percentage': str(cat.percentage),
                'count': cat.holding_count,
            })

        # 5. Extract investment-specific metrics if holding requested
        specific_holding_data: Optional[Dict[str, Any]] = None
        if investment:
            inv_perf: InvestmentPerformanceResult = InvestmentPerformanceService.get_investment_performance(
                investment=investment,
                end_date=as_of_date,
            )
            specific_holding_data = {
                'id': str(investment.id),
                'display_name': investment.display_name,
                'category': investment.category,
                'asset_type': investment.asset_type,
                'currency': inv_perf.currency,
                'current_quantity': str(inv_perf.current_quantity),
                'initial_invested_capital': str(inv_perf.initial_invested_capital),
                'cost_basis': str(inv_perf.current_cost_basis),
                'market_price': str(inv_perf.current_market_price) if inv_perf.current_market_price is not None else None,
                'market_value': str(inv_perf.current_market_value) if inv_perf.current_market_value is not None else None,
                'realized_pnl': str(inv_perf.realized_pnl),
                'unrealized_pnl': str(inv_perf.unrealized_pnl) if inv_perf.unrealized_pnl is not None else None,
                'total_pnl': str(inv_perf.total_pnl) if inv_perf.total_pnl is not None else None,
                'absolute_return_pct': str(inv_perf.absolute_return_pct) if inv_perf.absolute_return_pct is not None else None,
                'xirr_pct': str(inv_perf.xirr_pct) if inv_perf.xirr_pct is not None else None,
                'xirr_status': inv_perf.xirr_status,
                'first_transaction_date': inv_perf.first_transaction_date,
                'latest_transaction_date': inv_perf.latest_transaction_date,
                'data_completeness': inv_perf.data_completeness,
            }

        # 6. Data completeness and staleness indicators
        comp = perf.data_completeness
        completeness_warnings: List[str] = list(comp.get('fx_warnings', []))
        if comp.get('unvalued_holdings', 0) > 0:
            completeness_warnings.append(
                f"{comp['unvalued_holdings']} holding(s) currently lack market pricing and are excluded from valuation totals."
            )

        context_snapshot = {
            'context_version': '1.0',
            'as_of_date': as_of_date.isoformat() if as_of_date else date.today().isoformat(),
            'portfolio': {
                'id': str(portfolio.id),
                'name': portfolio.name,
                'base_currency': portfolio.base_currency,
            },
            'summary_metrics': {
                'current_market_value': str(perf.current_value),
                'total_invested_capital': str(perf.total_invested_capital),
                'current_cost_basis': str(perf.current_cost_basis),
                'realized_pnl': str(perf.realized_pnl),
                'unrealized_pnl': str(perf.unrealized_pnl),
                'total_pnl': str(perf.total_pnl),
                'absolute_return_pct': str(perf.absolute_return_pct) if perf.absolute_return_pct is not None else None,
                'cagr_pct': str(perf.cagr_pct) if perf.cagr_pct is not None else None,
                'xirr_pct': str(perf.xirr_pct) if perf.xirr_pct is not None else None,
                'twr_pct': str(perf.twr_pct) if perf.twr_pct is not None else None,
                'active_holdings_count': perf.active_holdings_count,
                'closed_holdings_count': perf.closed_holdings_count,
            },
            'data_completeness': {
                'is_complete': bool(comp.get('is_complete', True)),
                'total_holdings': comp.get('total_holdings', 0),
                'unvalued_holdings': comp.get('unvalued_holdings', 0),
                'warnings': completeness_warnings,
            },
            'allocation_breakdown': alloc_breakdown,
            'top_holdings': bounded_holdings,
            'selected_holding': specific_holding_data,
        }

        return context_snapshot
