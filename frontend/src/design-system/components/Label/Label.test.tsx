import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Label } from './Label';

describe('Label Component', () => {
  it('renders text with required indicator', () => {
    render(<Label required htmlFor="test-input">Username</Label>);
    expect(screen.getByText(/username/i)).toBeDefined();
    expect(screen.getByText('*')).toBeDefined();
  });
});

