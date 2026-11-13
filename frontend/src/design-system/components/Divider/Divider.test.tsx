import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Divider } from './Divider';

describe('Divider Component', () => {
  it('renders horizontal divider with role separator', () => {
    render(<Divider />);
    expect(screen.getByRole('separator')).toBeDefined();
  });

  it('renders divider with label', () => {
    render(<Divider label="OR" />);
    expect(screen.getByText('OR')).toBeDefined();
  });
});

