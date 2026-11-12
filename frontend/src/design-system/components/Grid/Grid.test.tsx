import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Grid } from './Grid';

describe('Grid Component', () => {
  it('renders grid with column layout', () => {
    render(
      <Grid cols={3} gap="lg">
        <div>Card 1</div>
        <div>Card 2</div>
        <div>Card 3</div>
      </Grid>
    );

    expect(screen.getByText('Card 1')).toBeDefined();
    expect(screen.getByText('Card 2')).toBeDefined();
    expect(screen.getByText('Card 3')).toBeDefined();
  });
});

