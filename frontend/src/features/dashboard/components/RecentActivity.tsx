import React from 'react';
import { History, ArrowDownLeft, ArrowUpRight, DollarSign, Clock, AlertCircle } from 'lucide-react';
import { useDashboardRecentActivity } from '../hooks/useDashboard';

interface RecentActivityProps {
  portfolioId?: string;
  className?: string;
}

export const RecentActivity: React.FC<RecentActivityProps> = ({
  portfolioId,
  className = '',
}) => {
  const { data: transactions, isLoading, isError } = useDashboardRecentActivity(portfolioId, 10);

  if (isLoading) {
    return (
      <div className={`rounded-2xl border border-theme-border bg-theme-surface p-5 h-80 flex items-center justify-center animate-pulse ${className}`}>
        <span className="text-xs text-theme-text-muted">Loading recent activity...</span>
      </div>
    );
  }

  if (isError || !transactions) {
    return (
      <div className={`rounded-2xl border border-theme-border bg-theme-surface p-5 h-80 flex flex-col items-center justify-center text-center ${className}`}>
        <AlertCircle className="h-6 w-6 text-amber-400 mb-2" />
        <span className="text-sm font-semibold text-theme-text">Recent Activity Unavailable</span>
        <span className="text-xs text-theme-text-muted mt-1">Unable to load transactions.</span>
      </div>
    );
  }

  const formatAmount = (val?: string | number) => {
    if (val === undefined || val === null) return '0.00';
    const num = typeof val === 'string' ? parseFloat(val) : val;
    return isNaN(num) ? '0.00' : num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const getTxTypeBadge = (type: string) => {
    const isBuy = type.toUpperCase().includes('BUY') || type.toUpperCase().includes('PURCHASE');
    const isSell = type.toUpperCase().includes('SELL');
    const isIncome = type.toUpperCase().includes('DIVIDEND') || type.toUpperCase().includes('INTEREST');

    if (isBuy) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <ArrowDownLeft className="h-3 w-3" />
          <span>{type.replace('_', ' ')}</span>
        </span>
      );
    }
    if (isSell) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <ArrowUpRight className="h-3 w-3" />
          <span>{type.replace('_', ' ')}</span>
        </span>
      );
    }
    if (isIncome) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <DollarSign className="h-3 w-3" />
          <span>{type.replace('_', ' ')}</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-theme-bg text-theme-text-muted border border-theme-border">
        <span>{type.replace('_', ' ')}</span>
      </span>
    );
  };

  return (
    <div className={`rounded-2xl border border-theme-border bg-theme-surface p-5 shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-theme-border/60">
        <div>
          <h2 className="text-sm font-bold tracking-tight text-theme-text flex items-center gap-1.5">
            <History className="h-4 w-4 text-theme-primary" />
            <span>Recent Activity</span>
          </h2>
          <p className="text-xs text-theme-text-muted mt-0.5">
            Latest persisted investment transactions & cash flows
          </p>
        </div>
      </div>

      {transactions.length === 0 ? (
        <div className="py-12 flex flex-col items-center justify-center text-center">
          <History className="h-7 w-7 text-theme-text-muted/40 mb-2" />
          <span className="text-xs font-semibold text-theme-text">No Transactions Recorded</span>
          <span className="text-[11px] text-theme-text-muted mt-0.5 max-w-xs">
            Acquisitions, buy orders, sales, and dividends will appear here automatically.
          </span>
        </div>
      ) : (
        <div className="divide-y divide-theme-border/40 mt-1 max-h-96 overflow-y-auto pr-1">
          {transactions.map((tx) => {
            const dateStr = new Date(tx.transaction_date).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            });

            const feesNum = parseFloat(tx.fees || '0') + parseFloat(tx.taxes || '0');

            return (
              <div key={tx.id} className="py-3 flex items-center justify-between gap-3 hover:bg-theme-hover/30 transition-colors px-1 rounded-lg">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-xs text-theme-text truncate max-w-xs">
                      {tx.investment_name}
                    </span>
                    {getTxTypeBadge(tx.transaction_type)}
                  </div>
                  <div className="text-[11px] text-theme-text-muted flex items-center gap-2 mt-0.5">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" /> {dateStr}
                    </span>
                    <span>• {tx.portfolio_name}</span>
                    {parseFloat(tx.units) > 0 && (
                      <span>• {tx.units} units @ {tx.currency} {formatAmount(tx.price_per_unit)}</span>
                    )}
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <div className="font-bold text-xs text-theme-text">
                    {tx.currency} {formatAmount(tx.net_cash_flow || tx.amount)}
                  </div>
                  {feesNum > 0 && (
                    <div className="text-[10px] text-theme-text-muted">
                      incl. {tx.currency} {formatAmount(feesNum)} fees/tax
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
