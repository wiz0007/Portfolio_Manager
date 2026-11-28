import React from 'react';
import { ArrowUpRight, ArrowDownRight, RefreshCw } from 'lucide-react';
import { DemoBadge } from './DemoBadge';
import { MarketQuote } from '../types';

interface QuoteCardProps {
  symbol: string;
  name?: string;
  exchange?: string;
  quote?: MarketQuote | null;
  marketCap?: string | null;
  volume24h?: string | null;
  fundHouse?: string | null;
  planType?: string | null;
  optionType?: string | null;
  isLoading?: boolean;
  onRefresh?: () => void;
  onSelect?: () => void;
  className?: string;
}

export const QuoteCard: React.FC<QuoteCardProps> = ({
  symbol,
  name,
  exchange,
  quote,
  marketCap,
  volume24h,
  fundHouse,
  planType,
  optionType,
  isLoading = false,
  onRefresh,
  onSelect,
  className = '',
}) => {
  const hasValidPrice = quote?.price != null && quote.price !== '' && !isNaN(parseFloat(quote.price));
  const priceNum = hasValidPrice ? parseFloat(quote!.price!) : null;
  const hasValidChange = quote?.change_percent != null && quote.change_percent !== '' && !isNaN(parseFloat(quote.change_percent));
  const changePct = hasValidChange ? parseFloat(quote!.change_percent!) : null;
  const isPositive = changePct !== null ? changePct >= 0 : true;

  const formattedPrice = priceNum !== null
    ? new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: quote?.currency || 'INR',
        maximumFractionDigits: priceNum < 1 && priceNum > 0 ? 4 : 2,
      }).format(priceNum)
    : '—';

  return (
    <div
      onClick={onSelect}
      className={`group relative p-4 rounded-xl border border-theme-border bg-theme-surface hover:border-theme-primary/40 hover:bg-theme-hover/40 transition-all duration-200 shadow-sm ${
        onSelect ? 'cursor-pointer' : ''
      } ${className}`}
    >
      {/* Header: Symbol, Exchange & Demo Badge */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-base tracking-tight text-theme-text group-hover:text-theme-primary transition-colors truncate">
              {symbol}
            </h3>
            {exchange && (
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-theme-bg-subtle text-theme-text-muted border border-theme-border/50 uppercase">
                {exchange}
              </span>
            )}
          </div>
          {name && (
            <p className="text-xs text-theme-text-muted truncate mt-0.5 max-w-[200px]" title={name}>
              {name}
            </p>
          )}
        </div>

        {quote?.is_synthetic && <DemoBadge size="sm" />}
      </div>

      {/* Main Metric: Price & Change */}
      <div className="mt-3 flex items-baseline justify-between gap-2">
        <div className="text-xl sm:text-2xl font-bold tracking-tight text-theme-text">
          {isLoading ? (
            <div className="h-7 w-24 bg-theme-border/40 animate-pulse rounded" />
          ) : (
            formattedPrice
          )}
        </div>

        {hasValidChange && (
          <div
            className={`flex items-center text-xs font-semibold px-2 py-0.5 rounded-full ${
              isPositive
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
            }`}
          >
            {isPositive ? (
              <ArrowUpRight className="h-3.5 w-3.5 mr-0.5 shrink-0" />
            ) : (
              <ArrowDownRight className="h-3.5 w-3.5 mr-0.5 shrink-0" />
            )}
            <span>
              {isPositive ? '+' : ''}
              {changePct!.toFixed(2)}%
            </span>
          </div>
        )}
      </div>

      {/* Optional Metadata: Crypto or Mutual Funds */}
      {(marketCap || volume24h || fundHouse || planType || optionType) && (
        <div className="mt-2.5 flex flex-wrap gap-1.5 text-[10px]">
          {marketCap && (
            <span className="px-1.5 py-0.5 rounded bg-theme-bg-subtle text-theme-text-muted border border-theme-border/40">
              MCap: {marketCap}
            </span>
          )}
          {volume24h && (
            <span className="px-1.5 py-0.5 rounded bg-theme-bg-subtle text-theme-text-muted border border-theme-border/40">
              Vol: {volume24h}
            </span>
          )}
          {fundHouse && (
            <span className="px-1.5 py-0.5 rounded bg-theme-bg-subtle text-theme-text-muted border border-theme-border/40 truncate max-w-[140px]" title={fundHouse}>
              {fundHouse}
            </span>
          )}
          {planType && (
            <span className="px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
              {planType}
            </span>
          )}
          {optionType && (
            <span className="px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
              {optionType}
            </span>
          )}
        </div>
      )}

      {/* Intraday Range / Details */}
      {quote && (quote.high_price || quote.volume) && (
        <div className="mt-3 pt-3 border-t border-theme-border/50 flex items-center justify-between text-[11px] text-theme-text-muted">
          {quote.high_price && quote.low_price ? (
            <div>
              <span className="text-theme-text-muted/70">Range: </span>
              <span>₹{parseFloat(quote.low_price).toFixed(1)} - ₹{parseFloat(quote.high_price).toFixed(1)}</span>
            </div>
          ) : (
            <div />
          )}

          {quote.volume ? (
            <div>
              <span className="text-theme-text-muted/70">Vol: </span>
              <span>{(quote.volume / 1000).toFixed(0)}k</span>
            </div>
          ) : null}
        </div>
      )}

      {/* Refresh Action (optional) */}
      {onRefresh && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRefresh();
          }}
          disabled={isLoading}
          aria-label="Refresh quote"
          className="absolute top-3 right-3 p-1 rounded-md text-theme-text-muted hover:text-theme-text hover:bg-theme-bg opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      )}
    </div>
  );
};
