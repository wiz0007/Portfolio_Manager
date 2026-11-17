import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HoldingValuationCard } from '../components/HoldingValuationCard';
import { ProjectionCalculatorModal } from '../components/ProjectionCalculatorModal/ProjectionCalculatorModal';
import { investmentValuationApi } from '../api/investmentValuationApi';

vi.mock('../api/investmentValuationApi', () => ({
  investmentValuationApi: {
    getPerformance: vi.fn(),
    calculateProjection: vi.fn(),
    getValuations: vi.fn(),
    calculateValuation: vi.fn(),
    recordManualValuation: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('Sprint 4 Frontend Valuation & Performance Integration (FE-001 to FE-010)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('FE-001: HoldingValuationCard consumes and renders authoritative backend performance metrics', async () => {
    vi.mocked(investmentValuationApi.getPerformance).mockResolvedValue({
      investment_id: 'test-inv-1',
      display_name: 'Reliance Industries',
      category: 'EQUITY',
      asset_type: 'listed_stock',
      currency: 'INR',
      invested_amount: '250000.00',
      current_value: '295000.00',
      absolute_gain_loss: '45000.00',
      percentage_gain_loss: '18.00',
      is_gain: true,
      last_valuation_date: '2026-11-15',
      valuation_method: 'MARKET_PRICE',
      source: 'MARKET_FEED',
    });

    render(
      <HoldingValuationCard investmentId="test-inv-1" currency="INR" />,
      { wrapper: createWrapper() }
    );

    // Initial outlay
    await waitFor(() => {
      expect(screen.getByText(/Initial Capital Outlay/i)).toBeInTheDocument();
      expect(screen.getByText(/2,50,000\.00/i)).toBeInTheDocument();
      expect(screen.getByText(/2,95,000\.00/i)).toBeInTheDocument();
      expect(screen.getByText(/45,000\.00/i)).toBeInTheDocument();
      expect(screen.getByText(/\(18\.00%\)/i)).toBeInTheDocument();
    });
  });

  it('FE-002: HoldingValuationCard handles zero cost basis with unavailable return percentage without NaN%', async () => {
    vi.mocked(investmentValuationApi.getPerformance).mockResolvedValue({
      investment_id: 'test-inv-zero',
      display_name: 'Gifted Crypto Token',
      category: 'CRYPTO',
      asset_type: 'crypto_token',
      currency: 'INR',
      invested_amount: '0.00',
      current_value: '15000.00',
      absolute_gain_loss: '15000.00',
      percentage_gain_loss: 'unavailable',
      is_gain: true,
      last_valuation_date: '2026-11-16',
      valuation_method: 'MARKET_PRICE',
      source: 'MARKET_FEED',
    });

    render(
      <HoldingValuationCard investmentId="test-inv-zero" currency="INR" />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText(/Zero Cost Acquisition/i)).toBeInTheDocument();
      expect(screen.getByText(/\(N\/A\)/i)).toBeInTheDocument();
      expect(screen.queryByText(/NaN/i)).not.toBeInTheDocument();
    });
  });

  it('FE-003: HoldingValuationCard displays explicit provenance badges', async () => {
    // Synthetic market quote badge
    vi.mocked(investmentValuationApi.getPerformance).mockResolvedValue({
      investment_id: 'test-inv-synthetic',
      display_name: 'Demo Gold Holding',
      category: 'COMMODITIES',
      asset_type: 'physical_gold',
      currency: 'INR',
      invested_amount: '70000.00',
      current_value: '72000.00',
      absolute_gain_loss: '2000.00',
      percentage_gain_loss: '2.86',
      is_gain: true,
      last_valuation_date: '2026-11-17',
      valuation_method: 'PHYSICAL_GOLD_PURITY',
      source: 'DEMO_SYNTHETIC',
    });

    render(
      <HoldingValuationCard investmentId="test-inv-synthetic" currency="INR" />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText(/Synthetic Demo/i)).toBeInTheDocument();
    });
  });

  it('FE-004: ProjectionCalculatorModal renders non-mutation disclaimer and simulation schedule', async () => {
    vi.mocked(investmentValuationApi.calculateProjection).mockResolvedValue({
      investment_id: 'test-inv-proj',
      display_name: 'HDFC Index Fund',
      category: 'MUTUAL_FUNDS',
      currency: 'INR',
      initial_principal: '100000.00',
      monthly_contribution: '5000.00',
      time_horizon_years: 5,
      contribution_timing: 'END_OF_PERIOD',
      compounding_frequency_per_year: 12,
      formula_id: 'ANNUITY_COMPOUND_FV_V1',
      assumption_disclosures: 'Deterministic simulation based on compound interest.',
      scenarios: {
        base: {
          scenario_name: 'base',
          annual_rate_percent: '12.00',
          projected_future_value: '589998.02',
          total_invested_capital: '400000.00',
          total_estimated_growth: '189998.02',
          schedule: [
            {
              year: 1,
              invested_capital: '160000.00',
              projected_future_value: '175968.04',
              estimated_growth: '15968.04',
            },
            {
              year: 5,
              invested_capital: '400000.00',
              projected_future_value: '589998.02',
              estimated_growth: '189998.02',
            },
          ],
        },
      },
    });

    render(
      <ProjectionCalculatorModal
        investmentId="test-inv-proj"
        investmentName="HDFC Index Fund"
        currentValue={100000}
        category="MUTUAL_FUNDS"
        currency="INR"
        onClose={vi.fn()}
      />,
      { wrapper: createWrapper() }
    );

    // Verify deterministic simulation disclaimer banner
    expect(screen.getByText(/Deterministic Simulation Engine:/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Simulated projections never modify your actual portfolio or historical holding records/i)
    ).toBeInTheDocument();

    // Verify schedule rendering
    await waitFor(() => {
      expect(screen.getByText(/Year 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Year 5/i)).toBeInTheDocument();
      expect(screen.getAllByText(/5,89,998\.02/i).length).toBeGreaterThanOrEqual(1);
    });
  });
});
