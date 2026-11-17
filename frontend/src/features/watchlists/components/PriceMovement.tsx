import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { PriceMovement as PriceMovementType } from '../types';

interface PriceMovementProps {
  movement: PriceMovementType;
  currency?: string;
  className?: string;
  compact?: boolean;
}

export const PriceMovement: React.FC<PriceMovementProps> = ({
  movement,
  currency = '₹',
  className = '',
  compact = false,
}) => {
  if (movement.status !== 'CALCULATED' || movement.change_percent === null) {
    return (
      <span
        className={`inline-flex items-center gap-1 text-xs text-theme-text-muted ${className}`}
        title={movement.notes || 'Historical price movement unavailable'}
        aria-label="Price change unavailable"
      >
        <Minus className="h-3 w-3" />
        <span>--</span>
      </span>
    );
  }

  const pct = parseFloat(movement.change_percent);
  const amt = movement.change_amount ? parseFloat(movement.change_amount) : null;
  const isPositive = pct > 0;
  const isZero = pct === 0;

  if (isZero) {
    return (
      <span
        className={`inline-flex items-center gap-1 text-xs font-medium text-theme-text-muted ${className}`}
        aria-label="Price unchanged"
      >
        <Minus className="h-3 w-3" />
        <span>0.00%</span>
      </span>
    );
  }

  const sign = isPositive ? '+' : '';
  const colorClass = isPositive ? 'text-emerald-400' : 'text-rose-400';
  const Icon = isPositive ? TrendingUp : TrendingDown;

  return (
    <div className={`inline-flex items-center gap-1 font-semibold text-xs ${colorClass} ${className}`}>
      <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
      <span aria-label={`Price change ${sign}${pct.toFixed(2)} percent`}>
        {sign}{pct.toFixed(2)}%
      </span>
      {!compact && amt !== null && (
        <span className="text-[11px] opacity-80 font-normal">
          ({sign}{currency === 'INR' ? '₹' : currency}{Math.abs(amt).toFixed(2)})
        </span>
      )}
    </div>
  );
};
