/**
 * React Query hooks for Stock API endpoints
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type {
  APIResponse,
  StockQuote,
  StockInfo,
  HistoricalData,
  TechnicalIndicators,
} from '../types';

// Query Keys
export const stockKeys = {
  all: ['stocks'] as const,
  quote: (ticker: string) => [...stockKeys.all, 'quote', ticker] as const,
  quotes: (tickers: string[]) => [...stockKeys.all, 'quotes', tickers.join(',')] as const,
  info: (ticker: string) => [...stockKeys.all, 'info', ticker] as const,
  history: (ticker: string, params?: HistoryParams) => 
    [...stockKeys.all, 'history', ticker, params] as const,
  technical: (ticker: string) => [...stockKeys.all, 'technical', ticker] as const,
};

interface HistoryParams {
  start_date?: string;
  end_date?: string;
  interval?: '1d' | '1wk' | '1mo';
}

/**
 * Get single stock quote
 */
export function useStockQuote(ticker: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: stockKeys.quote(ticker),
    queryFn: async () => {
      const response = await api.get<APIResponse<StockQuote>>(
        `/stocks/${ticker}/quote`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && !!ticker,
    staleTime: 30 * 1000, // 30 seconds - stock prices update frequently
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}

/**
 * Get batch stock quotes
 */
export function useStockQuotes(tickers: string[], options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: stockKeys.quotes(tickers),
    queryFn: async () => {
      const response = await api.post<APIResponse<StockQuote[]>>(
        '/stocks/batch',
        { tickers }
      );
      return response.data;
    },
    enabled: options?.enabled !== false && tickers.length > 0,
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  });
}

/**
 * Get stock info (company details)
 */
export function useStockInfo(ticker: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: stockKeys.info(ticker),
    queryFn: async () => {
      const response = await api.get<APIResponse<StockInfo>>(
        `/stocks/${ticker}/info`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && !!ticker,
    staleTime: 5 * 60 * 1000, // 5 minutes - company info changes less frequently
  });
}

/**
 * Get historical OHLCV data
 */
export function useStockHistory(
  ticker: string,
  params?: HistoryParams,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: stockKeys.history(ticker, params),
    queryFn: async () => {
      const queryParams = new URLSearchParams();
      if (params?.start_date) queryParams.set('start_date', params.start_date);
      if (params?.end_date) queryParams.set('end_date', params.end_date);
      if (params?.interval) queryParams.set('interval', params.interval);

      const url = `/stocks/${ticker}/history${queryParams.toString() ? `?${queryParams}` : ''}`;
      const response = await api.get<APIResponse<HistoricalData>>(url);
      return response.data;
    },
    enabled: options?.enabled !== false && !!ticker,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get technical indicators for a stock
 */
export function useTechnicalIndicators(
  ticker: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: stockKeys.technical(ticker),
    queryFn: async () => {
      const response = await api.get<APIResponse<TechnicalIndicators>>(
        `/technical/${ticker}/full`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && !!ticker,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Search stocks by query
 */
export function useStockSearch(query: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: [...stockKeys.all, 'search', query],
    queryFn: async () => {
      const response = await api.get<APIResponse<StockInfo[]>>(
        `/stocks/search?q=${encodeURIComponent(query)}`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && query.length >= 1,
    staleTime: 60 * 1000,
  });
}

/**
 * Prefetch stock quote (for hover previews)
 */
export function usePrefetchStockQuote() {
  const queryClient = useQueryClient();

  return (ticker: string) => {
    queryClient.prefetchQuery({
      queryKey: stockKeys.quote(ticker),
      queryFn: async () => {
        const response = await api.get<APIResponse<StockQuote>>(
          `/stocks/${ticker}/quote`
        );
        return response.data;
      },
      staleTime: 30 * 1000,
    });
  };
}

