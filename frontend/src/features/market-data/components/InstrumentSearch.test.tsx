import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { InstrumentSearch } from './InstrumentSearch';
import { marketDataApi } from '../api/marketDataApi';
import { Instrument } from '../types';

vi.mock('../api/marketDataApi', () => ({
  marketDataApi: {
    searchInstruments: vi.fn(),
  },
}));

describe('InstrumentSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockInstruments: Instrument[] = [
    {
      id: 'inst-1',
      symbol: 'RELIANCE',
      name: 'Reliance Industries Ltd.',
      asset_class: 'EQUITY',
      exchange: 'NSE',
      currency: 'INR',
      is_active: true,
      created_at: '',
      updated_at: '',
      latest_quote: {
        symbol: 'RELIANCE',
        price: '1344.8000',
        change_percent: '1.20',
        provider: 'DEMO',
        is_synthetic: true,
        currency: 'INR',
        timestamp: '',
      },
    },
  ];

  it('renders search input with placeholder', () => {
    render(<InstrumentSearch onSelect={vi.fn()} />);
    expect(screen.getByPlaceholderText(/Search stocks, mutual funds/i)).toBeInTheDocument();
  });

  it('searches and shows results in dropdown upon typing', async () => {
    (marketDataApi.searchInstruments as any).mockResolvedValue(mockInstruments);
    const onSelect = vi.fn();

    render(<InstrumentSearch onSelect={onSelect} />);
    const input = screen.getByPlaceholderText(/Search stocks, mutual funds/i);

    fireEvent.change(input, { target: { value: 'RELI' } });

    await waitFor(() => {
      expect(marketDataApi.searchInstruments).toHaveBeenCalledWith('RELI');
      expect(screen.getByText('Reliance Industries Ltd.')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('RELIANCE'));
    expect(onSelect).toHaveBeenCalledWith(mockInstruments[0]);
  });
});
