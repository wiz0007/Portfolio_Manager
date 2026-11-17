import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WatchlistPage } from '../pages/WatchlistPage';
import * as watchlistHooks from '../hooks/useWatchlist';
import { WatchlistItem } from '../types';

vi.mock('../hooks/useWatchlist', () => ({
  useWatchlist: vi.fn(),
  useAddWatchlistItem: vi.fn(),
  useRemoveWatchlistItem: vi.fn(),
  useInstrumentLatestPrice: vi.fn(),
  useInstrumentHistory: vi.fn(),
  useInstrumentMarketStatus: vi.fn(),
}));

const mockItems: WatchlistItem[] = [
  {
    id: 'item-1',
    instrument: {
      id: 'inst-1',
      symbol: 'RELIANCE',
      name: 'Reliance Industries Limited',
      asset_class: 'EQUITY',
      product_type: 'listed_stocks',
      exchange: 'NSE',
      currency: 'INR',
      isin: 'INE002A01018',
      scheme_code: null,
      sector: 'Energy',
      industry: 'Oil & Gas',
      status: 'ACTIVE',
    },
    notes: 'Watch for energy transition progress',
    target_price: '2800.0000',
    created_at: '2026-11-15T10:00:00Z',
    updated_at: '2026-11-15T10:00:00Z',
    market_data: {
      price: '2950.5000',
      currency: 'INR',
      unit: 'UNITS',
      effective_at: '2026-11-17T15:30:00Z',
      status: 'AVAILABLE',
      source: 'MANUAL_VERIFIED',
      source_reference: 'NSE Official',
      is_synthetic: false,
      notes: 'Verified session close',
      movement: {
        change_amount: '35.5000',
        change_percent: '1.2178',
        previous_price: '2915.0000',
        previous_effective_at: '2026-11-16T15:30:00Z',
        status: 'CALCULATED',
        notes: '',
      },
    },
  },
  {
    id: 'item-2',
    instrument: {
      id: 'inst-2',
      symbol: '122639',
      name: 'Parag Parikh Flexi Cap Fund',
      asset_class: 'MUTUAL_FUND',
      product_type: 'mutual_fund',
      exchange: 'AMFI',
      currency: 'INR',
      isin: 'INF879O01018',
      scheme_code: '122639',
      sector: 'Diversified',
      industry: 'Mutual Fund',
      status: 'ACTIVE',
    },
    notes: 'SIP core candidate',
    target_price: null,
    created_at: '2026-11-16T10:00:00Z',
    updated_at: '2026-11-16T10:00:00Z',
    market_data: {
      price: '82.4500',
      currency: 'INR',
      unit: 'UNITS',
      effective_at: '2026-11-17T21:00:00Z',
      status: 'AVAILABLE',
      source: 'AMFI',
      source_reference: 'AMFI Portal',
      is_synthetic: false,
      notes: 'Daily NAV publication',
      movement: {
        change_amount: '-0.3500',
        change_percent: '-0.4227',
        previous_price: '82.8000',
        previous_effective_at: '2026-11-16T21:00:00Z',
        status: 'CALCULATED',
        notes: '',
      },
    },
  },
];

const renderWatchlistPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <WatchlistPage />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('WatchlistPage Lifecycle', () => {
  const mockRemoveMutate = vi.fn();
  const mockAddMutate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (watchlistHooks.useAddWatchlistItem as any).mockReturnValue({
      mutate: mockAddMutate,
      isPending: false,
    });
    (watchlistHooks.useRemoveWatchlistItem as any).mockReturnValue({
      mutate: mockRemoveMutate,
      isPending: false,
    });
  });

  it('renders watchlist summary cards and items properly', () => {
    (watchlistHooks.useWatchlist as any).mockReturnValue({
      data: mockItems,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
      isFetching: false,
    });

    renderWatchlistPage();

    // Check title and metrics
    expect(screen.getByText('Market Watchlist')).toBeDefined();
    expect(screen.getByText('2')).toBeDefined(); // Total watched
    expect(screen.getAllByText('1').length).toBeGreaterThan(0); // 1 gainer, 1 loser, 1 alert

    // Check items present in view
    expect(screen.getAllByText('RELIANCE').length).toBeGreaterThan(0);
    expect(screen.getAllByText('122639').length).toBeGreaterThan(0);
    expect(screen.getAllByText('+1.22%').length).toBeGreaterThan(0);
    expect(screen.getAllByText('-0.42%').length).toBeGreaterThan(0);
  });

  it('renders empty state when user has no watchlist items', () => {
    (watchlistHooks.useWatchlist as any).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
      isFetching: false,
    });

    renderWatchlistPage();

    expect(screen.getByText('Your watchlist is empty')).toBeDefined();
    expect(screen.getByText('Add Instrument to Watchlist')).toBeDefined();
  });

  it('filters items dynamically by search input query', async () => {
    (watchlistHooks.useWatchlist as any).mockReturnValue({
      data: mockItems,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
      isFetching: false,
    });

    renderWatchlistPage();

    const searchInput = screen.getByPlaceholderText('Filter by symbol or name...');
    fireEvent.change(searchInput, { target: { value: 'Parag' } });

    await waitFor(() => {
      expect(screen.getAllByText('122639').length).toBeGreaterThan(0);
      expect(screen.queryByText('RELIANCE')).toBeNull();
    });
  });

  it('opens add to watchlist modal upon clicking Add Instrument', () => {
    (watchlistHooks.useWatchlist as any).mockReturnValue({
      data: mockItems,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
      isFetching: false,
    });

    renderWatchlistPage();

    const addButton = screen.getByText('Add Instrument');
    fireEvent.click(addButton);

    expect(screen.getAllByText('Add to Watchlist').length).toBeGreaterThan(0);
    expect(screen.getByText('Search canonical catalogue instruments')).toBeDefined();
  });
});
