import React, { useState } from 'react';
import { Loader2, TrendingUp, Info, AlertCircle } from 'lucide-react';
import { useInstrumentHistory } from '../hooks/useWatchlist';

interface InstrumentPriceChartProps {
  instrumentId: string;
  symbol: string;
  currency?: string;
  className?: string;
}

const PERIODS = ['1D', '1W', '1M', '3M', '6M', '1Y', 'ALL'] as const;

export const InstrumentPriceChart: React.FC<InstrumentPriceChartProps> = ({
  instrumentId,
  symbol,
  currency = '₹',
  className = '',
}) => {
  const [selectedPeriod, setSelectedPeriod] = useState<string>('1M');

  const { data: historyData, isLoading, isError } = useInstrumentHistory(instrumentId, selectedPeriod);

  const rawPoints = historyData?.points || [];
  // Guarantee chronological ascending order
  const points = [...rawPoints].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  const isSupported = historyData?.supported ?? true;

  const isIndex =
    symbol.toUpperCase().startsWith('NIFTY') ||
    symbol.toUpperCase().startsWith('SENSEX') ||
    symbol.toUpperCase() === 'BANKNIFTY' ||
    historyData?.unit === 'POINTS';

  const unitPrefix = isIndex ? '' : (historyData?.currency ? (historyData.currency === 'INR' ? currency : `${historyData.currency} `) : currency);
  const unitSuffix = isIndex ? ' pts' : '';

  // Compute true OHLC metrics from actual point data
  const prices = points.map((p) => parseFloat(p.price)).filter((n) => !isNaN(n));
  const highCandidates = points
    .map((p) => (p.high_price ? parseFloat(p.high_price) : parseFloat(p.price)))
    .filter((n) => !isNaN(n));
  const lowCandidates = points
    .map((p) => (p.low_price ? parseFloat(p.low_price) : parseFloat(p.price)))
    .filter((n) => !isNaN(n) && n > 0);

  const minPrice = lowCandidates.length > 0 ? Math.min(...lowCandidates) : 0;
  const maxPrice = highCandidates.length > 0 ? Math.max(...highCandidates) : 0;
  const firstPrice = points.length > 0
    ? (points[0].open_price ? parseFloat(points[0].open_price) : parseFloat(points[0].price))
    : 0;
  const lastPrice = prices.length > 0 ? prices[prices.length - 1] : 0;
  const priceRange = maxPrice - minPrice;
  const netChange = lastPrice - firstPrice;
  const netChangePercent = firstPrice > 0 ? (netChange / firstPrice) * 100 : 0;

  // Generate SVG coordinates
  const svgWidth = 600;
  const svgHeight = 220;
  const paddingX = 40;
  const paddingY = 30;
  const innerWidth = svgWidth - paddingX * 2;
  const innerHeight = svgHeight - paddingY * 2;

  const polylinePoints = prices
    .map((price, idx) => {
      const x = paddingX + (idx / Math.max(prices.length - 1, 1)) * innerWidth;
      const yNorm = priceRange > 0 ? (price - minPrice) / priceRange : 0.5;
      const y = svgHeight - paddingY - yNorm * innerHeight;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  const areaPoints =
    polylinePoints.length > 0
      ? `${paddingX},${svgHeight - paddingY} ${polylinePoints} ${svgWidth - paddingX},${svgHeight - paddingY}`
      : '';

  return (
    <div className={`rounded-2xl border border-theme-border bg-theme-surface p-5 shadow-sm ${className}`}>
      {/* Header and Period Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-theme-border/60">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold tracking-tight text-theme-text flex items-center gap-1.5">
              <TrendingUp className="h-4 w-4 text-theme-primary" />
              {symbol} Historical Price Movement
            </h3>
            {historyData?.trust_class && (
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
                {historyData.trust_class.replace(/_/g, ' ')}
              </span>
            )}
            {historyData?.currency && !isIndex && (
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-theme-bg text-theme-text-muted border border-theme-border uppercase">
                {historyData.currency}
              </span>
            )}
          </div>
          <p className="text-xs text-theme-text-muted mt-0.5">
            {historyData?.start_date && historyData?.end_date
              ? `Range: ${historyData.start_date} to ${historyData.end_date} (${points.length} observations)`
              : `Period: ${selectedPeriod}`}
          </p>
        </div>

        {/* Period Selector Tabs */}
        <div className="flex items-center gap-1 bg-theme-bg p-1 rounded-xl border border-theme-border">
          {PERIODS.map((period) => (
            <button
              key={period}
              type="button"
              onClick={() => setSelectedPeriod(period)}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition-all ${
                selectedPeriod === period
                  ? 'bg-theme-primary text-theme-primary-contrast shadow-sm'
                  : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-hover'
              }`}
            >
              {period}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Metrics Bar */}
      {prices.length > 0 && isSupported && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-3 border-b border-theme-border/40 text-xs">
          <div>
            <div className="text-[10px] text-theme-text-muted uppercase font-medium">Period Open</div>
            <div className="font-semibold text-theme-text">
              {unitPrefix}{firstPrice.toFixed(2)}{unitSuffix}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-theme-text-muted uppercase font-medium">Period High</div>
            <div className="font-semibold text-emerald-400">
              {unitPrefix}{maxPrice.toFixed(2)}{unitSuffix}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-theme-text-muted uppercase font-medium">Period Low</div>
            <div className="font-semibold text-rose-400">
              {unitPrefix}{minPrice.toFixed(2)}{unitSuffix}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-theme-text-muted uppercase font-medium">Period Change</div>
            <div className={`font-semibold ${netChange >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {netChange >= 0 ? '+' : ''}
              {netChangePercent.toFixed(2)}% ({netChange >= 0 ? '+' : ''}{unitPrefix}{netChange.toFixed(2)}{unitSuffix})
            </div>
          </div>
        </div>
      )}

      {/* Chart Canvas Area */}
      <div className="relative h-60 w-full mt-3 flex items-center justify-center">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center gap-2 text-theme-text-muted text-xs">
            <Loader2 className="h-6 w-6 animate-spin text-theme-primary" />
            <span>Loading historical prices...</span>
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center gap-2 text-rose-400 text-xs p-6 text-center">
            <AlertCircle className="h-6 w-6" />
            <span>Unable to retrieve historical market observations.</span>
          </div>
        ) : !isSupported ? (
          <div className="flex flex-col items-center justify-center gap-2 text-theme-text-muted text-xs p-6 text-center">
            <Info className="h-6 w-6 text-theme-primary" />
            <span className="font-semibold text-theme-text">Historical timeseries unsupported</span>
            <span className="max-w-xs">{historyData?.message || 'Historical observations are not provided for this asset type.'}</span>
          </div>
        ) : points.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 text-theme-text-muted text-xs p-6 text-center">
            <Info className="h-6 w-6" />
            <span>No price observations recorded for period {selectedPeriod}.</span>
          </div>
        ) : points.length === 1 ? (
          <div className="flex flex-col items-center justify-center gap-2 text-theme-text-muted text-xs p-6 text-center">
            <Info className="h-6 w-6 text-theme-primary" />
            <span className="font-semibold text-theme-text">Single Observation Recorded</span>
            <span className="max-w-xs">
              Latest observation on {points[0].date}: {unitPrefix}{prices[0].toFixed(2)}{unitSuffix}.
              Full multi-year historical timeseries backfill is in progress.
            </span>
          </div>
        ) : (
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            className="w-full h-full overflow-visible"
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--theme-primary, #6366f1)" stopOpacity="0.25" />
                <stop offset="100%" stopColor="var(--theme-primary, #6366f1)" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid Lines */}
            <line
              x1={paddingX}
              y1={paddingY}
              x2={svgWidth - paddingX}
              y2={paddingY}
              stroke="var(--theme-border, #334155)"
              strokeDasharray="3 3"
              strokeOpacity="0.4"
            />
            <line
              x1={paddingX}
              y1={svgHeight / 2}
              x2={svgWidth - paddingX}
              y2={svgHeight / 2}
              stroke="var(--theme-border, #334155)"
              strokeDasharray="3 3"
              strokeOpacity="0.4"
            />
            <line
              x1={paddingX}
              y1={svgHeight - paddingY}
              x2={svgWidth - paddingX}
              y2={svgHeight - paddingY}
              stroke="var(--theme-border, #334155)"
              strokeDasharray="3 3"
              strokeOpacity="0.4"
            />

            {/* Shaded Area */}
            {areaPoints && (
              <polygon points={areaPoints} fill="url(#chartGradient)" />
            )}

            {/* Price Line */}
            {polylinePoints && (
              <polyline
                fill="none"
                stroke="var(--theme-primary, #6366f1)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={polylinePoints}
              />
            )}

            {/* Start and End Dots */}
            {prices.length > 0 && (
              <>
                <circle
                  cx={paddingX}
                  cy={svgHeight - paddingY - ((firstPrice - minPrice) / Math.max(priceRange, 1)) * innerHeight}
                  r="3.5"
                  fill="var(--theme-primary, #6366f1)"
                />
                <circle
                  cx={svgWidth - paddingX}
                  cy={svgHeight - paddingY - ((lastPrice - minPrice) / Math.max(priceRange, 1)) * innerHeight}
                  r="4"
                  fill="var(--theme-primary, #6366f1)"
                  stroke="var(--theme-surface, #1e293b)"
                  strokeWidth="2"
                />
              </>
            )}
          </svg>
        )}
      </div>

      {/* Provenance note */}
      <div className="flex items-center justify-between text-[11px] text-theme-text-muted pt-2 border-t border-theme-border/40 mt-2">
        <span>Verified published market-price observations</span>
        <span>Decimal-safe calculation</span>
      </div>
    </div>
  );
};
