import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { InstrumentRequestModal } from '../components/InstrumentRequestModal';
import { ManualPriceEntryModal } from '../components/ManualPriceEntryModal';
import { CsvImportModal } from '../components/CsvImportModal';
import { Instrument } from '../types';

describe('Manual Market Operations Frontend Components', () => {
  const mockInstrument: Instrument = {
    id: 'test-inst-123',
    symbol: 'TCS',
    name: 'Tata Consultancy Services',
    asset_class: 'EQUITY',
    exchange: 'NSE',
    currency: 'INR',
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };

  it('renders InstrumentRequestModal and validates required inputs', () => {
    const handleClose = vi.fn();
    render(
      <InstrumentRequestModal
        isOpen={true}
        onClose={handleClose}
        initialQuery="Zomato"
      />
    );

    expect(screen.getByText('Request Instrument Addition')).toBeInTheDocument();
    expect(screen.getAllByDisplayValue('Zomato')).toHaveLength(2);
    expect(screen.getByRole('button', { name: /submit request/i })).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText('Close'));
    expect(handleClose).toHaveBeenCalled();
  });

  it('renders ManualPriceEntryModal with instrument identity and price inputs', () => {
    const handleClose = vi.fn();
    render(
      <ManualPriceEntryModal
        isOpen={true}
        onClose={handleClose}
        instrument={mockInstrument}
      />
    );

    expect(screen.getByText('Record Price Observation')).toBeInTheDocument();
    expect(screen.getByText(/TCS — Tata Consultancy Services/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('0.00')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /publish observation/i })).toBeInTheDocument();
  });

  it('renders CsvImportModal with upload and preview triggers', () => {
    const handleClose = vi.fn();
    render(
      <CsvImportModal
        isOpen={true}
        onClose={handleClose}
      />
    );

    expect(screen.getByText('Bulk CSV Price Import')).toBeInTheDocument();
    expect(screen.getByText(/Upload price collection batches matching schema v1.0/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /validate & preview/i })).toBeInTheDocument();
  });
});
