import React, { useMemo, useState } from 'react';
import { NormalizedPoint } from '../types';

interface BenchmarkComparisonChartProps {
  points: NormalizedPoint[];
  benchmarkSymbol: string;
  targetName?: string;
  excessReturnPct: string;
  className?: string;
}

export const BenchmarkComparisonChart: React.FC<BenchmarkComparisonChartProps> = ({
  points,
  benchmarkSymbol,
  targetName = 'Portfolio',
  excessReturnPct,
  className = '',
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const sortedPoints = useMemo(() => {
    return [...points].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [points]);

  const { coordinates, pathTarget, pathBench } = useMemo(() => {
    if (sortedPoints.length === 0) {
      return { coordinates: [], pathTarget: '', pathBench: '' };
    }

    const tVals = sortedPoints.map((p) => parseFloat(p.target_value));
    const bVals = sortedPoints.map((p) => parseFloat(p.benchmark_value));
    const all = [...tVals, ...bVals, 100];

    const min = Math.min(...all) * 0.98;
    const max = Math.max(...all) * 1.02;
    const range = max - min || 1;

    const width = 800;
    const height = 300;
    const padding = 20;

    const coords = sortedPoints.map((pt, idx) => {
      const x = padding + (idx / Math.max(1, sortedPoints.length - 1)) * (width - 2 * padding);
      const tVal = parseFloat(pt.target_value);
      const bVal = parseFloat(pt.benchmark_value);
      const yTarget = height - padding - ((tVal - min) / range) * (height - 2 * padding);
      const yBench = height - padding - ((bVal - min) / range) * (height - 2 * padding);
      return { x, yTarget, yBench, point: pt };
    });

    const targetLine = coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${c.yTarget.toFixed(1)}`).join(' ');
    const benchLine = coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${c.yBench.toFixed(1)}`).join(' ');

    return { coordinates: coords, pathTarget: targetLine, pathBench: benchLine };
  }, [sortedPoints]);

  if (sortedPoints.length === 0) {
    return (
      <div className={`p-8 text-center text-theme-text-muted border border-theme-border rounded-xl bg-theme-surface ${className}`}>
        No benchmark comparison points available.
      </div>
    );
  }

  const activeCoord = hoverIndex !== null && coordinates[hoverIndex] ? coordinates[hoverIndex] : null;
  const activePoint = activeCoord ? activeCoord.point : sortedPoints[sortedPoints.length - 1];

  const excessNum = parseFloat(excessReturnPct);
  const isExcessPositive = excessNum >= 0;

  return (
    <div className={`p-5 rounded-2xl border border-theme-border bg-theme-surface flex flex-col ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <div className="text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
            Normalized Performance (Base 100) vs {benchmarkSymbol}
          </div>
          <div className="flex items-baseline gap-3 mt-1">
            <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-theme-text">
              {parseFloat(activePoint.target_value).toFixed(2)}
            </span>
            <span className="text-xs text-theme-text-muted">
              Benchmark: {parseFloat(activePoint.benchmark_value).toFixed(2)}
            </span>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded ${isExcessPositive ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
              Excess Return: {excessNum >= 0 ? `+${excessReturnPct}%` : `${excessReturnPct}%`}
            </span>
          </div>
          <div className="text-xs text-theme-text-muted mt-0.5">
            Date: {activePoint.date}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs font-medium text-theme-text-muted">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            <span>{targetName}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
            <span>{benchmarkSymbol}</span>
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
          {/* Baseline 100 Reference */}
          <line x1={0} y1={150} x2={800} y2={150} stroke="#334155" strokeDasharray="2 2" strokeWidth="1" />

          {/* Benchmark Line */}
          <path d={pathBench} fill="none" stroke="#f59e0b" strokeWidth="2" strokeDasharray="3 3" />

          {/* Target / Portfolio Line */}
          <path d={pathTarget} fill="none" stroke="#10b981" strokeWidth="2.5" />

          {/* Hover Pointer */}
          {activeCoord && (
            <g>
              <line x1={activeCoord.x} y1={0} x2={activeCoord.x} y2={300} stroke="#64748b" strokeWidth="1" strokeDasharray="2 2" />
              <circle cx={activeCoord.x} cy={activeCoord.yTarget} r={4.5} fill="#10b981" stroke="#ffffff" strokeWidth="2" />
              <circle cx={activeCoord.x} cy={activeCoord.yBench} r={4.5} fill="#f59e0b" stroke="#ffffff" strokeWidth="2" />
            </g>
          )}

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
