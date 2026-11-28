import React from 'react';
import { InvestmentTimelineEntry } from '../types';
import { ArrowDownLeft, ArrowUpRight, DollarSign, Clock } from 'lucide-react';

interface TransactionTimelineViewProps {
  timeline: InvestmentTimelineEntry[];
  currency?: string;
  className?: string;
}

export const TransactionTimelineView: React.FC<TransactionTimelineViewProps> = ({
  timeline,
  currency = 'INR',
  className = '',
}) => {
  if (timeline.length === 0) {
    return (
      <div className={`p-6 text-center text-xs text-theme-text-muted border border-theme-border rounded-xl bg-theme-surface ${className}`}>
        No transaction history recorded for this holding.
      </div>
    );
  }

  return (
    <div className={`p-5 rounded-2xl border border-theme-border bg-theme-surface flex flex-col ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        <Clock className="h-4 w-4 text-theme-primary" />
        <h3 className="text-sm font-semibold text-theme-text">Transaction Ledger Timeline</h3>
      </div>

      <div className="space-y-3">
        {timeline.map((tx) => {
          const isAcquisition = ['BUY', 'INITIAL_PURCHASE', 'DEPOSIT'].includes(tx.type);
          const isDisposal = ['SELL', 'WITHDRAWAL'].includes(tx.type);

          return (
            <div
              key={tx.id}
              className="flex items-center justify-between p-3 rounded-xl border border-theme-border/60 bg-theme-card/60 text-xs"
            >
              <div className="flex items-center gap-3">
                <div
                  className={`h-8 w-8 rounded-lg flex items-center justify-center ${
                    isAcquisition
                      ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                      : isDisposal
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                  }`}
                >
                  {isAcquisition && <ArrowDownLeft className="h-4 w-4" />}
                  {isDisposal && <ArrowUpRight className="h-4 w-4" />}
                  {!isAcquisition && !isDisposal && <DollarSign className="h-4 w-4" />}
                </div>

                <div>
                  <div className="font-semibold text-theme-text flex items-center gap-2">
                    <span>{tx.type.replace('_', ' ')}</span>
                    {parseFloat(tx.units) > 0 && (
                      <span className="text-theme-text-muted font-normal">
                        ({parseFloat(tx.units).toFixed(4)} units @ {currency} {parseFloat(tx.price_per_unit).toFixed(2)})
                      </span>
                    )}
                  </div>
                  <div className="text-theme-text-muted text-[11px] mt-0.5">
                    {tx.date} {tx.notes ? `• ${tx.notes}` : ''}
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div
                  className={`font-semibold font-mono ${
                    isDisposal ? 'text-emerald-400' : isAcquisition ? 'text-theme-text' : 'text-purple-400'
                  }`}
                >
                  {currency} {Math.abs(parseFloat(tx.net_cash_flow)).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
                {(parseFloat(tx.fees) > 0 || parseFloat(tx.taxes) > 0) && (
                  <div className="text-[10px] text-theme-text-muted">
                    Fees: {currency} {parseFloat(tx.fees).toFixed(2)} | Tax: {currency} {parseFloat(tx.taxes).toFixed(2)}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
