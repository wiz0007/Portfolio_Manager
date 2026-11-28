import React from 'react';
import { AllocationItem } from '../types';

interface AllocationBreakdownCardProps {
  categories: AllocationItem[];
  currency?: string;
  totalMarketValue: string;
  className?: string;
}

const CATEGORY_COLORS = [
  '#10b981', // Emerald
  '#3b82f6', // Blue
  '#f59e0b', // Amber
  '#8b5cf6', // Purple
  '#ec4899', // Pink
  '#14b8a6', // Teal
  '#f97316', // Orange
];

export const AllocationBreakdownCard: React.FC<AllocationBreakdownCardProps> = ({
  categories,
  currency = 'INR',
  totalMarketValue,
  className = '',
}) => {
  return (
    <div className={`p-5 rounded-2xl border border-theme-border bg-theme-surface flex flex-col ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
            Asset Class Allocation
          </div>
          <div className="text-xl font-bold text-theme-text mt-0.5">
            {currency} {parseFloat(totalMarketValue).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      {/* Stacked Progress Bar */}
      <div className="h-3 w-full rounded-full overflow-hidden flex bg-slate-800 mb-6">
        {categories.map((cat, idx) => (
          <div
            key={cat.key}
            style={{
              width: `${cat.percentage}%`,
              backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length],
            }}
            title={`${cat.name}: ${cat.percentage}%`}
          />
        ))}
      </div>

      {/* Category List */}
      <div className="space-y-3">
        {categories.map((cat, idx) => (
          <div key={cat.key} className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length] }}
              />
              <span className="font-medium text-theme-text">{cat.name}</span>
              <span className="text-theme-text-muted">({cat.holding_count} holdings)</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-theme-text font-semibold">
                {currency} {parseFloat(cat.market_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className="text-theme-text-muted font-mono w-12 text-right">
                {parseFloat(cat.percentage).toFixed(1)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
