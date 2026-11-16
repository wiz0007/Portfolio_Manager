import React from 'react';
import { Sparkles, Info } from 'lucide-react';

interface DemoBadgeProps {
  size?: 'sm' | 'md' | 'lg';
  isBanner?: boolean;
  className?: string;
}

export const DemoBadge: React.FC<DemoBadgeProps> = ({
  size = 'md',
  isBanner = false,
  className = '',
}) => {
  if (isBanner) {
    return (
      <div
        className={`flex items-center justify-between gap-3 px-4 py-2.5 rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-300 text-xs sm:text-sm font-medium ${className}`}
        role="status"
        aria-label="Demo market data warning"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-amber-400 shrink-0 animate-pulse" />
          <span>
            <strong className="font-semibold text-amber-200">DEMO MODE ACTIVE:</strong>{' '}
            Prices shown are synthetic values anchored to researched November 2026 market prices, not live broker quotations.
          </span>
        </div>
        <div className="hidden sm:flex items-center gap-1 text-[11px] text-amber-400/80">
          <Info className="h-3.5 w-3.5" />
          <span>Awaiting vendor credentials</span>
        </div>
      </div>
    );
  }

  const sizeClasses = {
    sm: 'text-[10px] px-1.5 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
    lg: 'text-sm px-3 py-1.5 gap-2',
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-md font-medium border border-amber-500/40 bg-amber-500/15 text-amber-300 ${sizeClasses} ${className}`}
      title="DEMO DATA — Deterministic synthetic price, not a live market quotation"
    >
      <Sparkles className="h-3 w-3 text-amber-400 shrink-0" />
      <span>DEMO DATA</span>
    </span>
  );
};
