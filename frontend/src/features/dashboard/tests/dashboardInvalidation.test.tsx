import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import {
  useCreateInvestment,
  useUpdateInvestment,
  useDeleteInvestment,
  INVESTMENTS_QUERY_KEY,
} from '@/features/investments/hooks/useInvestments';
import {
  useCreatePortfolio,
  useUpdatePortfolio,
  useDeletePortfolio,
  PORTFOLIOS_QUERY_KEY,
} from '@/features/portfolios/hooks/usePortfolios';
import {
  DASHBOARD_OVERVIEW_QUERY_KEY,
  DASHBOARD_BASE_KEY,
  invalidateDashboardQueries,
} from '@/features/dashboard/hooks/useDashboard';
import { investmentApi } from '@/features/investments/api/investmentApi';
import { portfoliosApi } from '@/features/portfolios/api/portfoliosApi';

vi.mock('@/features/investments/api/investmentApi', () => ({
  investmentApi: {
    createInvestment: vi.fn(),
    updateInvestment: vi.fn(),
    deleteInvestment: vi.fn(),
  },
}));

vi.mock('@/features/portfolios/api/portfoliosApi', () => ({
  portfoliosApi: {
    createPortfolio: vi.fn(),
    updatePortfolio: vi.fn(),
    deletePortfolio: vi.fn(),
  },
}));

