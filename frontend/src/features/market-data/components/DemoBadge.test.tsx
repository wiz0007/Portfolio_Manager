import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DemoBadge } from './DemoBadge';

describe('DemoBadge', () => {
  it('renders standard inline badge with demo indicator text', () => {
    render(<DemoBadge />);
    expect(screen.getByText('DEMO DATA')).toBeInTheDocument();
  });

  it('renders prominent banner mode when isBanner is true', () => {
    render(<DemoBadge isBanner />);
    expect(screen.getByText(/DEMO MODE ACTIVE:/i)).toBeInTheDocument();
    expect(screen.getByText(/Prices shown are synthetic values/i)).toBeInTheDocument();
    expect(screen.getByText(/Awaiting vendor credentials/i)).toBeInTheDocument();
  });
});
