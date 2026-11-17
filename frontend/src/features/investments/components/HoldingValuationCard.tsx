import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, TrendingDown, ShieldAlert, Award, Clock } from 'lucide-react';
import { investmentValuationApi } from '../api/investmentValuationApi';

export interface HoldingValuationCardProps {
  investmentId: string;
  currency?: string;
  initialValueFallback?: string | number;
  currentValueFallback?: string | number;
  valuationMethodFallback?: string;
}

export const HoldingValuationCard: React.FC<HoldingValuationCardProps> = ({
  investmentId,
  currency = 'INR',
  initialValueFallback = 0,
  currentValueFallback = 0,
  valuationMethodFallback = 'MANUAL',
}) => {
  const { data: performance } = useQuery({
    queryKey: ['investment-performance', investmentId],
    queryFn: () => investmentValuationApi.getPerformance(investmentId),
    staleTime: 30000,
  });

  // Authoritative numbers from backend performance calculation or safe fallbacks
  const investedAmountStr = performance?.invested_amount ?? String(initialValueFallback);
  const currentValueStr = performance?.current_value ?? String(currentValueFallback);
  const absoluteGainStr = performance?.absolute_gain_loss ?? (
    (Number(currentValueStr) - Number(investedAmountStr)).toFixed(2)
  );
  const percentageGainStr = performance?.percentage_gain_loss ?? (
    Number(investedAmountStr) > 0
      ? (((Number(currentValueStr) - Number(investedAmountStr)) / Number(investedAmountStr)) * 100).toFixed(2)
      : 'unavailable'
  );
  const isGain = performance?.is_gain ?? (Number(currentValueStr) >= Number(investedAmountStr));
  const valMethod = performance?.valuation_method || valuationMethodFallback;
  const source = performance?.source || 'MANUAL';
  const valDate = performance?.last_valuation_date;

  const isSynthetic = source.toUpperCase().includes('SYNTHETIC') || source.toUpperCase().includes('DEMO');

  const getProvenanceBadge = () => {
    if (isSynthetic) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20" title="Simulated pricing derived from local synthetic provider">
          <ShieldAlert className="h-3 w-3" />
          Synthetic Demo
        </span>
      );
    }
    if (source.toUpperCase().includes('MARKET') || valMethod.toUpperCase().includes('MARKET') || valMethod.toUpperCase().includes('NAV')) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <Award className="h-3 w-3" />
          Market Feed
        </span>
      );
    }
    if (source.toUpperCase().includes('CONTRACT') || valMethod.toUpperCase().includes('CONTRACTUAL')) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
          <Award className="h-3 w-3" />
          Contractual
        </span>
      );
    }
    if (source.toUpperCase().includes('BANK') || valMethod.toUpperCase().includes('BANK')) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <Award className="h-3 w-3" />
          Bank Stated
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-gray-500/10 text-gray-400 border border-gray-500/20">
        <Clock className="h-3 w-3" />
        Manual Snapshot
      </span>
    );
  };

  const formattedInvested = Number(investedAmountStr).toLocaleString('en-IN', { minimumFractionDigits: 2 });
  const formattedCurrent = Number(currentValueStr).toLocaleString('en-IN', { minimumFractionDigits: 2 });
  const formattedAbsolute = Number(absoluteGainStr).toLocaleString('en-IN', { minimumFractionDigits: 2 });

  return (
    <div className="space-y-4">
      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Cost Outlay */}
        <div className="p-4 rounded-xl bg-theme-card border border-theme-border shadow-sm">
          <span className="text-xs text-theme-text-muted font-medium">Initial Capital Outlay</span>
          <div className="text-lg font-bold text-theme-text mt-1">
            {currency} {formattedInvested}
          </div>
          <span className="text-[10px] text-theme-text-muted block mt-0.5">Authoritative Cost Basis</span>
        </div>

        {/* Current Valuation */}
        <div className="p-4 rounded-xl bg-theme-card border border-theme-border shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-theme-text-muted font-medium">Current Valuation</span>
            {getProvenanceBadge()}
          </div>
          <div className="text-lg font-bold text-theme-text mt-1">
            {currency} {formattedCurrent}
          </div>
          <span className="text-[10px] text-theme-text-muted block mt-0.5">
            {valDate ? `As of ${valDate}` : 'Point-in-time value'}
          </span>
        </div>

        {/* Unrealized Gain / Loss */}
        <div className="p-4 rounded-xl bg-theme-card border border-theme-border shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-theme-text-muted font-medium">Unrealized Value Gain</span>
            {isGain ? (
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            ) : (
              <TrendingDown className="h-4 w-4 text-rose-400" />
            )}
          </div>
          <div
            className={`text-lg font-bold mt-1 ${
              isGain ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isGain && Number(absoluteGainStr) > 0 ? '+' : ''}
            {currency} {formattedAbsolute}
            <span className="text-xs font-normal ml-1.5 text-theme-text-muted">
              ({percentageGainStr === 'unavailable' ? 'N/A' : `${percentageGainStr}%`})
            </span>
          </div>
          <span className="text-[10px] text-theme-text-muted block mt-0.5">
            {percentageGainStr === 'unavailable' ? 'Zero Cost Acquisition' : 'Authoritative Backend Return'}
          </span>
        </div>
      </div>
    </div>
  );
};
