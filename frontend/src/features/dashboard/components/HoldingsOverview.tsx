import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowUpDown,
  ExternalLink,
  Briefcase,
  Layers,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useDashboardHoldings } from '../hooks/useDashboard';
import { PriceFreshnessBadge } from '@/features/watchlists/components/PriceFreshnessBadge';

interface HoldingsOverviewProps {
  portfolioId?: string;
  className?: string;
}

const CATEGORIES = [
  { id: '', label: 'All Assets' },
  { id: 'equity', label: 'Equities' },
  { id: 'mutual_funds', label: 'Mutual Funds' },
  { id: 'fixed_income', label: 'Fixed Income' },
  { id: 'cash', label: 'Cash & Deposits' },
  { id: 'gold', label: 'Gold & Metals' },
  { id: 'crypto', label: 'Crypto' },
  { id: 'real_estate', label: 'Real Estate' },
];

export const HoldingsOverview: React.FC<HoldingsOverviewProps> = ({
  portfolioId,
  className = '',
}) => {
  const [category, setCategory] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('current_value');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState<number>(0);
  const limit = 10;

  const { data: holdingsData, isLoading, isError } = useDashboardHoldings({
    portfolioId,
    category: category || undefined,
    sortBy,
    order,
    limit,
    offset: page * limit,
  });

  const toggleSort = (newSort: string) => {
    if (sortBy === newSort) {
      setOrder(order === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(newSort);
      setOrder('desc');
    }
    setPage(0);
  };

  const formatAmount = (val?: string | number) => {
    if (val === undefined || val === null) return '0.00';
    const num = typeof val === 'string' ? parseFloat(val) : val;
    return isNaN(num) ? '0.00' : num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const totalPages = holdingsData ? Math.ceil(holdingsData.count / limit) : 1;

  return (
    <div className={`rounded-2xl border border-theme-border bg-theme-surface p-5 shadow-sm ${className}`}>
      {/* Header and Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-theme-border/60">
        <div>
          <h2 className="text-sm font-bold tracking-tight text-theme-text flex items-center gap-1.5">
            <Layers className="h-4 w-4 text-theme-primary" />
            <span>Investment Holdings</span>
          </h2>
          <p className="text-xs text-theme-text-muted mt-0.5">
            Authoritative values, cost bases, and returns across your holdings
          </p>
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              type="button"
              onClick={() => {
                setCategory(cat.id);
                setPage(0);
              }}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg whitespace-nowrap transition-all ${
                category === cat.id
                  ? 'bg-theme-primary text-theme-text-inverse shadow-sm'
                  : 'bg-theme-bg text-theme-text-muted hover:text-theme-text hover:bg-theme-hover border border-theme-border/60'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Holdings Content */}
      {isLoading ? (
        <div className="py-16 text-center text-xs text-theme-text-muted animate-pulse">
          Loading investment holdings...
        </div>
      ) : isError || !holdingsData || holdingsData.results.length === 0 ? (
        <div className="py-16 flex flex-col items-center justify-center text-center">
          <Briefcase className="h-8 w-8 text-theme-text-muted/40 mb-2" />
          <span className="text-xs font-semibold text-theme-text">No Holdings Found</span>
          <span className="text-[11px] text-theme-text-muted mt-1 max-w-xs">
            {category
              ? 'No investments in this asset category. Try selecting All Assets.'
              : 'You have not added any investments to this portfolio yet.'}
          </span>
        </div>
      ) : (
        <div className="mt-3">
          {/* Desktop Table View */}
          <div className="hidden lg:block overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-theme-border/60 text-[11px] text-theme-text-muted uppercase font-semibold">
                  <th
                    className="pb-3 cursor-pointer hover:text-theme-text"
                    onClick={() => toggleSort('display_name')}
                  >
                    <div className="flex items-center gap-1">
                      <span>Investment</span>
                      <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </th>
                  <th className="pb-3">Portfolio</th>
                  <th
                    className="pb-3 text-right cursor-pointer hover:text-theme-text"
                    onClick={() => toggleSort('invested_capital')}
                  >
                    <div className="flex items-center justify-end gap-1">
                      <span>Invested</span>
                      <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </th>
                  <th
                    className="pb-3 text-right cursor-pointer hover:text-theme-text"
                    onClick={() => toggleSort('current_value')}
                  >
                    <div className="flex items-center justify-end gap-1">
                      <span>Current Value</span>
                      <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </th>
                  <th
                    className="pb-3 text-right cursor-pointer hover:text-theme-text"
                    onClick={() => toggleSort('gain_loss')}
                  >
                    <div className="flex items-center justify-end gap-1">
                      <span>Return</span>
                      <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </th>
                  <th className="pb-3 text-center">Freshness</th>
                  <th className="pb-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-theme-border/40">
                {holdingsData.results.map((holding) => {
                  const absGain = parseFloat(holding.absolute_gain_loss);
                  const isPos = absGain > 0;
                  const isNeg = absGain < 0;
                  const returnColor = isPos
                    ? 'text-emerald-400'
                    : isNeg
                    ? 'text-rose-400'
                    : 'text-theme-text-muted';

                  return (
                    <tr key={holding.id} className="hover:bg-theme-hover/40 transition-colors">
                      {/* Name & Asset Type */}
                      <td className="py-3 pr-3">
                        <div className="font-semibold text-theme-text truncate max-w-xs">
                          {holding.display_name}
                        </div>
                        <div className="text-[10px] text-theme-text-muted flex items-center gap-1.5 mt-0.5">
                          <span className="capitalize">{holding.category.replace('_', ' ')}</span>
                          {holding.quantity && (
                            <span>• {holding.quantity} units</span>
                          )}
                        </div>
                      </td>

                      {/* Portfolio */}
                      <td className="py-3 px-2 text-theme-text-muted">
                        <span className="inline-block px-2 py-0.5 rounded-md bg-theme-bg border border-theme-border/60 text-[11px] font-medium text-theme-text">
                          {holding.portfolio_name}
                        </span>
                      </td>

                      {/* Invested Capital */}
                      <td className="py-3 px-2 text-right font-medium text-theme-text-muted">
                        {holding.currency} {formatAmount(holding.invested_capital)}
                      </td>

                      {/* Current Value */}
                      <td className="py-3 px-2 text-right font-bold text-theme-text">
                        {holding.currency} {formatAmount(holding.current_value)}
                      </td>

                      {/* Return (Gain/Loss) */}
                      <td className="py-3 px-2 text-right">
                        <div className={`font-semibold ${returnColor}`}>
                          {isPos ? `+${formatAmount(holding.absolute_gain_loss)}` : formatAmount(holding.absolute_gain_loss)}
                        </div>
                        <div className={`text-[10px] font-medium ${returnColor}`}>
                          {holding.gain_loss_percentage !== null
                            ? `${isPos ? '+' : ''}${parseFloat(holding.gain_loss_percentage).toFixed(2)}%`
                            : 'N/A'}
                        </div>
                      </td>

                      {/* Price Freshness Badge */}
                      <td className="py-3 px-2 text-center">
                        <PriceFreshnessBadge
                          status={holding.price_freshness as any}
                          effectiveAt={holding.valuation_date}
                        />
                      </td>

                      {/* Link to detail */}
                      <td className="py-3 pl-2 text-right">
                        <Link
                          to={`/investments/${holding.id}`}
                          className="inline-flex items-center gap-1 text-[11px] font-semibold text-theme-primary hover:underline"
                        >
                          <span>Details</span>
                          <ExternalLink className="h-3 w-3" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile Card View */}
          <div className="lg:hidden space-y-3">
            {holdingsData.results.map((holding) => {
              const absGain = parseFloat(holding.absolute_gain_loss);
              const isPos = absGain > 0;
              const isNeg = absGain < 0;
              const returnColor = isPos
                ? 'text-emerald-400'
                : isNeg
                ? 'text-rose-400'
                : 'text-theme-text-muted';

              return (
                <div
                  key={holding.id}
                  className="rounded-xl border border-theme-border/60 bg-theme-bg/60 p-4 space-y-2.5"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="font-semibold text-theme-text text-sm">
                        {holding.display_name}
                      </div>
                      <div className="text-[10px] text-theme-text-muted mt-0.5">
                        {holding.portfolio_name} • {holding.category.replace('_', ' ')}
                      </div>
                    </div>
                    <PriceFreshnessBadge
                      status={holding.price_freshness as any}
                      effectiveAt={holding.valuation_date}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-theme-border/40">
                    <div>
                      <span className="text-[10px] text-theme-text-muted block uppercase">Invested</span>
                      <span className="font-medium text-theme-text-muted">
                        {holding.currency} {formatAmount(holding.invested_capital)}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-theme-text-muted block uppercase">Current Value</span>
                      <span className="font-bold text-theme-text">
                        {holding.currency} {formatAmount(holding.current_value)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-theme-border/40 text-xs">
                    <span className="text-[11px] text-theme-text-muted">Unrealized Return:</span>
                    <span className={`font-bold ${returnColor}`}>
                      {isPos ? `+${formatAmount(holding.absolute_gain_loss)}` : formatAmount(holding.absolute_gain_loss)}
                      {holding.gain_loss_percentage && ` (${isPos ? '+' : ''}${parseFloat(holding.gain_loss_percentage).toFixed(2)}%)`}
                    </span>
                  </div>

                  <div className="pt-1 text-right">
                    <Link
                      to={`/investments/${holding.id}`}
                      className="text-xs font-semibold text-theme-primary inline-flex items-center gap-1 hover:underline"
                    >
                      <span>View Investment</span>
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 mt-2 border-t border-theme-border/40 text-xs text-theme-text-muted">
              <span>
                Showing {page * limit + 1}–{Math.min((page + 1) * limit, holdingsData.count)} of {holdingsData.count} holdings
              </span>

              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  className="p-1.5 rounded-lg border border-theme-border bg-theme-surface text-theme-text disabled:opacity-40 disabled:cursor-not-allowed hover:bg-theme-hover"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
                <span className="font-semibold px-2">
                  Page {page + 1} of {totalPages}
                </span>
                <button
                  type="button"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => p + 1)}
                  className="p-1.5 rounded-lg border border-theme-border bg-theme-surface text-theme-text disabled:opacity-40 disabled:cursor-not-allowed hover:bg-theme-hover"
                >
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
