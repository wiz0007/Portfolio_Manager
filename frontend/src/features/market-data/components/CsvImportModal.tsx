import React, { useState } from 'react';
import { X, Upload, CheckCircle2, AlertCircle, Loader2, ChevronRight } from 'lucide-react';
import { marketDataApi } from '../api/marketDataApi';
import { ImportPreviewResult } from '../types';

interface CsvImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const CsvImportModal: React.FC<CsvImportModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [csvText, setCsvText] = useState('');
  const [fileName, setFileName] = useState('manual_quotes.csv');
  const [isLoading, setIsLoading] = useState(false);
  const [preview, setPreview] = useState<ImportPreviewResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCommitted, setIsCommitted] = useState(false);

  if (!isOpen) return null;

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      setCsvText(event.target?.result as string || '');
    };
    reader.readAsText(file);
  };

  const handlePreview = async () => {
    if (!csvText.trim()) {
      setError('Please upload or paste CSV content.');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const res: any = await marketDataApi.previewCsvImport(csvText.trim(), fileName);
      setPreview(res);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to parse CSV.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCommit = async () => {
    if (!preview) return;

    setIsLoading(true);
    setError(null);
    try {
      await marketDataApi.commitCsvImport(preview as any);
      setIsCommitted(true);
      if (onSuccess) onSuccess();
      setTimeout(() => {
        setIsCommitted(false);
        setPreview(null);
        setCsvText('');
        onClose();
      }, 1500);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to commit CSV draft observations.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-2xl p-6 rounded-2xl border border-theme-border bg-theme-surface shadow-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between pb-4 border-b border-theme-border shrink-0">
          <div>
            <h3 className="text-lg font-bold text-theme-text">Bulk CSV Price Import</h3>
            <p className="text-xs text-theme-text-muted mt-0.5">
              Upload price collection batches matching schema v1.0. All valid rows commit as reviewable drafts.
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

        <div className="py-4 overflow-y-auto flex-1 space-y-4">
          {error && (
            <div className="p-3 rounded-xl border border-rose-500/20 bg-rose-500/10 flex items-start gap-2.5 text-xs text-rose-400">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {isCommitted ? (
            <div className="py-12 flex flex-col items-center justify-center text-center">
              <CheckCircle2 className="h-12 w-12 text-emerald-400 mb-3" />
              <h4 className="text-base font-semibold text-theme-text">Draft Observations Committed!</h4>
              <p className="text-sm text-theme-text-muted mt-1 max-w-xs">
                Successfully created draft observations. Operators and publishers can now review and publish them.
              </p>
            </div>
          ) : !preview ? (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-theme-text mb-2">Upload CSV File</label>
                <div className="p-6 rounded-xl border-2 border-dashed border-theme-border hover:border-theme-primary/50 bg-theme-bg/50 flex flex-col items-center justify-center text-center transition-colors">
                  <Upload className="h-8 w-8 text-theme-text-muted mb-2" />
                  <p className="text-sm font-medium text-theme-text">
                    Choose a CSV file or drag and drop here
                  </p>
                  <p className="text-xs text-theme-text-muted mt-1">
                    Standard header: <code>schema_version,instrument_id,price_type,value,currency,unit,effective_at...</code>
                  </p>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    className="mt-4 text-xs text-theme-text file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-theme-primary file:text-white hover:file:bg-theme-primary/90 cursor-pointer"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-semibold text-theme-text">Or Paste CSV Content</label>
                  <button
                    type="button"
                    onClick={() => {
                      setCsvText(
                        'schema_version,worklist_item_id,instrument_id,symbol,price_type,value,currency,unit,effective_at,source_id,source_reference,notes\n'
                      );
                    }}
                    className="text-[11px] text-theme-primary hover:underline"
                  >
                    Insert template header
                  </button>
                </div>
                <textarea
                  value={csvText}
                  onChange={(e) => setCsvText(e.target.value)}
                  placeholder="Paste CSV rows here..."
                  rows={6}
                  className="w-full px-3.5 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text font-mono text-xs focus:outline-none focus:ring-2 focus:ring-theme-primary/40 focus:border-theme-primary resize-none"
                />
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Batch Summary */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-xl border border-theme-border bg-theme-bg text-center">
                  <div className="text-xs text-theme-text-muted font-medium">Total Rows</div>
                  <div className="text-lg font-bold text-theme-text mt-0.5">{preview.total_rows}</div>
                </div>
                <div className="p-3 rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-center">
                  <div className="text-xs text-emerald-400 font-medium">Valid Rows</div>
                  <div className="text-lg font-bold text-emerald-400 mt-0.5">{preview.valid_count}</div>
                </div>
                <div className="p-3 rounded-xl border border-rose-500/20 bg-rose-500/5 text-center">
                  <div className="text-xs text-rose-400 font-medium">Error Rows</div>
                  <div className="text-lg font-bold text-rose-400 mt-0.5">{preview.error_count}</div>
                </div>
              </div>

              {/* Error Rows Table if any */}
              {preview.error_count > 0 && (
                <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 overflow-hidden">
                  <div className="p-3 border-b border-rose-500/20 text-xs font-semibold text-rose-400">
                    Row Rejection Details ({preview.error_count})
                  </div>
                  <div className="max-h-40 overflow-y-auto divide-y divide-rose-500/10 text-xs">
                    {preview.errors.map((err, i) => (
                      <div key={i} className="p-2.5 flex items-start gap-2">
                        <span className="font-mono font-bold text-rose-400">Line {err.row_number}:</span>
                        <span className="text-theme-text font-medium">[{err.field}]</span>
                        <span className="text-theme-text-muted">{err.error}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Valid Rows Preview */}
              {preview.valid_count > 0 && (
                <div className="rounded-xl border border-theme-border overflow-hidden">
                  <div className="p-3 border-b border-theme-border bg-theme-bg/60 text-xs font-semibold text-theme-text flex items-center justify-between">
                    <span>Valid Observations Preview ({preview.valid_count})</span>
                    <span className="text-[10px] text-theme-text-muted uppercase">Ready for draft commit</span>
                  </div>
                  <div className="max-h-48 overflow-y-auto divide-y divide-theme-border text-xs">
                    {preview.valid_rows.map((row, i) => (
                      <div key={i} className="p-2.5 flex items-center justify-between font-mono">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-theme-text">{row.symbol}</span>
                          <span className="text-theme-text-muted text-[11px]">{row.instrument_name}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-theme-text-muted">{row.price_type}</span>
                          <span className="font-bold text-emerald-400">₹{parseFloat(row.value).toFixed(2)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-theme-border shrink-0">
          {preview ? (
            <button
              type="button"
              onClick={() => setPreview(null)}
              disabled={isLoading}
              className="text-xs text-theme-text-muted hover:text-theme-text font-medium"
            >
              ← Back to upload
            </button>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl border border-theme-border text-xs font-semibold text-theme-text hover:bg-theme-hover"
            >
              Cancel
            </button>

            {!preview ? (
              <button
                type="button"
                onClick={handlePreview}
                disabled={isLoading || !csvText.trim()}
                className="px-4 py-2 rounded-xl bg-theme-primary text-white text-xs font-semibold hover:bg-theme-primary/90 flex items-center gap-1.5 shadow-sm disabled:opacity-50"
              >
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ChevronRight className="h-4 w-4" />}
                Validate & Preview
              </button>
            ) : (
              <button
                type="button"
                onClick={handleCommit}
                disabled={isLoading || preview.valid_count === 0}
                className="px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-500 flex items-center gap-1.5 shadow-sm disabled:opacity-50"
              >
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                Commit {preview.valid_count} Drafts
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
