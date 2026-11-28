import React, { useState } from 'react';
import {
  X,
  FileText,
  History,
  RefreshCw,
  PlusCircle,
  TrendingUp,
  Layers,
} from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useInvestment } from '../../hooks/useInvestments';
import { investmentValuationApi } from '../../api/investmentValuationApi';
import { ValuationHistoryModal } from '../ValuationHistoryModal/ValuationHistoryModal';
import { ManualValuationModal } from '../ManualValuationModal/ManualValuationModal';
import { ProjectionCalculatorModal } from '../ProjectionCalculatorModal/ProjectionCalculatorModal';
import { HoldingValuationCard } from '../HoldingValuationCard';
import { useInvestmentPerformance } from '@/features/analytics/api/analyticsApi';
import { TransactionTimelineView } from '@/features/analytics/components/TransactionTimelineView';
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
  const queryClient = useQueryClient();
  const { data: investment, isLoading, isError } = useInvestment(portfolioId, investmentId);
  const { data: analyticsPerf } = useInvestmentPerformance(investmentId);

  const [showValuationHistory, setShowValuationHistory] = useState(false);
  const [showManualValuation, setShowManualValuation] = useState(false);
  const [showProjections, setShowProjections] = useState(false);

  const recalculateMutation = useMutation({
    mutationFn: () => investmentValuationApi.calculateValuation(investmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investment', portfolioId, investmentId] });
      queryClient.invalidateQueries({ queryKey: ['investment-valuations', investmentId] });
      queryClient.invalidateQueries({ queryKey: ['investments'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });

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
          {/* Authoritative Holding Valuation & Performance */}
          <HoldingValuationCard
            investmentId={investment.id}
            currency={investment.currency}
            initialValueFallback={investment.initial_value}
            currentValueFallback={investment.current_value}
            valuationMethodFallback={investment.valuation_method}
          />

          {/* Canonical Analytics Reconciliation Banner */}
          {analyticsPerf?.data_completeness?.reconciliation_status === 'DISCREPANCY' && (
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs space-y-1">
              <div className="font-semibold flex items-center gap-1.5">
                <span>⚠️ Ledger Reconciliation Advisory</span>
              </div>
              {analyticsPerf.data_completeness.reconciliation_notes?.map((note: string, idx: number) => (
                <div key={idx} className="text-[11px] text-amber-300/90">{note}</div>
              ))}
            </div>
          )}

          {/* Canonical Return Metrics */}
          {analyticsPerf && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-theme-card/30 border border-theme-border text-xs">
              <div>
                <span className="text-theme-text-muted text-[11px]">Realized P&L</span>
                <div className={`text-sm font-semibold mt-0.5 ${Number(analyticsPerf.realized_pnl) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {investment.currency} {Number(analyticsPerf.realized_pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
              </div>
              <div>
                <span className="text-theme-text-muted text-[11px]">Unrealized P&L</span>
                <div className={`text-sm font-semibold mt-0.5 ${Number(analyticsPerf.unrealized_pnl ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {analyticsPerf.unrealized_pnl !== null ? `${investment.currency} ${Number(analyticsPerf.unrealized_pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : 'N/A'}
                </div>
              </div>
              <div>
                <span className="text-theme-text-muted text-[11px]">XIRR Return</span>
                <div className="text-sm font-semibold text-theme-primary mt-0.5">
                  {analyticsPerf.xirr_pct !== null ? `${analyticsPerf.xirr_pct}%` : analyticsPerf.xirr_status}
                </div>
              </div>
              <div>
                <span className="text-theme-text-muted text-[11px]">Cost Basis</span>
                <div className="text-sm font-semibold text-theme-text mt-0.5">
                  {investment.currency} {Number(analyticsPerf.current_cost_basis).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
              </div>
            </div>
          )}

          {/* Valuation Engine & Projections Action Toolbar */}
          <div className="p-4 rounded-xl bg-theme-card/50 border border-theme-border space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-theme-text-muted">Method:</span>
                <span className="font-semibold text-theme-primary px-2 py-0.5 rounded bg-theme-primary/10 border border-theme-primary/20">
                  {investment.valuation_method || 'MANUAL'}
                </span>
              </div>
              <div className="text-theme-text-muted text-[11px]">
                Deterministic calculation engine
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 pt-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => recalculateMutation.mutate()}
                disabled={recalculateMutation.isPending}
                className="flex items-center gap-1.5 text-xs"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${recalculateMutation.isPending ? 'animate-spin' : ''}`} />
                <span>{recalculateMutation.isPending ? 'Calculating...' : 'Recalculate'}</span>
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowManualValuation(true)}
                className="flex items-center gap-1.5 text-xs"
              >
                <PlusCircle className="h-3.5 w-3.5 text-theme-primary" />
                <span>Record Snapshot</span>
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowValuationHistory(true)}
                className="flex items-center gap-1.5 text-xs"
              >
                <Layers className="h-3.5 w-3.5 text-theme-primary" />
                <span>Valuation History</span>
              </Button>

              <Button
                variant="primary"
                size="sm"
                onClick={() => setShowProjections(true)}
                className="flex items-center gap-1.5 text-xs ml-auto"
              >
                <TrendingUp className="h-3.5 w-3.5" />
                <span>Future Projections</span>
              </Button>
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

          {/* Canonical Transaction Timeline */}
          {analyticsPerf?.timeline && analyticsPerf.timeline.length > 0 && (
            <TransactionTimelineView timeline={analyticsPerf.timeline} currency={investment.currency} />
          )}

          {/* Transactions ledger fallback if timeline not yet loaded */}
          {(!analyticsPerf?.timeline || analyticsPerf.timeline.length === 0) && investment.transactions && investment.transactions.length > 0 && (
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
                      {Number(tx.units) > 0 && Number(tx.price_per_unit) > 0 && (
                        <div className="text-theme-text-muted text-[11px]">
                          Qty: {tx.units} @ {tx.currency} {Number(tx.price_per_unit).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-theme-text">
                        Net: {tx.currency} {Number(tx.net_cash_flow ?? tx.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-theme-text-muted text-[11px]">
                        Gross: {tx.currency} {Number(tx.gross_amount ?? tx.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        {(Number(tx.fees) > 0 || Number(tx.taxes) > 0) && (
                          <span> (Fees: {Number(tx.fees || 0).toFixed(2)}, Tax: {Number(tx.taxes || 0).toFixed(2)})</span>
                        )}
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

      {/* Sub-modals for Valuation Audit, Manual Recording, and Future Projections */}
      {showValuationHistory && (
        <ValuationHistoryModal
          investmentId={investmentId}
          investmentName={investment.display_name}
          currency={investment.currency}
          onClose={() => setShowValuationHistory(false)}
        />
      )}

      {showManualValuation && (
        <ManualValuationModal
          portfolioId={portfolioId}
          investmentId={investmentId}
          investmentName={investment.display_name}
          currentValue={Number(investment.current_value || investment.initial_value || 0)}
          currency={investment.currency}
          onClose={() => setShowManualValuation(false)}
          onSuccess={() => setShowManualValuation(false)}
        />
      )}

      {showProjections && (
        <ProjectionCalculatorModal
          investmentId={investmentId}
          investmentName={investment.display_name}
          currentValue={Number(investment.current_value || investment.initial_value || 0)}
          category={investment.category}
          currency={investment.currency}
          onClose={() => setShowProjections(false)}
        />
      )}
    </div>
  );
};
