import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EmptyState } from './EmptyState';

describe('EmptyState Component', () => {
  it('renders title and action correctly', () => {
    render(
      <EmptyState
        title="No Portfolios Yet"
        description="Create your first portfolio to begin tracking investments."
        action={<button>Create Portfolio</button>}
      />
    );

    expect(screen.getByText('No Portfolios Yet')).toBeDefined();
    expect(screen.getByText(/create your first portfolio/i)).toBeDefined();
    expect(screen.getByRole('button', { name: /create portfolio/i })).toBeDefined();
  });
});

