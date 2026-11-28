import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api/client';
import {
  Benchmark,
  BenchmarkComparison,
  InvestmentPerformance,
  PortfolioAllocation,
  PortfolioPerformance,
} from '../types';

export const analyticsKeys = {
  all: ['analytics'] as const,
  portfolioPerformance: (portfolioId: string, startDate?: string, endDate?: string) =>
    [...analyticsKeys.all, 'portfolio', portfolioId, 'performance', { startDate, endDate }] as const,
  portfolioAllocation: (portfolioId: string) =>
    [...analyticsKeys.all, 'portfolio', portfolioId, 'allocation'] as const,
  investmentPerformance: (investmentId: string, startDate?: string, endDate?: string) =>
    [...analyticsKeys.all, 'investment', investmentId, 'performance', { startDate, endDate }] as const,
  benchmarks: () => [...analyticsKeys.all, 'benchmarks'] as const,
  benchmarkComparison: (portfolioId: string, benchmarkId: string, startDate?: string, endDate?: string) =>
    [...analyticsKeys.all, 'portfolio', portfolioId, 'benchmark', benchmarkId, { startDate, endDate }] as const,
};

export const usePortfolioPerformance = (
  portfolioId?: string,
  startDate?: string,
  endDate?: string,
) => {
  return useQuery<PortfolioPerformance>({
    queryKey: analyticsKeys.portfolioPerformance(portfolioId || '', startDate, endDate),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      const queryStr = params.toString() ? `?${params.toString()}` : '';
      return apiClient.get<PortfolioPerformance>(
        `/analytics/portfolios/${portfolioId}/performance/${queryStr}`
      );
    },
    enabled: Boolean(portfolioId),
    staleTime: 60 * 1000,
  });
};

export const usePortfolioAllocation = (portfolioId?: string) => {
  return useQuery<PortfolioAllocation>({
    queryKey: analyticsKeys.portfolioAllocation(portfolioId || ''),
    queryFn: async () => {
      return apiClient.get<PortfolioAllocation>(
        `/analytics/portfolios/${portfolioId}/allocation/`
      );
    },
    enabled: Boolean(portfolioId),
    staleTime: 60 * 1000,
  });
};

export const useInvestmentPerformance = (
  investmentId?: string,
  startDate?: string,
  endDate?: string,
) => {
  return useQuery<InvestmentPerformance>({
    queryKey: analyticsKeys.investmentPerformance(investmentId || '', startDate, endDate),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      const queryStr = params.toString() ? `?${params.toString()}` : '';
      return apiClient.get<InvestmentPerformance>(
        `/analytics/investments/${investmentId}/performance/${queryStr}`
      );
    },
    enabled: Boolean(investmentId),
    staleTime: 60 * 1000,
  });
};

export const useBenchmarks = () => {
  return useQuery<Benchmark[]>({
    queryKey: analyticsKeys.benchmarks(),
    queryFn: async () => {
      return apiClient.get<Benchmark[]>('/analytics/benchmarks/');
    },
    staleTime: 5 * 60 * 1000,
  });
};

export const useBenchmarkComparison = (
  portfolioId?: string,
  benchmarkId?: string,
  startDate?: string,
  endDate?: string,
) => {
  return useQuery<BenchmarkComparison>({
    queryKey: analyticsKeys.benchmarkComparison(portfolioId || '', benchmarkId || '', startDate, endDate),
    queryFn: async () => {
      const params = new URLSearchParams({ benchmark_id: benchmarkId! });
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      return apiClient.get<BenchmarkComparison>(
        `/analytics/portfolios/${portfolioId}/benchmark-comparison/?${params.toString()}`
      );
    },
    enabled: Boolean(portfolioId && benchmarkId),
    staleTime: 60 * 1000,
  });
};
