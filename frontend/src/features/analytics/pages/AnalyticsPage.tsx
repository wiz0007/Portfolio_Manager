import React, { useState } from 'react';
import { usePortfolios } from '@/features/portfolios/hooks/usePortfolios';
import {
  useBenchmarks,
  useBenchmarkComparison,
  usePortfolioAllocation,
  usePortfolioPerformance,
} from '../api/analyticsApi';
import { HistoricalPerformanceChart } from '../components/HistoricalPerformanceChart';
import { BenchmarkComparisonChart } from '../components/BenchmarkComparisonChart';
import { AllocationBreakdownCard } from '../components/AllocationBreakdownCard';
import { Card } from '@/shared/ui/Card';
import { Loader2, BarChart3 } from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const { data: portfolios, isLoading: isPortfoliosLoading } = usePortfolios();
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string>('');
  const [selectedRange, setSelectedRange] = useState<string>('1Y');
  const [selectedBenchmarkId, setSelectedBenchmarkId] = useState<string>('');

  // Auto-select first portfolio
  const activePortfolioId = selectedPortfolioId || (portfolios && portfolios.length > 0 ? portfolios[0].id : '');

  // Compute start_date dynamically from selectedRange
  const { startDate, endDate } = React.useMemo(() => {
    const end = new Date();
    const start = new Date();
    switch (selectedRange) {
      case '1M':
        start.setMonth(start.getMonth() - 1);
        break;
      case '3M':
        start.setMonth(start.getMonth() - 3);
        break;
      case '6M':
        start.setMonth(start.getMonth() - 6);
        break;
      case '1Y':
        start.setFullYear(start.getFullYear() - 1);
        break;
      case '3Y':
        start.setFullYear(start.getFullYear() - 3);
        break;
      case '5Y':
        start.setFullYear(start.getFullYear() - 5);
        break;
      case 'ALL':
      default:
        return { startDate: undefined, endDate: undefined };
    }
    return {
      startDate: start.toISOString().split('T')[0],
      endDate: end.toISOString().split('T')[0],
    };
  }, [selectedRange]);

  const { data: performance, isLoading: isPerfLoading } = usePortfolioPerformance(activePortfolioId, startDate, endDate);
  const { data: allocation } = usePortfolioAllocation(activePortfolioId);
  const { data: benchmarks } = useBenchmarks();

  const activeBenchmarkId = selectedBenchmarkId || (benchmarks && benchmarks.length > 0 ? benchmarks[0].id : '');
  const { data: comparison } = useBenchmarkComparison(activePortfolioId, activeBenchmarkId, startDate, endDate);

  const ranges = ['1M', '3M', '6M', '1Y', '3Y', '5Y', 'ALL'];

  if (isPortfoliosLoading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-theme-text-muted">
        <Loader2 className="h-8 w-8 animate-spin text-theme-primary mb-2" />
        <p className="text-sm">Loading analytics intelligence...</p>
      </div>
    );
  }

  if (!portfolios || portfolios.length === 0) {
    return (
      <Card className="p-8 text-center border-theme-border bg-theme-surface">
        <div className="h-12 w-12 rounded-2xl bg-theme-primary-subtle border border-theme-primary/30 text-theme-primary flex items-center justify-center mx-auto mb-4">
          <BarChart3 className="h-6 w-6" />
        </div>
        <h2 className="text-lg font-bold text-theme-text">No Portfolios Found</h2>
        <p className="text-xs text-theme-text-muted mt-1">
          Create a portfolio and record investments to unlock performance analytics, allocation breakdowns, and benchmark comparisons.
        </p>
      </Card>
    );
  }

  const currency = performance?.currency || 'INR';

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Page Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-theme-text">Personal & Portfolio Analytics</h1>
          <p className="text-xs text-theme-text-muted mt-0.5">
            Reconstructed historical performance, money-weighted XIRR, and verified benchmark alignment.
          </p>
        </div>

        {/* Portfolio Selector and Range Filter */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={activePortfolioId}
            onChange={(e) => setSelectedPortfolioId(e.target.value)}
            className="text-xs rounded-xl border border-theme-border bg-theme-surface text-theme-text px-3 py-2 font-medium"
          >
            {portfolios.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.base_currency})
              </option>
            ))}
          </select>

          <div className="flex rounded-xl border border-theme-border bg-theme-surface p-0.5">
            {ranges.map((r) => (
              <button
                key={r}
                onClick={() => setSelectedRange(r)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition-colors ${
                  selectedRange === r
                    ? 'bg-theme-primary text-theme-primary-foreground'
                    : 'text-theme-text-muted hover:text-theme-text'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Primary KPI Metrics Summary */}
      {performance && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl border border-theme-border bg-theme-surface">
            <span className="text-xs font-semibold text-theme-text-muted uppercase tracking-wider">Current Market Value</span>
            <div className="text-xl font-bold text-theme-text mt-1">
              {currency} {parseFloat(performance.current_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-theme-text-muted">
              Invested: {currency} {parseFloat(performance.current_cost_basis).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>

          <div className="p-4 rounded-xl border border-theme-border bg-theme-surface">
            <span className="text-xs font-semibold text-theme-text-muted uppercase tracking-wider">Total Profit / Loss</span>
            <div
              className={`text-xl font-bold mt-1 ${
                parseFloat(performance.total_pnl) >= 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {currency} {parseFloat(performance.total_pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-theme-text-muted">
              Realized: {currency} {parseFloat(performance.realized_pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>

          <div className="p-4 rounded-xl border border-theme-border bg-theme-surface">
            <span className="text-xs font-semibold text-theme-text-muted uppercase tracking-wider">Absolute Return</span>
            <div className="text-xl font-bold text-theme-text mt-1">
              {performance.absolute_return_pct ? `${parseFloat(performance.absolute_return_pct).toFixed(2)}%` : '—'}
            </div>
            <span className="text-[11px] text-theme-text-muted">
              Cumulative Growth
            </span>
          </div>

          <div className="p-4 rounded-xl border border-theme-border bg-theme-surface">
            <span className="text-xs font-semibold text-theme-text-muted uppercase tracking-wider">Money-Weighted (XIRR)</span>
            <div className="text-xl font-bold text-theme-primary mt-1">
              {performance.xirr_pct ? `${parseFloat(performance.xirr_pct).toFixed(2)}%` : '—'}
            </div>
            <span className="text-[11px] text-theme-text-muted">
              Status: {performance.xirr_status}
            </span>
          </div>
        </div>
      )}

      {/* Historical Growth Chart */}
      {isPerfLoading ? (
        <div className="py-16 flex justify-center text-theme-text-muted">
          <Loader2 className="h-6 w-6 animate-spin text-theme-primary" />
        </div>
      ) : performance ? (
        <HistoricalPerformanceChart points={performance.history} currency={currency} />
      ) : null}

      {/* Grid: Allocation and Benchmark Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {allocation && (
          <AllocationBreakdownCard
            categories={allocation.by_asset_category}
            currency={currency}
            totalMarketValue={allocation.total_market_value}
          />
        )}

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-theme-text">Benchmark Relative Performance</h3>
            {benchmarks && benchmarks.length > 0 && (
              <select
                value={activeBenchmarkId}
                onChange={(e) => setSelectedBenchmarkId(e.target.value)}
                className="text-xs rounded-xl border border-theme-border bg-theme-surface text-theme-text px-2.5 py-1.5"
              >
                {benchmarks.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} ({b.symbol})
                  </option>
                ))}
              </select>
            )}
          </div>

          {comparison ? (
            <BenchmarkComparisonChart
              points={comparison.points}
              benchmarkSymbol={comparison.benchmark_symbol}
              targetName={performance?.portfolio_name || 'Portfolio'}
              excessReturnPct={comparison.excess_return_pct}
            />
          ) : (
            <div className="p-8 text-center text-xs text-theme-text-muted border border-theme-border rounded-xl bg-theme-surface">
              Select an index benchmark above to inspect normalized Alpha and relative returns.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
