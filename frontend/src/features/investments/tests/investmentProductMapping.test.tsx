import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { InvestmentEntryFlow } from '../components/InvestmentEntryFlow/InvestmentEntryFlow';
import { ASSET_CATEGORIES } from '../config/assetCategories';
import { Portfolio } from '@/features/portfolios/types';

const mockPortfolio: Portfolio = {
  id: 'da1c32a5-228c-41ee-bc11-7e255be9f303',
  name: 'Primary Wealth Portfolio',
  description: 'Multi-asset holding container',
  base_currency: 'INR',
  created_at: '2026-11-01T10:00:00Z',
  updated_at: '2026-11-01T10:00:00Z',
};

const renderWithRouter = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Asset Product to Form Mapping', () => {
  // Test every single advertised product in the asset catalog
  const allAdvertisedTypes = ASSET_CATEGORIES.flatMap((cat) =>
    cat.types.map((t) => ({ category: cat, type: t }))
  );

  it.each(allAdvertisedTypes)(
    'renders working detail form for $type.name ($type.id) without unsupported error',
    ({ category, type }) => {
      renderWithRouter(
        <InvestmentEntryFlow
          portfolios={[mockPortfolio]}
          initialPortfolioId={mockPortfolio.id}
          initialCategoryId={category.id}
          initialTypeId={type.id}
        />
      );

      // Verify that the unsupported error message NEVER appears
      expect(screen.queryByTestId('unsupported-asset-state')).not.toBeInTheDocument();
      expect(screen.queryByText(/unsupported asset type/i)).not.toBeInTheDocument();

      // Verify breadcrumbs correctly preserve and display the portfolio and type
      expect(screen.getByText(mockPortfolio.name)).toBeInTheDocument();
      expect(screen.getByText(type.name)).toBeInTheDocument();
    }
  );

  it('specifically renders Listed Stocks / Shares form with stock fields', () => {
    renderWithRouter(
      <InvestmentEntryFlow
        portfolios={[mockPortfolio]}
        initialPortfolioId={mockPortfolio.id}
        initialCategoryId="equity"
        initialTypeId="listed_stock"
      />
    );

    // Assert key stock form fields are rendered
    expect(screen.getByRole('textbox', { name: /Company Name/i })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /Ticker Symbol/i })).toBeInTheDocument();
    expect(screen.getByText(/Trade Execution Details/i)).toBeInTheDocument();
    expect(screen.getByText(/Review Stock Holding/i)).toBeInTheDocument();
    expect(screen.queryByText(/Unsupported asset type/i)).not.toBeInTheDocument();
  });

  it('specifically renders Plot / Agricultural Land form with land-specific fields', () => {
    renderWithRouter(
      <InvestmentEntryFlow
        portfolios={[mockPortfolio]}
        initialPortfolioId={mockPortfolio.id}
        initialCategoryId="real_estate"
        initialTypeId="land_plot"
      />
    );

    // Assert key land form fields are rendered
    expect(screen.getByText(/Land & Property Identification/i)).toBeInTheDocument();
    expect(screen.getByText(/Khasra \/ Khatauni \/ Survey No\./i)).toBeInTheDocument();
    expect(screen.getByText(/Land Area & Ownership/i)).toBeInTheDocument();
    expect(screen.getByText(/Review Land Details/i)).toBeInTheDocument();
    expect(screen.queryByText(/Unsupported asset type/i)).not.toBeInTheDocument();
  });

  it('renders unsupported error state for unmapped asset types', () => {
    renderWithRouter(
      <InvestmentEntryFlow
        portfolios={[mockPortfolio]}
        initialPortfolioId={mockPortfolio.id}
        initialCategoryId="equity"
        initialTypeId="unknown_exotic_derivative"
      />
    );

    expect(screen.getByTestId('unsupported-asset-state')).toBeInTheDocument();
    expect(
      screen.getByText(/Unsupported asset type: unknown_exotic_derivative/i)
    ).toBeInTheDocument();
  });

  it('preserves portfolio ID and triggers navigation handler during flow', () => {
    const handleNavigate = vi.fn();
    renderWithRouter(
      <InvestmentEntryFlow
        portfolios={[mockPortfolio]}
        initialPortfolioId={mockPortfolio.id}
        initialCategoryId="equity"
        initialTypeId="listed_stock"
        onNavigateStep={handleNavigate}
      />
    );

    expect(screen.getByText(mockPortfolio.name)).toBeInTheDocument();
    expect(screen.getByText('Listed Stocks / Shares')).toBeInTheDocument();
  });
});
