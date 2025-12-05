/**
 * React Query hooks for AI-Enhanced Screening API endpoints
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type {
  APIResponse,
  StockExplanation,
  BatchExplanationRequest,
  AIUsageStats,
  InvestorPersona,
} from '../types';

// Query Keys
export const aiScreeningKeys = {
  all: ['ai-screening'] as const,
  explanation: (strategy: string, ticker: string, persona?: InvestorPersona | null) =>
    [...aiScreeningKeys.all, 'explanation', strategy, ticker, persona] as const,
  batch: (tickers: string[]) =>
    [...aiScreeningKeys.all, 'batch', tickers.join(',')] as const,
  usage: () => [...aiScreeningKeys.all, 'usage'] as const,
};

/**
 * Get AI explanation for a single stock
 */
export function useStockExplanation(
  strategy: string,
  ticker: string,
  options?: {
    persona?: InvestorPersona | null;
    forceRefresh?: boolean;
    enabled?: boolean;
  }
) {
  return useQuery({
    queryKey: aiScreeningKeys.explanation(strategy, ticker, options?.persona),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (options?.persona) params.set('persona', options.persona);
      if (options?.forceRefresh) params.set('force_refresh', 'true');
      const queryString = params.toString();
      const url = `/ai-screening/${strategy}/${ticker}/explain${queryString ? `?${queryString}` : ''}`;
      const response = await api.get<APIResponse<StockExplanation>>(url);
      return response.data;
    },
    enabled: options?.enabled !== false && !!ticker && !!strategy,
    staleTime: 24 * 60 * 60 * 1000, // 24 hours - matches backend cache
    gcTime: 24 * 60 * 60 * 1000,
  });
}

/**
 * Lazy fetch explanation (doesn't auto-fetch)
 */
export function useLazyStockExplanation(
  strategy: string,
  ticker: string,
  options?: {
    persona?: InvestorPersona | null;
    forceRefresh?: boolean;
  }
) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      const params = new URLSearchParams();
      if (options?.persona) params.set('persona', options.persona);
      if (options?.forceRefresh) params.set('force_refresh', 'true');
      const queryString = params.toString();
      const url = `/ai-screening/${strategy}/${ticker}/explain${queryString ? `?${queryString}` : ''}`;
      const response = await api.get<APIResponse<StockExplanation>>(url);
      return response.data;
    },
    onSuccess: (data) => {
      // Cache the result
      queryClient.setQueryData(
        aiScreeningKeys.explanation(strategy, ticker, options?.persona),
        data
      );
    },
  });
}

/**
 * Get AI explanations for multiple stocks
 */
export function useBatchExplanations(
  options?: { enabled?: boolean }
) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: BatchExplanationRequest) => {
      const response = await api.post<APIResponse<StockExplanation[]>>(
        '/ai-screening/explain-batch',
        request
      );
      return response.data;
    },
    onSuccess: (data, variables) => {
      // Cache each individual explanation
      data.forEach((explanation) => {
        queryClient.setQueryData(
          aiScreeningKeys.explanation(
            variables.strategy || 'maverick',
            explanation.ticker,
            variables.persona
          ),
          explanation
        );
      });
    },
  });
}

/**
 * Get AI usage statistics
 */
export function useAIUsageStats(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: aiScreeningKeys.usage(),
    queryFn: async () => {
      const response = await api.get<APIResponse<AIUsageStats>>(
        '/ai-screening/usage'
      );
      return response.data;
    },
    enabled: options?.enabled !== false,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook that combines stock explanation with loading/error states
 */
export function useStockExplanationWithStatus(
  strategy: string,
  ticker: string,
  persona?: InvestorPersona | null
) {
  const query = useStockExplanation(strategy, ticker, { persona, enabled: false });
  const lazyFetch = useLazyStockExplanation(strategy, ticker, { persona });
  
  return {
    // Data
    explanation: query.data || lazyFetch.data,
    
    // Status
    isLoading: query.isLoading || lazyFetch.isPending,
    isError: query.isError || lazyFetch.isError,
    error: query.error || lazyFetch.error,
    
    // From cache?
    isCached: query.data?.cached ?? false,
    
    // Actions
    fetch: lazyFetch.mutate,
    fetchAsync: lazyFetch.mutateAsync,
    
    // Query state
    isFetched: query.isFetched || lazyFetch.isSuccess,
  };
}

