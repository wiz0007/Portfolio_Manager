import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { PortfolioOverview } from '../components/PortfolioOverview';
import { AssetAllocationChart } from '../components/AssetAllocationChart';
import { HoldingsOverview } from '../components/HoldingsOverview';
import { RecentActivity } from '../components/RecentActivity';
import { ValuationDataQuality } from '../components/ValuationDataQuality';
import { WatchlistPreview } from '../components/WatchlistPreview';

import * as dashboardHooks from '../hooks/useDashboard';

vi.mock('../hooks/useDashboard', () => ({
  useDashboardOverview: vi.fn(),
  useDashboardAllocation: vi.fn(),
  useDashboardHoldings: vi.fn(),
  useDashboardRecentActivity: vi.fn(),
  useDashboardDataQuality: vi.fn(),
  useDashboardWatchlistPreview: vi.fn(),
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

describe('Dashboard Modular Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('PortfolioOverview', () => {
    it('renders authoritative metrics, invested capital, and gain/loss', () => {
      const mockOverview: any = {
        portfolio_count: 2,
        active_investment_count: 5,
        summary: {
          currency: 'INR',
          total_current_value: '125000.00',
          total_invested_capital: '100000.00',
          absolute_gain_loss: '25000.00',
          gain_loss_percentage: '25.00',
          valued_investment_count: 5,
          unvalued_investment_count: 0,
        },
        data_completeness: {
          completeness_percentage: 100.0,
          valued_holdings: 5,
          total_active_holdings: 5,
          unvalued_holdings: 0,
        },
      };

      renderWithProviders(<PortfolioOverview overview={mockOverview} />);

      expect(screen.getByText('125,000.00')).toBeInTheDocument();
      expect(screen.getByText('100,000.00')).toBeInTheDocument();
      expect(screen.getByText('+25,000.00')).toBeInTheDocument();
      expect(screen.getByText('+25.00%')).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument();
      expect(screen.getByText('5 active holdings')).toBeInTheDocument();
    });

    it('renders N/A return when invested capital is zero without crash or division by zero', () => {
      const mockOverview: any = {
        portfolio_count: 1,
        active_investment_count: 1,
        summary: {
          currency: 'INR',
          total_current_value: '500.00',
          total_invested_capital: '0.00',
          absolute_gain_loss: '500.00',
          gain_loss_percentage: null,
          valued_investment_count: 1,
          unvalued_investment_count: 0,
        },
        data_completeness: {
          completeness_percentage: 100.0,
          valued_holdings: 1,
          total_active_holdings: 1,
          unvalued_holdings: 0,
        },
      };

      renderWithProviders(<PortfolioOverview overview={mockOverview} />);

      expect(screen.getByText('500.00')).toBeInTheDocument();
      expect(screen.getByText(/N\/A \(Zero invested capital\)/i)).toBeInTheDocument();
    });

    it('displays multi-currency banner when holdings span different currencies', () => {
      const mockOverview: any = {
        portfolio_count: 2,
        active_investment_count: 2,
        summary: {
          currency: 'INR',
          total_current_value: '50000.00',
          total_invested_capital: '50000.00',
          absolute_gain_loss: '0.00',
          gain_loss_percentage: '0.00',
        },
        totals_by_currency: {
          INR: { total_current_value: '50000.00' },
          USD: { total_current_value: '1000.00' },
        },
      };

      renderWithProviders(<PortfolioOverview overview={mockOverview} />);

      expect(screen.getByText(/Multi-Currency Portfolio:/i)).toBeInTheDocument();
      expect(screen.getByText(/INR, USD/i)).toBeInTheDocument();
    });
  });

  describe('AssetAllocationChart', () => {
    it('renders asset class breakdown and valuation denominator', () => {
      (dashboardHooks.useDashboardAllocation as any).mockReturnValue({
        data: {
          currency: 'INR',
          denominator_value: '100000.00',
          valued_count: 2,
          unvalued_count: 1,
          has_unvalued_assets: true,
          asset_class_allocation: [
            { category: 'equity', display_name: 'Listed Equities', total_value: '60000.00', percentage: '60.00', count: 1 },
            { category: 'mutual_funds', display_name: 'Mutual Funds', total_value: '40000.00', percentage: '40.00', count: 1 },
          ],
          portfolio_allocation: [],
          top_holdings_allocation: [],
        },
        isLoading: false,
        isError: false,
      });

      renderWithProviders(<AssetAllocationChart />);

      expect(screen.getByText('Listed Equities')).toBeInTheDocument();
      expect(screen.getByText('60.00%')).toBeInTheDocument();
      expect(screen.getByText('Mutual Funds')).toBeInTheDocument();
      expect(screen.getByText('40.00%')).toBeInTheDocument();
      expect(screen.getByText(/Valuation Denominator: INR 100,000.00/i)).toBeInTheDocument();
      expect(screen.getByText(/Excludes 1 unvalued holding/i)).toBeInTheDocument();
    });
  });

  describe('HoldingsOverview', () => {
    it('renders holdings rows with gain/loss and details link', () => {
      (dashboardHooks.useDashboardHoldings as any).mockReturnValue({
        data: {
          count: 1,
          limit: 10,
          offset: 0,
          results: [
            {
              id: 'inv-123',
              display_name: 'Infosys Limited',
              category: 'equity',
              asset_type: 'listed_stocks',
              portfolio_id: 'port-1',
              portfolio_name: 'Core Growth',
              currency: 'INR',
              quantity: '10',
              invested_capital: '15000.00',
              current_value: '18500.00',
              absolute_gain_loss: '3500.00',
              gain_loss_percentage: '23.33',
              valuation_date: '2026-11-18',
              valuation_source: 'TEST',
              price_freshness: 'AVAILABLE',
              is_stale: false,
            },
          ],
        },
        isLoading: false,
        isError: false,
      });

      renderWithProviders(<HoldingsOverview />);

      expect(screen.getAllByText('Infosys Limited').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Core Growth').length).toBeGreaterThan(0);
      expect(screen.getAllByText('+3,500.00').length).toBeGreaterThan(0);
      expect(screen.getAllByText('+23.33%').length).toBeGreaterThan(0);
    });
  });

  describe('RecentActivity', () => {
    it('renders transactions with canonical amount and date', () => {
      (dashboardHooks.useDashboardRecentActivity as any).mockReturnValue({
        data: [
          {
            id: 'tx-1',
            investment_id: 'inv-1',
            investment_name: 'Reliance Industries',
            portfolio_id: 'port-1',
            portfolio_name: 'Bluechip',
            transaction_type: 'BUY',
            transaction_date: '2026-11-15',
            units: '5',
            price_per_unit: '2400.00',
            amount: '12000.00',
            gross_amount: '12000.00',
            fees: '25.00',
            taxes: '15.00',
            net_cash_flow: '12040.00',
            currency: 'INR',
          },
        ],
        isLoading: false,
        isError: false,
      });

      renderWithProviders(<RecentActivity />);

      expect(screen.getByText('Reliance Industries')).toBeInTheDocument();
      expect(screen.getByText('BUY')).toBeInTheDocument();
      expect(screen.getByText(/INR 12,040.00/i)).toBeInTheDocument();
      expect(screen.getByText(/incl. INR 40.00 fees\/tax/i)).toBeInTheDocument();
    });
  });

  describe('ValuationDataQuality', () => {
    it('renders quality status counts and explanatory descriptions', () => {
      (dashboardHooks.useDashboardDataQuality as any).mockReturnValue({
        data: {
          overall_status: 'WARNING',
          total_active_holdings: 4,
          categories: {
            valued: { count: 3, label: 'Up-to-Date', description: 'desc', items: [] },
            stale: { count: 1, label: 'Stale Price', description: 'desc', items: [] },
            missing_price: { count: 0, label: 'Missing Price', description: 'desc', items: [] },
            awaiting_verification: { count: 0, label: 'Awaiting Review', description: 'desc', items: [] },
            unsupported: { count: 0, label: 'Manual/Appraisal', description: 'desc', items: [] },
          },
        },
        isLoading: false,
        isError: false,
      });

      renderWithProviders(<ValuationDataQuality />);

      expect(screen.getByText('Stale Valuations Detected')).toBeInTheDocument();
      expect(screen.getByText('Transparency status on 4 active holdings')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
    });
  });

  describe('WatchlistPreview', () => {
    it('renders preview items with price and link to full watchlist', () => {
      (dashboardHooks.useDashboardWatchlistPreview as any).mockReturnValue({
        data: [
          {
            id: 'wch-1',
            instrument: {
              id: 'inst-1',
              symbol: 'TCS',
              name: 'Tata Consultancy Services',
              currency: 'INR',
              asset_class: 'EQUITY',
              exchange: 'NSE',
            },
            market_data: {
              price: '4150.00',
              currency: 'INR',
              status: 'AVAILABLE',
              movement: {
                change_percent: '1.25',
                change_amount: '51.25',
                status: 'CALCULATED',
              },
            },
          },
        ],
        isLoading: false,
        isError: false,
      });

      renderWithProviders(<WatchlistPreview />);

      expect(screen.getByText('TCS')).toBeInTheDocument();
      expect(screen.getByText('Tata Consultancy Services')).toBeInTheDocument();
      expect(screen.getByText('INR 4,150.00')).toBeInTheDocument();
      expect(screen.getByText('View All')).toBeInTheDocument();
    });
  });
});
