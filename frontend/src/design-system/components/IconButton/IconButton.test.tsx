import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { IconButton } from './IconButton';

describe('IconButton Component', () => {
  it('renders with accessible aria-label', () => {
    render(<IconButton icon={<span>+</span>} aria-label="Add item" />);
    const btn = screen.getByRole('button', { name: /add item/i });
    expect(btn).toBeDefined();
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<IconButton icon={<span>+</span>} aria-label="Add item" onClick={handleClick} />);
    fireEvent.click(screen.getByRole('button', { name: /add item/i }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

