import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RegisterPage } from './RegisterPage';

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

describe('RegisterPage', () => {
  beforeEach(() => {
    delete (window as any).google;
  });
  it('renders registration form elements properly', () => {
    renderWithProviders(<RegisterPage />);

    expect(screen.getByRole('heading', { name: /create an account/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign up with google/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/john doe/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/name@example.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/minimum 8 characters/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/repeat your password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument();
  });

  it('displays validation errors on empty submission', async () => {
    renderWithProviders(<RegisterPage />);

    const submitBtn = screen.getByRole('button', { name: /create account/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/full name must be at least 2 characters/i)).toBeInTheDocument();
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument();
    });
  });

  it('validates password mismatch correctly', async () => {
    renderWithProviders(<RegisterPage />);

    fireEvent.change(screen.getByPlaceholderText(/john doe/i), { target: { value: 'Jane Doe' } });
    fireEvent.change(screen.getByPlaceholderText(/name@example.com/i), { target: { value: 'jane@example.com' } });
    fireEvent.change(screen.getByPlaceholderText(/minimum 8 characters/i), { target: { value: 'Password123!' } });
    fireEvent.change(screen.getByPlaceholderText(/repeat your password/i), { target: { value: 'DifferentPass123!' } });

    const submitBtn = screen.getByRole('button', { name: /create account/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
  });

  it('handles Google sign up action', () => {
    const requestTokenMock = vi.fn();
    (window as any).google = {
      accounts: {
        oauth2: {
          initTokenClient: vi.fn(() => ({
            requestAccessToken: requestTokenMock,
          })),
        },
      },
    };

    renderWithProviders(<RegisterPage />);

    const googleBtn = screen.getByRole('button', { name: /sign up with google/i });
    fireEvent.click(googleBtn);

    expect(requestTokenMock).toHaveBeenCalled();
  });
});
