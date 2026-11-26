import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useMarketHistory, MARKET_HISTORY_QUERY_KEYS } from '../hooks/useMarketHistory';
import { marketDataApi } from '../api/marketDataApi';
import { HistoricalPoint, HistoricalSeriesResponse } from '../types';

describe('Market History TanStack Query Caching Architecture', () => {
  let queryClient: QueryClient;

  const mockPoints: HistoricalPoint[] = [
    {
      timestamp: '2026-11-18T10:00:00Z',
      price: '1420.0000',
      open_price: '1410.0000',
      high_price: '1425.0000',
      low_price: '1405.0000',
      close_price: '1420.0000',
      volume: 120000,
      interval: '1D',
      is_synthetic: false,
    },
    {
      timestamp: '2026-11-19T10:00:00Z',
      price: '1435.0000',
      open_price: '1420.0000',
      high_price: '1440.0000',
      low_price: '1418.0000',
      close_price: '1435.0000',
      volume: 150000,
      interval: '1D',
      is_synthetic: false,
    },
    {
      timestamp: '2026-11-20T10:00:00Z',
      price: '1428.0000',
      open_price: '1435.0000',
      high_price: '1438.0000',
      low_price: '1422.0000',
      close_price: '1428.0000',
      volume: 98000,
      interval: '1D',
      is_synthetic: false,
    },
  ];
  const mockHistory: HistoricalSeriesResponse = {
    instrument_id: 'inst-infy-1',
    series_id: '00000000-0000-4000-8000-000000000001',
    data_version: 3,
    frequency: 'daily',
    price_type: 'LTP',
    currency: 'INR',
    unit: 'SHARES',
    start_date: '2026-10-21',
    end_date: '2026-11-20',
    last_published_at: '2026-11-20T12:00:00Z',
    trust_class: 'VERIFIED_PERMITTED_SECONDARY',
    message: 'ok',
    points: mockPoints,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(marketDataApi, 'getSeriesVersion').mockResolvedValue({
      series_id: '00000000-0000-4000-8000-000000000001',
      instrument_id: 'inst-infy-1',
      data_version: 3,
      last_published_at: '2026-11-20T12:00:00Z',
    });
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('generates fully isolated query keys containing instrument, series, range, frequency, and priceType', () => {
    const key1 = MARKET_HISTORY_QUERY_KEYS.detail('inst-1', 'INFY_LTP_INR', '1M', '1D', 'LTP');
    const key2 = MARKET_HISTORY_QUERY_KEYS.detail('inst-2', 'TCS_LTP_INR', '1M', '1D', 'LTP');
    const key3 = MARKET_HISTORY_QUERY_KEYS.detail('inst-1', 'INFY_LTP_INR', '1Y', '1D', 'LTP');

    expect(key1).toEqual(['market-history', 'inst-1', 'INFY_LTP_INR', '1M', '1D', 'LTP']);
    expect(key2).toEqual(['market-history', 'inst-2', 'TCS_LTP_INR', '1M', '1D', 'LTP']);
    expect(key3).toEqual(['market-history', 'inst-1', 'INFY_LTP_INR', '1Y', '1D', 'LTP']);
    expect(key1).not.toEqual(key2);
    expect(key1).not.toEqual(key3);
  });

  it('fetches historical series on first mount and caches with 1h staleTime and 24h gcTime', async () => {
    const getHistorySpy = vi.spyOn(marketDataApi, 'getHistory').mockResolvedValue(mockHistory);

    const { result } = renderHook(
      () =>
        useMarketHistory({
          instrumentId: 'inst-infy-1',
          seriesId: 'INFY_LTP_INR',
          range: '1M',
        }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockHistory);
    expect(getHistorySpy).toHaveBeenCalledTimes(1);

    // Verify query cache entry options
    const query = queryClient
      .getQueryCache()
      .find({ queryKey: ['market-history', 'inst-infy-1', 'INFY_LTP_INR', '1M', '1D', 'LTP'] });
    expect(query).toBeDefined();
    // @ts-ignore
    expect(query?.options.staleTime).toBe(60 * 60 * 1000); // 1 hour
    // @ts-ignore
    expect(query?.options.gcTime).toBe(24 * 60 * 60 * 1000); // 24 hours
  });

  it('serves subsequent requests from cache without issuing redundant network calls while data is fresh', async () => {
    const getHistorySpy = vi.spyOn(marketDataApi, 'getHistory').mockResolvedValue(mockHistory);

    // First render
    const { result, unmount } = renderHook(
      () =>
        useMarketHistory({
          instrumentId: 'inst-infy-1',
          seriesId: 'INFY_LTP_INR',
          range: '1M',
        }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(getHistorySpy).toHaveBeenCalledTimes(1);
    unmount();

    // Re-render the same query while fresh
    const { result: cachedResult } = renderHook(
      () =>
        useMarketHistory({
          instrumentId: 'inst-infy-1',
          seriesId: 'INFY_LTP_INR',
          range: '1M',
        }),
      { wrapper }
    );

    // Should immediately have data and NOT call the API again
    expect(cachedResult.current.data).toEqual(mockHistory);
    expect(getHistorySpy).toHaveBeenCalledTimes(1);
  });

  it('preserves valid cached historical data if a background refetch fails', async () => {
    const getHistorySpy = vi.spyOn(marketDataApi, 'getHistory').mockResolvedValue(mockHistory);

    const { result, rerender } = renderHook(
      () =>
        useMarketHistory({
          instrumentId: 'inst-infy-1',
          seriesId: 'INFY_LTP_INR',
          range: '1M',
        }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockHistory);

    // Now mock network error on next fetch
    getHistorySpy.mockRejectedValueOnce(new Error('Network connection timeout'));

    // Invalidate to force a refetch
    await queryClient.invalidateQueries({
      queryKey: ['market-history', 'inst-infy-1'],
    });

    rerender();

    // The query should still retain the previous cached data rather than wiping the chart
    expect(result.current.data).toEqual(mockHistory);
  });
});
