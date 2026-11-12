import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@/app/providers';
import { ThemeToggle } from './ThemeToggle';

describe('ThemeToggle Component', () => {
  it('switches between light and dark themes on click', () => {
    render(
      <ThemeProvider defaultTheme="dark">
        <ThemeToggle />
      </ThemeProvider>
    );

    const lightBtn = screen.getByRole('button', { name: /switch to light mode/i });
    fireEvent.click(lightBtn);

    expect(document.documentElement.getAttribute('data-theme')).toBe('light');

    const darkBtn = screen.getByRole('button', { name: /switch to dark mode/i });
    fireEvent.click(darkBtn);

    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });
});

