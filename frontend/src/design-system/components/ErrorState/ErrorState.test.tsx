import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorState } from './ErrorState';

describe('ErrorState Component', () => {
  it('renders title, error message, and handles retry', () => {
    const handleRetry = vi.fn();
    render(<ErrorState title="Connection Lost" message="Network error" onRetry={handleRetry} />);

    expect(screen.getByRole('alert')).toBeDefined();
    expect(screen.getByText('Connection Lost')).toBeDefined();
    expect(screen.getByText('Network error')).toBeDefined();

    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });
});

