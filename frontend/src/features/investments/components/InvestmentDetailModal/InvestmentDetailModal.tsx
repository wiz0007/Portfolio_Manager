import React from 'react';
import {
  X,
  FileText,
  History,
} from 'lucide-react';
import { useInvestment } from '../../hooks/useInvestments';
import { Button } from '@/shared/ui/Button';

export interface InvestmentDetailModalProps {
  portfolioId: string;
  investmentId: string;
  onClose: () => void;
  onEdit: () => void;
}

export const InvestmentDetailModal: React.FC<InvestmentDetailModalProps> = ({
  portfolioId,
  investmentId,
  onClose,
  onEdit,
}) => {
  const { data: investment, isLoading, isError } = useInvestment(portfolioId, investmentId);

  if (isLoading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
        <div className="w-full max-w-2xl bg-theme-surface border border-theme-border rounded-xl p-8 text-center text-theme-text-muted">
          Loading holding details...
        </div>
      </div>
    );
  }

  if (isError || !investment) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
        <div className="w-full max-w-md bg-theme-surface border border-theme-border rounded-xl p-6 text-center space-y-4">
          <p className="text-sm text-theme-text">Could not load investment details.</p>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    );
  }

  const initialVal = Number(investment.initial_value || 0);
  const currentVal = Number(investment.current_value || 0);
  const netGain = currentVal - initialVal;
  const netGainPct = initialVal > 0 ? (netGain / initialVal) * 100 : 0;

  const detailEntries = investment.details
    ? Object.entries(investment.details).filter(([key, val]) => {
        if (key === 'id' || key === 'investment' || val === null || val === undefined || val === '')
          return false;
        return true;
      })
    : [];

  const formatKey = (key: string): string => {
    return key
      .replace(/_/g, ' ')
      .replace(/pct/i, '(%)')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const formatVal = (val: any): string => {
    if (typeof val === 'boolean') return val ? 'Yes' : 'No';
    if (typeof val === 'number') {
      return val.toLocaleString('en-IN');
    }
    return String(val);
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="investment-detail-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto"
    >
      <div className="relative w-full max-w-3xl bg-theme-surface border border-theme-border rounded-2xl shadow-2xl overflow-hidden my-8 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-theme-border bg-theme-card/40">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-theme-primary/10 text-theme-primary border border-theme-primary/20 uppercase tracking-wide">
                {investment.category.replace('_', ' ')}
              </span>
              <span className="text-xs text-theme-text-muted capitalize">
                {investment.asset_type.replace(/_/g, ' ')}
              </span>
            </div>
            <h2 id="investment-detail-title" className="text-xl font-bold text-theme-text mt-1">
              {investment.display_name}
            </h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="p-1.5 rounded-lg text-theme-text-muted hover:text-theme-text hover:bg-theme-hover transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Metrics summary */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-4 rounded-xl bg-theme-card border border-theme-border">
              <span className="text-xs text-theme-text-muted font-medium">Initial Capital Outlay</span>
              <div className="text-lg font-bold text-theme-text mt-1">
                {investment.currency} {initialVal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-theme-card border border-theme-border">
              <span className="text-xs text-theme-text-muted font-medium">Current Valuation</span>
              <div className="text-lg font-bold text-theme-text mt-1">
                {investment.currency} {currentVal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-theme-card border border-theme-border">
              <span className="text-xs text-theme-text-muted font-medium">Unrealized Value Gain</span>
              <div
                className={`text-lg font-bold mt-1 ${
                  netGain >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {netGain >= 0 ? '+' : ''}
                {investment.currency} {netGain.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                <span className="text-xs font-normal ml-1 text-theme-text-muted">
                  ({netGainPct.toFixed(2)}%)
                </span>
              </div>
            </div>
          </div>

          {/* Asset details breakdown */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-theme-text-muted mb-3 flex items-center gap-2">
              <FileText className="h-4 w-4 text-theme-primary" />
              Holding Specifications & Terms
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {detailEntries.map(([k, v]) => (
                <div key={k} className="p-3 rounded-lg bg-theme-card/60 border border-theme-border/60">
                  <div className="text-[11px] font-medium text-theme-text-muted">{formatKey(k)}</div>
                  <div className="text-sm font-semibold text-theme-text mt-0.5 break-words">
                    {formatVal(v)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Notes */}
          {investment.notes && (
            <div className="p-4 rounded-xl bg-theme-card/40 border border-theme-border">
              <span className="text-xs font-medium text-theme-text-muted">Investment Notes</span>
              <p className="text-sm text-theme-text mt-1 whitespace-pre-wrap">{investment.notes}</p>
            </div>
          )}

          {/* Transactions ledger */}
          {investment.transactions && investment.transactions.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-theme-text-muted mb-3 flex items-center gap-2">
                <History className="h-4 w-4 text-theme-primary" />
                Transaction Ledger
              </h3>
              <div className="border border-theme-border rounded-xl overflow-hidden divide-y divide-theme-border">
                {investment.transactions.map((tx) => (
                  <div key={tx.id} className="p-3 flex items-center justify-between text-xs bg-theme-card/40">
                    <div>
                      <div className="font-semibold text-theme-text">{tx.transaction_type}</div>
                      <div className="text-theme-text-muted text-[11px]">Date: {tx.transaction_date}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-theme-text">
                        {tx.currency} {Number(tx.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                      {tx.notes && <div className="text-theme-text-muted text-[11px]">{tx.notes}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-theme-border bg-theme-card/40">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          <Button variant="primary" onClick={onEdit}>
            Edit Investment
          </Button>
        </div>
      </div>
    </div>
  );
};
