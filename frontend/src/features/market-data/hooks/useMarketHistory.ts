import { useQuery, useQueryClient } from '@tanstack/react-query';
import { marketDataApi } from '../api/marketDataApi';
import { HistoricalPoint } from '../types';

export const MARKET_HISTORY_QUERY_KEYS = {
  detail: (
    instrumentId: string,
    seriesId: string = 'default',
    range: string = '1M',
    frequency: string = '1D',
    priceType: string = 'LTP'
  ) => ['market-history', instrumentId, seriesId, range, frequency, priceType] as const,
};

export interface UseMarketHistoryOptions {
  instrumentId: string;
  seriesId?: string;
  range?: string;
  frequency?: string;
  priceType?: string;
  enabled?: boolean;
}

export const useMarketHistory = ({
  instrumentId,
  seriesId = 'default',
  range = '1M',
  frequency = '1D',
  priceType = 'LTP',
  enabled = true,
}: UseMarketHistoryOptions) => {
  const daysMap: Record<string, number> = {
    '1W': 7,
    '1M': 30,
    '3M': 90,
    '6M': 180,
    '1Y': 365,
    'ALL': 1825, // 5 years consistent across backend and frontend (ERD Section 14.5)
  };
  const days = daysMap[range] || 30;

  return useQuery<HistoricalPoint[]>({
    queryKey: MARKET_HISTORY_QUERY_KEYS.detail(instrumentId, seriesId, range, frequency, priceType),
    queryFn: ({ signal }) =>
      marketDataApi.getHistory(instrumentId, {
        days,
        interval: frequency,
        period: range,
        price_type: priceType,
        signal,
      }),
    enabled: Boolean(instrumentId) && enabled,
    staleTime: 60 * 60 * 1000, // 1 hour (ERD 10.2)
    gcTime: 24 * 60 * 60 * 1000, // 24 hours (ERD 10.2)
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    refetchInterval: false,
    retry: 2,
  });
};

export interface SeriesVersionData {
  series_id: string;
  instrument_id: string;
  data_version: number;
  last_published_at: string | null;
}

export const useMarketSeriesVersion = (seriesId?: string, enabled = true) => {
  return useQuery<SeriesVersionData>({
    queryKey: ['market-series-version', seriesId],
    queryFn: async ({ signal }) => {
      const res = await fetch(`/api/v1/market-data/series/${seriesId}/version/`, { signal });
      if (!res.ok) throw new Error('Failed to retrieve series version');
      return res.json();
    },
    enabled: Boolean(seriesId) && seriesId !== 'default' && enabled,
    staleTime: 0, // Checks on focus to discover publication changes without full history polling
    refetchOnWindowFocus: true,
  });
};

export const useInvalidateMarketHistory = () => {
  const queryClient = useQueryClient();
  return (instrumentId?: string) => {
    if (instrumentId) {
      queryClient.invalidateQueries({
        queryKey: ['market-history', instrumentId],
      });
    } else {
      queryClient.invalidateQueries({
        queryKey: ['market-history'],
      });
    }
  };
};
