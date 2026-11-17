import React, { useState } from 'react';
import { X, TrendingUp, Sparkles, Clock, AlertCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { investmentValuationApi } from '../../api/investmentValuationApi';
import { Button } from '@/shared/ui/Button';

export interface ProjectionCalculatorModalProps {
  investmentId: string;
  investmentName: string;
  currentValue: number;
  category: string;
  currency?: string;
  onClose: () => void;
}

export const ProjectionCalculatorModal: React.FC<ProjectionCalculatorModalProps> = ({
  investmentId,
  investmentName,
  currentValue,
  category: _category,
  currency = 'INR',
  onClose,
}) => {
  const [horizonYears, setHorizonYears] = useState<number>(5);
  const [monthlyContribution, setMonthlyContribution] = useState<number>(0);
  const [timing, setTiming] = useState<'END_OF_PERIOD' | 'BEGINNING_OF_PERIOD'>('END_OF_PERIOD');
  const [activeScenario, setActiveScenario] = useState<string>('base');
  const [customRate, setCustomRate] = useState<string>('');

  const { data: projection, isLoading, isError } = useQuery({
    queryKey: [
      'investment-projections',
      investmentId,
      horizonYears,
      monthlyContribution,
      timing,
      customRate,
    ],
    queryFn: () =>
      investmentValuationApi.calculateProjection(investmentId, {
        time_horizon_years: horizonYears,
        monthly_contribution: monthlyContribution,
        contribution_timing: timing,
        compounding_frequency_per_year: 12,
        custom_annual_rate: customRate ? parseFloat(customRate) : null,
      }),
  });

  const scenarios = projection?.scenarios || {};
  const currentScenarioData = scenarios[activeScenario] || scenarios['base'] || Object.values(scenarios)[0];

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="projection-calc-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 overflow-y-auto"
    >
      <div className="relative w-full max-w-4xl bg-theme-surface border border-theme-border rounded-2xl shadow-2xl overflow-hidden my-8 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-theme-border bg-theme-card/40">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-theme-primary" />
              <span className="text-xs font-semibold text-theme-primary uppercase tracking-wider">
                Future-Value Scenario Engine
              </span>
            </div>
            <h2 id="projection-calc-title" className="text-lg font-bold text-theme-text mt-0.5">
              Growth Projections — {investmentName}
            </h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="p-1.5 rounded-lg text-theme-text-muted hover:text-theme-text hover:bg-theme-hover transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Non-mutation disclaimer banner */}
          <div className="flex items-start gap-3 p-3.5 rounded-xl bg-theme-primary/10 border border-theme-primary/20 text-xs text-theme-text">
            <AlertCircle className="h-4 w-4 text-theme-primary shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-theme-primary">Deterministic Simulation Engine:</span>{' '}
              These calculations model potential trajectories under explicit compound interest assumptions.
              Simulated projections never modify your actual portfolio or historical holding records.
            </div>
          </div>

          {/* Controls Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-xl bg-theme-card/50 border border-theme-border">
            {/* Horizon */}
            <div>
              <label className="block text-xs font-semibold text-theme-text mb-1">
                Time Horizon: {horizonYears} {horizonYears === 1 ? 'Year' : 'Years'}
              </label>
              <div className="flex items-center gap-2 mt-2">
                {[1, 3, 5, 10, 15, 20].map((yr) => (
                  <button
                    key={yr}
                    type="button"
                    onClick={() => setHorizonYears(yr)}
                    className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                      horizonYears === yr
                        ? 'bg-theme-primary text-black'
                        : 'bg-theme-bg border border-theme-border text-theme-text-muted hover:text-theme-text'
                    }`}
                  >
                    {yr}y
                  </button>
                ))}
              </div>
            </div>

            {/* Monthly Contribution */}
            <div>
              <label className="block text-xs font-semibold text-theme-text mb-1">
                Monthly Regular Inflow ({currency})
              </label>
              <input
                type="number"
                min="0"
                step="500"
                value={monthlyContribution || ''}
                onChange={(e) => setMonthlyContribution(Math.max(0, Number(e.target.value)))}
                placeholder="0"
                className="w-full px-3 py-1.5 bg-theme-bg border border-theme-border rounded-lg text-sm text-theme-text focus:outline-none focus:border-theme-primary"
              />
              <span className="text-[10px] text-theme-text-muted block mt-1">
                Compounded monthly alongside current principal
              </span>
            </div>

            {/* Inflow Timing */}
            <div>
              <label className="block text-xs font-semibold text-theme-text mb-1">
                Inflow Timing
              </label>
              <div className="grid grid-cols-2 gap-1.5 mt-1">
                <button
                  type="button"
                  onClick={() => setTiming('END_OF_PERIOD')}
                  className={`px-2 py-1.5 text-xs font-medium rounded-md transition-colors text-center ${
                    timing === 'END_OF_PERIOD'
                      ? 'bg-theme-primary/20 border border-theme-primary text-theme-primary font-bold'
                      : 'bg-theme-bg border border-theme-border text-theme-text-muted hover:text-theme-text'
                  }`}
                >
                  End of Month
                </button>
                <button
                  type="button"
                  onClick={() => setTiming('BEGINNING_OF_PERIOD')}
                  className={`px-2 py-1.5 text-xs font-medium rounded-md transition-colors text-center ${
                    timing === 'BEGINNING_OF_PERIOD'
                      ? 'bg-theme-primary/20 border border-theme-primary text-theme-primary font-bold'
                      : 'bg-theme-bg border border-theme-border text-theme-text-muted hover:text-theme-text'
                  }`}
                >
                  Start of Month
                </button>
              </div>
            </div>
          </div>

          {/* Scenario Tabs */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-theme-border pb-3">
            <div className="flex items-center gap-2">
              {['conservative', 'base', 'optimistic'].map((scenKey) => {
                const scen = scenarios[scenKey];
                const isActive = activeScenario === scenKey && !customRate;
                return (
                  <button
                    key={scenKey}
                    type="button"
                    onClick={() => {
                      setActiveScenario(scenKey);
                      setCustomRate('');
                    }}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors capitalize ${
                      isActive
                        ? 'bg-theme-primary text-black'
                        : 'bg-theme-card border border-theme-border text-theme-text-muted hover:text-theme-text'
                    }`}
                  >
                    {scenKey} ({scen ? `${scen.annual_rate_percent}%` : '--'})
                  </button>
                );
              })}
            </div>

            {/* Custom Rate input */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-theme-text-muted">Custom Rate:</span>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                placeholder="e.g. 11.5"
                value={customRate}
                onChange={(e) => {
                  setCustomRate(e.target.value);
                  if (e.target.value) setActiveScenario('custom');
                }}
                className="w-24 px-2 py-1 bg-theme-bg border border-theme-border rounded text-xs text-theme-text focus:outline-none focus:border-theme-primary"
              />
              <span className="text-xs text-theme-text-muted">%</span>
            </div>
          </div>

          {/* Projection Summary Cards */}
          {isLoading && (
            <div className="py-12 text-center text-sm text-theme-text-muted">
              Calculating deterministic projections...
            </div>
          )}

          {isError && (
            <div className="py-8 text-center text-sm text-rose-400">
              Failed to calculate projections. Please try again.
            </div>
          )}

          {!isLoading && currentScenarioData && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <div className="p-4 rounded-xl bg-theme-card border border-theme-border">
                  <span className="text-[11px] text-theme-text-muted uppercase tracking-wider font-semibold">
                    Current Valuation
                  </span>
                  <div className="text-base font-bold text-theme-text mt-1">
                    {currency} {Number(currentValue).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-theme-card border border-theme-border">
                  <span className="text-[11px] text-theme-text-muted uppercase tracking-wider font-semibold">
                    Total Invested
                  </span>
                  <div className="text-base font-bold text-theme-text mt-1">
                    {currency}{' '}
                    {Number(currentScenarioData.total_invested_capital).toLocaleString('en-IN', {
                      minimumFractionDigits: 2,
                    })}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                  <span className="text-[11px] text-emerald-400 uppercase tracking-wider font-semibold">
                    Estimated Growth
                  </span>
                  <div className="text-base font-bold text-emerald-400 mt-1">
                    +{currency}{' '}
                    {Number(currentScenarioData.total_estimated_growth).toLocaleString('en-IN', {
                      minimumFractionDigits: 2,
                    })}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-theme-primary/10 border border-theme-primary/30">
                  <span className="text-[11px] text-theme-primary uppercase tracking-wider font-semibold flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" />
                    Projected Value
                  </span>
                  <div className="text-lg font-black text-theme-primary mt-1">
                    {currency}{' '}
                    {Number(currentScenarioData.projected_future_value).toLocaleString('en-IN', {
                      minimumFractionDigits: 2,
                    })}
                  </div>
                </div>
              </div>

              {/* Year-by-year trajectory schedule */}
              <div>
                <h4 className="text-xs font-semibold text-theme-text uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-theme-primary" />
                  Year-by-Year Compound Trajectory
                </h4>
                <div className="border border-theme-border rounded-xl overflow-hidden divide-y divide-theme-border">
                  <div className="grid grid-cols-4 p-2.5 bg-theme-card font-semibold text-[11px] text-theme-text-muted uppercase tracking-wider">
                    <div>Timeline</div>
                    <div>Invested Capital</div>
                    <div>Estimated Growth</div>
                    <div className="text-right">Projected Value</div>
                  </div>
                  {currentScenarioData.schedule?.map((item) => {
                    const inv = Number(item.invested_capital);
                    const fv = Number(item.projected_future_value);
                    const gr = Number(item.estimated_growth);
                    return (
                      <div
                        key={item.year}
                        className="grid grid-cols-4 p-2.5 bg-theme-surface hover:bg-theme-card/60 transition-colors text-xs items-center"
                      >
                        <div className="font-semibold text-theme-text">Year {item.year}</div>
                        <div className="text-theme-text-muted">
                          {currency} {inv.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                        <div className="text-emerald-400 font-medium">
                          +{currency} {gr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                        <div className="text-right font-bold text-theme-primary">
                          {currency} {fv.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-theme-border bg-theme-card/40">
          <span className="text-[11px] text-theme-text-muted">
            Formula: Lump Sum Compound + Monthly Annuity Compounding
          </span>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};
