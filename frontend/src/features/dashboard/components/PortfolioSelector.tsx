import React from 'react';
import { Briefcase, Layers } from 'lucide-react';
import { usePortfolios } from '@/features/portfolios/hooks/usePortfolios';

interface PortfolioSelectorProps {
  selectedPortfolioId?: string;
  onSelectPortfolio: (id?: string) => void;
  className?: string;
}

export const PortfolioSelector: React.FC<PortfolioSelectorProps> = ({
  selectedPortfolioId,
  onSelectPortfolio,
  className = '',
}) => {
  const { data: portfolios, isLoading } = usePortfolios();

  if (isLoading || !portfolios || portfolios.length === 0) {
    return null;
  }

  return (
    <div className={`flex items-center gap-2 flex-wrap ${className}`}>
      <label htmlFor="portfolio-scope-select" className="text-xs font-semibold text-theme-text-muted flex items-center gap-1.5 uppercase tracking-wider">
        <Briefcase className="h-3.5 w-3.5 text-theme-primary" />
        <span>Portfolio Scope:</span>
      </label>

      <div className="relative inline-block">
        <select
          id="portfolio-scope-select"
          value={selectedPortfolioId || 'all'}
          onChange={(e) => {
            const val = e.target.value;
            onSelectPortfolio(val === 'all' ? undefined : val);
          }}
          className="appearance-none rounded-xl border border-theme-border bg-theme-surface py-1.5 pl-3 pr-8 text-xs font-semibold text-theme-text shadow-sm focus:border-theme-primary focus:outline-none focus:ring-1 focus:ring-theme-primary transition-all cursor-pointer hover:bg-theme-hover"
        >
          <option value="all">
            All Portfolios (Combined View)
          </option>
          {portfolios.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} ({p.base_currency})
            </option>
          ))}
        </select>
        <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2.5 text-theme-text-muted">
          <Layers className="h-3 w-3" />
        </span>
      </div>
    </div>
  );
};
