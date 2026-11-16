import React, { useState, useMemo } from 'react';
import { HistoricalPoint } from '../types';

interface PriceChartProps {
  points: HistoricalPoint[];
  symbol?: string;
  currency?: string;
  selectedRange: string;
  onRangeChange: (range: string) => void;
  isLoading?: boolean;
  className?: string;
}

export const PriceChart: React.FC<PriceChartProps> = ({
  points,
  symbol,
  currency = 'INR',
  selectedRange,
  onRangeChange,
  isLoading = false,
  className = '',
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const ranges = ['1W', '1M', '3M', '6M', '1Y', 'ALL'];

  // Parse and sort points chronologically
  const sortedPoints = useMemo(() => {
    return [...points].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }, [points]);

  const { minPrice, maxPrice, startPrice, endPrice, isPositive, pathD, areaD, coordinates } =
    useMemo(() => {
      if (sortedPoints.length === 0) {
        return {
          minPrice: 0,
          maxPrice: 0,
          startPrice: 0,
          endPrice: 0,
          isPositive: true,
          pathD: '',
          areaD: '',
          coordinates: [],
        };
      }

      const prices = sortedPoints.map((p) => parseFloat(p.price));
      const min = Math.min(...prices);
      const max = Math.max(...prices);
      const range = max - min || 1;
      const start = prices[0];
      const end = prices[prices.length - 1];
      const positive = end >= start;

      // SVG viewbox dimensions: 800 x 300
      const width = 800;
      const height = 300;
      const padding = 20;

      const coords = sortedPoints.map((pt, idx) => {
        const x = padding + (idx / Math.max(1, sortedPoints.length - 1)) * (width - 2 * padding);
        const priceVal = parseFloat(pt.price);
        const y = height - padding - ((priceVal - min) / range) * (height - 2 * padding);
        return { x, y, point: pt };
      });

      const lineCommands = coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`).join(' ');
      const areaCommands = `${lineCommands} L ${coords[coords.length - 1].x.toFixed(1)} ${height} L ${coords[0].x.toFixed(1)} ${height} Z`;

      return {
        minPrice: min,
        maxPrice: max,
        startPrice: start,
        endPrice: end,
        isPositive: positive,
        pathD: lineCommands,
        areaD: areaCommands,
        coordinates: coords,
      };
    }, [sortedPoints]);

  const activeCoord = hoverIndex !== null && coordinates[hoverIndex] ? coordinates[hoverIndex] : null;
  const displayPoint = activeCoord ? activeCoord.point : sortedPoints[sortedPoints.length - 1];
  const displayPrice = displayPoint ? parseFloat(displayPoint.price) : endPrice;

  const totalChange = endPrice - startPrice;
  const totalChangePct = startPrice > 0 ? (totalChange / startPrice) * 100 : 0;

  return (
    <div className={`p-5 rounded-2xl border border-theme-border bg-theme-surface flex flex-col ${className}`}>
      {/* Header with Title, Price and Range Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <div className="text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
            {symbol ? `${symbol} Historical Performance` : 'Price History'}
          </div>
          <div className="flex items-baseline gap-3 mt-1">
            <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-theme-text">
              {new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency,
                maximumFractionDigits: 2,
              }).format(displayPrice)}
            </span>
            {sortedPoints.length > 1 && (
              <span
                className={`text-xs sm:text-sm font-semibold ${
                  isPositive ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {isPositive ? '+' : ''}
                {totalChange >= 0 ? '+' : ''}
                {totalChange.toFixed(2)} ({isPositive ? '+' : ''}
                {totalChangePct.toFixed(2)}%)
              </span>
            )}
          </div>
          {displayPoint && (
            <div className="text-[11px] text-theme-text-muted mt-0.5">
              {new Date(displayPoint.timestamp).toLocaleDateString('en-IN', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })}
            </div>
          )}
        </div>

        {/* Range Selector */}
        <div className="flex items-center gap-1 p-1 rounded-xl bg-theme-bg border border-theme-border self-start sm:self-auto">
          {ranges.map((r) => (
            <button
              key={r}
              onClick={() => onRangeChange(r)}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition-all ${
                selectedRange === r
                  ? 'bg-theme-primary text-theme-text-inverse shadow-sm'
                  : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-hover'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* SVG Chart Canvas */}
      <div className="relative w-full h-56 sm:h-64 mt-2 select-none">
        {isLoading ? (
          <div className="w-full h-full flex items-center justify-center text-sm text-theme-text-muted">
            <div className="animate-pulse">Loading market timeseries...</div>
          </div>
        ) : sortedPoints.length === 0 ? (
          <div className="w-full h-full flex items-center justify-center text-sm text-theme-text-muted">
            No historical data available for this range.
          </div>
        ) : (
          <svg
            viewBox="0 0 800 300"
            className="w-full h-full overflow-visible"
            onMouseLeave={() => setHoverIndex(null)}
          >
            <defs>
              <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="0%"
                  stopColor={isPositive ? '#10b981' : '#f43f5e'}
                  stopOpacity="0.25"
                />
                <stop
                  offset="100%"
                  stopColor={isPositive ? '#10b981' : '#f43f5e'}
                  stopOpacity="0.0"
                />
              </linearGradient>
            </defs>

            {/* Horizontal Gridlines */}
            <line x1="20" y1="30" x2="780" y2="30" stroke="currentColor" strokeOpacity="0.08" strokeDasharray="4 4" />
            <line x1="20" y1="150" x2="780" y2="150" stroke="currentColor" strokeOpacity="0.08" strokeDasharray="4 4" />
            <line x1="20" y1="270" x2="780" y2="270" stroke="currentColor" strokeOpacity="0.08" strokeDasharray="4 4" />

            {/* Area under curve */}
            <path d={areaD} fill="url(#chartGradient)" />

            {/* Price Line */}
            <path
              d={pathD}
              fill="none"
              stroke={isPositive ? '#10b981' : '#f43f5e'}
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Hover Crosshair & Pointer */}
            {activeCoord && (
              <g>
                <line
                  x1={activeCoord.x}
                  y1="10"
                  x2={activeCoord.x}
                  y2="280"
                  stroke="currentColor"
                  strokeOpacity="0.3"
                  strokeWidth="1.5"
                  strokeDasharray="3 3"
                />
                <circle
                  cx={activeCoord.x}
                  cy={activeCoord.y}
                  r="5"
                  fill={isPositive ? '#10b981' : '#f43f5e'}
                  stroke="#ffffff"
                  strokeWidth="2"
                />
              </g>
            )}

            {/* Invisible hover interaction bars */}
            {coordinates.map((c, i) => (
              <rect
                key={i}
                x={c.x - (800 / coordinates.length) / 2}
                y="0"
                width={800 / coordinates.length}
                height="300"
                fill="transparent"
                onMouseEnter={() => setHoverIndex(i)}
                className="cursor-crosshair"
              />
            ))}
          </svg>
        )}
      </div>

      {/* Footer Metrics */}
      <div className="mt-4 pt-3 border-t border-theme-border/60 flex items-center justify-between text-xs text-theme-text-muted">
        <div>
          <span>Low: </span>
          <span className="font-semibold text-theme-text">₹{minPrice.toFixed(2)}</span>
        </div>
        <div>
          <span>High: </span>
          <span className="font-semibold text-theme-text">₹{maxPrice.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
};
