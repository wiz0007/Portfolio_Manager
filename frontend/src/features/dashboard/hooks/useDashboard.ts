import { useQuery, useQueryClient } from '@tanstack/react-query';
import { dashboardService } from '../services/dashboardService';
import {
  AssetAllocationResponse,
  DashboardOverview,
  DataQualityResponse,
  HoldingsOverviewResponse,
  RecentActivityItem,
} from '../types/dashboard';
import { WatchlistItem } from '@/features/watchlists/types';
import { ApiClientError } from '@/services/api/client';

export const DASHBOARD_OVERVIEW_QUERY_KEY = ['dashboardOverview'];
export const DASHBOARD_BASE_KEY = ['dashboard'];

export function useDashboardOverview(portfolioId?: string) {
  return useQuery<DashboardOverview, ApiClientError>({
    queryKey: portfolioId ? [...DASHBOARD_OVERVIEW_QUERY_KEY, portfolioId] : DASHBOARD_OVERVIEW_QUERY_KEY,
    queryFn: () => dashboardService.getOverview(portfolioId),
    staleTime: 30 * 1000,
  });
}

export function useDashboardAllocation(portfolioId?: string, currency?: string) {
  return useQuery<AssetAllocationResponse, ApiClientError>({
    queryKey: ['dashboard', 'allocation', portfolioId || 'all', currency || 'default'],
    queryFn: () => dashboardService.getAllocation(portfolioId, currency),
    staleTime: 30 * 1000,
  });
}

export function useDashboardHoldings(params?: {
  portfolioId?: string;
  category?: string;
  sortBy?: string;
  order?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery<HoldingsOverviewResponse, ApiClientError>({
    queryKey: [
      'dashboard',
      'holdings',
      params?.portfolioId || 'all',
      params?.category || 'all',
      params?.sortBy || 'current_value',
      params?.order || 'desc',
      params?.limit || 20,
      params?.offset || 0,
    ],
    queryFn: () => dashboardService.getHoldings(params),
    staleTime: 30 * 1000,
  });
}

export function useDashboardRecentActivity(portfolioId?: string, limit: number = 10) {
  return useQuery<RecentActivityItem[], ApiClientError>({
    queryKey: ['dashboard', 'recentActivity', portfolioId || 'all', limit],
    queryFn: () => dashboardService.getRecentActivity(portfolioId, limit),
    staleTime: 30 * 1000,
  });
}

export function useDashboardDataQuality(portfolioId?: string) {
  return useQuery<DataQualityResponse, ApiClientError>({
    queryKey: ['dashboard', 'dataQuality', portfolioId || 'all'],
    queryFn: () => dashboardService.getDataQuality(portfolioId),
    staleTime: 30 * 1000,
  });
}

export function useDashboardWatchlistPreview(limit: number = 5) {
  return useQuery<WatchlistItem[], ApiClientError>({
    queryKey: ['dashboard', 'watchlistPreview', limit],
    queryFn: () => dashboardService.getWatchlistPreview(limit),
    staleTime: 30 * 1000,
  });
}

export function useInvalidateDashboard() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: DASHBOARD_OVERVIEW_QUERY_KEY });
    queryClient.invalidateQueries({ queryKey: DASHBOARD_BASE_KEY });
    queryClient.invalidateQueries({ queryKey: ['watchlist'] });
  };
}
