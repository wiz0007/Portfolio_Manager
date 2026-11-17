import React, { useState } from 'react';
import { X, Send, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { marketDataApi } from '../api/marketDataApi';
import { AssetClassType } from '../types';

interface InstrumentRequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialQuery?: string;
  onSuccess?: () => void;
}

export const InstrumentRequestModal: React.FC<InstrumentRequestModalProps> = ({
  isOpen,
  onClose,
  initialQuery = '',
  onSuccess,
}) => {
  const [rawName, setRawName] = useState(initialQuery);
  const [assetClass, setAssetClass] = useState<AssetClassType>('EQUITY');
  const [symbol, setSymbol] = useState(initialQuery);
  const [exchange, setExchange] = useState('NSE');
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawName.trim()) {
      setError('Instrument name is required.');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      await marketDataApi.createInstrumentRequest({
        raw_name: rawName.trim(),
        asset_class: assetClass,
        symbol: symbol.trim().toUpperCase(),
        exchange: exchange.trim().toUpperCase(),
        notes: notes.trim(),
      });
      setIsSuccess(true);
      if (onSuccess) onSuccess();
      setTimeout(() => {
        setIsSuccess(false);
        onClose();
      }, 1500);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.symbol?.[0] || 'Failed to submit instrument request.';
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
            <h3 className="text-lg font-bold text-theme-text">Request Instrument Addition</h3>
            <p className="text-xs text-theme-text-muted mt-0.5">
              Submit an unlisted instrument for verification and central price coverage.
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

        {isSuccess ? (
          <div className="py-8 flex flex-col items-center justify-center text-center">
            <CheckCircle2 className="h-12 w-12 text-emerald-400 mb-3" />
            <h4 className="text-base font-semibold text-theme-text">Request Submitted!</h4>
            <p className="text-sm text-theme-text-muted mt-1 max-w-xs">
              Our market data operations team will verify and catalog this instrument shortly.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            {error && (
              <div className="p-3 rounded-xl border border-rose-500/20 bg-rose-500/10 flex items-start gap-2.5 text-xs text-rose-400">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-theme-text mb-1">
                Instrument Name <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                value={rawName}
                onChange={(e) => setRawName(e.target.value)}
                placeholder="e.g. Tata Technologies Limited"
                className="w-full px-3.5 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/40 focus:border-theme-primary"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-theme-text mb-1">Asset Class</label>
                <select
                  value={assetClass}
                  onChange={(e) => setAssetClass(e.target.value as AssetClassType)}
                  className="w-full px-3 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/40"
                >
                  <option value="EQUITY">Listed Stock</option>
                  <option value="MUTUAL_FUND">Mutual Fund</option>
                  <option value="COMMODITY">Gold / Precious Metal</option>
                  <option value="FIXED_INCOME">Bond / Fixed Income</option>
                  <option value="REAL_ESTATE">REIT / InvIT</option>
                  <option value="CRYPTO">Cryptocurrency</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-theme-text mb-1">Ticker / Symbol</label>
                <input
                  type="text"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  placeholder="e.g. TATATECH"
                  className="w-full px-3.5 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-sm uppercase focus:outline-none focus:ring-2 focus:ring-theme-primary/40 focus:border-theme-primary"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-theme-text mb-1">Exchange / Platform</label>
                <input
                  type="text"
                  value={exchange}
                  onChange={(e) => setExchange(e.target.value)}
                  placeholder="NSE, BSE, AMFI..."
                  className="w-full px-3.5 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-sm uppercase focus:outline-none focus:ring-2 focus:ring-theme-primary/40 focus:border-theme-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-theme-text mb-1">Currency</label>
                <input
                  type="text"
                  value="INR"
                  disabled
                  className="w-full px-3.5 py-2 rounded-xl border border-theme-border bg-theme-bg/60 text-theme-text-muted text-sm cursor-not-allowed"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-theme-text mb-1">Additional Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optional link to exchange page, ISIN, or prospectus detail..."
                rows={2}
                className="w-full px-3.5 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/40 focus:border-theme-primary resize-none"
              />
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
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Submit Request
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
