import React from 'react';
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  HelpCircle,
  ShieldAlert,
  Cpu,
  AlertCircle,
  FileText,
} from 'lucide-react';
import { PriceFreshnessStatus } from '../types';

interface PriceFreshnessBadgeProps {
  status: PriceFreshnessStatus;
  isSynthetic?: boolean;
  effectiveAt?: string | null;
  publishedAt?: string | null;
  ageSeconds?: number | null;
  className?: string;
}

const formatRelativeAge = (
  ageSeconds?: number | null,
  publishedAt?: string | null,
  effectiveAt?: string | null
): string => {
  if (ageSeconds !== null && ageSeconds !== undefined && !isNaN(ageSeconds)) {
    if (ageSeconds < 0 || ageSeconds < 60) return 'just now';
    if (ageSeconds < 3600) return `${Math.floor(ageSeconds / 60)}m ago`;
    if (ageSeconds < 86400) return `${Math.floor(ageSeconds / 3600)}h ago`;
    const days = Math.floor(ageSeconds / 86400);
    if (days === 1) return 'yesterday';
    return `${days}d ago`;
  }
  const ts = publishedAt || effectiveAt;
  if (!ts) return '';
  const date = new Date(ts);
  if (isNaN(date.getTime())) return '';
  const diffSec = Math.floor((Date.now() - date.getTime()) / 1000);
  if (diffSec < 0 || diffSec < 60) return 'just now';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  const diffDays = Math.floor(diffSec / 86400);
  if (diffDays === 1) return 'yesterday';
  return `${diffDays}d ago`;
};

export const PriceFreshnessBadge: React.FC<PriceFreshnessBadgeProps> = ({
  status,
  isSynthetic,
  effectiveAt,
  publishedAt,
  ageSeconds,
  className = '',
}) => {
  const relativeAge = formatRelativeAge(ageSeconds, publishedAt, effectiveAt);

  // If explicitly flagged synthetic, emphasize synthetic demo indicator
  if (isSynthetic || status === 'SYNTHETIC') {
    const hasValidEffective = effectiveAt && !isNaN(new Date(effectiveAt).getTime());
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 ${className}`}
        title={hasValidEffective ? `Synthetic demo quote generated at ${new Date(effectiveAt).toLocaleString()}` : 'Deterministic development data'}
        role="status"
        aria-label="Synthetic demo price"
      >
        <Cpu className="h-3 w-3" />
        <span>Demo Price</span>
      </span>
    );
  }

  switch (status) {
    case 'AVAILABLE': {
      const hasValidPublished = publishedAt && !isNaN(new Date(publishedAt).getTime());
      const hasValidEffective = effectiveAt && !isNaN(new Date(effectiveAt).getTime());
      const title = hasValidPublished
        ? `Verified market price updated ${relativeAge} (${new Date(publishedAt).toLocaleString()})`
        : hasValidEffective
        ? `Verified market price effective ${new Date(effectiveAt).toLocaleDateString()}`
        : 'Verified current';
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 ${className}`}
          title={title}
          role="status"
          aria-label="Verified market price"
        >
          <CheckCircle2 className="h-3 w-3" />
          <span>Verified</span>
        </span>
      );
    }

    case 'STALE': {
      const hasValidEffective = effectiveAt && !isNaN(new Date(effectiveAt).getTime());
      const title = hasValidEffective
        ? `Last verified observation was at ${new Date(effectiveAt).toLocaleDateString()} (${relativeAge})`
        : 'Observation exceeds freshness threshold';
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30 ${className}`}
          title={title}
          role="status"
          aria-label="Stale market price"
        >
          <Clock className="h-3 w-3" />
          <span>Stale</span>
        </span>
      );
    }

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

    case 'UNVERIFIED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 ${className}`}
          title="Price observation has not been verified by authoritative source"
          role="status"
          aria-label="Unverified price"
        >
          <AlertCircle className="h-3 w-3" />
          <span>Unverified</span>
        </span>
      );

    case 'INCOMPATIBLE':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/30 ${className}`}
          title="Market data currency or unit does not match instrument specification"
          role="status"
          aria-label="Incompatible data"
        >
          <AlertTriangle className="h-3 w-3" />
          <span>Incompatible Data</span>
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

    case 'MANUAL':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/30 ${className}`}
          title="Non-market asset valued via recorded acquisition cost or manual snapshot"
          role="status"
          aria-label="Manual valuation"
        >
          <FileText className="h-3 w-3" />
          <span>Manual Valuation</span>
        </span>
      );

    case 'UNSUPPORTED':
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

    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/30 ${className}`}
          title={typeof status === 'string' ? `Status: ${status}` : 'Unknown pricing status'}
          role="status"
          aria-label="Unknown pricing status"
        >
          <HelpCircle className="h-3 w-3" />
          <span>{typeof status === 'string' ? status : 'Unknown'}</span>
        </span>
      );
  }
};
