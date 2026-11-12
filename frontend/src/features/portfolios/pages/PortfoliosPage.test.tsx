import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PortfoliosPage } from './PortfoliosPage';
import * as portfolioHooks from '../hooks/usePortfolios';

vi.mock('../hooks/usePortfolios', () => ({
  usePortfolios: vi.fn(),
  useDeletePortfolio: vi.fn(),
}));

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe('PortfoliosPage', () => {
  it('renders empty state when user has no portfolios', () => {
    (portfolioHooks.usePortfolios as any).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });
    (portfolioHooks.useDeletePortfolio as any).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });

    renderWithProviders(<PortfoliosPage />);

    expect(screen.getByText('No Portfolios Found')).toBeInTheDocument();
    expect(screen.getByText('Create Your First Portfolio')).toBeInTheDocument();
  });

  it('renders portfolio cards when portfolios exist', () => {
    (portfolioHooks.usePortfolios as any).mockReturnValue({
      data: [
        {
          id: 'p-1',
          name: 'Retirement Growth',
          description: 'Long term index funds',
          base_currency: 'INR',
          created_at: '2026-11-10T10:00:00Z',
          updated_at: '2026-11-10T10:00:00Z',
        },
      ],
      isLoading: false,
      isError: false,
    });
    (portfolioHooks.useDeletePortfolio as any).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });

    renderWithProviders(<PortfoliosPage />);

    expect(screen.getByText('Retirement Growth')).toBeInTheDocument();
    expect(screen.getByText('Long term index funds')).toBeInTheDocument();
    expect(screen.getByText('INR')).toBeInTheDocument();
    expect(screen.getByText(/view details/i)).toBeInTheDocument();
  });

  it('opens delete confirmation modal when delete button is clicked', () => {
    (portfolioHooks.usePortfolios as any).mockReturnValue({
      data: [
        {
          id: 'p-1',
          name: 'Test Portfolio To Delete',
          description: '',
          base_currency: 'USD',
          created_at: '2026-11-10T10:00:00Z',
          updated_at: '2026-11-10T10:00:00Z',
        },
      ],
      isLoading: false,
      isError: false,
    });
    (portfolioHooks.useDeletePortfolio as any).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });

    renderWithProviders(<PortfoliosPage />);

    const deleteBtn = screen.getByTitle('Delete portfolio');
    fireEvent.click(deleteBtn);

    expect(screen.getByText(/are you sure you want to delete/i)).toBeInTheDocument();
    expect(screen.getByText(/"Test Portfolio To Delete"/i)).toBeInTheDocument();
  });
});
