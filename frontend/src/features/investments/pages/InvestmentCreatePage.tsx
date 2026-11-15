import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { usePortfolios } from '@/features/portfolios/hooks/usePortfolios';
import { InvestmentEntryFlow } from '../components/InvestmentEntryFlow/InvestmentEntryFlow';

export const InvestmentCreatePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const portfolioIdParam = searchParams.get('portfolioId') || undefined;
  const categoryParam = searchParams.get('category') || undefined;
  const typeParam = searchParams.get('type') || undefined;
  const { data: portfolios = [], isLoading } = usePortfolios();

  const handleNavigateStep = (params: { portfolioId?: string; category?: string; type?: string }) => {
    const nextParams = new URLSearchParams();
    if (params.portfolioId) nextParams.set('portfolioId', params.portfolioId);
    if (params.category) nextParams.set('category', params.category);
    if (params.type) nextParams.set('type', params.type);
    setSearchParams(nextParams, { replace: true });
  };

  return (
    <div style={{ padding: '0.5rem 0', width: '100%' }}>
      <InvestmentEntryFlow
        portfolios={portfolios}
        initialPortfolioId={portfolioIdParam}
        initialCategoryId={categoryParam}
        initialTypeId={typeParam}
        onNavigateStep={handleNavigateStep}
        isLoadingPortfolios={isLoading}
      />
    </div>
  );
};
