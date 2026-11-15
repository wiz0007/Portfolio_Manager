import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HoldingsList } from '../components/HoldingsList/HoldingsList';
import { InvestmentListItem } from '../types/investmentApiTypes';

const mockInvestments: InvestmentListItem[] = [
  {
    id: 'inv-1',
    portfolio: 'port-1',
    category: 'equity',
    asset_type: 'listed_stock',
    display_name: 'Tata Consultancy Services (TCS)',
    currency: 'INR',
    is_active: true,
    valuation_method: 'MANUAL',
    initial_value: 200055,
    current_value: 220000,
    created_at: '2026-11-01T10:00:00Z',
    updated_at: '2026-11-01T10:00:00Z',
  },
  {
    id: 'inv-2',
    portfolio: 'port-1',
    category: 'real_estate',
    asset_type: 'land_plot',
    display_name: 'Dehradun Mango Orchard',
    currency: 'INR',
    is_active: true,
    valuation_method: 'USER_ESTIMATE',
    initial_value: 5400000,
    current_value: 5800000,
    created_at: '2026-11-02T10:00:00Z',
    updated_at: '2026-11-02T10:00:00Z',
  },
];

const renderComponent = (investments: InvestmentListItem[] = mockInvestments) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <HoldingsList
          portfolioId="port-1"
          baseCurrency="INR"
          investments={investments}
        />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('HoldingsList Component', () => {
  it('renders empty state when there are no investments in the portfolio', () => {
    renderComponent([]);
    expect(screen.getByText(/No Holdings Found/i)).toBeInTheDocument();
    expect(screen.getByText(/This portfolio has no recorded investments yet/i)).toBeInTheDocument();
  });

  it('renders summary statistics and holdings table when investments exist', () => {
    renderComponent();

    // Summary cards
    expect(screen.getByText('Total Holdings')).toBeInTheDocument();
    expect(screen.getByText('Capital Invested')).toBeInTheDocument();
    expect(screen.getByText('Current Valuation')).toBeInTheDocument();

    // Holdings rows
    expect(screen.getByText('Tata Consultancy Services (TCS)')).toBeInTheDocument();
    expect(screen.getByText('Dehradun Mango Orchard')).toBeInTheDocument();
  });

  it('filters investments by category when filter pill is clicked', () => {
    renderComponent();

    // Click on Real Estate filter
    const realEstateBtn = screen.getByRole('button', { name: /Real Estate/i });
    fireEvent.click(realEstateBtn);

    // Land plot should remain, stock should be filtered out
    expect(screen.getByText('Dehradun Mango Orchard')).toBeInTheDocument();
    expect(screen.queryByText('Tata Consultancy Services (TCS)')).not.toBeInTheDocument();
  });

  it('opens delete confirmation modal when delete action is clicked', () => {
    renderComponent();

    const deleteButtons = screen.getAllByTitle('Delete holding');
    fireEvent.click(deleteButtons[0]);

    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getByText(/Delete Investment Holding\?/i)).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: /Delete Holding/i })).toBeInTheDocument();
  });
});
