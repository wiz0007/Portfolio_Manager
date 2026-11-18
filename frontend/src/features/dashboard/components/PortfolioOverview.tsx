import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Briefcase,
  Layers,
  Activity,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import { DashboardOverview } from '../types/dashboard';

interface PortfolioOverviewProps {
  overview?: DashboardOverview;
  isLoading?: boolean;
}

export const PortfolioOverview: React.FC<PortfolioOverviewProps> = ({
  overview,
  isLoading = false,
}) => {
  if (isLoading || !overview) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 rounded-2xl bg-theme-surface/50 border border-theme-border/60 p-5" />
        ))}
      </div>
    );
  }

  const summary = overview.summary;
  const currency = summary?.currency || 'INR';

  // Format currency numbers
  const formatCurrency = (val?: string | number) => {
    if (val === undefined || val === null) return '0.00';
    const num = typeof val === 'string' ? parseFloat(val) : val;
    return isNaN(num) ? '0.00' : num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const totalCurrent = summary?.total_current_value || '0.00';
  const totalInvested = summary?.total_invested_capital || '0.00';
  const absGainLoss = summary?.absolute_gain_loss || '0.00';
  const glPct = summary?.gain_loss_percentage;

  const isPositive = parseFloat(absGainLoss) > 0;
  const isNegative = parseFloat(absGainLoss) < 0;

  // Trend color classes
  const trendColor = isPositive
    ? 'text-emerald-400'
    : isNegative
    ? 'text-rose-400'
    : 'text-theme-text-muted';

  const trendBg = isPositive
    ? 'bg-emerald-500/10 border-emerald-500/20'
    : isNegative
    ? 'bg-rose-500/10 border-rose-500/20'
    : 'bg-theme-bg border-theme-border';

  const hasMultipleCurrencies =
    overview.totals_by_currency && Object.keys(overview.totals_by_currency).length > 1;

  return (
    <div className="space-y-4">
      {hasMultipleCurrencies && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300">
          <AlertCircle className="h-4 w-4 shrink-0 text-amber-400" />
          <span>
            <strong>Multi-Currency Portfolio:</strong> You have assets held across multiple currencies ({Object.keys(overview.totals_by_currency!).join(', ')}). Totals below show the primary currency ({currency}). Consolidated cross-currency totals require explicit FX conversion.
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Total Portfolio Value */}
        <div className="rounded-2xl border border-theme-border bg-theme-surface p-5 shadow-sm hover:border-theme-border/80 transition-all">
          <div className="flex items-center justify-between text-xs font-semibold text-theme-text-muted mb-2">
            <span className="uppercase tracking-wider">Total Current Value</span>
            <div className="p-2 rounded-xl bg-theme-primary/10 text-theme-primary">
              <DollarSign className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xs font-bold text-theme-text-muted">{currency}</span>
            <span className="text-2xl font-bold tracking-tight text-theme-text">
              {formatCurrency(totalCurrent)}
            </span>
          </div>
          <div className="mt-2 text-[11px] text-theme-text-muted flex items-center justify-between">
            <span>Authoritative valuation</span>
            <span className="font-medium text-theme-text">
              {overview.active_investment_count ?? 0} active holdings
            </span>
          </div>
        </div>

        {/* Metric 2: Invested Capital */}
        <div className="rounded-2xl border border-theme-border bg-theme-surface p-5 shadow-sm hover:border-theme-border/80 transition-all">
          <div className="flex items-center justify-between text-xs font-semibold text-theme-text-muted mb-2">
            <span className="uppercase tracking-wider">Invested Capital</span>
            <div className="p-2 rounded-xl bg-theme-bg text-theme-text-muted">
              <Briefcase className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xs font-bold text-theme-text-muted">{currency}</span>
            <span className="text-2xl font-bold tracking-tight text-theme-text">
              {formatCurrency(totalInvested)}
            </span>
          </div>
          <div className="mt-2 text-[11px] text-theme-text-muted flex items-center justify-between">
            <span>Total cost basis</span>
            <span className="font-medium text-theme-text">
              {overview.portfolio_count} {overview.portfolio_count === 1 ? 'portfolio' : 'portfolios'}
            </span>
          </div>
        </div>

        {/* Metric 3: Total Gain/Loss */}
        <div className="rounded-2xl border border-theme-border bg-theme-surface p-5 shadow-sm hover:border-theme-border/80 transition-all">
          <div className="flex items-center justify-between text-xs font-semibold text-theme-text-muted mb-2">
            <span className="uppercase tracking-wider">Unrealized Gain / Loss</span>
            <div className={`p-2 rounded-xl ${trendBg} ${trendColor}`}>
              {isPositive ? (
                <TrendingUp className="h-4 w-4" />
              ) : isNegative ? (
                <TrendingDown className="h-4 w-4" />
              ) : (
                <Activity className="h-4 w-4" />
              )}
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xs font-bold text-theme-text-muted">{currency}</span>
            <span className={`text-2xl font-bold tracking-tight ${trendColor}`}>
              {isPositive ? `+${formatCurrency(absGainLoss)}` : formatCurrency(absGainLoss)}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs font-semibold">
            {glPct !== null && glPct !== undefined ? (
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[11px] ${trendBg} ${trendColor}`}>
                {isPositive ? `+${parseFloat(glPct).toFixed(2)}%` : `${parseFloat(glPct).toFixed(2)}%`}
              </span>
            ) : (
              <span className="text-theme-text-muted text-[11px] flex items-center gap-1">
                <HelpCircle className="h-3 w-3" /> N/A (Zero invested capital)
              </span>
            )}
            <span className="text-[11px] text-theme-text-muted">return</span>
          </div>
        </div>

        {/* Metric 4: Valuation Completeness */}
        <div className="rounded-2xl border border-theme-border bg-theme-surface p-5 shadow-sm hover:border-theme-border/80 transition-all">
          <div className="flex items-center justify-between text-xs font-semibold text-theme-text-muted mb-2">
            <span className="uppercase tracking-wider">Data Reliability</span>
            <div className="p-2 rounded-xl bg-theme-bg text-theme-text-muted">
              <Layers className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold tracking-tight text-theme-text">
              {overview.data_completeness?.completeness_percentage !== undefined
                ? `${overview.data_completeness.completeness_percentage}%`
                : '100%'}
            </span>
            <span className="text-xs text-theme-text-muted">coverage</span>
          </div>
          <div className="mt-2 text-[11px] text-theme-text-muted flex items-center justify-between">
            <span>
              {overview.data_completeness?.valued_holdings ?? 0} of {overview.data_completeness?.total_active_holdings ?? 0} valued
            </span>
            {(overview.data_completeness?.unvalued_holdings ?? 0) > 0 && (
              <span className="text-amber-400 font-semibold">
                {overview.data_completeness?.unvalued_holdings} unvalued
              </span>
            )}
          </div>
        </div>
      </div>

      {hasMultipleCurrencies && overview.totals_by_currency && (
        <div className="space-y-2 mt-4 pt-2 border-t border-theme-border/60">
          <div className="text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
            Currency Breakdown
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(overview.totals_by_currency).map(([currKey, currSummary]) => {
              const cGainLoss = currSummary.absolute_gain_loss || '0.00';
              const cIsPos = parseFloat(cGainLoss) > 0;
              const cIsNeg = parseFloat(cGainLoss) < 0;
              const cColor = cIsPos ? 'text-emerald-400' : cIsNeg ? 'text-rose-400' : 'text-theme-text-muted';
              return (
                <div key={currKey} className="p-3.5 rounded-xl border border-theme-border bg-theme-surface/70 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-theme-text">{currKey}</span>
                    <span className="text-xs text-theme-text-muted">
                      {currSummary.total_investment_count} {currSummary.total_investment_count === 1 ? 'asset' : 'assets'}
                    </span>
                  </div>
                  <div className="flex items-baseline justify-between text-xs">
                    <span className="text-theme-text-muted">Value:</span>
                    <span className="font-semibold text-theme-text">
                      {currKey} {formatCurrency(currSummary.total_current_value)}
                    </span>
                  </div>
                  <div className="flex items-baseline justify-between text-xs">
                    <span className="text-theme-text-muted">Invested:</span>
                    <span className="text-theme-text-muted">
                      {currKey} {formatCurrency(currSummary.total_invested_capital)}
                    </span>
                  </div>
                  <div className="flex items-baseline justify-between text-xs pt-1 border-t border-theme-border/40">
                    <span className="text-theme-text-muted">Gain/Loss:</span>
                    <span className={`font-semibold ${cColor}`}>
                      {cIsPos ? `+${formatCurrency(cGainLoss)}` : formatCurrency(cGainLoss)}
                      {currSummary.gain_loss_percentage && (
                        <span className="ml-1 text-[11px]">
                          ({cIsPos ? '+' : ''}{parseFloat(currSummary.gain_loss_percentage).toFixed(2)}%)
                        </span>
                      )}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
