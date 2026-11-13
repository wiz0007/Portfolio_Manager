import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PageHeader } from './PageHeader';

describe('PageHeader Component', () => {
  it('renders title, description and action slot', () => {
    render(
      <PageHeader
        title="Portfolios"
        description="Manage your multi-asset investment portfolios."
        actions={<button>New Portfolio</button>}
      />
    );

    expect(screen.getByRole('heading', { level: 1, name: 'Portfolios' })).toBeDefined();
    expect(screen.getByText(/manage your multi-asset investment portfolios/i)).toBeDefined();
    expect(screen.getByRole('button', { name: /new portfolio/i })).toBeDefined();
  });
});

