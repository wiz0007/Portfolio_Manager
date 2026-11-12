import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Stack } from './Stack';

describe('Stack Component', () => {
  it('renders stacked elements with flex layout', () => {
    render(
      <Stack direction="row" spacing="sm">
        <span>Item 1</span>
        <span>Item 2</span>
      </Stack>
    );

    expect(screen.getByText('Item 1')).toBeDefined();
    expect(screen.getByText('Item 2')).toBeDefined();
  });
});

