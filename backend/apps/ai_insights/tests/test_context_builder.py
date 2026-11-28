import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from apps.ai_insights.services.context_builder import MAX_HOLDINGS_IN_CONTEXT, AIContextBuilder


@pytest.mark.django_db
class TestAIContextBuilder:

    def test_build_portfolio_context_basic(self, auth_user, sample_portfolio, sample_investment):
        context = AIContextBuilder.build_portfolio_context(
            user=auth_user,
            portfolio=sample_portfolio,
        )

        assert context['portfolio']['name'] == sample_portfolio.name
        assert context['portfolio']['base_currency'] == sample_portfolio.base_currency
        assert 'summary_metrics' in context
        assert 'allocation_breakdown' in context
        assert 'top_holdings' in context
        assert 'data_completeness' in context

        # Zero PII guarantee
        context_str = json.dumps(context)
        assert auth_user.email not in context_str
        assert getattr(auth_user, 'password', '') not in context_str

    def test_build_portfolio_context_with_specific_holding(self, auth_user, sample_portfolio, sample_investment):
        context = AIContextBuilder.build_portfolio_context(
            user=auth_user,
            portfolio=sample_portfolio,
            investment=sample_investment,
        )

        assert context['selected_holding'] is not None
        assert context['selected_holding']['id'] == str(sample_investment.id)
        assert context['selected_holding']['display_name'] == sample_investment.display_name
        assert 'cost_basis' in context['selected_holding']
        assert 'market_value' in context['selected_holding']

    def test_top_holdings_cap_at_twenty(self, auth_user, sample_portfolio):
        # Mock portfolio performance with 25 holdings
        mock_holdings = [
            {
                'investment_id': f"00000000-0000-0000-0000-{i:012d}",
                'current_quantity': Decimal('10'),
                'cost_basis': Decimal('1000'),
                'market_value': Decimal('1200'),
                'realized_pnl': Decimal('0'),
                'unrealized_pnl': Decimal('200'),
                'total_pnl': Decimal('200'),
                'xirr_pct': Decimal('12.5'),
                'is_active': True,
                'is_valued': True,
            }
            for i in range(25)
        ]

        with patch('apps.ai_insights.services.context_builder.PortfolioPerformanceService.get_portfolio_performance') as mock_perf:
            mock_res = MagicMock()
            mock_res.holdings_summary = mock_holdings
            mock_res.current_value = Decimal('30000')
            mock_res.total_invested_capital = Decimal('25000')
            mock_res.current_cost_basis = Decimal('25000')
            mock_res.realized_pnl = Decimal('0')
            mock_res.unrealized_pnl = Decimal('5000')
            mock_res.total_pnl = Decimal('5000')
            mock_res.absolute_return_pct = Decimal('20.0')
            mock_res.cagr_pct = None
            mock_res.xirr_pct = Decimal('15.0')
            mock_res.twr_pct = None
            mock_res.active_holdings_count = 25
            mock_res.closed_holdings_count = 0
            mock_res.data_completeness = {'is_complete': True, 'total_holdings': 25, 'unvalued_holdings': 0, 'fx_warnings': []}
            mock_perf.return_value = mock_res

            context = AIContextBuilder.build_portfolio_context(
                user=auth_user,
                portfolio=sample_portfolio,
            )

            assert len(context['top_holdings']) == MAX_HOLDINGS_IN_CONTEXT
