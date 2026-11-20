import { apiClient } from '@/services/api/client';
import {
  AddWatchlistPayload,
  InstrumentHistoryResponse,
  InstrumentMarketStatus,
  WatchlistItem,
  WatchlistMarketData,
} from '../types';

export const watchlistApi = {
  getWatchlist: (): Promise<WatchlistItem[]> => {
    return apiClient.get<WatchlistItem[]>('/watchlist/');
  },

  getWatchlistItem: (id: string): Promise<WatchlistItem> => {
    return apiClient.get<WatchlistItem>(`/watchlist/${id}/`);
  },

  addToWatchlist: (data: AddWatchlistPayload): Promise<WatchlistItem> => {
    return apiClient.post<WatchlistItem>('/watchlist/', data);
  },

  removeFromWatchlist: (id: string): Promise<void> => {
    return apiClient.delete<void>(`/watchlist/${id}/`);
  },

  getInstrumentLatestMarketData: (instrumentId: string): Promise<WatchlistMarketData & { instrument_id: string; symbol: string }> => {
    return apiClient.get(`/instruments/${instrumentId}/market-data/latest/`);
  },

  getInstrumentHistory: (
    instrumentId: string,
    period: string = '1M',
    options?: {
      from?: string;
      to?: string;
      interval?: string;
      series_id?: string;
      price_type?: string;
      signal?: AbortSignal;
    }
  ): Promise<InstrumentHistoryResponse> => {
    const params = new URLSearchParams({ period });
    if (options?.from) params.append('from', options.from);
    if (options?.to) params.append('to', options.to);
    if (options?.interval) params.append('interval', options.interval);
    if (options?.series_id) params.append('series_id', options.series_id);
    if (options?.price_type) params.append('price_type', options.price_type);
    return apiClient.get<InstrumentHistoryResponse>(
      `/instruments/${instrumentId}/market-data/history/?${params.toString()}`,
      { signal: options?.signal }
    );
  },

  getInstrumentMarketStatus: (instrumentId: string): Promise<InstrumentMarketStatus> => {
    return apiClient.get<InstrumentMarketStatus>(`/instruments/${instrumentId}/market-data/status/`);
  },
};
