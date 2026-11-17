import React, { useState } from 'react';
import { X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { marketDataApi } from '../api/marketDataApi';
import { Instrument } from '../types';

interface ManualPriceEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  instrument: Instrument | null;
  onSuccess?: () => void;
}

export const ManualPriceEntryModal: React.FC<ManualPriceEntryModalProps> = ({
  isOpen,
  onClose,
  instrument,
  onSuccess,
}) => {
  const [price, setPrice] = useState('');
  const [priceType, setPriceType] = useState('LTP');
  const [effectiveDate, setEffectiveDate] = useState(new Date().toISOString().split('T')[0]);
  const [source, setSource] = useState('MANUAL_VERIFIED');
  const [sourceRef, setSourceRef] = useState('');
  const [notes, setNotes] = useState('');
  const [shouldPublish, setShouldPublish] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !instrument) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!price || parseFloat(price) <= 0) {
      setError('Please enter a valid positive price amount.');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const effectiveAt = `${effectiveDate}T10:00:00Z`;
      const res = await marketDataApi.createPriceObservation({
        instrument: instrument.id,
        price_type: priceType,
        value: price.trim(),
        currency: instrument.currency,
        effective_at: effectiveAt,
        source: source.trim() || 'MANUAL_VERIFIED',
        source_reference: sourceRef.trim(),
        notes: notes.trim(),
      });

      if (shouldPublish && res && (res as any).id) {
        await marketDataApi.publishPriceObservation((res as any).id);
      }

      if (onSuccess) onSuccess();
      onClose();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.value?.[0] || 'Failed to record price observation.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg p-6 rounded-2xl border border-theme-border bg-theme-surface shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-theme-border">
          <div>
            <h3 className="text-lg font-bold text-theme-text">Record Price Observation</h3>
            <p className="text-xs text-theme-text-muted mt-0.5">
              {instrument.symbol} — {instrument.name} ({instrument.exchange || instrument.asset_class})
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-theme-text-muted hover:text-theme-text hover:bg-theme-hover"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {error && (
            <div className="p-3 rounded-xl border border-rose-500/20 bg-rose-500/10 flex items-start gap-2.5 text-xs text-rose-400">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-theme-text mb-1">
                Observed Price ({instrument.currency}) <span className="text-rose-400">*</span>
              </label>
              <input
                type="number"
                step="0.0001"
                min="0.0001"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="0.00"
                className="w-full px-3.5 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-sm font-mono focus:outline-none focus:ring-2 focus:ring-theme-primary/40 focus:border-theme-primary"
                required
                autoFocus
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-theme-text mb-1">Price Basis</label>
              <select
                value={priceType}
                onChange={(e) => setPriceType(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/40"
              >
                <option value="LTP">LTP (Last Traded Price)</option>
                <option value="NAV">NAV (Net Asset Value)</option>
                <option value="CLOSE">Daily Close</option>
                <option value="INDICATIVE_VALUATION">Indicative Valuation</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-theme-text mb-1">Effective Date</label>
              <input
                type="date"
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/40 focus:border-theme-primary"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-theme-text mb-1">Source Guidance</label>
              <input
                type="text"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="e.g. NSE, BSE, AMFI..."
                className="w-full px-3.5 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/40 focus:border-theme-primary"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-theme-text mb-1">Source Reference / Evidence</label>
            <input
              type="text"
              value={sourceRef}
              onChange={(e) => setSourceRef(e.target.value)}
              placeholder="URL, circular reference, or bulletin quote..."
              className="w-full px-3.5 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/40 focus:border-theme-primary"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-theme-text mb-1">Notes / Verification Details</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional audit remarks..."
              rows={2}
              className="w-full px-3.5 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/40 focus:border-theme-primary resize-none"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="shouldPublishCheckbox"
              checked={shouldPublish}
              onChange={(e) => setShouldPublish(e.target.checked)}
              className="h-4 w-4 rounded border-theme-border text-theme-primary focus:ring-theme-primary"
            />
            <label htmlFor="shouldPublishCheckbox" className="text-xs text-theme-text select-none cursor-pointer">
              Publish immediately and trigger holding valuation refresh
            </label>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-theme-border">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl border border-theme-border text-xs font-semibold text-theme-text hover:bg-theme-hover"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 rounded-xl bg-theme-primary text-white text-xs font-semibold hover:bg-theme-primary/90 flex items-center gap-1.5 shadow-sm"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle2 className="h-4 w-4" />
              )}
              {shouldPublish ? 'Publish Observation' : 'Save as Draft'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
