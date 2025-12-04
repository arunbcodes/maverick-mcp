/**
 * React Query hooks for Screening API endpoints
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '../client';
import type {
  APIResponse,
  ScreeningResponse,
  ScreeningFilters,
  ScreeningResult,
} from '../types';

// Query Keys
export const screeningKeys = {
  all: ['screening'] as const,
  maverick: (limit?: number) => [...screeningKeys.all, 'maverick', limit] as const,
  maverickBear: (limit?: number) => [...screeningKeys.all, 'maverick-bear', limit] as const,
  breakouts: (limit?: number) => [...screeningKeys.all, 'breakouts', limit] as const,
  filtered: (filters: ScreeningFilters) => [...screeningKeys.all, 'filtered', filters] as const,
  allStrategies: () => [...screeningKeys.all, 'all-strategies'] as const,
};

/**
 * Get Maverick (bullish) stock picks
 */
export function useMaverickStocks(limit: number = 20, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: screeningKeys.maverick(limit),
    queryFn: async () => {
      const response = await api.get<APIResponse<ScreeningResponse>>(
        `/screening/maverick?limit=${limit}`
      );
      return response.data;
    },
    enabled: options?.enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes - screening results update less frequently
  });
}

/**
 * Get Maverick Bear (bearish) stock picks
 */
export function useMaverickBearStocks(limit: number = 20, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: screeningKeys.maverickBear(limit),
    queryFn: async () => {
      const response = await api.get<APIResponse<ScreeningResponse>>(
        `/screening/maverick-bear?limit=${limit}`
      );
      return response.data;
    },
    enabled: options?.enabled,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get supply/demand breakout stocks
 */
export function useBreakoutStocks(limit: number = 20, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: screeningKeys.breakouts(limit),
    queryFn: async () => {
      const response = await api.get<APIResponse<ScreeningResponse>>(
        `/screening/breakouts?limit=${limit}`
      );
      return response.data;
    },
    enabled: options?.enabled,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get all screening strategies results
 */
export function useAllScreeningStrategies(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: screeningKeys.allStrategies(),
    queryFn: async () => {
      const response = await api.get<
        APIResponse<{
          maverick: ScreeningResponse;
          maverick_bear: ScreeningResponse;
          breakouts: ScreeningResponse;
        }>
      >('/screening/all');
      return response.data;
    },
    enabled: options?.enabled,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get filtered screening results
 */
export function useFilteredScreening(
  filters: ScreeningFilters,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: screeningKeys.filtered(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.min_price) params.set('min_price', filters.min_price.toString());
      if (filters.max_price) params.set('max_price', filters.max_price.toString());
      if (filters.min_volume) params.set('min_volume', filters.min_volume.toString());
      if (filters.min_market_cap)
        params.set('min_market_cap', filters.min_market_cap.toString());
      if (filters.sectors?.length)
        params.set('sectors', filters.sectors.join(','));
      if (filters.min_momentum_score)
        params.set('min_momentum_score', filters.min_momentum_score.toString());

      const response = await api.get<APIResponse<ScreeningResponse>>(
        `/screening/filter?${params.toString()}`
      );
      return response.data;
    },
    enabled: options?.enabled !== false,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook for screening with custom strategy selection
 */
export function useScreeningByStrategy(
  strategy: 'maverick' | 'maverick-bear' | 'breakouts',
  limit: number = 20,
  options?: { enabled?: boolean }
) {
  const strategyMap = {
    maverick: useMaverickStocks,
    'maverick-bear': useMaverickBearStocks,
    breakouts: useBreakoutStocks,
  };

  return strategyMap[strategy](limit, options);
}

/**
 * Get available sectors for filtering
 */
export function useAvailableSectors(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: [...screeningKeys.all, 'sectors'],
    queryFn: async () => {
      const response = await api.get<APIResponse<string[]>>('/screening/sectors');
      return response.data;
    },
    enabled: options?.enabled,
    staleTime: 60 * 60 * 1000, // 1 hour - sectors don't change often
  });
}

