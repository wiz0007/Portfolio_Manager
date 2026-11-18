import React, { useState } from 'react';
import { X, Loader2, Plus, BellRing, FileText, CheckCircle2 } from 'lucide-react';
import { InstrumentSearch } from '@/features/market-data/components/InstrumentSearch';
import { Instrument } from '@/features/market-data/types';
import { useAddWatchlistItem } from '../hooks/useWatchlist';
import { Button } from '@/shared/ui/Button';

interface AddToWatchlistModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialInstrument?: Instrument | null;
}

export const AddToWatchlistModal: React.FC<AddToWatchlistModalProps> = ({
  isOpen,
  onClose,
  initialInstrument = null,
}) => {
  const [selectedInstrument, setSelectedInstrument] = useState<Instrument | null>(initialInstrument);
  const [notes, setNotes] = useState('');
  const [targetPrice, setTargetPrice] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const addMutation = useAddWatchlistItem();

  if (!isOpen) return null;

  const handleSelectInstrument = (inst: Instrument) => {
    setSelectedInstrument(inst);
    setErrorMessage(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInstrument) {
      setErrorMessage('Please select an instrument to add.');
      return;
    }

    setErrorMessage(null);
    addMutation.mutate(
      {
        instrument_id: selectedInstrument.id,
        notes: notes.trim(),
        target_price: targetPrice ? targetPrice.trim() : null,
      },
      {
        onSuccess: () => {
          setSelectedInstrument(null);
          setNotes('');
          setTargetPrice('');
          onClose();
        },
        onError: (err: any) => {
          const detail = err?.response?.data?.detail || err?.message || 'Failed to add instrument to watchlist.';
          setErrorMessage(detail);
        },
      }
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg rounded-2xl border border-theme-border bg-theme-surface p-6 shadow-2xl text-theme-text transition-all">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-theme-border/70 mb-5">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-theme-primary-subtle text-theme-primary">
              <Plus className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold tracking-tight">Add to Watchlist</h2>
              <p className="text-xs text-theme-text-muted">Search canonical catalogue instruments</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-theme-text-muted hover:text-theme-text hover:bg-theme-hover transition-colors"
            aria-label="Close modal"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {errorMessage && (
          <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Instrument Selector */}
          <div>
            <label className="block text-xs font-semibold text-theme-text mb-1.5">
              Select Instrument <span className="text-rose-400">*</span>
            </label>
            {!selectedInstrument ? (
              <InstrumentSearch onSelect={handleSelectInstrument} autoFocus />
            ) : (
              <div className="p-3.5 rounded-xl border border-theme-primary/40 bg-theme-primary-subtle/30 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-theme-text">
                      {selectedInstrument.symbol}
                    </span>
                    {selectedInstrument.exchange && (
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-theme-bg text-theme-text-muted border border-theme-border uppercase">
                        {selectedInstrument.exchange}
                      </span>
                    )}
                    <span className="text-[10px] uppercase text-theme-primary font-semibold">
                      {selectedInstrument.asset_class}
                    </span>
                  </div>
                  <div className="text-xs text-theme-text-muted mt-0.5 truncate max-w-xs">
                    {selectedInstrument.name}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedInstrument(null)}
                  className="text-xs text-theme-text-muted hover:text-theme-primary hover:underline px-2 py-1"
                >
                  Change
                </button>
              </div>
            )}
          </div>

          {/* Optional Target Price */}
          <div>
            <label className="block text-xs font-semibold text-theme-text mb-1.5">
              <span className="flex items-center gap-1.5">
                <BellRing className="h-3.5 w-3.5 text-theme-primary" />
                Configured Price Target (Optional)
              </span>
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-xs font-semibold text-theme-text-muted">
                ₹
              </span>
              <input
                type="number"
                step="0.0001"
                min="0.0001"
                value={targetPrice}
                onChange={(e) => setTargetPrice(e.target.value)}
                placeholder="e.g. 1500.00"
                className="w-full pl-8 pr-3 py-2 rounded-xl border border-theme-border bg-theme-surface text-theme-text placeholder:text-theme-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/40"
              />
            </div>
            <p className="text-[11px] text-theme-text-muted mt-1">
              Trigger threshold alert when the market price breaches this value.
            </p>
          </div>

          {/* Optional Personal Notes */}
          <div>
            <label className="block text-xs font-semibold text-theme-text mb-1.5">
              <span className="flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-theme-primary" />
                Personal Notes (Optional)
              </span>
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Watch for quarterly earnings release; accumulate on dip."
              className="w-full px-3 py-2 rounded-xl border border-theme-border bg-theme-surface text-theme-text placeholder:text-theme-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/40 resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-theme-border/70 mt-6">
            <Button variant="ghost" type="button" onClick={onClose} disabled={addMutation.isPending}>
              Cancel
            </Button>
            <Button
              variant="primary"
              type="submit"
              disabled={!selectedInstrument || addMutation.isPending}
              leftIcon={
                addMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-4 w-4" />
                )
              }
            >
              {addMutation.isPending ? 'Adding...' : 'Add to Watchlist'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
