import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardPage } from './DashboardPage';
import * as authHooks from '@/features/authentication/hooks/useAuth';
import * as dashboardHooks from '@/features/dashboard/hooks/useDashboard';
import * as healthHooks from '@/shared/hooks/useHealth';

vi.mock('@/features/authentication/hooks/useAuth', () => ({
  useCurrentUser: vi.fn(),
}));

vi.mock('@/features/dashboard/hooks/useDashboard', () => ({
  useDashboardOverview: vi.fn(),
}));

vi.mock('@/shared/hooks/useHealth', () => ({
  useHealthCheck: vi.fn(),
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
  it('renders welcome message and real zero empty-state when user has no portfolios', () => {
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

    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: { status: 'healthy', database: 'connected' },
      isLoading: false,
      isError: false,
    });

    renderWithProviders(<DashboardPage />);

    expect(screen.getByText(/welcome back, ayush kumar!/i)).toBeInTheDocument();
    expect(screen.getByText(/portfolios created/i)).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText(/you haven't created a portfolio yet/i)).toBeInTheDocument();
    expect(screen.getByText(/postgresql connected/i)).toBeInTheDocument();
  });

  it('renders actual portfolios when user has created portfolios', () => {
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
        portfolio_count: 2,
        recent_portfolios: [
          {
            id: 'p-1',
            name: 'Long Term Index Fund',
            base_currency: 'INR',
            created_at: '2026-11-10T12:00:00Z',
          },
          {
            id: 'p-2',
            name: 'US Tech Equities',
            base_currency: 'USD',
            created_at: '2026-11-10T14:00:00Z',
          },
        ],
      },
      isLoading: false,
    });

    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: { status: 'healthy', database: 'connected' },
      isLoading: false,
      isError: false,
    });

    renderWithProviders(<DashboardPage />);

    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Long Term Index Fund')).toBeInTheDocument();
    expect(screen.getByText('US Tech Equities')).toBeInTheDocument();
  });
});
