import React, { useState } from 'react';
import { X } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { investmentValuationApi } from '../../api/investmentValuationApi';
import { Button } from '@/shared/ui/Button';

export interface ManualValuationModalProps {
  portfolioId: string;
  investmentId: string;
  investmentName: string;
  currentValue: number;
  currency?: string;
  onClose: () => void;
  onSuccess: () => void;
}

const getTodayLocalDate = (): string => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const ManualValuationModal: React.FC<ManualValuationModalProps> = ({
  portfolioId,
  investmentId,
  investmentName,
  currentValue,
  currency = 'INR',
  onClose,
  onSuccess,
}) => {
  const queryClient = useQueryClient();
  const todayStr = getTodayLocalDate();
  const [amount, setAmount] = useState<string>(String(currentValue || ''));
  const [valuationDate, setValuationDate] = useState<string>(todayStr);
  const [notes, setNotes] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (data: { amount: number | string; valuation_date: string; notes?: string }) =>
      investmentValuationApi.recordManualValuation(investmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investment', portfolioId, investmentId] });
      queryClient.invalidateQueries({ queryKey: ['investment-valuations', investmentId] });
      queryClient.invalidateQueries({ queryKey: ['investments'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['holdings'] });
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
      onSuccess();
    },
    onError: (err: any) => {
      const msg =
        err?.data?.amount?.[0] ||
        err?.data?.valuation_date?.[0] ||
        err?.data?.detail ||
        err?.message ||
        'Failed to record valuation snapshot.';
      setErrorMsg(msg);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    const trimmed = amount.trim();
    const num = parseFloat(trimmed);
    if (!trimmed || isNaN(num) || num <= 0) {
      setErrorMsg('Please enter a valid positive valuation amount.');
      return;
    }
    mutation.mutate({
      amount: trimmed,
      valuation_date: valuationDate,
      notes,
    });
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="manual-val-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto"
    >
      <div className="relative w-full max-w-md bg-theme-surface border border-theme-border rounded-2xl shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-theme-border bg-theme-card/40">
          <div>
            <h2 id="manual-val-title" className="text-lg font-bold text-theme-text">
              Record Valuation Snapshot
            </h2>
            <p className="text-xs text-theme-text-muted mt-0.5 truncate max-w-xs">
              {investmentName}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="p-1.5 rounded-lg text-theme-text-muted hover:text-theme-text hover:bg-theme-hover transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {errorMsg && (
            <div className="p-3 text-xs rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
              {errorMsg}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-theme-text mb-1">
              Valuation Amount ({currency}) <span className="text-rose-400">*</span>
            </label>
            <div className="relative">
              <span className="absolute left-3 top-2.5 text-xs font-semibold text-theme-text-muted">
                {currency}
              </span>
              <input
                type="number"
                step="any"
                min="0.01"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full pl-12 pr-3 py-2 bg-theme-bg border border-theme-border rounded-lg text-sm text-theme-text focus:outline-none focus:border-theme-primary"
              />
            </div>
            <p className="text-[11px] text-theme-text-muted mt-1">
              Current holding value is ₹{Number(currentValue).toLocaleString('en-IN')}.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-theme-text mb-1">
              Valuation Date <span className="text-rose-400">*</span>
            </label>
            <div className="relative">
              <input
                type="date"
                required
                max={todayStr}
                value={valuationDate}
                onChange={(e) => setValuationDate(e.target.value)}
                className="w-full px-3 py-2 bg-theme-bg border border-theme-border rounded-lg text-sm text-theme-text focus:outline-none focus:border-theme-primary"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-theme-text mb-1">
              Observation Notes
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Month-end statement appraisal or latest broker statement"
              className="w-full px-3 py-2 bg-theme-bg border border-theme-border rounded-lg text-sm text-theme-text focus:outline-none focus:border-theme-primary"
            />
          </div>

          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-300">
            <strong>Financial note:</strong> Recording a valuation preserves an immutable snapshot and updates current valuation. It will not alter historical acquisition cost.
          </div>

          {/* Footer buttons */}
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-theme-border">
            <Button type="button" variant="outline" onClick={onClose} disabled={mutation.isPending}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={mutation.isPending}>
              {mutation.isPending ? 'Saving...' : 'Save Snapshot'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
