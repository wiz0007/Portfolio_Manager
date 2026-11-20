import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { watchlistApi } from '../api/watchlistApi';
import { AddWatchlistPayload } from '../types';

export const WATCHLIST_QUERY_KEYS = {
  all: ['watchlist'] as const,
  detail: (id: string) => ['watchlist-detail', id] as const,
  latestPrice: (instrumentId: string) => ['instrument-latest-price', instrumentId] as const,
  history: (
    instrumentId: string,
    period: string = '1M',
    seriesId: string = 'default',
    frequency: string = '1D',
    priceType: string = 'LTP'
  ) => ['market-history', instrumentId, seriesId, period, frequency, priceType] as const,
  status: (instrumentId: string) => ['instrument-market-status', instrumentId] as const,
};

export const useWatchlist = () => {
  return useQuery({
    queryKey: WATCHLIST_QUERY_KEYS.all,
    queryFn: watchlistApi.getWatchlist,
    staleTime: 60 * 1000,
  });
};

export const useWatchlistItem = (id: string) => {
  return useQuery({
    queryKey: WATCHLIST_QUERY_KEYS.detail(id),
    queryFn: () => watchlistApi.getWatchlistItem(id),
    enabled: !!id,
  });
};

export const useAddWatchlistItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: AddWatchlistPayload) => watchlistApi.addToWatchlist(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WATCHLIST_QUERY_KEYS.all });
    },
  });
};

export const useRemoveWatchlistItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => watchlistApi.removeFromWatchlist(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WATCHLIST_QUERY_KEYS.all });
    },
  });
};

export const useInstrumentLatestPrice = (instrumentId: string) => {
  return useQuery({
    queryKey: WATCHLIST_QUERY_KEYS.latestPrice(instrumentId),
    queryFn: () => watchlistApi.getInstrumentLatestMarketData(instrumentId),
    enabled: !!instrumentId,
    staleTime: 30 * 1000,
  });
};

export const useInstrumentHistory = (
  instrumentId: string,
  period: string = '1M',
  options?: { seriesId?: string; frequency?: string; priceType?: string }
) => {
  const seriesId = options?.seriesId || 'default';
  const frequency = options?.frequency || '1D';
  const priceType = options?.priceType || 'LTP';

  return useQuery({
    queryKey: WATCHLIST_QUERY_KEYS.history(instrumentId, period, seriesId, frequency, priceType),
    queryFn: ({ signal }) =>
      watchlistApi.getInstrumentHistory(instrumentId, period, {
        interval: frequency,
        series_id: seriesId !== 'default' ? seriesId : undefined,
        price_type: priceType,
        signal,
      }),
    enabled: !!instrumentId,
    staleTime: 60 * 60 * 1000, // 1 hour (ERD 10.2)
    gcTime: 24 * 60 * 60 * 1000, // 24 hours (ERD 10.2)
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    refetchInterval: false,
    retry: 2,
  });
};

export const useInstrumentMarketStatus = (instrumentId: string) => {
  return useQuery({
    queryKey: WATCHLIST_QUERY_KEYS.status(instrumentId),
    queryFn: () => watchlistApi.getInstrumentMarketStatus(instrumentId),
    enabled: !!instrumentId,
    staleTime: 5 * 60 * 1000,
  });
};
