import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { HoldingsOverview } from '../components/HoldingsOverview';
import { PriceFreshnessBadge } from '@/features/watchlists/components/PriceFreshnessBadge';
import { PriceFreshnessStatus } from '@/features/watchlists/types';
import * as dashboardHooks from '../hooks/useDashboard';

vi.mock('../hooks/useDashboard', () => ({
  useDashboardHoldings: vi.fn(),
}));

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Issue 2 & 3: Holdings Market Timestamps and Price Freshness Badge', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('PriceFreshnessBadge Component Status Handling', () => {
    const statuses: Array<{
      status: PriceFreshnessStatus;
      expectedText: string;
      expectedAria: string;
    }> = [
      { status: 'AVAILABLE', expectedText: 'Verified', expectedAria: 'Verified market price' },
      { status: 'STALE', expectedText: 'Stale', expectedAria: 'Stale market price' },
      { status: 'MISSING', expectedText: 'Unavailable', expectedAria: 'Price unavailable' },
      { status: 'AWAITING_VERIFICATION', expectedText: 'Pending Review', expectedAria: 'Pending review' },
      { status: 'UNVERIFIED', expectedText: 'Unverified', expectedAria: 'Unverified price' },
      { status: 'UNSUPPORTED', expectedText: 'Unsupported', expectedAria: 'Unsupported asset pricing' },
      { status: 'INCOMPATIBLE', expectedText: 'Incompatible Data', expectedAria: 'Incompatible data' },
      { status: 'SYNTHETIC', expectedText: 'Demo Price', expectedAria: 'Synthetic demo price' },
      { status: 'CONFLICTED', expectedText: 'Conflicted', expectedAria: 'Conflicted price' },
      { status: 'MANUAL', expectedText: 'Manual Valuation', expectedAria: 'Manual valuation' },
    ];

    statuses.forEach(({ status, expectedText, expectedAria }) => {
      it(`renders "${expectedText}" for status ${status}`, () => {
        render(<PriceFreshnessBadge status={status} />);
        const badge = screen.getByRole('status', { name: expectedAria });
        expect(badge).toBeInTheDocument();
        expect(badge).toHaveTextContent(expectedText);
      });
    });

    it('UNVERIFIED does not fall through to the unsupported default', () => {
      render(<PriceFreshnessBadge status="UNVERIFIED" />);
      expect(screen.getByText('Unverified')).toBeInTheDocument();
      expect(screen.queryByText('Unsupported')).not.toBeInTheDocument();
    });

    it('INCOMPATIBLE does not fall through to the unsupported default', () => {
      render(<PriceFreshnessBadge status="INCOMPATIBLE" />);
      expect(screen.getByText('Incompatible Data')).toBeInTheDocument();
      expect(screen.queryByText('Unsupported')).not.toBeInTheDocument();
    });

    it('MANUAL is clearly distinguishable from verified market pricing', () => {
      render(<PriceFreshnessBadge status="MANUAL" />);
      expect(screen.getByText('Manual Valuation')).toBeInTheDocument();
      expect(screen.queryByText('Verified')).not.toBeInTheDocument();
    });

    it('SYNTHETIC continues to render the demo-price indicator', () => {
      render(<PriceFreshnessBadge status="SYNTHETIC" isSynthetic={true} />);
      expect(screen.getByText('Demo Price')).toBeInTheDocument();
    });

    it('AWAITING_VERIFICATION continues to render pending review', () => {
      render(<PriceFreshnessBadge status="AWAITING_VERIFICATION" />);
      expect(screen.getByText('Pending Review')).toBeInTheDocument();
    });

    it('handles unknown future status values gracefully without crashing', () => {
      // @ts-expect-error Testing runtime fallback for unexpected status
      render(<PriceFreshnessBadge status="EXPERIMENTAL_FUTURE_STATUS" />);
      expect(screen.getByText('EXPERIMENTAL_FUTURE_STATUS')).toBeInTheDocument();
      expect(screen.getByRole('status', { name: 'Unknown pricing status' })).toBeInTheDocument();
    });

    it('prefers supplied ageSeconds over browser clock calculation', () => {
      render(
        <PriceFreshnessBadge
          status="AVAILABLE"
          publishedAt="2020-01-01T00:00:00Z" // Very old date if browser clock were used
          ageSeconds={45} // Authoritative 45 seconds supplied by backend resolver
        />
      );
      const badge = screen.getByRole('status');
      // 45 seconds maps to "just now"
      expect(badge).toHaveAttribute('title', expect.stringContaining('just now'));
    });

    it('null or invalid timestamps do not produce fabricated dates', () => {
      render(
        <PriceFreshnessBadge
          status="MISSING"
          effectiveAt={null}
          publishedAt={null}
        />
      );
      const badge = screen.getByRole('status');
      expect(badge).toHaveAttribute('title', 'No verified price observation available');
      expect(badge).not.toHaveAttribute('title', expect.stringContaining('Invalid Date'));
    });
  });

  describe('HoldingsOverview Component Market Timestamp Propagation', () => {
    it('passes market price timestamps and age to PriceFreshnessBadge, not valuation_date', () => {
      const mockHoldings = {
        count: 1,
        limit: 10,
        offset: 0,
        results: [
          {
            id: 'holding-1',
            display_name: 'Reliance Industries',
            category: 'equity',
            asset_type: 'listed_stocks',
            portfolio_id: 'port-1',
            portfolio_name: 'Main Port',
            is_active: true,
            currency: 'INR',
            invested_capital: '10000.00',
            current_value: '12500.00',
            absolute_gain_loss: '2500.00',
            gain_loss_percentage: '25.00',
            valuation_date: '2026-11-10', // Valuation snapshot date (must NOT be passed as effective market time)
            valuation_source: 'SNAPSHOT',
            price_freshness: 'AVAILABLE' as PriceFreshnessStatus,
            is_stale: false,
            price_effective_at: '2026-11-20T15:30:00Z', // Real market observation timestamp
            price_published_at: '2026-11-20T16:00:00Z',
            price_age_seconds: 120, // 2 minutes ago
          },
        ],
      };

      vi.mocked(dashboardHooks.useDashboardHoldings).mockReturnValue({
        data: mockHoldings,
        isLoading: false,
        isError: false,
      } as any);

      renderWithProviders(<HoldingsOverview portfolioId="port-1" />);

      // Both desktop and mobile views render PriceFreshnessBadge
      const badges = screen.getAllByRole('status', { name: 'Verified market price' });
      expect(badges.length).toBeGreaterThanOrEqual(1);

      badges.forEach((badge) => {
        // Must contain publication time relative age based on price_age_seconds (120s -> 2m ago)
        expect(badge).toHaveAttribute('title', expect.stringContaining('2m ago'));
        // Must NOT reference the historical valuation snapshot date (2026-11-10) in the market tooltip
        expect(badge.getAttribute('title')).not.toContain('2026-11-10');
        expect(badge.getAttribute('title')).not.toContain('11/10/2026');
      });
    });
  });
});
