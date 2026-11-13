import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from './Badge';

describe('Badge Component', () => {
  it('renders badge with text and dot', () => {
    render(<Badge variant="positive" dot>Verified</Badge>);
    expect(screen.getByText('Verified')).toBeDefined();
  });
});

