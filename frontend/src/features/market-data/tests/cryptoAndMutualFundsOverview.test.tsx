import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { MarketOverviewPage } from '../pages/MarketOverviewPage';
import { marketDataApi } from '../api/marketDataApi';
import { MarketOverviewData } from '../types';

vi.mock('../api/marketDataApi', () => ({
  marketDataApi: {
    getMarketOverview: vi.fn(),
    getInstrument: vi.fn(),
    getHistory: vi.fn(),
  },
}));

const mockOverview: MarketOverviewData = {
  indices: [
    {
      id: 'idx-1',
      symbol: 'NIFTY50',
      name: 'NIFTY 50 Benchmark',
      asset_class: 'INDEX',
      exchange: 'NSE',
      price: '24500.00',
      change_amount: '120.00',
      change_percent: '0.49',
      is_synthetic: false,
      timestamp: '2026-11-26T10:00:00Z',
    },
  ],
  equities: [
    {
      id: 'eq-1',
      symbol: 'RELIANCE',
      name: 'Reliance Industries Ltd.',
      asset_class: 'EQUITY',
      exchange: 'NSE',
      price: '1350.00',
      change_amount: '15.00',
      change_percent: '1.12',
      is_synthetic: false,
      timestamp: '2026-11-26T10:00:00Z',
    },
  ],
  mutual_funds: [
    {
      id: 'mf-1',
      symbol: '122639',
      name: 'Parag Parikh Flexi Cap Fund - Direct Plan - Growth',
      asset_class: 'MUTUAL_FUND',
      exchange: 'AMFI',
      price: '94.2590',
      change_amount: '0.7590',
      change_percent: '0.81',
      is_synthetic: false,
      timestamp: '2026-11-26T15:30:00Z',
      fund_house: 'PPFAS Mutual Fund',
      plan_type: 'DIRECT',
      option_type: 'GROWTH',
    },
    {
      id: 'mf-2',
      symbol: '999999',
      name: 'Pending Valuation Fund',
      asset_class: 'MUTUAL_FUND',
      exchange: 'AMFI',
      price: null,
      change_amount: null,
      change_percent: null,
      is_synthetic: false,
      timestamp: '2026-11-26T15:30:00Z',
      fund_house: 'Test AMC',
      plan_type: 'REGULAR',
      option_type: 'GROWTH',
    },
  ],
  cryptocurrencies: [
    {
      id: 'crypto-1',
      symbol: 'BTC',
      name: 'Bitcoin',
      asset_class: 'CRYPTO',
      exchange: 'CRYPTO',
      price: '8500000.00',
      change_amount: '120000.00',
      change_percent: '1.43',
      is_synthetic: false,
      timestamp: '2026-11-26T12:00:00Z',
      market_cap: '₹168.0T',
      volume_24h: '₹3.5T',
    },
  ],
  is_demo_mode: false,
  demo_notice: '',
};

describe('MarketOverviewPage Crypto and Mutual Funds Integration', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    vi.mocked(marketDataApi.getMarketOverview).mockResolvedValue(mockOverview);
    vi.mocked(marketDataApi.getInstrument).mockResolvedValue({
      id: 'eq-1',
      symbol: 'RELIANCE',
      name: 'Reliance Industries Ltd.',
      asset_class: 'EQUITY',
      exchange: 'NSE',
      currency: 'INR',
      is_active: true,
      created_at: '2026-11-01T00:00:00Z',
      updated_at: '2026-11-01T00:00:00Z',
    });
    vi.mocked(marketDataApi.getHistory).mockResolvedValue({
      instrument_id: 'eq-1',
      series_id: 's-1',
      data_version: 1,
      frequency: 'daily',
      price_type: 'LTP',
      currency: 'INR',
      unit: 'SHARES',
      start_date: '2026-10-26',
      end_date: '2026-11-26',
      last_published_at: '2026-11-26T10:00:00Z',
      trust_class: 'VERIFIED_OFFICIAL',
      message: 'OK',
      points: [
        {
          timestamp: '2026-11-26T10:00:00Z',
          price: '1350.00',
          close_price: '1350.00',
          interval: '1D',
          is_synthetic: false,
        },
      ],
    });
  });

  const renderComponent = () =>
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <MarketOverviewPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

  it('renders all asset class tabs including Mutual Funds and Cryptocurrencies', async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Equities & Stocks')).toBeInTheDocument();
      expect(screen.getByText('Mutual Funds')).toBeInTheDocument();
      expect(screen.getByText('Cryptocurrencies')).toBeInTheDocument();
    });
  });

  it('switches to Cryptocurrencies tab and displays crypto quote card with metrics', async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Cryptocurrencies')).toBeInTheDocument();
    });

    const cryptoTab = screen.getByText('Cryptocurrencies');
    fireEvent.click(cryptoTab);

    await waitFor(() => {
      expect(screen.getByText('Bitcoin')).toBeInTheDocument();
      expect(screen.getByText('BTC')).toBeInTheDocument();
      expect(screen.getByText('MCap: ₹168.0T')).toBeInTheDocument();
      expect(screen.getByText('Vol: ₹3.5T')).toBeInTheDocument();
    });
  });

  it('switches to Mutual Funds tab and displays mutual fund quote card and plan types', async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Mutual Funds')).toBeInTheDocument();
    });

    const mfTab = screen.getByText('Mutual Funds');
    fireEvent.click(mfTab);

    await waitFor(() => {
      expect(screen.getByText(/Parag Parikh Flexi Cap Fund/i)).toBeInTheDocument();
      expect(screen.getByText('122639')).toBeInTheDocument();
      expect(screen.getByText('DIRECT')).toBeInTheDocument();
      expect(screen.getAllByText('GROWTH').length).toBeGreaterThan(0);
    });
  });

  it('handles null price safely by displaying em-dash without crashing or showing zero', async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Mutual Funds')).toBeInTheDocument();
    });

    const mfTab = screen.getByText('Mutual Funds');
    fireEvent.click(mfTab);

    await waitFor(() => {
      expect(screen.getByText('Pending Valuation Fund')).toBeInTheDocument();
      expect(screen.getByText('—')).toBeInTheDocument();
    });
  });
});
