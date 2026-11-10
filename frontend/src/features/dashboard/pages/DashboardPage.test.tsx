import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardPage } from './DashboardPage';
import * as authHooks from '@/features/authentication/hooks/useAuth';
import * as dashboardHooks from '@/features/dashboard/hooks/useDashboard';

vi.mock('@/features/authentication/hooks/useAuth', () => ({
  useCurrentUser: vi.fn(),
}));

vi.mock('@/features/dashboard/hooks/useDashboard', () => ({
  useDashboardOverview: vi.fn(),
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

describe('DashboardPage', () => {
  it('renders welcome message and real zero empty-state without fake financial values', () => {
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: {
        id: 'u-123',
        full_name: 'Ayush Kumar',
        email: 'ayush@example.com',
      },
    });

    (dashboardHooks.useDashboardOverview as any).mockReturnValue({
      data: {
        user: {
          id: 'u-123',
          full_name: 'Ayush Kumar',
          email: 'ayush@example.com',
        },
        portfolio_count: 0,
        recent_portfolios: [],
      },
      isLoading: false,
    });

    renderWithProviders(<DashboardPage />);

    expect(screen.getByText(/welcome back, ayush kumar!/i)).toBeInTheDocument();
    expect(screen.getByText(/portfolios created/i)).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText(/you haven't created a portfolio yet/i)).toBeInTheDocument();
    expect(screen.getByText(/portfolio management and multi-asset tracking/i)).toBeInTheDocument();
    expect(screen.getAllByText(/neon postgresql/i)[0]).toBeInTheDocument();
  });
});
