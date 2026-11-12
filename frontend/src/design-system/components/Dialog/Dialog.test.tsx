import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Dialog } from './Dialog';

describe('Dialog Component', () => {
  it('renders modal when isOpen is true', () => {
    render(
      <Dialog isOpen={true} onClose={vi.fn()} title="Delete Portfolio">
        Are you sure?
      </Dialog>
    );

    expect(screen.getByRole('dialog')).toBeDefined();
    expect(screen.getByText('Delete Portfolio')).toBeDefined();
    expect(screen.getByText('Are you sure?')).toBeDefined();
  });

  it('calls onClose when close button or Escape is triggered', () => {
    const handleClose = vi.fn();
    render(
      <Dialog isOpen={true} onClose={handleClose} title="Modal Title">
        Content
      </Dialog>
    );

    fireEvent.click(screen.getByRole('button', { name: /close dialog/i }));
    expect(handleClose).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(handleClose).toHaveBeenCalledTimes(2);
  });
});

