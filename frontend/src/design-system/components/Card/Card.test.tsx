import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardTitle, CardContent } from './Card';

describe('Card Component', () => {
  it('renders header, title and content', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Portfolio Summary</CardTitle>
        </CardHeader>
        <CardContent>Total value: $10,000</CardContent>
      </Card>
    );

    expect(screen.getByText('Portfolio Summary')).toBeDefined();
    expect(screen.getByText('Total value: $10,000')).toBeDefined();
  });
});

