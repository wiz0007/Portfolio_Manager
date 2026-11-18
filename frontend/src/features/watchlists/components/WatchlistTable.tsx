import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Trash2, ExternalLink, PlusCircle, BellRing } from 'lucide-react';
import { WatchlistItem } from '../types';
import { PriceFreshnessBadge } from './PriceFreshnessBadge';
import { PriceMovement } from './PriceMovement';

interface WatchlistTableProps {
  items: WatchlistItem[];
  onRemove: (id: string, symbol: string) => void;
  isRemoving?: string | null;
}

const CURRENCY_SYMBOLS: Record<string, string> = {
  INR: '₹',
  USD: '$',
  EUR: '€',
  GBP: '£',
};

const getCurrencySymbol = (currency?: string): string => {
  if (!currency) return '₹';
  return CURRENCY_SYMBOLS[currency.toUpperCase()] || `${currency} `;
};

export const WatchlistTable: React.FC<WatchlistTableProps> = ({
  items,
  onRemove,
  isRemoving = null,
}) => {
  const navigate = useNavigate();

  return (
    <div className="overflow-x-auto rounded-2xl border border-theme-border bg-theme-surface shadow-sm">
      <table className="w-full text-left border-collapse text-sm text-theme-text">
        <thead>
          <tr className="border-b border-theme-border/70 bg-theme-bg/60 text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
            <th className="py-3.5 px-4">Instrument</th>
            <th className="py-3.5 px-4">Market</th>
            <th className="py-3.5 px-4 text-right">Latest Price</th>
            <th className="py-3.5 px-4 text-right">Session Movement</th>
            <th className="py-3.5 px-4 text-center">Status</th>
            <th className="py-3.5 px-4">Target Alert</th>
            <th className="py-3.5 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-theme-border/50">
          {items.map((item) => {
            const inst = item.instrument;
            const md = item.market_data;
            const priceNum = md.price ? parseFloat(md.price) : null;
            const targetNum = item.target_price ? parseFloat(item.target_price) : null;
            const isRemovingThis = isRemoving === item.id;
            const currSymbol = getCurrencySymbol(inst.currency);

            return (
              <tr
                key={item.id}
                className="hover:bg-theme-hover/40 transition-colors group cursor-pointer"
                onClick={() => navigate(`/instruments/${inst.id}`)}
              >
                {/* Instrument */}
                <td className="py-3.5 px-4">
                  <div className="flex flex-col">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-theme-text tracking-tight group-hover:text-theme-primary transition-colors">
                        {inst.symbol}
                      </span>
                      <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-theme-bg text-theme-text-muted border border-theme-border">
                        {inst.asset_class}
                      </span>
                    </div>
                    <span className="text-xs text-theme-text-muted truncate max-w-xs mt-0.5">
                      {inst.name}
                    </span>
                  </div>
                </td>

                {/* Market & Exchange */}
                <td className="py-3.5 px-4">
                  <div className="flex flex-col">
                    <span className="text-xs font-medium text-theme-text">
                      {inst.exchange || 'Canonical'}
                    </span>
                    {inst.sector && (
                      <span className="text-[11px] text-theme-text-muted truncate max-w-[140px]">
                        {inst.sector}
                      </span>
                    )}
                  </div>
                </td>

                {/* Latest Price */}
                <td className="py-3.5 px-4 text-right">
                  <div className="flex flex-col items-end">
                    <span className="font-bold text-sm text-theme-text">
                      {priceNum !== null
                        ? `${currSymbol}${priceNum.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 4 })}`
                        : '--'}
                    </span>
                    <span className="text-[10px] text-theme-text-muted">
                      {md.unit !== 'UNITS' ? md.unit : inst.currency}
                    </span>
                  </div>
                </td>

                {/* Session Movement */}
                <td className="py-3.5 px-4 text-right">
                  <PriceMovement movement={md.movement} currency={inst.currency} />
                </td>

                {/* Status & Freshness */}
                <td className="py-3.5 px-4 text-center">
                  <PriceFreshnessBadge
                    status={md.status}
                    isSynthetic={md.is_synthetic}
                    effectiveAt={md.effective_at}
                    publishedAt={md.published_at}
                    ageSeconds={md.age_seconds}
                  />
                </td>

                {/* Target Alert */}
                <td className="py-3.5 px-4">
                  {targetNum !== null ? (
                    <div
                      className="flex items-center gap-1.5 text-xs font-semibold text-theme-primary"
                      title="Configured Price Target"
                    >
                      <BellRing className="h-3.5 w-3.5 shrink-0" />
                      <span>{currSymbol}{targetNum.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                    </div>
                  ) : (
                    <span className="text-xs text-theme-text-muted">None</span>
                  )}
                </td>

                {/* Actions */}
                <td
                  className="py-3.5 px-4 text-right"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="flex items-center justify-end gap-1.5">
                    {/* Add to Portfolio */}
                    <Link
                      to={`/investments/new?instrument_id=${inst.id}`}
                      className="p-1.5 rounded-lg text-theme-text-muted hover:text-theme-primary hover:bg-theme-primary-subtle transition-colors"
                      title="Add to Portfolio"
                      aria-label={`Invest in ${inst.symbol}`}
                    >
                      <PlusCircle className="h-4 w-4" />
                    </Link>

                    {/* View Detail */}
                    <Link
                      to={`/instruments/${inst.id}`}
                      className="p-1.5 rounded-lg text-theme-text-muted hover:text-theme-text hover:bg-theme-hover transition-colors"
                      title="View Instrument Details"
                      aria-label={`View ${inst.symbol} detail`}
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Link>

                    {/* Remove */}
                    <button
                      type="button"
                      disabled={isRemovingThis}
                      onClick={() => onRemove(item.id, inst.symbol)}
                      className="p-1.5 rounded-lg text-theme-text-muted hover:text-rose-400 hover:bg-rose-500/10 transition-colors disabled:opacity-50"
                      title="Remove from Watchlist"
                      aria-label={`Remove ${inst.symbol} from watchlist`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
