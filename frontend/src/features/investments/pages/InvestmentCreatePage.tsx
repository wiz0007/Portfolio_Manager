import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { usePortfolios } from '@/features/portfolios/hooks/usePortfolios';
import { InvestmentEntryFlow } from '../components/InvestmentEntryFlow/InvestmentEntryFlow';

export const InvestmentCreatePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const portfolioIdParam = searchParams.get('portfolioId') || undefined;
  const categoryParam = searchParams.get('category') || undefined;
  const typeParam = searchParams.get('type') || undefined;
  const instrumentIdParam = searchParams.get('instrument_id') || undefined;
  const symbolParam = searchParams.get('symbol') || undefined;
  const nameParam = searchParams.get('name') || undefined;
  const { data: portfolios = [], isLoading } = usePortfolios();

  const handleNavigateStep = (params: { portfolioId?: string; category?: string; type?: string }) => {
    const nextParams = new URLSearchParams();
    if (params.portfolioId) nextParams.set('portfolioId', params.portfolioId);
    if (params.category) nextParams.set('category', params.category);
    if (params.type) nextParams.set('type', params.type);
    if (instrumentIdParam) nextParams.set('instrument_id', instrumentIdParam);
    if (symbolParam) nextParams.set('symbol', symbolParam);
    if (nameParam) nextParams.set('name', nameParam);
    setSearchParams(nextParams, { replace: true });
  };

  return (
    <div style={{ padding: '0.5rem 0', width: '100%' }}>
      <InvestmentEntryFlow
        portfolios={portfolios}
        initialPortfolioId={portfolioIdParam}
        initialCategoryId={categoryParam}
        initialTypeId={typeParam}
        initialInstrumentId={instrumentIdParam}
        initialSymbol={symbolParam}
        initialName={nameParam}
        onNavigateStep={handleNavigateStep}
        isLoadingPortfolios={isLoading}
      />
    </div>
  );
};
