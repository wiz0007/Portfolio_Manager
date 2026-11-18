import React, { useState } from 'react';
import { PieChart, Layers, Briefcase, Info, AlertTriangle } from 'lucide-react';
import { useDashboardAllocation } from '../hooks/useDashboard';

interface AssetAllocationChartProps {
  portfolioId?: string;
  currency?: string;
  className?: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  equity: '#6366f1', // Indigo
  mutual_funds: '#3b82f6', // Blue
  fixed_income: '#10b981', // Emerald
  cash: '#14b8a6', // Teal
  gold: '#f59e0b', // Amber
  real_estate: '#8b5cf6', // Violet
  crypto: '#ec4899', // Pink
};

const DEFAULT_COLOR = '#94a3b8'; // Slate

export const AssetAllocationChart: React.FC<AssetAllocationChartProps> = ({
  portfolioId,
  currency,
  className = '',
}) => {
  const [viewMode, setViewMode] = useState<'asset_class' | 'portfolio'>('asset_class');
  const { data: allocation, isLoading, isError } = useDashboardAllocation(portfolioId, currency);

  if (isLoading) {
    return (
      <div className={`rounded-2xl border border-theme-border bg-theme-surface p-5 h-80 flex items-center justify-center animate-pulse ${className}`}>
        <span className="text-xs text-theme-text-muted">Loading asset allocation...</span>
      </div>
    );
  }

  if (isError || !allocation) {
    return (
      <div className={`rounded-2xl border border-theme-border bg-theme-surface p-5 h-80 flex flex-col items-center justify-center text-center ${className}`}>
        <AlertTriangle className="h-6 w-6 text-amber-400 mb-2" />
        <span className="text-sm font-semibold text-theme-text">Allocation Data Unavailable</span>
        <span className="text-xs text-theme-text-muted mt-1 max-w-xs">
          Unable to calculate current asset allocation. Please verify investment valuations.
        </span>
      </div>
    );
  }

  const items =
    viewMode === 'asset_class'
      ? allocation.asset_class_allocation
      : allocation.portfolio_allocation;

  const denominator = parseFloat(allocation.denominator_value || '0');

  return (
    <div className={`rounded-2xl border border-theme-border bg-theme-surface p-5 shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-theme-border/60">
        <div>
          <h2 className="text-sm font-bold tracking-tight text-theme-text flex items-center gap-1.5">
            <PieChart className="h-4 w-4 text-theme-primary" />
            <span>Asset Allocation</span>
          </h2>
          <p className="text-xs text-theme-text-muted mt-0.5">
            Distribution by eligible valuation ({allocation.currency})
          </p>
        </div>

        {/* View mode toggle */}
        <div className="flex items-center gap-1 bg-theme-bg p-1 rounded-xl border border-theme-border self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setViewMode('asset_class')}
            className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
              viewMode === 'asset_class'
                ? 'bg-theme-primary text-theme-text-inverse shadow-sm'
                : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-hover'
            }`}
          >
            <Layers className="h-3 w-3" />
            <span>Asset Class</span>
          </button>
          <button
            type="button"
            onClick={() => setViewMode('portfolio')}
            className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
              viewMode === 'portfolio'
                ? 'bg-theme-primary text-theme-text-inverse shadow-sm'
                : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-hover'
            }`}
          >
            <Briefcase className="h-3 w-3" />
            <span>Portfolio</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      {items.length === 0 || denominator <= 0 ? (
        <div className="py-12 flex flex-col items-center justify-center text-center">
          <PieChart className="h-8 w-8 text-theme-text-muted/50 mb-2" />
          <span className="text-xs font-medium text-theme-text-muted">
            No valued holdings to display in this scope.
          </span>
          {allocation.unvalued_count > 0 && (
            <span className="text-[11px] text-amber-400 mt-1">
              ({allocation.unvalued_count} holdings currently unvalued)
            </span>
          )}
        </div>
      ) : (
        <div className="mt-4 space-y-4">
          {/* Visual Distribution Bar */}
          <div className="h-3.5 w-full rounded-full bg-theme-bg overflow-hidden flex shadow-inner">
            {items.map((item, idx) => {
              const pct = parseFloat(item.percentage);
              const color =
                viewMode === 'asset_class'
                  ? CATEGORY_COLORS[(item as any).category] || DEFAULT_COLOR
                  : [
                      '#6366f1',
                      '#10b981',
                      '#f59e0b',
                      '#ec4899',
                      '#3b82f6',
                      '#8b5cf6',
                    ][idx % 6];

              if (pct <= 0) return null;

              return (
                <div
                  key={idx}
                  style={{ width: `${pct}%`, backgroundColor: color }}
                  className="h-full transition-all duration-300 first:rounded-l-full last:rounded-r-full"
                  title={`${(item as any).display_name || (item as any).portfolio_name}: ${pct}%`}
                />
              );
            })}
          </div>

          {/* Allocation Breakdown Rows */}
          <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
            {items.map((item, idx) => {
              const name = (item as any).display_name || (item as any).portfolio_name;
              const val = parseFloat(item.total_value).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              });
              const pct = item.percentage;
              const color =
                viewMode === 'asset_class'
                  ? CATEGORY_COLORS[(item as any).category] || DEFAULT_COLOR
                  : [
                      '#6366f1',
                      '#10b981',
                      '#f59e0b',
                      '#ec4899',
                      '#3b82f6',
                      '#8b5cf6',
                    ][idx % 6];

              return (
                <div
                  key={idx}
                  className="flex items-center justify-between text-xs py-1.5 px-2 rounded-lg hover:bg-theme-hover/60 transition-colors"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className="h-2.5 w-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: color }}
                    />
                    <span className="font-medium text-theme-text truncate">{name}</span>
                    <span className="text-[10px] text-theme-text-muted">
                      ({item.count} {item.count === 1 ? 'asset' : 'assets'})
                    </span>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span className="font-semibold text-theme-text">
                      {allocation.currency} {val}
                    </span>
                    <span className="font-bold text-theme-primary min-w-[45px] text-right">
                      {pct}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Denominator & Completeness Footnote */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-theme-text-muted pt-3 border-t border-theme-border/40 gap-1.5">
            <span className="flex items-center gap-1">
              <Info className="h-3 w-3 shrink-0" />
              <span>Valuation Denominator: {allocation.currency} {denominator.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            </span>
            {allocation.has_unvalued_assets && (
              <span className="text-amber-400 font-medium">
                * Excludes {allocation.unvalued_count} unvalued {allocation.unvalued_count === 1 ? 'holding' : 'holdings'}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
