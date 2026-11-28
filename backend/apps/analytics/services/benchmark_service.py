import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.analytics.services.portfolio_performance_service import PortfolioPerformanceService
from apps.market_data.models.instrument import AssetClass, Instrument
from apps.market_data.services.history_service import MARKET_TZ, MarketHistoryService
from apps.portfolios.models import Portfolio

logger = logging.getLogger(__name__)


@dataclass
class NormalizedPoint:
    date: str
    target_value: Decimal  # Normalized to 100 on start date (TWR cash-flow neutral)
    benchmark_value: Decimal  # Normalized to 100 on start date
    target_raw: Decimal
    benchmark_raw: Decimal


@dataclass
class BenchmarkComparisonResult:
    target_id: str
    target_type: str  # 'PORTFOLIO'
    benchmark_id: str
    benchmark_symbol: str
    benchmark_name: str
    start_date: str
    end_date: str
    target_total_return_pct: Decimal
    benchmark_total_return_pct: Decimal
    excess_return_pct: Decimal  # Correct financial terminology per ERD Section 14.6
    points: List[NormalizedPoint] = field(default_factory=list)


class BenchmarkService:
    """Provides market index discovery, series alignment, and cash-flow neutral
    normalized comparison (Base 100) using time-weighted return linking.
    """

    @classmethod
    def get_available_benchmarks(cls) -> List[Dict[str, str]]:
        benchmarks = Instrument.objects.filter(
            asset_class=AssetClass.INDEX,
            is_active=True,
        ).order_by('symbol')
        return [
            {
                'id': str(b.id),
                'symbol': b.symbol,
                'name': b.name,
                'exchange': b.exchange,
                'currency': b.currency,
            }
            for b in benchmarks
        ]

    @classmethod
    def compare_portfolio_to_benchmark(
        cls,
        portfolio: Portfolio,
        benchmark_instrument: Instrument,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> BenchmarkComparisonResult:
        if benchmark_instrument.asset_class != AssetClass.INDEX:
            raise ValidationError(f"Instrument {benchmark_instrument.symbol} is not a valid market index benchmark.")

        perf = PortfolioPerformanceService.get_portfolio_performance(
            portfolio=portfolio,
            start_date=start_date,
            end_date=end_date,
        )

        today = timezone.now().astimezone(MARKET_TZ).date()
        resolved_end = min(end_date or today, today)
        resolved_start = start_date or (date.fromisoformat(perf.history[0].date) if perf.history else (resolved_end - timedelta(days=365)))

        hist = MarketHistoryService.get_history(
            benchmark_instrument,
            period='ALL',
            start_date=resolved_start,
            end_date=resolved_end,
        )

        bench_map = {pt.date: pt.price for pt in (hist.points or [])}
        # Use TWR growth curve where 100 + twr_pct provides cash-flow neutralized return
        target_map = {
            pt.date: (Decimal('100.00') + (pt.twr_cumulative_pct or Decimal('0.00')))
            for pt in perf.history
        }

        # Find common dates
        common_dates = sorted(list(set(target_map.keys()) & set(bench_map.keys())))
        if not common_dates:
            raise ValidationError("No overlapping dates found between portfolio and benchmark history.")

        first_d = common_dates[0]
        t0 = target_map[first_d]
        b0 = bench_map[first_d]

        norm_points: List[NormalizedPoint] = []
        for d in common_dates:
            t_raw = target_map[d]
            b_raw = bench_map[d]
            t_norm = ((t_raw / t0) * Decimal('100')).quantize(Decimal('0.01')) if t0 > 0 else Decimal('100.00')
            b_norm = ((b_raw / b0) * Decimal('100')).quantize(Decimal('0.01')) if b0 > 0 else Decimal('100.00')
            norm_points.append(NormalizedPoint(
                date=d,
                target_value=t_norm,
                benchmark_value=b_norm,
                target_raw=t_raw,
                benchmark_raw=b_raw,
            ))

        last_pt = norm_points[-1]
        t_return = last_pt.target_value - Decimal('100.00')
        b_return = last_pt.benchmark_value - Decimal('100.00')
        excess_return = t_return - b_return

        return BenchmarkComparisonResult(
            target_id=str(portfolio.id),
            target_type='PORTFOLIO',
            benchmark_id=str(benchmark_instrument.id),
            benchmark_symbol=benchmark_instrument.symbol,
            benchmark_name=benchmark_instrument.name,
            start_date=first_d,
            end_date=common_dates[-1],
            target_total_return_pct=t_return,
            benchmark_total_return_pct=b_return,
            excess_return_pct=excess_return,
            points=norm_points,
        )
