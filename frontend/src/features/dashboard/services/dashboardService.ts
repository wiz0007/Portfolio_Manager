import { apiClient } from '@/services/api/client';
import {
  AssetAllocationResponse,
  DashboardOverview,
  DataQualityResponse,
  HoldingsOverviewResponse,
  RecentActivityItem,
} from '../types/dashboard';
import { WatchlistItem } from '@/features/watchlists/types';

export const dashboardService = {
  async getOverview(portfolioId?: string): Promise<DashboardOverview> {
    const query = portfolioId ? `?portfolio_id=${encodeURIComponent(portfolioId)}` : '';
    return apiClient.get<DashboardOverview>(`/dashboard/overview/${query}`);
  },

  async getAllocation(portfolioId?: string, currency?: string): Promise<AssetAllocationResponse> {
    const params = new URLSearchParams();
    if (portfolioId) params.append('portfolio_id', portfolioId);
    if (currency) params.append('currency', currency);
    const query = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get<AssetAllocationResponse>(`/dashboard/allocation/${query}`);
  },

  async getHoldings(params?: {
    portfolioId?: string;
    category?: string;
    sortBy?: string;
    order?: string;
    limit?: number;
    offset?: number;
  }): Promise<HoldingsOverviewResponse> {
    const q = new URLSearchParams();
    if (params?.portfolioId) q.append('portfolio_id', params.portfolioId);
    if (params?.category) q.append('category', params.category);
    if (params?.sortBy) q.append('sort_by', params.sortBy);
    if (params?.order) q.append('order', params.order);
    if (params?.limit !== undefined) q.append('limit', String(params.limit));
    if (params?.offset !== undefined) q.append('offset', String(params.offset));
    const query = q.toString() ? `?${q.toString()}` : '';
    return apiClient.get<HoldingsOverviewResponse>(`/dashboard/holdings/${query}`);
  },

  async getRecentActivity(portfolioId?: string, limit: number = 10): Promise<RecentActivityItem[]> {
    const q = new URLSearchParams();
    q.append('limit', String(limit));
    if (portfolioId) q.append('portfolio_id', portfolioId);
    return apiClient.get<RecentActivityItem[]>(`/dashboard/recent-activity/?${q.toString()}`);
  },

  async getDataQuality(portfolioId?: string): Promise<DataQualityResponse> {
    const query = portfolioId ? `?portfolio_id=${encodeURIComponent(portfolioId)}` : '';
    return apiClient.get<DataQualityResponse>(`/dashboard/data-quality/${query}`);
  },

  async getWatchlistPreview(limit: number = 5): Promise<WatchlistItem[]> {
    return apiClient.get<WatchlistItem[]>(`/dashboard/watchlist-preview/?limit=${limit}`);
  },
};
