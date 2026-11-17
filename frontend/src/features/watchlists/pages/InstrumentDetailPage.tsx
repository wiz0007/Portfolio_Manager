import React, { useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  PlusCircle,
  Eye,
  Trash2,
  Building2,
  Calendar,
  Layers,
  CheckCircle2,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { marketDataApi } from '@/features/market-data/api/marketDataApi';
import {
  useWatchlist,
  useAddWatchlistItem,
  useRemoveWatchlistItem,
  useInstrumentLatestPrice,
  useInstrumentMarketStatus,
} from '../hooks/useWatchlist';
import { PriceFreshnessBadge } from '../components/PriceFreshnessBadge';
import { PriceMovement } from '../components/PriceMovement';
import { InstrumentPriceChart } from '../components/InstrumentPriceChart';
import { Button } from '@/shared/ui/Button';

export const InstrumentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Fetch canonical instrument
  const { data: instrument, isLoading: isInstrumentLoading } = useQuery({
    queryKey: ['instrument-detail', id],
    queryFn: () => marketDataApi.getInstrument(id!),
    enabled: !!id,
  });

  // Fetch resolved latest market data
  const { data: latestData, isLoading: isPriceLoading } = useInstrumentLatestPrice(id || '');

  // Fetch market coverage status
  const { data: marketStatus } = useInstrumentMarketStatus(id || '');

  // Check if item is already in current user's watchlist
  const { data: watchlistItems = [] } = useWatchlist();
  const existingWatchlistItem = useMemo(() => {
    return watchlistItems.find((item) => item.instrument.id === id);
  }, [watchlistItems, id]);

  const addMutation = useAddWatchlistItem();
  const removeMutation = useRemoveWatchlistItem();

  if (isInstrumentLoading) {
    return (
      <div className="p-12 text-center text-sm text-theme-text-muted">
        Loading instrument details...
      </div>
    );
  }

  if (!instrument) {
    return (
      <div className="p-12 text-center space-y-4">
        <h2 className="text-lg font-bold text-theme-text">Instrument Not Found</h2>
        <p className="text-sm text-theme-text-muted">
          The requested instrument does not exist or has been retired.
        </p>
        <Button variant="outline" onClick={() => navigate('/watchlist')}>
          Back to Watchlist
        </Button>
      </div>
    );
  }

  const priceNum = latestData?.price ? parseFloat(latestData.price) : null;

  const handleWatchlistToggle = () => {
    if (existingWatchlistItem) {
      removeMutation.mutate(existingWatchlistItem.id);
    } else {
      addMutation.mutate({ instrument_id: instrument.id });
    }
  };

  const isTogglingWatchlist = addMutation.isPending || removeMutation.isPending;

  return (
    <div className="space-y-6 animate-fade-in max-w-6xl mx-auto">
      {/* Navigation and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-theme-text-muted hover:text-theme-text transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back</span>
        </button>

        <div className="flex items-center gap-2">
          {/* Watchlist Toggle */}
          <Button
            variant={existingWatchlistItem ? 'outline' : 'secondary'}
            onClick={handleWatchlistToggle}
            disabled={isTogglingWatchlist}
            leftIcon={
              existingWatchlistItem ? (
                <Trash2 className="h-4 w-4 text-rose-400" />
              ) : (
                <Eye className="h-4 w-4 text-theme-primary" />
              )
            }
          >
            {existingWatchlistItem ? 'Remove from Watchlist' : 'Add to Watchlist'}
          </Button>

          {/* Add to Portfolio / Invest CTA */}
          <Link to={`/investments/new?instrument_id=${instrument.id}`}>
            <Button
              variant="primary"
              leftIcon={<PlusCircle className="h-4 w-4" />}
            >
              Add to Portfolio
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Hero Header */}
      <div className="rounded-3xl border border-theme-border bg-theme-surface p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Left: Identity */}
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-extrabold text-2xl sm:text-3xl text-theme-text tracking-tight">
                {instrument.symbol}
              </span>
              {instrument.exchange && (
                <span className="text-xs font-bold px-2 py-0.5 rounded-lg bg-theme-bg text-theme-text-muted border border-theme-border uppercase tracking-wide">
                  {instrument.exchange}
                </span>
              )}
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-lg bg-theme-primary-subtle text-theme-primary border border-theme-primary/30 uppercase tracking-wide">
                {instrument.asset_class}
              </span>
              {latestData && (
                <PriceFreshnessBadge
                  status={latestData.status}
                  isSynthetic={latestData.is_synthetic}
                  effectiveAt={latestData.effective_at}
                />
              )}
            </div>

            <h1 className="text-base sm:text-lg text-theme-text-muted font-medium">
              {instrument.name}
            </h1>

            {/* Identifiers pills */}
            <div className="flex flex-wrap items-center gap-3 text-xs text-theme-text-muted pt-1">
              {instrument.isin && (
                <span className="font-mono bg-theme-bg px-2 py-0.5 rounded border border-theme-border">
                  ISIN: {instrument.isin}
                </span>
              )}
              {instrument.scheme_code && (
                <span className="font-mono bg-theme-bg px-2 py-0.5 rounded border border-theme-border">
                  Scheme: {instrument.scheme_code}
                </span>
              )}
              {instrument.currency && (
                <span className="bg-theme-bg px-2 py-0.5 rounded border border-theme-border">
                  Currency: {instrument.currency}
                </span>
              )}
            </div>
          </div>

          {/* Right: Latest Price Hero */}
          <div className="bg-theme-bg p-5 rounded-2xl border border-theme-border flex flex-col items-start lg:items-end min-w-[220px]">
            <div className="text-[11px] font-semibold text-theme-text-muted uppercase tracking-wider">
              Latest Published Price
            </div>
            <div className="text-3xl font-extrabold text-theme-text mt-1">
              {isPriceLoading ? (
                '--'
              ) : priceNum !== null ? (
                `₹${priceNum.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 4 })}`
              ) : (
                'Unavailable'
              )}
            </div>

            {latestData?.movement && (
              <div className="mt-1">
                <PriceMovement movement={latestData.movement} currency={instrument.currency} />
              </div>
            )}

            {latestData?.effective_at && (
              <div className="text-[10px] text-theme-text-muted mt-2">
                As of {new Date(latestData.effective_at).toLocaleString()}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Historical Timeseries Chart */}
      <InstrumentPriceChart
        instrumentId={instrument.id}
        symbol={instrument.symbol}
        currency="₹"
      />

      {/* Instrument Reference and Metadata Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Market Coverage Policy */}
        <div className="rounded-2xl border border-theme-border bg-theme-surface p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 text-theme-text font-bold text-sm border-b border-theme-border/60 pb-3">
            <Layers className="h-4 w-4 text-theme-primary" />
            <span>Pricing Policy & Coverage</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-1.5 border-b border-theme-border/40">
              <span className="text-theme-text-muted">Observation Source</span>
              <span className="font-semibold text-theme-text">
                {latestData?.source || 'Central Market-Data Repository'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-theme-border/40">
              <span className="text-theme-text-muted">Freshness Threshold</span>
              <span className="font-semibold text-theme-text">
                {marketStatus?.freshness_hours ? `${marketStatus.freshness_hours} hours` : 'Trading Session Close'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-theme-border/40">
              <span className="text-theme-text-muted">Price Type</span>
              <span className="font-semibold text-theme-text">
                {marketStatus?.price_type || 'Last Traded Price (LTP)'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-theme-border/40">
              <span className="text-theme-text-muted">Quotation Unit</span>
              <span className="font-semibold text-theme-text">
                {marketStatus?.quotation_unit || 'Per Unit'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5">
              <span className="text-theme-text-muted">Provenance Integrity</span>
              <span className="font-semibold text-theme-text">
                {latestData?.is_synthetic ? 'Synthetic Demo Provider' : 'Verified Publisher Ledger'}
              </span>
            </div>
          </div>
        </div>

        {/* Fundamental Reference Data */}
        <div className="rounded-2xl border border-theme-border bg-theme-surface p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 text-theme-text font-bold text-sm border-b border-theme-border/60 pb-3">
            <Building2 className="h-4 w-4 text-theme-primary" />
            <span>Catalogue Metadata</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-1.5 border-b border-theme-border/40">
              <span className="text-theme-text-muted">Product Type</span>
              <span className="font-semibold text-theme-text capitalize">
                {instrument.product_type || 'Standard'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-theme-border/40">
              <span className="text-theme-text-muted">Trading Status</span>
              <span className="font-semibold text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>{instrument.status}</span>
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-theme-border/40">
              <span className="text-theme-text-muted">Registered Exchange</span>
              <span className="font-semibold text-theme-text">
                {instrument.exchange || 'National Stock Exchange (NSE)'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5">
              <span className="text-theme-text-muted">Catalogue Addition</span>
              <span className="font-semibold text-theme-text flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5 text-theme-text-muted" />
                <span>Verified</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
