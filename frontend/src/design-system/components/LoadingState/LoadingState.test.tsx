import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingState } from './LoadingState';

describe('LoadingState Component', () => {
  it('renders loading status message', () => {
    render(<LoadingState message="Fetching market data..." />);
    expect(screen.getByRole('status')).toBeDefined();
    expect(screen.getByText('Fetching market data...')).toBeDefined();
  });
});

