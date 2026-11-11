import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProfilePage } from './ProfilePage';
import * as authHooks from '@/features/authentication/hooks/useAuth';

vi.mock('@/features/authentication/hooks/useAuth', () => ({
  useCurrentUser: vi.fn(),
  useUpdateProfile: vi.fn(),
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

describe('ProfilePage', () => {
  it('displays user profile information and allows updating full_name', async () => {
    const mockUpdateProfile = vi.fn();
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: {
        id: 'u-456',
        full_name: 'John Doe',
        email: 'john@example.com',
        date_joined: '2026-01-01T00:00:00Z',
      },
    });

    (authHooks.useUpdateProfile as any).mockReturnValue({
      mutate: mockUpdateProfile,
      isPending: false,
      error: null,
    });

    renderWithProviders(<ProfilePage />);

    expect(screen.getByText('Profile Settings')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
    expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument();

    const nameInput = screen.getByLabelText(/full name/i);
    fireEvent.change(nameInput, { target: { value: 'Johnathan Doe' } });

    const saveButton = screen.getByRole('button', { name: /save changes/i });
    expect(saveButton).not.toBeDisabled();
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockUpdateProfile).toHaveBeenCalledWith(
        { full_name: 'Johnathan Doe' },
        expect.anything()
      );
    });
  });

  it('rejects submissions with name less than 2 characters', async () => {
    (authHooks.useCurrentUser as any).mockReturnValue({
      data: {
        id: 'u-456',
        full_name: 'John Doe',
        email: 'john@example.com',
        date_joined: '2026-01-01T00:00:00Z',
      },
    });

    (authHooks.useUpdateProfile as any).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      error: null,
    });

    renderWithProviders(<ProfilePage />);

    const nameInput = screen.getByLabelText(/full name/i);
    fireEvent.change(nameInput, { target: { value: 'J' } });

    const saveButton = screen.getByRole('button', { name: /save changes/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/full name must be at least 2 characters/i)).toBeInTheDocument();
    });
  });
});
