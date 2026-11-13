import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Input } from './Input';

describe('Input Component', () => {
  it('renders input with placeholder', () => {
    render(<Input placeholder="Enter your email" />);
    expect(screen.getByPlaceholderText(/enter your email/i)).toBeDefined();
  });

  it('displays error message and sets aria-invalid', () => {
    render(<Input error="Email is required" placeholder="Email" />);
    const input = screen.getByPlaceholderText(/email/i);
    expect(input.getAttribute('aria-invalid')).toBe('true');
    expect(screen.getByRole('alert').textContent).toBe('Email is required');
  });
});