describe('Issue 1: Dashboard Cache Invalidation on Mutations', () => {
  let queryClient: QueryClient;

  const createWrapper = () => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    return ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Investment Mutations', () => {
    it('1. successful investment creation invalidates overview and dashboard data queries', async () => {
      vi.mocked(investmentApi.createInvestment).mockResolvedValueOnce({ id: 'inv-1' } as any);
      const wrapper = createWrapper();
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useCreateInvestment(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({
          name: 'New Stock',
          category: 'equity',
          asset_type: 'listed_stocks',
          currency: 'INR',
          initial_value: '1000',
          portfolio: 'port-1',
        } as any);
      });

      const calls = invalidateSpy.mock.calls.map((c) => c[0]?.queryKey);
      expect(calls).toContainEqual(DASHBOARD_OVERVIEW_QUERY_KEY);
      expect(calls).toContainEqual(DASHBOARD_BASE_KEY);
      expect(calls).toContainEqual(INVESTMENTS_QUERY_KEY);
      expect(calls).toContainEqual(PORTFOLIOS_QUERY_KEY);
    });

    it('2. successful investment update invalidates both dashboard namespaces', async () => {
      vi.mocked(investmentApi.updateInvestment).mockResolvedValueOnce({ id: 'inv-1' } as any);
      const wrapper = createWrapper();
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useUpdateInvestment('port-1'), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({
          id: 'inv-1',
          payload: { name: 'Updated Stock' } as any,
        });
      });

      const calls = invalidateSpy.mock.calls.map((c) => c[0]?.queryKey);
      expect(calls).toContainEqual(DASHBOARD_OVERVIEW_QUERY_KEY);
      expect(calls).toContainEqual(DASHBOARD_BASE_KEY);
    });

    it('3. successful investment deletion invalidates both dashboard namespaces', async () => {
      vi.mocked(investmentApi.deleteInvestment).mockResolvedValueOnce(undefined as any);
      const wrapper = createWrapper();
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useDeleteInvestment('port-1'), { wrapper });

      await act(async () => {
        await result.current.mutateAsync('inv-1');
      });

      const calls = invalidateSpy.mock.calls.map((c) => c[0]?.queryKey);
      expect(calls).toContainEqual(DASHBOARD_OVERVIEW_QUERY_KEY);
      expect(calls).toContainEqual(DASHBOARD_BASE_KEY);
    });

    it('7a. failed investment mutation does not invalidate dashboard queries', async () => {
      vi.mocked(investmentApi.createInvestment).mockRejectedValueOnce(new Error('Network error'));
      const wrapper = createWrapper();
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useCreateInvestment(), { wrapper });

      await act(async () => {
        try {
          await result.current.mutateAsync({ name: 'Fail Stock' } as any);
        } catch {
          // Expected failure
        }
      });

      const calls = invalidateSpy.mock.calls.map((c) => c[0]?.queryKey);
      expect(calls).not.toContainEqual(DASHBOARD_OVERVIEW_QUERY_KEY);
      expect(calls).not.toContainEqual(DASHBOARD_BASE_KEY);
    });
  });

  describe('Portfolio Mutations', () => {
    it('4. successful portfolio creation invalidates both dashboard namespaces', async () => {
      vi.mocked(portfoliosApi.createPortfolio).mockResolvedValueOnce({ id: 'port-new' } as any);
      const wrapper = createWrapper();
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useCreatePortfolio(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({ name: 'Retirement Fund', base_currency: 'INR' });
      });

      const calls = invalidateSpy.mock.calls.map((c) => c[0]?.queryKey);
      expect(calls).toContainEqual(DASHBOARD_OVERVIEW_QUERY_KEY);
      expect(calls).toContainEqual(DASHBOARD_BASE_KEY);
      expect(calls).toContainEqual(PORTFOLIOS_QUERY_KEY);
    });

    it('5. successful portfolio update invalidates both dashboard namespaces', async () => {
      vi.mocked(portfoliosApi.updatePortfolio).mockResolvedValueOnce({ id: 'port-1' } as any);
      const wrapper = createWrapper();
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useUpdatePortfolio(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({ id: 'port-1', payload: { name: 'Renamed' } });
      });

      const calls = invalidateSpy.mock.calls.map((c) => c[0]?.queryKey);
      expect(calls).toContainEqual(DASHBOARD_OVERVIEW_QUERY_KEY);
      expect(calls).toContainEqual(DASHBOARD_BASE_KEY);
    });

    it('6. successful portfolio deletion invalidates both dashboard namespaces', async () => {
      vi.mocked(portfoliosApi.deletePortfolio).mockResolvedValueOnce(undefined as any);
      const wrapper = createWrapper();
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useDeletePortfolio(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync('port-1');
      });

      const calls = invalidateSpy.mock.calls.map((c) => c[0]?.queryKey);
      expect(calls).toContainEqual(DASHBOARD_OVERVIEW_QUERY_KEY);
      expect(calls).toContainEqual(DASHBOARD_BASE_KEY);
    });

    it('7b. failed portfolio mutation does not invalidate dashboard queries', async () => {
      vi.mocked(portfoliosApi.deletePortfolio).mockRejectedValueOnce(new Error('Not found'));
      const wrapper = createWrapper();
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useDeletePortfolio(), { wrapper });

      await act(async () => {
        try {
          await result.current.mutateAsync('port-404');
        } catch {
          // Expected
        }
      });

      const calls = invalidateSpy.mock.calls.map((c) => c[0]?.queryKey);
      expect(calls).not.toContainEqual(DASHBOARD_OVERVIEW_QUERY_KEY);
      expect(calls).not.toContainEqual(DASHBOARD_BASE_KEY);
    });
  });

  describe('Prefix Invalidation Coverage for Scoped and Combined Queries', () => {
    it('8. prefix invalidation marks both portfolio-scoped and combined-dashboard queries as stale', async () => {
      const qc = new QueryClient();

      // Seed queries with fresh data
      qc.setQueryData(['dashboardOverview'], { total: 100 });
      qc.setQueryData(['dashboardOverview', 'port-123'], { total: 50 });
      qc.setQueryData(['dashboard', 'allocation', 'all', 'INR'], { alloc: [] });
      qc.setQueryData(['dashboard', 'allocation', 'port-123', 'INR'], { alloc: [] });
      qc.setQueryData(['dashboard', 'holdings', 'all'], { results: [] });
      qc.setQueryData(['dashboard', 'holdings', 'port-123'], { results: [] });
      qc.setQueryData(['dashboard', 'dataQuality', 'all'], { overall_status: 'HEALTHY' });
      qc.setQueryData(['dashboard', 'recentActivity', 'all', 10], []);

      // Verify queries are initially fresh
      expect(qc.getQueryState(['dashboardOverview'])?.isInvalidated).toBe(false);
      expect(qc.getQueryState(['dashboardOverview', 'port-123'])?.isInvalidated).toBe(false);
      expect(qc.getQueryState(['dashboard', 'allocation', 'all', 'INR'])?.isInvalidated).toBe(false);
      expect(qc.getQueryState(['dashboard', 'allocation', 'port-123', 'INR'])?.isInvalidated).toBe(false);
      expect(qc.getQueryState(['dashboard', 'holdings', 'all'])?.isInvalidated).toBe(false);
      expect(qc.getQueryState(['dashboard', 'holdings', 'port-123'])?.isInvalidated).toBe(false);

      // Perform invalidation via shared helper
      invalidateDashboardQueries(qc);

      // Both combined and portfolio-scoped variants should now be invalidated
      expect(qc.getQueryState(['dashboardOverview'])?.isInvalidated).toBe(true);
      expect(qc.getQueryState(['dashboardOverview', 'port-123'])?.isInvalidated).toBe(true);
      expect(qc.getQueryState(['dashboard', 'allocation', 'all', 'INR'])?.isInvalidated).toBe(true);
      expect(qc.getQueryState(['dashboard', 'allocation', 'port-123', 'INR'])?.isInvalidated).toBe(true);
      expect(qc.getQueryState(['dashboard', 'holdings', 'all'])?.isInvalidated).toBe(true);
      expect(qc.getQueryState(['dashboard', 'holdings', 'port-123'])?.isInvalidated).toBe(true);
      expect(qc.getQueryState(['dashboard', 'dataQuality', 'all'])?.isInvalidated).toBe(true);
      expect(qc.getQueryState(['dashboard', 'recentActivity', 'all', 10])?.isInvalidated).toBe(true);
    });

    it('9. existing investment and portfolio queries continue to be invalidated appropriately', async () => {
      vi.mocked(investmentApi.createInvestment).mockResolvedValueOnce({ id: 'inv-10' } as any);
      const wrapper = createWrapper();
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useCreateInvestment(), { wrapper });

      await act(async () => {
        await result.current.mutateAsync({
          name: 'Asset',
          portfolio: 'portfolio-abc',
        } as any);
      });

      const calls = invalidateSpy.mock.calls.map((c) => c[0]?.queryKey);
      expect(calls).toContainEqual(['investments']);
      expect(calls).toContainEqual(['investments', { portfolioId: 'portfolio-abc' }]);
      expect(calls).toContainEqual(['portfolios']);
    });
  });
});
