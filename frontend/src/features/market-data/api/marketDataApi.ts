import { apiClient } from '@/services/api/client';
import {
  HistoricalPoint,
  Instrument,
  MarketOverviewData,
  MarketQuote,
  ProviderHealthReport,
} from '../types';

export const marketDataApi = {
  // Instrument endpoints
  searchInstruments: (query: string): Promise<Instrument[]> => {
    return apiClient.get<Instrument[]>(`/instruments/search/?q=${encodeURIComponent(query)}`);
  },

  getInstruments: (params?: { asset_class?: string; search?: string }): Promise<{ results: Instrument[] } | Instrument[]> => {
    const query = new URLSearchParams();
    if (params?.asset_class) query.append('asset_class', params.asset_class);
    if (params?.search) query.append('search', params.search);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiClient.get<{ results: Instrument[] } | Instrument[]>(`/instruments/${qs}`);
  },

  getInstrument: (id: string): Promise<Instrument> => {
    return apiClient.get<Instrument>(`/instruments/${id}/`);
  },

  // Quote & Market Data endpoints
  getQuote: (id: string, forceRefresh: boolean = false): Promise<MarketQuote> => {
    const query = forceRefresh ? '?refresh=true' : '';
    return apiClient.get<MarketQuote>(`/market-data/quotes/${id}/${query}`);
  },

  getBulkQuotes: (symbols: string[]): Promise<Record<string, MarketQuote>> => {
    return apiClient.get<Record<string, MarketQuote>>(
      `/market-data/quotes/?symbols=${encodeURIComponent(symbols.join(','))}`
    );
  },

  getHistory: (
    id: string,
    options?: { days?: number; from?: string; to?: string; interval?: string }
  ): Promise<HistoricalPoint[]> => {
    const query = new URLSearchParams();
    if (options?.days) query.append('days', options.days.toString());
    if (options?.from) query.append('from', options.from);
    if (options?.to) query.append('to', options.to);
    if (options?.interval) query.append('interval', options.interval);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiClient.get<HistoricalPoint[]>(`/market-data/history/${id}/${qs}`);
  },

  getMarketOverview: (): Promise<MarketOverviewData> => {
    return apiClient.get<MarketOverviewData>('/market-data/overview/');
  },

  getProviders: (): Promise<Array<{ name: string; capabilities: Record<string, unknown> }>> => {
    return apiClient.get<Array<{ name: string; capabilities: Record<string, unknown> }>>('/market-data/providers/');
  },

  getHealth: (): Promise<ProviderHealthReport[]> => {
    return apiClient.get<ProviderHealthReport[]>('/market-data/health/');
  },

  refreshQuote: (id: string): Promise<MarketQuote> => {
    return apiClient.post<MarketQuote>(`/market-data/refresh/${id}/`);
  },
};
