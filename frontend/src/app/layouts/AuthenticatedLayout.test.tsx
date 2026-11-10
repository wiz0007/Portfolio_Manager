import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthenticatedLayout } from './AuthenticatedLayout';
import * as authHooks from '@/features/authentication/hooks/useAuth';

vi.mock('@/features/authentication/hooks/useAuth', () => ({
  useCurrentUser: vi.fn(),
  useLogout: vi.fn(),
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

    renderLayout('/dashboard');

    const logoutButtons = screen.getAllByTitle('Log out');
    if (logoutButtons.length > 0) {
      fireEvent.click(logoutButtons[0]);
      expect(mockLogout).toHaveBeenCalled();
    }
  });
});
