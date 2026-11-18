import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { watchlistApi } from '../api/watchlistApi';
import { AddWatchlistPayload } from '../types';

export const WATCHLIST_QUERY_KEYS = {
  all: ['watchlist'] as const,
  detail: (id: string) => ['watchlist-detail', id] as const,
  latestPrice: (instrumentId: string) => ['instrument-latest-price', instrumentId] as const,
  history: (instrumentId: string, period: string) => ['instrument-price-history', instrumentId, period] as const,
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

export const useInstrumentHistory = (instrumentId: string, period: string = '1M') => {
  return useQuery({
    queryKey: WATCHLIST_QUERY_KEYS.history(instrumentId, period),
    queryFn: () => watchlistApi.getInstrumentHistory(instrumentId, period),
    enabled: !!instrumentId,
    staleTime: 5 * 60 * 1000,
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
