import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusIndicator } from './StatusIndicator';

describe('StatusIndicator Component', () => {
  it('renders with label and positive status', () => {
    render(<StatusIndicator variant="positive" label="Database Online" pulse />);
    expect(screen.getByText('Database Online')).toBeDefined();
  });
});

