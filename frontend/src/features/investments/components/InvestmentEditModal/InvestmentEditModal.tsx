import React, { useState } from 'react';
import { X, Save, AlertCircle } from 'lucide-react';
import { useInvestment, useUpdateInvestment } from '../../hooks/useInvestments';
import { Button } from '@/shared/ui/Button';

export interface InvestmentEditModalProps {
  portfolioId: string;
  investmentId: string;
  onClose: () => void;
  onSaved?: () => void;
}

export const InvestmentEditModal: React.FC<InvestmentEditModalProps> = ({
  portfolioId,
  investmentId,
  onClose,
  onSaved,
}) => {
  const { data: investment, isLoading } = useInvestment(portfolioId, investmentId);
  const updateMutation = useUpdateInvestment(portfolioId);

  const [displayName, setDisplayName] = useState(investment?.display_name || '');
  const [currentValue, setCurrentValue] = useState(investment?.current_value?.toString() || '0');
  const [notes, setNotes] = useState(investment?.notes || '');
  const [isActive, setIsActive] = useState(investment?.is_active ?? true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Sync state once data loads
  React.useEffect(() => {
    if (investment) {
      setDisplayName(investment.display_name || '');
      setCurrentValue(investment.current_value?.toString() || '0');
      setNotes(investment.notes || '');
      setIsActive(investment.is_active ?? true);
    }
  }, [investment]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const numericVal = parseFloat(currentValue);
    if (isNaN(numericVal) || numericVal < 0) {
      setErrorMessage('Please enter a valid positive current valuation.');
      return;
    }

    try {
      await updateMutation.mutateAsync({
        id: investmentId,
        payload: {
          display_name: displayName.trim(),
          current_value: numericVal,
          notes: notes.trim(),
          is_active: isActive,
        },
      });
      onSaved?.();
      onClose();
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.detail ||
          err?.message ||
          'Failed to update holding. Please try again.'
      );
    }
  };

  if (isLoading || !investment) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
        <div className="w-full max-w-lg bg-theme-surface border border-theme-border rounded-xl p-8 text-center text-theme-text-muted">
          Loading holding details...
        </div>
      </div>
    );
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-holding-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
    >
      <div className="relative w-full max-w-lg bg-theme-surface border border-theme-border rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-theme-border bg-theme-card/40">
          <div>
            <h2 id="edit-holding-title" className="text-lg font-bold text-theme-text">
              Edit Investment Holding
            </h2>
            <p className="text-xs text-theme-text-muted">
              Update holding name, notes, and latest current valuation.
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
        <form onSubmit={handleSave} className="p-6 space-y-4">
          {errorMessage && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-theme-text uppercase tracking-wider mb-1.5">
              Holding Display Name
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
              className="w-full h-10 px-3 rounded-lg bg-theme-card border border-theme-border text-sm text-theme-text outline-none focus:border-theme-primary focus:ring-1 focus:ring-theme-primary"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-theme-text uppercase tracking-wider mb-1.5">
              Current Valuation ({investment.currency})
            </label>
            <input
              type="number"
              step="any"
              min="0"
              value={currentValue}
              onChange={(e) => setCurrentValue(e.target.value)}
              required
              className="w-full h-10 px-3 rounded-lg bg-theme-card border border-theme-border text-sm text-theme-text outline-none focus:border-theme-primary focus:ring-1 focus:ring-theme-primary"
            />
            <p className="text-[11px] text-theme-text-muted mt-1">
              Initial capital outlay was {investment.currency}{' '}
              {Number(investment.initial_value).toLocaleString('en-IN')}.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-theme-text uppercase tracking-wider mb-1.5">
              Investment Notes
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add holding notes, thesis, or reminder details..."
              className="w-full p-3 rounded-lg bg-theme-card border border-theme-border text-sm text-theme-text outline-none focus:border-theme-primary focus:ring-1 focus:ring-theme-primary resize-y"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="is_active_toggle"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="h-4 w-4 rounded border-theme-border text-theme-primary focus:ring-theme-primary"
            />
            <label htmlFor="is_active_toggle" className="text-xs text-theme-text font-medium cursor-pointer">
              Active holding (included in active portfolio calculation)
            </label>
          </div>

          {/* Footer buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-theme-border">
            <Button type="button" variant="outline" onClick={onClose} disabled={updateMutation.isPending}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={updateMutation.isPending}>
              <Save className="h-4 w-4 mr-1.5" />
              {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
