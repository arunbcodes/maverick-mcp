/**
 * React Query hooks for Risk Analytics API endpoints
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../client';
import type { APIResponse } from '../types';

// ============================================
// Types
// ============================================

export interface CorrelationMatrix {
  tickers: string[];
  matrix: number[][];
  period_days: number;
  data_points: number;
  calculated_at: string;
  stats: CorrelationStats;
}

export interface CorrelationStats {
  avg_correlation: number;
  max_correlation: number;
  min_correlation: number;
  high_correlation_count: number;
  low_correlation_count: number;
}

export interface PairCorrelation {
  ticker1: string;
  ticker2: string;
  correlation: number;
  period_days: number;
  data_points: number;
  calculated_at: string;
  interpretation: string;
}

export interface HighCorrelationPair {
  ticker1: string;
  ticker2: string;
  correlation: number;
}

export interface RollingCorrelationPoint {
  date: string;
  correlation: number;
}

export interface MultiPeriodCorrelation {
  ticker1: string;
  ticker2: string;
  periods: Record<string, {
    correlation: number;
    data_points: number;
    interpretation: string;
  }>;
}

// ============================================
// Query Keys
// ============================================

export const riskKeys = {
  all: ['risk'] as const,
  correlation: () => [...riskKeys.all, 'correlation'] as const,
  matrix: (tickers: string[], period: number) => [...riskKeys.correlation(), 'matrix', tickers.join(','), period] as const,
  pair: (t1: string, t2: string, period: number) => [...riskKeys.correlation(), 'pair', t1, t2, period] as const,
  rolling: (t1: string, t2: string) => [...riskKeys.correlation(), 'rolling', t1, t2] as const,
  diversification: () => [...riskKeys.all, 'diversification'] as const,
  sectors: () => [...riskKeys.all, 'sectors'] as const,
  metrics: () => [...riskKeys.all, 'metrics'] as const,
};

// ============================================
// Correlation Hooks
// ============================================

/**
 * Calculate correlation matrix for multiple tickers
 */
export function useCorrelationMatrix(
  tickers: string[],
  periodDays: number = 90,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: riskKeys.matrix(tickers, periodDays),
    queryFn: async () => {
      const response = await api.post<APIResponse<CorrelationMatrix>>(
        '/risk/correlation/matrix',
        { tickers, period_days: periodDays }
      );
      return response.data;
    },
    enabled: options?.enabled !== false && tickers.length >= 2,
    staleTime: 60 * 60 * 1000, // 1 hour
  });
}

/**
 * Lazy version of correlation matrix (manual trigger)
 */
export function useCalculateCorrelationMatrix() {
  return useMutation({
    mutationFn: async ({ tickers, periodDays = 90 }: { tickers: string[]; periodDays?: number }) => {
      const response = await api.post<APIResponse<CorrelationMatrix>>(
        '/risk/correlation/matrix',
        { tickers, period_days: periodDays }
      );
      return response.data;
    },
  });
}

/**
 * Get correlation between two tickers
 */
export function usePairCorrelation(
  ticker1: string,
  ticker2: string,
  periodDays: number = 90,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: riskKeys.pair(ticker1, ticker2, periodDays),
    queryFn: async () => {
      const response = await api.get<APIResponse<PairCorrelation>>(
        `/risk/correlation/pair?ticker1=${ticker1}&ticker2=${ticker2}&period_days=${periodDays}`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && !!ticker1 && !!ticker2 && ticker1 !== ticker2,
    staleTime: 60 * 60 * 1000,
  });
}

/**
 * Get correlation across multiple periods
 */
export function useMultiPeriodCorrelation(
  ticker1: string,
  ticker2: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: [...riskKeys.pair(ticker1, ticker2, 0), 'multi'],
    queryFn: async () => {
      const response = await api.get<APIResponse<MultiPeriodCorrelation>>(
        `/risk/correlation/pair/multi-period?ticker1=${ticker1}&ticker2=${ticker2}`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && !!ticker1 && !!ticker2,
    staleTime: 60 * 60 * 1000,
  });
}

/**
 * Get rolling correlation time series
 */
export function useRollingCorrelation(
  ticker1: string,
  ticker2: string,
  window: number = 30,
  totalDays: number = 252,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: [...riskKeys.rolling(ticker1, ticker2), window, totalDays],
    queryFn: async () => {
      const response = await api.get<APIResponse<RollingCorrelationPoint[]>>(
        `/risk/correlation/rolling?ticker1=${ticker1}&ticker2=${ticker2}&window=${window}&total_days=${totalDays}`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && !!ticker1 && !!ticker2,
    staleTime: 60 * 60 * 1000,
  });
}

/**
 * Find high correlation pairs
 */
export function useHighCorrelationPairs(
  tickers: string[],
  threshold: number = 0.7,
  periodDays: number = 90,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: [...riskKeys.matrix(tickers, periodDays), 'high', threshold],
    queryFn: async () => {
      const response = await api.post<APIResponse<HighCorrelationPair[]>>(
        `/risk/correlation/high-pairs?threshold=${threshold}`,
        { tickers, period_days: periodDays }
      );
      return response.data;
    },
    enabled: options?.enabled !== false && tickers.length >= 2,
    staleTime: 60 * 60 * 1000,
  });
}

// ============================================
// Utility Functions
// ============================================

/**
 * Get color for correlation value (for heatmap)
 */
export function getCorrelationColor(correlation: number): string {
  const absCorr = Math.abs(correlation);
  
  if (absCorr >= 0.8) {
    return correlation > 0 ? '#ef4444' : '#3b82f6'; // Red for high positive, blue for high negative
  } else if (absCorr >= 0.6) {
    return correlation > 0 ? '#f97316' : '#6366f1'; // Orange / Indigo
  } else if (absCorr >= 0.4) {
    return correlation > 0 ? '#fbbf24' : '#8b5cf6'; // Amber / Violet
  } else if (absCorr >= 0.2) {
    return '#a3e635'; // Lime
  } else {
    return '#10b981'; // Emerald (low correlation = good)
  }
}

/**
 * Get background color with opacity for heatmap cells
 */
export function getCorrelationBgColor(correlation: number): string {
  const absCorr = Math.abs(correlation);
  
  if (absCorr >= 0.8) {
    return 'rgba(239, 68, 68, 0.3)'; // Red
  } else if (absCorr >= 0.6) {
    return 'rgba(249, 115, 22, 0.25)'; // Orange
  } else if (absCorr >= 0.4) {
    return 'rgba(251, 191, 36, 0.2)'; // Amber
  } else if (absCorr >= 0.2) {
    return 'rgba(163, 230, 53, 0.15)'; // Lime
  } else {
    return 'rgba(16, 185, 129, 0.1)'; // Emerald
  }
}

/**
 * Get text color for correlation interpretation
 */
export function getCorrelationTextColor(correlation: number): string {
  const absCorr = Math.abs(correlation);
  
  if (absCorr >= 0.7) return 'text-red-400';
  if (absCorr >= 0.5) return 'text-orange-400';
  if (absCorr >= 0.3) return 'text-yellow-400';
  return 'text-emerald-400';
}

