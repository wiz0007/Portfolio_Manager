import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthenticatedLayout } from './AuthenticatedLayout';
import * as authHooks from '@/features/authentication/hooks/useAuth';
import * as healthHooks from '@/shared/hooks/useHealth';

vi.mock('@/features/authentication/hooks/useAuth', () => ({
  useCurrentUser: vi.fn(),
  useLogout: vi.fn(),
}));

vi.mock('@/shared/hooks/useHealth', () => ({
  useHealthCheck: vi.fn(),
}));

const renderLayout = (initialRoute = '/dashboard') => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route element={<AuthenticatedLayout />}>
            <Route path="/dashboard" element={<div>Dashboard Content</div>} />
            <Route path="/portfolios" element={<div>Portfolios Content</div>} />
            <Route path="/settings/profile" element={<div>Profile Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('AuthenticatedLayout', () => {
  it('renders sidebar navigation links and active page title', () => {
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: {
        id: '123-uuid',
        full_name: 'Jane Doe',
        email: 'jane@example.com',
      },
      isLoading: false,
    });
    (authHooks.useLogout as any).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: { status: 'healthy', database: 'connected' },
      isLoading: false,
      isError: false,
    });

    renderLayout('/dashboard');

    expect(screen.getAllByText(/portfolio manager/i)[0]).toBeInTheDocument();
    expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
    expect(screen.getAllByText('Portfolios')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Analytics')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Watchlist')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Profile')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Account')[0]).toBeInTheDocument();
    expect(screen.getByText('Dashboard Content')).toBeInTheDocument();
  });

  it('triggers logout when logout button is clicked', () => {
    const mockLogout = vi.fn();
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: {
        id: '123-uuid',
        full_name: 'Jane Doe',
        email: 'jane@example.com',
      },
      isLoading: false,
    });
    (authHooks.useLogout as any).mockReturnValue({
      mutate: mockLogout,
      isPending: false,
    });
    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: { status: 'healthy', database: 'connected' },
      isLoading: false,
      isError: false,
    });

    renderLayout('/dashboard');

    const logoutButtons = screen.getAllByTitle('Log out');
    if (logoutButtons.length > 0) {
      fireEvent.click(logoutButtons[0]);
      expect(mockLogout).toHaveBeenCalled();
    }
  });

  it('displays DB: Checking... when health status is loading', () => {
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: { id: '123-uuid', full_name: 'Jane Doe', email: 'jane@example.com' },
      isLoading: false,
    });
    (authHooks.useLogout as any).mockReturnValue({ mutate: vi.fn(), isPending: false });
    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });

    renderLayout('/dashboard');
    expect(screen.getAllByText('DB: Checking...')[0]).toBeInTheDocument();
  });

  it('displays DB: Unavailable when health check fails or reports disconnected', () => {
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: { id: '123-uuid', full_name: 'Jane Doe', email: 'jane@example.com' },
      isLoading: false,
    });
    (authHooks.useLogout as any).mockReturnValue({ mutate: vi.fn(), isPending: false });
    (healthHooks.useHealthCheck as any).mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
    });

    renderLayout('/dashboard');
    expect(screen.getAllByText('DB: Unavailable')[0]).toBeInTheDocument();
  });
});
