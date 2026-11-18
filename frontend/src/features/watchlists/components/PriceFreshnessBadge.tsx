import React from 'react';
import { CheckCircle2, Clock, AlertTriangle, HelpCircle, ShieldAlert, Cpu } from 'lucide-react';
import { PriceFreshnessStatus } from '../types';

interface PriceFreshnessBadgeProps {
  status: PriceFreshnessStatus;
  isSynthetic?: boolean;
  effectiveAt?: string | null;
  className?: string;
}

export const PriceFreshnessBadge: React.FC<PriceFreshnessBadgeProps> = ({
  status,
  isSynthetic,
  effectiveAt,
  className = '',
}) => {
  // If explicitly flagged synthetic, emphasize synthetic demo indicator
  if (isSynthetic || status === 'SYNTHETIC') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 ${className}`}
        title={effectiveAt ? `Synthetic demo quote generated at ${new Date(effectiveAt).toLocaleString()}` : 'Deterministic development data'}
        role="status"
        aria-label="Synthetic demo price"
      >
        <Cpu className="h-3 w-3" />
        <span>Demo Price</span>
      </span>
    );
  }

  switch (status) {
    case 'AVAILABLE':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 ${className}`}
          title={effectiveAt ? `Verified market price effective ${new Date(effectiveAt).toLocaleDateString()}` : 'Verified current'}
          role="status"
          aria-label="Verified market price"
        >
          <CheckCircle2 className="h-3 w-3" />
          <span>Verified</span>
        </span>
      );

    case 'STALE':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30 ${className}`}
          title={effectiveAt ? `Last verified observation was at ${new Date(effectiveAt).toLocaleDateString()}` : 'Observation exceeds freshness threshold'}
          role="status"
          aria-label="Stale market price"
        >
          <Clock className="h-3 w-3" />
          <span>Stale</span>
        </span>
      );

    case 'MISSING':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/30 ${className}`}
          title="No verified price observation available"
          role="status"
          aria-label="Price unavailable"
        >
          <AlertTriangle className="h-3 w-3" />
          <span>Unavailable</span>
        </span>
      );

    case 'AWAITING_VERIFICATION':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/30 ${className}`}
          title="Price observation draft submitted, awaiting publisher approval"
          role="status"
          aria-label="Pending review"
        >
          <Clock className="h-3 w-3" />
          <span>Pending Review</span>
        </span>
      );

    case 'CONFLICTED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-orange-500/10 text-orange-400 border border-orange-500/30 ${className}`}
          title="Discrepancy detected between sources"
          role="status"
          aria-label="Conflicted price"
        >
          <ShieldAlert className="h-3 w-3" />
          <span>Conflicted</span>
        </span>
      );

    case 'UNSUPPORTED':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/30 ${className}`}
          title="Automated pricing not supported for this asset type"
          role="status"
          aria-label="Unsupported asset pricing"
        >
          <HelpCircle className="h-3 w-3" />
          <span>Unsupported</span>
        </span>
      );
  }
};
