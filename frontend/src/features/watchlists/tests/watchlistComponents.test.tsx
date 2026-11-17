import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PriceFreshnessBadge } from '../components/PriceFreshnessBadge';
import { PriceMovement } from '../components/PriceMovement';
import { InstrumentPriceChart } from '../components/InstrumentPriceChart';
import * as watchlistHooks from '../hooks/useWatchlist';
import { PriceMovement as PriceMovementType } from '../types';

vi.mock('../hooks/useWatchlist', () => ({
  useInstrumentHistory: vi.fn(),
}));

describe('Watchlist Micro-Components', () => {
  describe('PriceFreshnessBadge', () => {
    it('renders Verified badge for AVAILABLE status', () => {
      render(<PriceFreshnessBadge status="AVAILABLE" effectiveAt="2026-11-17T15:30:00Z" />);
      expect(screen.getByText('Verified')).toBeDefined();
      expect(screen.getByRole('status').getAttribute('aria-label')).toBe('Verified market price');
    });

    it('renders Stale badge for STALE status', () => {
      render(<PriceFreshnessBadge status="STALE" effectiveAt="2026-11-10T15:30:00Z" />);
      expect(screen.getByText('Stale')).toBeDefined();
    });

    it('renders Unavailable badge for MISSING status', () => {
      render(<PriceFreshnessBadge status="MISSING" />);
      expect(screen.getByText('Unavailable')).toBeDefined();
    });

    it('renders Demo badge when isSynthetic is true', () => {
      render(<PriceFreshnessBadge status="AVAILABLE" isSynthetic={true} />);
      expect(screen.getByText('Demo Price')).toBeDefined();
    });
  });

  describe('PriceMovement', () => {
    it('renders positive movement with green styling and sign', () => {
      const movement: PriceMovementType = {
        change_amount: '12.5000',
        change_percent: '2.5000',
        previous_price: '500.0000',
        previous_effective_at: '2026-11-16T15:30:00Z',
        status: 'CALCULATED',
        notes: '',
      };
      render(<PriceMovement movement={movement} currency="INR" />);
      expect(screen.getByText('+2.50%')).toBeDefined();
      expect(screen.getByText('(+₹12.50)')).toBeDefined();
    });

    it('renders negative movement with red styling and sign', () => {
      const movement: PriceMovementType = {
        change_amount: '-8.0000',
        change_percent: '-1.6000',
        previous_price: '500.0000',
        previous_effective_at: '2026-11-16T15:30:00Z',
        status: 'CALCULATED',
        notes: '',
      };
      render(<PriceMovement movement={movement} currency="INR" />);
      expect(screen.getByText('-1.60%')).toBeDefined();
      expect(screen.getByText('(₹8.00)')).toBeDefined();
    });

    it('renders neutral placeholder when movement is unavailable', () => {
      const movement: PriceMovementType = {
        change_amount: null,
        change_percent: null,
        previous_price: null,
        previous_effective_at: null,
        status: 'UNAVAILABLE',
        notes: 'Prior observation unavailable',
      };
      render(<PriceMovement movement={movement} />);
      expect(screen.getByText('--')).toBeDefined();
      expect(screen.getByLabelText('Price change unavailable')).toBeDefined();
    });
  });

  describe('InstrumentPriceChart', () => {
    it('renders chart canvas with price points and summary statistics', () => {
      (watchlistHooks.useInstrumentHistory as any).mockReturnValue({
        data: {
          supported: true,
          period: '1M',
          start_date: '2026-10-18',
          end_date: '2026-11-17',
          currency: 'INR',
          unit: 'UNITS',
          message: 'Retrieved 3 points',
          points: [
            {
              timestamp: '2026-10-20T10:00:00Z',
              date: '2026-10-20',
              price: '1000.0000',
              currency: 'INR',
              unit: 'UNITS',
              source: 'MANUAL_VERIFIED',
              is_synthetic: false,
            },
            {
              timestamp: '2026-11-01T10:00:00Z',
              date: '2026-11-01',
              price: '1050.0000',
              currency: 'INR',
              unit: 'UNITS',
              source: 'MANUAL_VERIFIED',
              is_synthetic: false,
            },
            {
              timestamp: '2026-11-17T10:00:00Z',
              date: '2026-11-17',
              price: '1100.0000',
              currency: 'INR',
              unit: 'UNITS',
              source: 'MANUAL_VERIFIED',
              is_synthetic: false,
            },
          ],
        },
        isLoading: false,
        isError: false,
      });

      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });

      render(
        <QueryClientProvider client={queryClient}>
          <InstrumentPriceChart instrumentId="inst-test-1" symbol="INFY" />
        </QueryClientProvider>
      );

      expect(screen.getByText('Historical Price Movement')).toBeDefined();
      expect(screen.getByText('Period High')).toBeDefined();
      expect(screen.getByText('Period Low')).toBeDefined();
      expect(screen.getByText('₹1100.00')).toBeDefined();
      expect(screen.getAllByText('₹1000.00').length).toBeGreaterThan(0);
    });

    it('renders unsupported message when historical timeseries is unsupported', () => {
      (watchlistHooks.useInstrumentHistory as any).mockReturnValue({
        data: {
          supported: false,
          period: '1M',
          currency: 'INR',
          message: 'Historical observations are not provided for this asset type.',
          points: [],
        },
        isLoading: false,
        isError: false,
      });

      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });

      render(
        <QueryClientProvider client={queryClient}>
          <InstrumentPriceChart instrumentId="inst-test-2" symbol="PHYSICAL_GOLD" />
        </QueryClientProvider>
      );

      expect(screen.getByText('Historical timeseries unsupported')).toBeDefined();
    });
  });
});
