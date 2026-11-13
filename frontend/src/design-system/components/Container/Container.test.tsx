import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Container } from './Container';

describe('Container Component', () => {
  it('renders children with max-width container', () => {
    render(<Container maxWidth="lg">Page Content</Container>);
    expect(screen.getByText('Page Content')).toBeDefined();
  });
});

