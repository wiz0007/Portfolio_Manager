import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ForgotPasswordPage } from './ForgotPasswordPage';

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

describe('ForgotPasswordPage', () => {
  it('renders forgot password form elements properly', () => {
    renderWithProviders(<ForgotPasswordPage />);

    expect(screen.getByRole('heading', { name: /forgot password\?/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/name@example.com/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /back to sign in/i })).toBeInTheDocument();
  });

  it('validates empty email submission', async () => {
    renderWithProviders(<ForgotPasswordPage />);

    const submitBtn = screen.getByRole('button', { name: /send reset link/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
    });
  });

  it('submits valid email and transitions to confirmation screen', async () => {
    renderWithProviders(<ForgotPasswordPage />);

    const input = screen.getByPlaceholderText(/name@example.com/i);
    fireEvent.change(input, { target: { value: 'alex@example.com' } });

    const submitBtn = screen.getByRole('button', { name: /send reset link/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /check your email/i })).toBeInTheDocument();
      expect(screen.getByText(/alex@example.com/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /resend email/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /return to sign in/i })).toBeInTheDocument();
    });
  });
});

