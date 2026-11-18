import React from 'react';
import { ShieldCheck, AlertTriangle, AlertCircle, Clock, CheckCircle2, HelpCircle } from 'lucide-react';
import { useDashboardDataQuality } from '../hooks/useDashboard';

interface ValuationDataQualityProps {
  portfolioId?: string;
  className?: string;
}

export const ValuationDataQuality: React.FC<ValuationDataQualityProps> = ({
  portfolioId,
  className = '',
}) => {
  const { data: qualityData, isLoading, isError } = useDashboardDataQuality(portfolioId);

  if (isLoading) {
    return (
      <div className={`rounded-2xl border border-theme-border bg-theme-surface p-5 animate-pulse ${className}`}>
        <span className="text-xs text-theme-text-muted">Analyzing data reliability...</span>
      </div>
    );
  }

  if (isError || !qualityData) {
    return null;
  }

  const { overall_status, total_active_holdings, categories } = qualityData;

  const getStatusBadge = () => {
    switch (overall_status) {
      case 'HEALTHY':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Reliable Valuations</span>
          </span>
        );
      case 'WARNING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Clock className="h-3.5 w-3.5" />
            <span>Stale Valuations Detected</span>
          </span>
        );
      case 'INCOMPLETE':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>Incomplete Pricing Data</span>
          </span>
        );
    }
  };

  const valuedCount = categories.valued?.count ?? 0;
  const staleCount = categories.stale?.count ?? 0;
  const missingCount = categories.missing_price?.count ?? 0;
  const awaitingCount = categories.awaiting_verification?.count ?? 0;
  const unsupportedCount = categories.unsupported?.count ?? 0;

  return (
    <div className={`rounded-2xl border border-theme-border bg-theme-surface p-5 shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-theme-border/60">
        <div>
          <h2 className="text-sm font-bold tracking-tight text-theme-text flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-theme-primary" />
            <span>Data Reliability & Freshness Diagnostics</span>
          </h2>
          <p className="text-xs text-theme-text-muted mt-0.5">
            Transparency status on {total_active_holdings} active {total_active_holdings === 1 ? 'holding' : 'holdings'}
          </p>
        </div>

        <div>{getStatusBadge()}</div>
      </div>

      {/* Grid of Diagnostic Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mt-4">
        {/* Valued */}
        <div className="p-3 rounded-xl bg-theme-bg border border-theme-border/60">
          <div className="flex items-center justify-between text-[11px] text-theme-text-muted mb-1">
            <span className="font-medium">Up-to-Date</span>
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-emerald-400">{valuedCount}</div>
          <p className="text-[10px] text-theme-text-muted mt-1 leading-tight">
            Latest trading session or active schedule
          </p>
        </div>

        {/* Stale */}
        <div className={`p-3 rounded-xl bg-theme-bg border ${staleCount > 0 ? 'border-amber-500/40 bg-amber-500/5' : 'border-theme-border/60'}`}>
          <div className="flex items-center justify-between text-[11px] text-theme-text-muted mb-1">
            <span className="font-medium">Stale Price</span>
            <Clock className={`h-3.5 w-3.5 ${staleCount > 0 ? 'text-amber-400' : 'text-theme-text-muted'}`} />
          </div>
          <div className={`text-lg font-bold ${staleCount > 0 ? 'text-amber-400' : 'text-theme-text'}`}>
            {staleCount}
          </div>
          <p className="text-[10px] text-theme-text-muted mt-1 leading-tight">
            Older than instrument coverage window
          </p>
        </div>

        {/* Missing Price */}
        <div className={`p-3 rounded-xl bg-theme-bg border ${missingCount > 0 ? 'border-rose-500/40 bg-rose-500/5' : 'border-theme-border/60'}`}>
          <div className="flex items-center justify-between text-[11px] text-theme-text-muted mb-1">
            <span className="font-medium">Missing Price</span>
            <AlertCircle className={`h-3.5 w-3.5 ${missingCount > 0 ? 'text-rose-400' : 'text-theme-text-muted'}`} />
          </div>
          <div className={`text-lg font-bold ${missingCount > 0 ? 'text-rose-400' : 'text-theme-text'}`}>
            {missingCount}
          </div>
          <p className="text-[10px] text-theme-text-muted mt-1 leading-tight">
            No published observation available
          </p>
        </div>

        {/* Awaiting Verification */}
        <div className={`p-3 rounded-xl bg-theme-bg border ${awaitingCount > 0 ? 'border-indigo-500/40 bg-indigo-500/5' : 'border-theme-border/60'}`}>
          <div className="flex items-center justify-between text-[11px] text-theme-text-muted mb-1">
            <span className="font-medium">Awaiting Review</span>
            <HelpCircle className={`h-3.5 w-3.5 ${awaitingCount > 0 ? 'text-indigo-400' : 'text-theme-text-muted'}`} />
          </div>
          <div className={`text-lg font-bold ${awaitingCount > 0 ? 'text-indigo-400' : 'text-theme-text'}`}>
            {awaitingCount}
          </div>
          <p className="text-[10px] text-theme-text-muted mt-1 leading-tight">
            Pending operator verification
          </p>
        </div>

        {/* Unsupported */}
        <div className="p-3 rounded-xl bg-theme-bg border border-theme-border/60">
          <div className="flex items-center justify-between text-[11px] text-theme-text-muted mb-1">
            <span className="font-medium">Manual/Appraisal</span>
            <ShieldCheck className="h-3.5 w-3.5 text-theme-text-muted" />
          </div>
          <div className="text-lg font-bold text-theme-text">{unsupportedCount}</div>
          <p className="text-[10px] text-theme-text-muted mt-1 leading-tight">
            Requires manual cost basis update
          </p>
        </div>
      </div>

      {/* Explanatory Note */}
      <div className="mt-3 pt-3 border-t border-theme-border/40 text-[11px] text-theme-text-muted">
        <span>
          💡 <strong>Integrity Guarantee:</strong> Incomplete or missing valuations are never silently replaced with historical purchase prices or zeroed out without explicit indication.
        </span>
      </div>
    </div>
  );
};
