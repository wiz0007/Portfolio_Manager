import React from 'react';
import { Link } from 'react-router-dom';
import { Bookmark, ArrowRight } from 'lucide-react';
import { useDashboardWatchlistPreview } from '../hooks/useDashboard';
import { PriceFreshnessBadge } from '@/features/watchlists/components/PriceFreshnessBadge';
import { PriceMovement } from '@/features/watchlists/components/PriceMovement';

interface WatchlistPreviewProps {
  className?: string;
}

export const WatchlistPreview: React.FC<WatchlistPreviewProps> = ({
  className = '',
}) => {
  const { data: items, isLoading, isError } = useDashboardWatchlistPreview(5);

  if (isLoading) {
    return (
      <div className={`rounded-2xl border border-theme-border bg-theme-surface p-5 h-80 flex items-center justify-center animate-pulse ${className}`}>
        <span className="text-xs text-theme-text-muted">Loading watchlist preview...</span>
      </div>
    );
  }

  if (isError || !items) {
    return null;
  }

  const formatPrice = (val?: string | number | null) => {
    if (val === undefined || val === null) return '—';
    const num = typeof val === 'string' ? parseFloat(val) : val;
    return isNaN(num) ? '—' : num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  return (
    <div className={`rounded-2xl border border-theme-border bg-theme-surface p-5 shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-theme-border/60">
        <div>
          <h2 className="text-sm font-bold tracking-tight text-theme-text flex items-center gap-1.5">
            <Bookmark className="h-4 w-4 text-theme-primary" />
            <span>Watchlist Preview</span>
          </h2>
          <p className="text-xs text-theme-text-muted mt-0.5">
            Live market prices from your monitored catalogue
          </p>
        </div>

        <Link
          to="/watchlist"
          className="text-xs font-semibold text-theme-primary flex items-center gap-1 hover:underline"
        >
          <span>View All</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {items.length === 0 ? (
        <div className="py-12 flex flex-col items-center justify-center text-center">
          <Bookmark className="h-7 w-7 text-theme-text-muted/40 mb-2" />
          <span className="text-xs font-semibold text-theme-text">Watchlist is Empty</span>
          <span className="text-[11px] text-theme-text-muted mt-0.5 max-w-xs">
            Monitor stocks and funds independently of owning them in a portfolio.
          </span>
          <Link
            to="/watchlist"
            className="mt-3 text-xs font-semibold px-3 py-1.5 rounded-lg bg-theme-primary text-theme-text-inverse hover:bg-theme-primary-hover shadow-sm transition-all"
          >
            Explore Catalogue
          </Link>
        </div>
      ) : (
        <div className="divide-y divide-theme-border/40 mt-1">
          {items.map((item) => {
            const inst = item.instrument;
            const md = item.market_data;

            return (
              <div
                key={item.id}
                className="py-3 flex items-center justify-between gap-3 hover:bg-theme-hover/30 transition-colors px-1 rounded-lg"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-xs text-theme-text truncate">
                      {inst.symbol}
                    </span>
                    <span className="text-[10px] text-theme-text-muted">
                      ({inst.exchange || inst.asset_class})
                    </span>
                  </div>
                  <div className="text-[11px] text-theme-text-muted truncate max-w-xs mt-0.5">
                    {inst.name}
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <div className="font-bold text-xs text-theme-text flex items-center justify-end gap-1.5">
                    <span>{inst.currency} {formatPrice(md?.price)}</span>
                    <PriceFreshnessBadge
                      status={md?.status as any}
                      isSynthetic={md?.is_synthetic}
                      effectiveAt={md?.effective_at}
                    />
                  </div>

                  {md?.movement && (
                    <div className="mt-0.5 flex justify-end">
                      <PriceMovement
                        movement={md.movement}
                        currency={inst.currency}
                      />
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
