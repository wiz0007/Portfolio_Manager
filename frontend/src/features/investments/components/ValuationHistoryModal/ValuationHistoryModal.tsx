import React from 'react';
import { X, Calendar, Layers, ShieldCheck } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { investmentValuationApi } from '../../api/investmentValuationApi';
import { Button } from '@/shared/ui/Button';

export interface ValuationHistoryModalProps {
  investmentId: string;
  investmentName: string;
  currency?: string;
  onClose: () => void;
}

export const ValuationHistoryModal: React.FC<ValuationHistoryModalProps> = ({
  investmentId,
  investmentName,
  currency = 'INR',
  onClose,
}) => {
  const { data: snapshots = [], isLoading, isError } = useQuery({
    queryKey: ['investment-valuations', investmentId],
    queryFn: () => investmentValuationApi.getValuations(investmentId),
  });

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="valuation-history-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto"
    >
      <div className="relative w-full max-w-2xl bg-theme-surface border border-theme-border rounded-2xl shadow-2xl overflow-hidden my-8 max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-theme-border bg-theme-card/40">
          <div>
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-theme-primary" />
              <span className="text-xs font-semibold text-theme-primary uppercase tracking-wider">
                Audit & Provenance
              </span>
            </div>
            <h2 id="valuation-history-title" className="text-lg font-bold text-theme-text mt-0.5">
              Valuation History — {investmentName}
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

        {/* Content */}
        <div className="p-5 overflow-y-auto flex-1 space-y-4">
          {isLoading && (
            <div className="py-12 text-center text-sm text-theme-text-muted">
              Loading historical snapshots...
            </div>
          )}

          {isError && (
            <div className="py-8 text-center text-sm text-rose-400">
              Failed to load valuation snapshots.
            </div>
          )}

          {!isLoading && !isError && snapshots.length === 0 && (
            <div className="py-12 text-center text-sm text-theme-text-muted">
              No historical valuation snapshots recorded yet.
            </div>
          )}

          {!isLoading && snapshots.length > 0 && (
            <div className="border border-theme-border rounded-xl overflow-hidden divide-y divide-theme-border">
              {snapshots.map((snap) => (
                <div key={snap.id} className="p-4 bg-theme-card/40 hover:bg-theme-card/70 transition-colors">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-base font-bold text-theme-text">
                        {snap.currency || currency}{' '}
                        {Number(snap.amount).toLocaleString('en-IN', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 4,
                        })}
                      </div>
                      <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-theme-text-muted">
                        <span className="flex items-center gap-1 font-medium">
                          <Calendar className="h-3.5 w-3.5" />
                          {snap.valuation_date}
                        </span>
                        <span>•</span>
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-theme-bg border border-theme-border text-[11px] font-medium text-theme-text">
                          <ShieldCheck className="h-3 w-3 text-theme-primary" />
                          {snap.valuation_method || 'MANUAL'}
                        </span>
                        <span>•</span>
                        <span>Source: {snap.source || 'SYSTEM'}</span>
                        {snap.source_reference && <span>({snap.source_reference})</span>}
                      </div>
                    </div>
                    {snap.observed_at && (
                      <div className="text-[11px] text-theme-text-muted text-right shrink-0">
                        Observed: {new Date(snap.observed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    )}
                  </div>
                  {snap.notes && (
                    <div className="mt-2 text-xs text-theme-text-muted bg-theme-bg/60 p-2 rounded border border-theme-border/40">
                      {snap.notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-theme-border bg-theme-card/40 flex justify-end">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};
