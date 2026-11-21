import React, { useEffect, useState } from 'react';
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
  const [seriesList, setSeriesList] = useState<Array<{ id: string; source: string; exchange: string; price_type: string; currency: string; unit: string }>>([]);
  const [seriesId, setSeriesId] = useState('');
  const [seriesCurrency, setSeriesCurrency] = useState('INR');
  const [seriesUnit, setSeriesUnit] = useState('SHARES');
  const [isLoadingSeries, setIsLoadingSeries] = useState(false);
  const [isCreatingSeries, setIsCreatingSeries] = useState(false);
  const [effectiveDate, setEffectiveDate] = useState(new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata' }).format(new Date()));
  const [source, setSource] = useState('MANUAL_VERIFIED');
  const [sourceRef, setSourceRef] = useState('');
  const [notes, setNotes] = useState('');
  const [shouldPublish, setShouldPublish] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !instrument) return;
    let cancelled = false;
    setIsLoadingSeries(true);
    setError(null);
    setSeriesId('');
    setSeriesList([]);
    marketDataApi.getSeries(instrument.id)
      .then((rows) => {
        if (cancelled) return;
        const manualRows = rows.filter((row) => row.source === 'MANUAL_VERIFIED');
        setSeriesList(manualRows);
        const preferredType = instrument.asset_class === 'MUTUAL_FUND'
          ? 'NAV'
          : instrument.asset_class === 'INDEX' ? 'CLOSE'
            : instrument.asset_class === 'COMMODITY' ? 'INDICATIVE_VALUATION'
              : instrument.asset_class === 'REAL_ESTATE' || instrument.asset_class === 'FIXED_INCOME'
                ? 'APPRAISAL' : 'LTP';
        setPriceType(preferredType);
        const preferred = manualRows.find((row) => row.price_type === preferredType) || manualRows[0];
        if (preferred) {
          setSeriesId(preferred.id);
          setPriceType(preferred.price_type);
          setSource(preferred.source);
          setSeriesCurrency(preferred.currency);
          setSeriesUnit(preferred.unit);
        } else {
          setError('No publisher-reviewed manual series exists yet. Create one before recording a manual observation.');
        }
      })
      .catch(() => {
        if (!cancelled) setError("Unable to load the instrument's market-data series.");
      })
      .finally(() => {
        if (!cancelled) setIsLoadingSeries(false);
      });
    return () => { cancelled = true; };
  }, [isOpen, instrument?.id]);

  if (!isOpen || !instrument) return null;

  const handleCreateManualSeries = async () => {
    if (!instrument) return;
    setIsCreatingSeries(true);
    setError(null);
    const unit = instrument.asset_class === 'MUTUAL_FUND' || instrument.asset_class === 'INDEX'
      ? 'UNITS'
      : instrument.asset_class === 'COMMODITY' ? 'GRAMS_24K'
        : instrument.asset_class === 'REAL_ESTATE' || instrument.asset_class === 'FIXED_INCOME' || instrument.asset_class === 'CASH_EQUIVALENT'
          ? 'CURRENCY' : 'SHARES';
    try {
      const created = await marketDataApi.createManualSeries(instrument.id, priceType, unit);
      setSeriesList((current) => [...current.filter((row) => row.id !== created.id), created]);
      setSeriesId(created.id);
      setPriceType(created.price_type);
      setSource(created.source);
      setSeriesCurrency(created.currency);
      setSeriesUnit(created.unit);
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to create the manual price series.';
      setError(typeof message === 'string' ? message : JSON.stringify(message));
    } finally {
      setIsCreatingSeries(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!seriesId) {
      setError('Select an exact market-data series before recording an observation.');
      return;
    }
    if (!price || !Number.isFinite(Number(price)) || parseFloat(price) <= 0) {
      setError('Please enter a valid positive price amount.');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const effectiveAt = new Date(`${effectiveDate}T15:30:00+05:30`).toISOString();
      const res = await marketDataApi.createPriceObservation({
        instrument: instrument.id,
        series: seriesId,
        price_type: priceType,
        value: price.trim(),
        currency: seriesCurrency,
        unit: seriesUnit,
        effective_at: effectiveAt,
        source: source.trim() || 'MANUAL_VERIFIED',
        source_reference: sourceRef.trim(),
        notes: notes.trim(),
      });

      if (shouldPublish && res && (res as any).id) {
        await marketDataApi.submitPriceObservationForReview((res as any).id);
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
                Observed Price ({seriesCurrency}) <span className="text-rose-400">*</span>
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
              <label className="block text-xs font-semibold text-theme-text mb-1">Exact Market-Data Series</label>
              <select
                value={seriesId}
                disabled={isLoadingSeries || seriesList.length === 0}
                onChange={(e) => {
                  const selected = seriesList.find((row) => row.id === e.target.value);
                  setSeriesId(e.target.value);
                  if (selected) {
                    setPriceType(selected.price_type);
                    setSource(selected.source);
                    setSeriesCurrency(selected.currency);
                    setSeriesUnit(selected.unit);
                  }
                }}
                className="w-full px-3 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/40"
              >
                <option value="">{isLoadingSeries ? 'Loading series…' : 'Select series'}</option>
                {seriesList.map((row) => (
                  <option key={row.id} value={row.id}>{row.exchange || 'No exchange'} · {row.price_type} · {row.source} · {row.currency}/{row.unit}</option>
                ))}
              </select>
              {!isLoadingSeries && seriesList.length === 0 && (
                <button
                  type="button"
                  onClick={handleCreateManualSeries}
                  disabled={isCreatingSeries}
                  className="mt-2 text-xs font-semibold text-theme-primary hover:underline disabled:opacity-50"
                >
                  {isCreatingSeries ? 'Creating manual series…' : 'Create publisher-reviewed manual series'}
                </button>
              )}
            </div>
            <div>
              <label className="block text-xs font-semibold text-theme-text mb-1">Price Basis</label>
              <select
                value={priceType}
                disabled={Boolean(seriesId)}
                onChange={(e) => setPriceType(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/40"
              >
                <option value="LTP">LTP (Last Traded Price)</option>
                <option value="NAV">NAV (Net Asset Value)</option>
                <option value="CLOSE">Daily Close</option>
                <option value="INDICATIVE_VALUATION">Indicative Valuation</option>
                <option value="APPRAISAL">Appraisal</option>
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
                readOnly
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
              disabled={isLoading || isLoadingSeries || !seriesId}
              className="px-4 py-2 rounded-xl border border-theme-border text-xs font-semibold text-theme-text hover:bg-theme-hover"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || isLoadingSeries || !seriesId}
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
