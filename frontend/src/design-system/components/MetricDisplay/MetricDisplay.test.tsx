import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MetricDisplay } from './MetricDisplay';

describe('MetricDisplay Component', () => {
  it('renders label, tabular value and positive delta', () => {
    render(<MetricDisplay label="Total Balance" value="$125,400.00" delta="+12.4%" />);
    expect(screen.getByText('Total Balance')).toBeDefined();
    expect(screen.getByText('$125,400.00')).toBeDefined();
    expect(screen.getByText('+12.4%')).toBeDefined();
  });
});

