import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AccountPage } from './AccountPage';
import * as authHooks from '@/features/authentication/hooks/useAuth';

vi.mock('@/features/authentication/hooks/useAuth', () => ({
  useCurrentUser: vi.fn(),
  useLogout: vi.fn(),
  useResendVerification: vi.fn(),
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

describe('AccountPage', () => {
  it('displays verified account status and provides sign out capability', () => {
    const mockLogout = vi.fn();
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: {
        id: 'u-789',
        full_name: 'Alice Smith',
        email: 'alice@example.com',
        is_active: true,
        is_email_verified: true,
      },
    });

    (authHooks.useLogout as any).mockReturnValue({
      mutate: mockLogout,
      isPending: false,
    });

    (authHooks.useResendVerification as any).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });

    renderWithProviders(<AccountPage />);

    expect(screen.getByText('Account Settings')).toBeInTheDocument();
    expect(screen.getByText('alice@example.com')).toBeInTheDocument();
    expect(screen.getByText('Verified')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();

    const signOutBtn = screen.getByRole('button', { name: /sign out/i });
    expect(signOutBtn).toBeInTheDocument();
    fireEvent.click(signOutBtn);

    expect(mockLogout).toHaveBeenCalled();
  });

  it('displays unverified status and allows resending verification link', () => {
    const mockResend = vi.fn();
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: {
        id: 'u-789',
        full_name: 'Bob Unverified',
        email: 'bob@example.com',
        is_active: true,
        is_email_verified: false,
      },
    });

    (authHooks.useLogout as any).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });

    (authHooks.useResendVerification as any).mockReturnValue({
      mutate: mockResend,
      isPending: false,
    });

    renderWithProviders(<AccountPage />);

    expect(screen.getByText('Unverified')).toBeInTheDocument();
    const resendBtn = screen.getByRole('button', { name: /resend verification link/i });
    expect(resendBtn).toBeInTheDocument();

    fireEvent.click(resendBtn);
    expect(mockResend).toHaveBeenCalled();
  });
});
