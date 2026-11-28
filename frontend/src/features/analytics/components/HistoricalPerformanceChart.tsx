import React, { useMemo, useState } from 'react';
import { PortfolioTimeSeriesPoint } from '../types';

interface HistoricalPerformanceChartProps {
  points: PortfolioTimeSeriesPoint[];
  currency?: string;
  className?: string;
}

export const HistoricalPerformanceChart: React.FC<HistoricalPerformanceChartProps> = ({
  points,
  currency = 'INR',
  className = '',
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const sortedPoints = useMemo(() => {
    return [...points].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [points]);

  const { coordinates, pathVal, areaVal, pathCap } = useMemo(() => {
    if (sortedPoints.length === 0) {
      return { coordinates: [], pathVal: '', areaVal: '', pathCap: '' };
    }

    const values = sortedPoints.map((p) => parseFloat(p.market_value));
    const capitals = sortedPoints.map((p) => parseFloat(p.invested_capital));
    const all = [...values, ...capitals];

    const min = Math.min(...all);
    const max = Math.max(...all);
    const range = max - min || 1;

    const width = 800;
    const height = 300;
    const padding = 20;

    const coords = sortedPoints.map((pt, idx) => {
      const x = padding + (idx / Math.max(1, sortedPoints.length - 1)) * (width - 2 * padding);
      const val = parseFloat(pt.market_value);
      const cap = parseFloat(pt.invested_capital);
      const yVal = height - padding - ((val - min) / range) * (height - 2 * padding);
      const yCap = height - padding - ((cap - min) / range) * (height - 2 * padding);
      return { x, yVal, yCap, point: pt };
    });

    const valLine = coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${c.yVal.toFixed(1)}`).join(' ');
    const capLine = coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${c.yCap.toFixed(1)}`).join(' ');
    const valArea = `${valLine} L ${coords[coords.length - 1].x.toFixed(1)} ${height} L ${coords[0].x.toFixed(1)} ${height} Z`;

    return {
      coordinates: coords,
      pathVal: valLine,
      areaVal: valArea,
      pathCap: capLine,
    };
  }, [sortedPoints]);

  if (sortedPoints.length === 0) {
    return (
      <div className={`p-8 text-center text-theme-text-muted border border-theme-border rounded-xl bg-theme-surface ${className}`}>
        No historical performance data available for the selected period.
      </div>
    );
  }

  const activeCoord = hoverIndex !== null && coordinates[hoverIndex] ? coordinates[hoverIndex] : null;
  const activePoint = activeCoord ? activeCoord.point : sortedPoints[sortedPoints.length - 1];

  return (
    <div className={`p-5 rounded-2xl border border-theme-border bg-theme-surface flex flex-col ${className}`}>
      {/* Chart Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <div className="text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
            Portfolio Historical Growth
          </div>
          <div className="flex items-baseline gap-3 mt-1">
            <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-theme-text">
              {currency} {parseFloat(activePoint.market_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
            <span className="text-xs text-theme-text-muted">
              Invested: {currency} {parseFloat(activePoint.invested_capital).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="text-xs text-theme-text-muted mt-0.5">
            Date: {activePoint.date} • Total P/L: {currency} {parseFloat(activePoint.total_pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs font-medium text-theme-text-muted">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            <span>Market Value</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-blue-500" />
            <span>Invested Capital</span>
          </div>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full overflow-hidden">
        <svg
          viewBox="0 0 800 300"
          className="w-full h-auto cursor-crosshair select-none"
          onMouseLeave={() => setHoverIndex(null)}
        >
          <defs>
            <linearGradient id="growthGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Area Fill */}
          <path d={areaVal} fill="url(#growthGradient)" />

          {/* Invested Capital Line */}
          <path d={pathCap} fill="none" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 4" />

          {/* Market Value Line */}
          <path d={pathVal} fill="none" stroke="#10b981" strokeWidth="2.5" />

          {/* Interactive Hover Line and Points */}
          {activeCoord && (
            <g>
              <line
                x1={activeCoord.x}
                y1={0}
                x2={activeCoord.x}
                y2={300}
                stroke="#64748b"
                strokeWidth="1"
                strokeDasharray="2 2"
              />
              <circle cx={activeCoord.x} cy={activeCoord.yVal} r={4.5} fill="#10b981" stroke="#ffffff" strokeWidth="2" />
              <circle cx={activeCoord.x} cy={activeCoord.yCap} r={4.5} fill="#3b82f6" stroke="#ffffff" strokeWidth="2" />
            </g>
          )}

          {/* Invisible Overlay for Mouse Events */}
          {coordinates.map((c, i) => (
            <rect
              key={i}
              x={c.x - 800 / (2 * coordinates.length)}
              y={0}
              width={800 / coordinates.length}
              height={300}
              fill="transparent"
              onMouseEnter={() => setHoverIndex(i)}
            />
          ))}
        </svg>
      </div>
    </div>
  );
};
