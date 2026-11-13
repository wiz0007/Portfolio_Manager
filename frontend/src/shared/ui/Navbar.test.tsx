import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Navbar } from './Navbar';

describe('Navbar Component', () => {
  it('renders brand name on top left and theme selector on top right', () => {
    render(
      <BrowserRouter>
        <Navbar />
      </BrowserRouter>
    );

    expect(screen.getByText('Portfolio Manager')).toBeInTheDocument();
    expect(screen.getByRole('group', { name: /color theme selector/i })).toBeInTheDocument();
  });
});

