import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Trash2, ExternalLink, PlusCircle, BellRing } from 'lucide-react';
import { WatchlistItem } from '../types';
import { PriceFreshnessBadge } from './PriceFreshnessBadge';
import { PriceMovement } from './PriceMovement';

interface WatchlistCardProps {
  item: WatchlistItem;
  onRemove: (id: string, symbol: string) => void;
  isRemoving?: boolean;
}

export const WatchlistCard: React.FC<WatchlistCardProps> = ({
  item,
  onRemove,
  isRemoving = false,
}) => {
  const navigate = useNavigate();
  const inst = item.instrument;
  const md = item.market_data;
  const priceNum = md.price ? parseFloat(md.price) : null;
  const targetNum = item.target_price ? parseFloat(item.target_price) : null;

  return (
    <div
      onClick={() => navigate(`/instruments/${inst.id}`)}
      className="rounded-2xl border border-theme-border bg-theme-surface p-4 shadow-sm hover:border-theme-primary/40 transition-all cursor-pointer space-y-3"
    >
      {/* Top row: Symbol, Name, Freshness Badge */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-bold text-base text-theme-text tracking-tight">
              {inst.symbol}
            </span>
            {inst.exchange && (
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-theme-bg text-theme-text-muted border border-theme-border uppercase">
                {inst.exchange}
              </span>
            )}
            <span className="text-[10px] uppercase font-semibold text-theme-primary">
              {inst.asset_class}
            </span>
          </div>
          <div className="text-xs text-theme-text-muted truncate mt-0.5">
            {inst.name}
          </div>
        </div>

        <PriceFreshnessBadge
          status={md.status}
          isSynthetic={md.is_synthetic}
          effectiveAt={md.effective_at}
        />
      </div>

      {/* Price and Movement Row */}
      <div className="flex items-end justify-between pt-1">
        <div>
          <div className="text-[10px] text-theme-text-muted uppercase font-medium">Latest Price</div>
          <div className="font-bold text-lg text-theme-text">
            {priceNum !== null
              ? `₹${priceNum.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 4 })}`
              : '--'}
          </div>
        </div>

        <div className="text-right">
          <div className="text-[10px] text-theme-text-muted uppercase font-medium">24h Movement</div>
          <PriceMovement movement={md.movement} currency={inst.currency} />
        </div>
      </div>

      {/* Target Price alert if configured */}
      {targetNum !== null && (
        <div className="flex items-center gap-1.5 text-xs font-semibold text-theme-primary pt-2 border-t border-theme-border/40">
          <BellRing className="h-3.5 w-3.5 shrink-0" />
          <span>Alert Target: ₹{targetNum.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
        </div>
      )}

      {/* Actions footer */}
      <div
        className="flex items-center justify-between pt-2 border-t border-theme-border/50 text-xs"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2">
          <Link
            to={`/investments/new?instrument_id=${inst.id}`}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-theme-primary-subtle text-theme-primary hover:bg-theme-primary/20 font-medium transition-colors"
          >
            <PlusCircle className="h-3.5 w-3.5" />
            <span>Invest</span>
          </Link>

          <Link
            to={`/instruments/${inst.id}`}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-theme-border text-theme-text-muted hover:text-theme-text hover:bg-theme-hover font-medium transition-colors"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            <span>Details</span>
          </Link>
        </div>

        <button
          type="button"
          disabled={isRemoving}
          onClick={() => onRemove(item.id, inst.symbol)}
          className="p-1.5 rounded-lg text-theme-text-muted hover:text-rose-400 hover:bg-rose-500/10 transition-colors disabled:opacity-50"
          aria-label={`Remove ${inst.symbol} from watchlist`}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};
