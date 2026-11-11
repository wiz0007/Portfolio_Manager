import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { VerifyEmailPage } from './VerifyEmailPage';
import * as authHooks from '../hooks/useAuth';

vi.mock('../hooks/useAuth', () => ({
  useVerifyEmail: vi.fn(),
  useResendVerification: vi.fn(),
  useCurrentUser: vi.fn(),
}));

const renderWithProviders = (initialRoute = '/verify-email?token=valid-token') => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <VerifyEmailPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('VerifyEmailPage', () => {
  it('calls verifyEmail when token is present in search params', () => {
    const mockVerify = vi.fn();
    (authHooks.useVerifyEmail as any).mockReturnValue({
      mutate: mockVerify,
      isPending: true,
    });
    (authHooks.useResendVerification as any).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: null,
    });

    renderWithProviders('/verify-email?token=my-secret-token');

    expect(mockVerify).toHaveBeenCalledWith(
      { token: 'my-secret-token' },
      expect.any(Object)
    );
    expect(screen.getByText(/verifying your email.../i)).toBeInTheDocument();
  });

  it('shows invalid state when token is missing', () => {
    (authHooks.useVerifyEmail as any).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    (authHooks.useResendVerification as any).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: null,
    });

    renderWithProviders('/verify-email');

    expect(screen.getByText(/invalid verification link/i)).toBeInTheDocument();
  });
});
