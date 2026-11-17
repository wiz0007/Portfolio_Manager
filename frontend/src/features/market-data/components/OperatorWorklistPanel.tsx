import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  FileSpreadsheet, 
  FileText, 
  Upload, 
  Plus, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Loader2 
} from 'lucide-react';
import { marketDataApi } from '../api/marketDataApi';
import { MarketDataWorklist, MarketDataWorklistItem, Instrument } from '../types';
import { ManualPriceEntryModal } from './ManualPriceEntryModal';
import { CsvImportModal } from './CsvImportModal';

export const OperatorWorklistPanel: React.FC = () => {
  const [worklist, setWorklist] = useState<MarketDataWorklist | null>(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedInstrument, setSelectedInstrument] = useState<Instrument | null>(null);
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);

  const loadWorklist = async (dateStr: string) => {
    setIsLoading(true);
    setError(null);
    try {
      let res: any;
      try {
        res = await marketDataApi.getDailyWorklist(dateStr);
      } catch (err: any) {
        if (err.response?.status === 404) {
          // If not generated yet, generate automatically
          res = await marketDataApi.generateDailyWorklist(dateStr);
        } else {
          throw err;
        }
      }
      setWorklist(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load daily market data worklist.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadWorklist(selectedDate);
  }, [selectedDate]);

  const handleDownload = (format: 'md' | 'csv') => {
    const url = `/api/v1/market-data/worklists/${selectedDate}/export-${format}/`;
    window.open(url, '_blank');
  };

  const getDueBadge = (reason: string) => {
    switch (reason) {
      case 'FIRST_PRICE':
        return <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">First Price</span>;
      case 'DUE_TODAY':
        return <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/20">Due Today</span>;
      case 'STALE':
        return <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">Stale</span>;
      case 'SKIPPED_HOLIDAY':
        return <span className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-theme-bg text-theme-text-muted border border-theme-border">Holiday / Off-Market</span>;
      default:
        return <span className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-theme-bg text-theme-text-muted border border-theme-border">{reason}</span>;
    }
  };

  const handleEnterPrice = (item: MarketDataWorklistItem) => {
    const instObj: Instrument = {
      id: item.instrument,
      symbol: item.symbol,
      name: item.canonical_name,
      asset_class: item.asset_class as any,
      exchange: item.exchange,
      currency: item.currency,
      isin: item.isin,
      is_active: true,
      created_at: '',
      updated_at: '',
    };
    setSelectedInstrument(instObj);
    setIsManualModalOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Header & Action Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl border border-theme-border bg-theme-surface">
        <div>
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-theme-primary" />
            <h2 className="text-base font-bold text-theme-text">Market Data Collection Worklist</h2>
          </div>
          <p className="text-xs text-theme-text-muted mt-1">
            Centrally scheduled instruments due for verification, manual quote entry, or CSV import.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-xs focus:outline-none focus:ring-2 focus:ring-theme-primary/40"
          />

          <button
            onClick={() => loadWorklist(selectedDate)}
            disabled={isLoading}
            className="p-2 rounded-xl border border-theme-border text-theme-text-muted hover:text-theme-text hover:bg-theme-hover"
            title="Refresh Worklist"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={() => handleDownload('md')}
            className="px-3 py-1.5 rounded-xl border border-theme-border bg-theme-bg hover:bg-theme-hover text-theme-text text-xs font-semibold flex items-center gap-1.5 shadow-sm"
          >
            <FileText className="h-3.5 w-3.5 text-theme-text-muted" />
            Export Markdown
          </button>

          <button
            onClick={() => handleDownload('csv')}
            className="px-3 py-1.5 rounded-xl border border-theme-border bg-theme-bg hover:bg-theme-hover text-theme-text text-xs font-semibold flex items-center gap-1.5 shadow-sm"
          >
            <FileSpreadsheet className="h-3.5 w-3.5 text-theme-text-muted" />
            Export CSV
          </button>

          <button
            onClick={() => setIsCsvModalOpen(true)}
            className="px-3.5 py-1.5 rounded-xl bg-theme-primary text-white text-xs font-semibold hover:bg-theme-primary/90 flex items-center gap-1.5 shadow-sm"
          >
            <Upload className="h-3.5 w-3.5" />
            Bulk CSV Import
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 flex items-start gap-3 text-sm text-rose-400">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Summary KPI Cards */}
      {worklist && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl border border-theme-border bg-theme-surface">
            <div className="text-xs text-theme-text-muted font-medium">Total Items Due</div>
            <div className="text-xl font-bold text-theme-text mt-1">{worklist.total_items}</div>
          </div>
          <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5">
            <div className="text-xs text-emerald-400 font-medium">Completed</div>
            <div className="text-xl font-bold text-emerald-400 mt-1">{worklist.completed_items}</div>
          </div>
          <div className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/5">
            <div className="text-xs text-amber-400 font-medium">Pending Collection</div>
            <div className="text-xl font-bold text-amber-400 mt-1">
              {worklist.total_items - worklist.completed_items}
            </div>
          </div>
          <div className="p-4 rounded-xl border border-theme-border bg-theme-surface">
            <div className="text-xs text-theme-text-muted font-medium">Worklist Status</div>
            <div className="text-sm font-bold text-theme-text mt-1 uppercase tracking-wider">
              {worklist.status}
            </div>
          </div>
        </div>
      )}

      {/* Worklist Items Table */}
      <div className="rounded-2xl border border-theme-border bg-theme-surface overflow-hidden shadow-sm">
        <div className="p-4 border-b border-theme-border flex items-center justify-between">
          <h3 className="text-sm font-bold text-theme-text">Collection Line Items</h3>
          <span className="text-xs text-theme-text-muted font-mono">{selectedDate}</span>
        </div>

        {isLoading ? (
          <div className="py-16 flex flex-col items-center justify-center">
            <Loader2 className="h-8 w-8 text-theme-primary animate-spin mb-2" />
            <span className="text-xs text-theme-text-muted">Loading collection schedule...</span>
          </div>
        ) : worklist?.items && worklist.items.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-theme-border bg-theme-bg/50 text-theme-text-muted font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-4">Instrument</th>
                  <th className="py-3 px-4">Asset Class</th>
                  <th className="py-3 px-4">Expected Price</th>
                  <th className="py-3 px-4">Due Reason</th>
                  <th className="py-3 px-4">Last Published</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-theme-border">
                {worklist.items.map((item) => (
                  <tr key={item.id} className="hover:bg-theme-hover/50 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-theme-text">{item.symbol}</div>
                      <div className="text-[11px] text-theme-text-muted truncate max-w-xs">{item.canonical_name}</div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-theme-bg text-theme-text-muted border border-theme-border">
                        {item.asset_class}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono">
                      {item.expected_price_type} ({item.unit})
                    </td>
                    <td className="py-3 px-4">
                      {getDueBadge(item.due_reason)}
                    </td>
                    <td className="py-3 px-4 font-mono text-theme-text-muted">
                      {item.last_published_price ? `₹${parseFloat(item.last_published_price).toFixed(2)}` : 'None'}
                    </td>
                    <td className="py-3 px-4">
                      {item.status === 'COMPLETED' ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                          <CheckCircle2 className="h-3.5 w-3.5" /> Published
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-amber-400 font-semibold text-[11px]">
                          <Clock className="h-3.5 w-3.5" /> Pending
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleEnterPrice(item)}
                        className="px-2.5 py-1 rounded-lg border border-theme-border bg-theme-bg hover:bg-theme-hover text-theme-text text-[11px] font-semibold inline-flex items-center gap-1"
                      >
                        <Plus className="h-3 w-3" /> Enter Price
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-sm text-theme-text-muted">
            No instruments scheduled for collection on {selectedDate}.
          </div>
        )}
      </div>

      <ManualPriceEntryModal
        isOpen={isManualModalOpen}
        onClose={() => setIsManualModalOpen(false)}
        instrument={selectedInstrument}
        onSuccess={() => loadWorklist(selectedDate)}
      />

      <CsvImportModal
        isOpen={isCsvModalOpen}
        onClose={() => setIsCsvModalOpen(false)}
        onSuccess={() => loadWorklist(selectedDate)}
      />
    </div>
  );
};
