import { apiClient } from '@/services/api/client';
import {
  HistoricalSeriesResponse,
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
    options?: {
      days?: number;
      from?: string;
      to?: string;
      interval?: string;
      period?: string;
      price_type?: string;
      series_id?: string;
      signal?: AbortSignal;
    }
  ): Promise<HistoricalSeriesResponse> => {
    const query = new URLSearchParams();
    if (options?.days) query.append('days', options.days.toString());
    if (options?.from) query.append('from', options.from);
    if (options?.to) query.append('to', options.to);
    if (options?.interval) query.append('interval', options.interval);
    if (options?.period) query.append('period', options.period);
    if (options?.price_type) query.append('price_type', options.price_type);
    if (options?.series_id) query.append('series_id', options.series_id);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiClient.get<HistoricalSeriesResponse>(`/market-data/history/${id}/${qs}`, { signal: options?.signal });
  },

  getSeries: (instrumentId: string) => {
    return apiClient.get<Array<{
      id: string; instrument_id: string; exchange: string; source: string;
      price_type: string; currency: string; unit: string; data_version: number;
      last_published_at: string | null;
    }>>(`/market-data/series/?instrument_id=${encodeURIComponent(instrumentId)}`);
  },

  createManualSeries: (instrumentId: string, priceType: string, unit: string) => {
    return apiClient.post<{
      id: string; instrument_id: string; exchange: string; source: string;
      price_type: string; currency: string; unit: string; data_version: number;
      last_published_at: string | null;
    }>('/market-data/series/', { instrument_id: instrumentId, price_type: priceType, unit });
  },

  getSeriesVersion: (seriesId: string) => {
    return apiClient.get<{ series_id: string; instrument_id: string; data_version: number; last_published_at: string | null }>(
      `/market-data/series/${seriesId}/version/`
    );
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

  // Manual Market-Data Operations & Requests
  createInstrumentRequest: (data: {
    raw_name: string;
    asset_class: string;
    symbol?: string;
    exchange?: string;
    isin?: string;
    scheme_code?: string;
    notes?: string;
  }) => {
    return apiClient.post('/market-data/requests/', data);
  },

  getInstrumentRequests: (statusParam?: string) => {
    const qs = statusParam ? `?status=${encodeURIComponent(statusParam)}` : '';
    return apiClient.get(`/market-data/requests/${qs}`);
  },

  matchInstrumentRequest: (id: string, instrumentId: string) => {
    return apiClient.post(`/market-data/requests/${id}/match/`, { instrument_id: instrumentId });
  },

  approveInstrumentRequest: (id: string, data: Record<string, unknown>) => {
    return apiClient.post(`/market-data/requests/${id}/approve/`, data);
  },

  rejectInstrumentRequest: (id: string, reason: string) => {
    return apiClient.post(`/market-data/requests/${id}/reject/`, { reason });
  },

  getDailyWorklist: (dateStr?: string) => {
    const target = dateStr || new Date().toISOString().split('T')[0];
    return apiClient.get(`/market-data/worklists/${target}/`);
  },

  generateDailyWorklist: (dateStr?: string) => {
    return apiClient.post('/market-data/worklists/generate/', dateStr ? { date: dateStr } : {});
  },

  createPriceObservation: (data: {
    instrument: string;
    series: string;
    price_type: string;
    value: string;
    currency?: string;
    unit?: string;
    effective_at: string;
    source?: string;
    source_reference?: string;
    notes?: string;
  }) => {
    return apiClient.post('/market-data/observations/', data);
  },

  getObservations: (params?: { instrument?: string; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.instrument) query.append('instrument', params.instrument);
    if (params?.status) query.append('status', params.status);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiClient.get(`/market-data/observations/${qs}`);
  },

  submitPriceObservationForReview: (id: string) => {
    return apiClient.post(`/market-data/observations/${id}/submit-for-review/`);
  },

  publishPriceObservation: (id: string) => {
    return apiClient.post(`/market-data/observations/${id}/publish/`);
  },

  rejectPriceObservation: (id: string, reason: string) => {
    return apiClient.post(`/market-data/observations/${id}/reject/`, { reason });
  },

  correctPriceObservation: (id: string, data: { value: string; correction_reason: string; notes?: string }) => {
    return apiClient.post(`/market-data/observations/${id}/correct/`, data);
  },

  previewCsvImport: (csvContent: string, filename?: string) => {
    return apiClient.post('/market-data/import/preview/', { csv_content: csvContent, filename });
  },

  commitCsvImport: (previewResult: Record<string, unknown>) => {
    const batchId = (previewResult as { batch_id?: string }).batch_id;
    return apiClient.post('/market-data/import/commit/', { batch_id: batchId });
  },

  resolvePrice: (instrumentId: string, asOf?: string) => {
    const qs = asOf ? `?as_of=${encodeURIComponent(asOf)}` : '';
    return apiClient.get(`/market-data/resolve/${instrumentId}/${qs}`);
  },
};
