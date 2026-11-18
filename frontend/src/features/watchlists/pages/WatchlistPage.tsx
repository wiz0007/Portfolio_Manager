import React, { useState, useMemo } from 'react';
import {
  Eye,
  Plus,
  Search,
  Loader2,
  TrendingUp,
  TrendingDown,
  BellRing,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { useWatchlist, useRemoveWatchlistItem } from '../hooks/useWatchlist';
import { WatchlistTable } from '../components/WatchlistTable';
import { WatchlistCard } from '../components/WatchlistCard';
import { WatchlistEmptyState } from '../components/WatchlistEmptyState';
import { AddToWatchlistModal } from '../components/AddToWatchlistModal';
import { Button } from '@/shared/ui/Button';

export const WatchlistPage: React.FC = () => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAssetClass, setSelectedAssetClass] = useState<string>('ALL');
  const [removingId, setRemovingId] = useState<string | null>(null);

  const { data: watchlistItems = [], isLoading, isError, refetch, isFetching } = useWatchlist();
  const removeMutation = useRemoveWatchlistItem();

  // Summary Metrics
  const summaryMetrics = useMemo(() => {
    let gainers = 0;
    let losers = 0;
    let alerts = 0;

    watchlistItems.forEach((item) => {
      if (item.target_price) alerts += 1;
      const pct = item.market_data.movement?.change_percent;
      if (pct) {
        const val = parseFloat(pct);
        if (val > 0) gainers += 1;
        else if (val < 0) losers += 1;
      }
    });

    return { total: watchlistItems.length, gainers, losers, alerts };
  }, [watchlistItems]);

  // Unique Asset Classes
  const assetClasses = useMemo(() => {
    const set = new Set<string>();
    watchlistItems.forEach((item) => {
      if (item.instrument.asset_class) {
        set.add(item.instrument.asset_class);
      }
    });
    return ['ALL', ...Array.from(set)];
  }, [watchlistItems]);

  // Filtered Items
  const filteredItems = useMemo(() => {
    return watchlistItems.filter((item) => {
      const inst = item.instrument;
      const matchesSearch =
        !searchQuery.trim() ||
        inst.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        inst.name.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesClass =
        selectedAssetClass === 'ALL' || inst.asset_class === selectedAssetClass;

      return matchesSearch && matchesClass;
    });
  }, [watchlistItems, searchQuery, selectedAssetClass]);

  const handleRemove = (id: string, symbol: string) => {
    if (window.confirm(`Are you sure you want to remove ${symbol} from your watchlist?`)) {
      setRemovingId(id);
      removeMutation.mutate(id, {
        onSettled: () => setRemovingId(null),
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-theme-primary-subtle text-theme-primary border border-theme-primary/30">
              <Eye className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-theme-text">Market Watchlist</h1>
              <p className="text-sm text-theme-text-muted">
                Track assets with verified central market prices and freshness guarantees
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            leftIcon={<RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />}
            title="Refresh prices"
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            onClick={() => setIsAddModalOpen(true)}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Add Instrument
          </Button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-theme-border bg-theme-surface p-4 shadow-sm">
          <div className="text-xs font-medium text-theme-text-muted uppercase">Watched Assets</div>
          <div className="text-2xl font-bold text-theme-text mt-1">{summaryMetrics.total}</div>
        </div>

        <div className="rounded-2xl border border-theme-border bg-theme-surface p-4 shadow-sm">
          <div className="flex items-center gap-1.5 text-xs font-medium text-theme-text-muted uppercase">
            <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
            <span>24h Gainers</span>
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{summaryMetrics.gainers}</div>
        </div>

        <div className="rounded-2xl border border-theme-border bg-theme-surface p-4 shadow-sm">
          <div className="flex items-center gap-1.5 text-xs font-medium text-theme-text-muted uppercase">
            <TrendingDown className="h-3.5 w-3.5 text-rose-400" />
            <span>24h Decliners</span>
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-1">{summaryMetrics.losers}</div>
        </div>

        <div className="rounded-2xl border border-theme-border bg-theme-surface p-4 shadow-sm">
          <div className="flex items-center gap-1.5 text-xs font-medium text-theme-text-muted uppercase">
            <BellRing className="h-3.5 w-3.5 text-theme-primary" />
            <span>Target Alerts</span>
          </div>
          <div className="text-2xl font-bold text-theme-primary mt-1">{summaryMetrics.alerts}</div>
        </div>
      </div>

      {/* Search and Filters Bar */}
      {watchlistItems.length > 0 && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-theme-surface p-3.5 rounded-2xl border border-theme-border shadow-sm">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-theme-text-muted pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter by symbol or name..."
              className="w-full pl-9 pr-4 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text placeholder:text-theme-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/40"
            />
          </div>

          {/* Asset Class Filter Chips */}
          {assetClasses.length > 2 && (
            <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
              {assetClasses.map((ac) => (
                <button
                  key={ac}
                  type="button"
                  onClick={() => setSelectedAssetClass(ac)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-xl whitespace-nowrap transition-colors ${
                    selectedAssetClass === ac
                      ? 'bg-theme-primary text-theme-primary-contrast shadow-sm'
                      : 'text-theme-text-muted hover:text-theme-text bg-theme-bg hover:bg-theme-hover border border-theme-border'
                  }`}
                >
                  {ac}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Content Area */}
      {isLoading ? (
        <div className="rounded-2xl border border-theme-border bg-theme-surface p-12 text-center flex flex-col items-center justify-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-theme-primary" />
          <p className="text-sm text-theme-text-muted">Resolving latest verified market prices...</p>
        </div>
      ) : isError ? (
        <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-8 text-center text-rose-400 space-y-3">
          <AlertCircle className="h-8 w-8 mx-auto" />
          <h3 className="text-base font-semibold">Failed to load watchlist</h3>
          <p className="text-xs text-rose-300 max-w-md mx-auto">
            Unable to connect to the market-data price resolver. Please check your connection.
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      ) : watchlistItems.length === 0 ? (
        <WatchlistEmptyState onAddClick={() => setIsAddModalOpen(true)} />
      ) : filteredItems.length === 0 ? (
        <WatchlistEmptyState
          onAddClick={() => setIsAddModalOpen(true)}
          isFiltered={true}
          onClearFilter={() => {
            setSearchQuery('');
            setSelectedAssetClass('ALL');
          }}
        />
      ) : (
        <>
          {/* Desktop Table View */}
          <div className="hidden md:block">
            <WatchlistTable
              items={filteredItems}
              onRemove={handleRemove}
              isRemoving={removingId}
            />
          </div>

          {/* Mobile Card List View */}
          <div className="grid grid-cols-1 gap-3 md:hidden">
            {filteredItems.map((item) => (
              <WatchlistCard
                key={item.id}
                item={item}
                onRemove={handleRemove}
                isRemoving={removingId === item.id}
              />
            ))}
          </div>
        </>
      )}

      {/* Add to Watchlist Modal */}
      <AddToWatchlistModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
      />
    </div>
  );
};
