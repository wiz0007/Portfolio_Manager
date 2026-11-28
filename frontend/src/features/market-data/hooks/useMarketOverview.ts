import { useQuery } from '@tanstack/react-query';
import { marketDataApi } from '../api/marketDataApi';
import { MarketOverviewData } from '../types';

export const MARKET_OVERVIEW_QUERY_KEY = ['market-overview'] as const;

export interface UseMarketOverviewOptions {
  enabled?: boolean;
}

export const useMarketOverview = (options?: UseMarketOverviewOptions) => {
  return useQuery<MarketOverviewData>({
    queryKey: MARKET_OVERVIEW_QUERY_KEY,
    queryFn: () => marketDataApi.getMarketOverview(),
    staleTime: 5 * 60 * 1000, // 5 minutes fresh
    gcTime: 30 * 60 * 1000, // 30 minutes in cache
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    retry: 2,
    enabled: options?.enabled ?? true,
  });
};
