import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
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
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading UI and skeletons when dashboard request is pending (no empty state, no false zero)', () => {
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: {
        id: 'u-123',
        full_name: 'Ayush Kumar',
        email: 'ayush@example.com',
      },
    });

    (dashboardHooks.useDashboardOverview as any).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    });

    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: { status: 'healthy', database: 'connected' },
      isLoading: false,
      isError: false,
    });

    renderWithProviders(<DashboardPage />);

    expect(screen.getByText(/welcome back, ayush kumar!/i)).toBeInTheDocument();
    expect(screen.getByText('Loading active portfolios...')).toBeInTheDocument();
    // Must NOT show 0 or empty state message
    expect(screen.queryByText('No active portfolios yet')).not.toBeInTheDocument();
    expect(screen.queryByText(/you haven't created a portfolio yet/i)).not.toBeInTheDocument();
    // Must NOT show error banner
    expect(screen.queryByText(/unable to load dashboard overview/i)).not.toBeInTheDocument();
  });

  it('renders zero count and empty state when API successfully returns zero portfolios', () => {
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
      isError: false,
      refetch: vi.fn(),
    });

    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: { status: 'healthy', database: 'connected' },
      isLoading: false,
      isError: false,
    });

    renderWithProviders(<DashboardPage />);

    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('No active portfolios yet')).toBeInTheDocument();
    expect(screen.getByText(/you haven't created a portfolio yet/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create portfolio/i })).toBeInTheDocument();
    // Ensure primary currency metric is not displayed
    expect(screen.queryByText(/primary currency/i)).not.toBeInTheDocument();
    // Ensure error banner is not displayed
    expect(screen.queryByText(/unable to load dashboard overview/i)).not.toBeInTheDocument();
  });

  it('renders actual portfolios and count when API returns valid portfolios, without primary currency metric', () => {
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
      isError: false,
      refetch: vi.fn(),
    });

    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: { status: 'healthy', database: 'connected' },
      isLoading: false,
      isError: false,
    });

    renderWithProviders(<DashboardPage />);

    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('2 active portfolios')).toBeInTheDocument();
    expect(screen.getByText('Long Term Index Fund')).toBeInTheDocument();
    expect(screen.getByText('INR')).toBeInTheDocument();
    expect(screen.getByText('US Tech Equities')).toBeInTheDocument();
    expect(screen.getByText('USD')).toBeInTheDocument();
    // Ensure no misleading primary currency metric exists
    expect(screen.queryByText(/primary currency/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/you haven't created a portfolio yet/i)).not.toBeInTheDocument();
  });

  it('renders error state banner with retry button when query fails without cached data (no empty state)', () => {
    const mockRefetch = vi.fn();
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: {
        id: 'u-123',
        full_name: 'Ayush Kumar',
        email: 'ayush@example.com',
      },
    });

    (dashboardHooks.useDashboardOverview as any).mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      refetch: mockRefetch,
    });

    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: { status: 'healthy', database: 'connected' },
      isLoading: false,
      isError: false,
    });

    renderWithProviders(<DashboardPage />);

    expect(screen.getByText(/unable to load dashboard overview/i)).toBeInTheDocument();
    expect(screen.getByText('Unable to load count')).toBeInTheDocument();
    // Must NOT show empty state when request fails
    expect(screen.queryByText(/you haven't created a portfolio yet/i)).not.toBeInTheDocument();

    const retryBtns = screen.getAllByRole('button', { name: /retry/i });
    expect(retryBtns.length).toBeGreaterThan(0);
    fireEvent.click(retryBtns[0]);
    expect(mockRefetch).toHaveBeenCalled();
  });

  it('preserves existing content when refetch fails after previously successful load', () => {
    const mockRefetch = vi.fn();
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: { id: 'u-123', full_name: 'Ayush Kumar', email: 'ayush@example.com' },
    });

    // Cached data is present, but isError is true (background refetch failed)
    (dashboardHooks.useDashboardOverview as any).mockReturnValue({
      data: {
        user: { id: 'u-123', full_name: 'Ayush Kumar', email: 'ayush@example.com' },
        portfolio_count: 1,
        recent_portfolios: [
          {
            id: 'p-1',
            name: 'Long Term Index Fund',
            base_currency: 'INR',
            created_at: '2026-11-10T12:00:00Z',
          },
        ],
      },
      isLoading: false,
      isError: true,
      refetch: mockRefetch,
    });

    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: { status: 'healthy', database: 'connected' },
      isLoading: false,
      isError: false,
    });

    renderWithProviders(<DashboardPage />);

    // Existing data remains visible
    expect(screen.getByText('Long Term Index Fund')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    // Warning banner is displayed for the failed refetch
    expect(screen.getByText(/unable to load dashboard overview/i)).toBeInTheDocument();
    // NOT replaced with empty state
    expect(screen.queryByText(/you haven't created a portfolio yet/i)).not.toBeInTheDocument();
  });

  it('displays Checking connection... when database health check is loading', () => {
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: { id: 'u-123', full_name: 'Ayush Kumar', email: 'ayush@example.com' },
    });
    (dashboardHooks.useDashboardOverview as any).mockReturnValue({
      data: { user: { id: 'u-123', full_name: 'Ayush Kumar', email: 'ayush@example.com' }, portfolio_count: 0, recent_portfolios: [] },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });

    renderWithProviders(<DashboardPage />);

    const checkingElements = screen.getAllByText(/checking connection\.\.\./i);
    expect(checkingElements.length).toBeGreaterThan(0);
    expect(screen.queryByText(/service connected/i)).not.toBeInTheDocument();
  });

  it('displays Service connected when database health check succeeds', () => {
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: { id: 'u-123', full_name: 'Ayush Kumar', email: 'ayush@example.com' },
    });
    (dashboardHooks.useDashboardOverview as any).mockReturnValue({
      data: { user: { id: 'u-123', full_name: 'Ayush Kumar', email: 'ayush@example.com' }, portfolio_count: 0, recent_portfolios: [] },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: { status: 'healthy', database: 'connected' },
      isLoading: false,
      isError: false,
    });

    renderWithProviders(<DashboardPage />);

    const connectedElements = screen.getAllByText(/service connected/i);
    expect(connectedElements.length).toBeGreaterThan(0);
  });

  it('displays Connection unavailable when database health check fails, without crashing dashboard', () => {
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: { id: 'u-123', full_name: 'Ayush Kumar', email: 'ayush@example.com' },
    });
    (dashboardHooks.useDashboardOverview as any).mockReturnValue({
      data: { user: { id: 'u-123', full_name: 'Ayush Kumar', email: 'ayush@example.com' }, portfolio_count: 0, recent_portfolios: [] },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
    });

    renderWithProviders(<DashboardPage />);

    const unavailableElements = screen.getAllByText(/connection unavailable/i);
    expect(unavailableElements.length).toBeGreaterThan(0);
    // Dashboard content remains rendered and functional
    expect(screen.getByText(/welcome back, ayush kumar!/i)).toBeInTheDocument();
    expect(screen.getByText(/you haven't created a portfolio yet/i)).toBeInTheDocument();
  });
});
