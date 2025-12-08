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


// ============================================
// Diversification Types
// ============================================

export interface PositionConcentration {
  ticker: string;
  weight: number;
  is_overconcentrated: boolean;
}

export interface SectorConcentration {
  sector: string;
  weight: number;
  benchmark_weight: number;
  deviation: number;
  is_overweight: boolean;
  is_underweight: boolean;
}

export interface DiversificationBreakdown {
  position_score: number;
  sector_score: number;
  correlation_score: number;
  concentration_score: number;
  weights: {
    position: number;
    sector: number;
    correlation: number;
    concentration: number;
  };
}

export type DiversificationLevel = 'excellent' | 'good' | 'moderate' | 'poor' | 'very_poor';

export interface DiversificationScore {
  score: number;
  level: DiversificationLevel;
  hhi: number;
  hhi_normalized: number;
  effective_positions: number;
  position_count: number;
  largest_position: PositionConcentration | null;
  overconcentrated_count: number;
  sector_count: number;
  avg_correlation: number | null;
  breakdown: DiversificationBreakdown;
  recommendations: string[];
  calculated_at: string;
}

export interface SectorBenchmarks {
  sectors: string[];
  weights: Record<string, number>;
}

// ============================================
// Diversification Hooks
// ============================================

/**
 * Calculate diversification score
 */
export function useDiversificationScore(
  positions: { ticker: string; market_value: number; sector?: string }[],
  sectorMap?: Record<string, string>,
  avgCorrelation?: number,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: [...riskKeys.diversification(), positions.map(p => p.ticker).join(',')],
    queryFn: async () => {
      const response = await api.post<APIResponse<DiversificationScore>>(
        '/risk/diversification/score',
        {
          positions,
          sector_map: sectorMap,
          avg_correlation: avgCorrelation,
        }
      );
      return response.data;
    },
    enabled: options?.enabled !== false && positions.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Calculate diversification score (manual trigger)
 */
export function useCalculateDiversification() {
  return useMutation({
    mutationFn: async ({
      positions,
      sectorMap,
      avgCorrelation,
    }: {
      positions: { ticker: string; market_value: number; sector?: string }[];
      sectorMap?: Record<string, string>;
      avgCorrelation?: number;
    }) => {
      const response = await api.post<APIResponse<DiversificationScore>>(
        '/risk/diversification/score',
        {
          positions,
          sector_map: sectorMap,
          avg_correlation: avgCorrelation,
        }
      );
      return response.data;
    },
  });
}

/**
 * Get sector breakdown
 */
export function useSectorBreakdown(
  positions: { ticker: string; market_value: number; sector?: string }[],
  sectorMap?: Record<string, string>,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: [...riskKeys.sectors(), positions.map(p => p.ticker).join(',')],
    queryFn: async () => {
      const response = await api.post<APIResponse<SectorConcentration[]>>(
        '/risk/diversification/sectors',
        {
          positions,
          sector_map: sectorMap,
        }
      );
      return response.data;
    },
    enabled: options?.enabled !== false && positions.length > 0,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get S&P 500 sector benchmarks
 */
export function useSectorBenchmarks() {
  return useQuery({
    queryKey: [...riskKeys.sectors(), 'benchmarks'],
    queryFn: async () => {
      const response = await api.get<APIResponse<SectorBenchmarks>>(
        '/risk/diversification/sectors/benchmark'
      );
      return response.data;
    },
    staleTime: 24 * 60 * 60 * 1000, // 24 hours
  });
}

// ============================================
// Diversification Utilities
// ============================================

/**
 * Get color for diversification level
 */
export function getDiversificationLevelColor(level: DiversificationLevel): string {
  switch (level) {
    case 'excellent': return 'text-emerald-400';
    case 'good': return 'text-green-400';
    case 'moderate': return 'text-yellow-400';
    case 'poor': return 'text-orange-400';
    case 'very_poor': return 'text-red-400';
    default: return 'text-slate-400';
  }
}

/**
 * Get badge color for diversification level
 */
export function getDiversificationBadgeColor(level: DiversificationLevel): string {
  switch (level) {
    case 'excellent': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    case 'good': return 'bg-green-500/20 text-green-400 border-green-500/30';
    case 'moderate': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    case 'poor': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    case 'very_poor': return 'bg-red-500/20 text-red-400 border-red-500/30';
    default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  }
}

/**
 * Get score color based on numeric value
 */
export function getScoreColor(score: number): string {
  if (score >= 80) return 'text-emerald-400';
  if (score >= 60) return 'text-green-400';
  if (score >= 40) return 'text-yellow-400';
  if (score >= 20) return 'text-orange-400';
  return 'text-red-400';
}


// ============================================
// Sector Exposure Types
// ============================================

export interface SectorExposureItem {
  sector: string;
  weight: number;
  benchmark_weight: number;
  deviation: number;
  status: 'overweight' | 'underweight' | 'neutral' | 'missing';
  recommendation: string | null;
}

export interface SectorExposure {
  sectors: SectorExposureItem[];
  total_weight: number;
  covered_sectors: number;
  total_sectors: number;
  overweight_count: number;
  underweight_count: number;
}

export interface SectorComparison {
  sector: string;
  portfolio_weight: number;
  benchmark_weight: number;
}

export type RebalanceAction = 'buy' | 'sell' | 'hold';
export type RebalancePriority = 'high' | 'medium' | 'low';

export interface SectorRebalanceSuggestion {
  sector: string;
  current_weight: number;
  target_weight: number;
  action: RebalanceAction;
  change_needed: number;
  priority: RebalancePriority;
}

// ============================================
// Sector Exposure Hooks
// ============================================

/**
 * Get sector exposure analysis
 */
export function useSectorExposure(
  positions: { ticker: string; market_value: number; sector?: string }[],
  sectorMap?: Record<string, string>,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: [...riskKeys.sectors(), 'exposure', positions.map(p => p.ticker).join(',')],
    queryFn: async () => {
      const response = await api.post<APIResponse<SectorExposure>>(
        '/risk/sectors/exposure',
        {
          positions,
          sector_map: sectorMap,
        }
      );
      return response.data;
    },
    enabled: options?.enabled !== false && positions.length > 0,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get sector comparison for chart
 */
export function useSectorComparison(
  positions: { ticker: string; market_value: number; sector?: string }[],
  sectorMap?: Record<string, string>,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: [...riskKeys.sectors(), 'comparison', positions.map(p => p.ticker).join(',')],
    queryFn: async () => {
      const response = await api.post<APIResponse<SectorComparison[]>>(
        '/risk/sectors/comparison',
        {
          positions,
          sector_map: sectorMap,
        }
      );
      return response.data;
    },
    enabled: options?.enabled !== false && positions.length > 0,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get sector rebalance suggestions
 */
export function useSectorRebalance(
  positions: { ticker: string; market_value: number; sector?: string }[],
  targetProfile: 'balanced' | 'aggressive' | 'defensive' = 'balanced',
  sectorMap?: Record<string, string>,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: [...riskKeys.sectors(), 'rebalance', targetProfile, positions.map(p => p.ticker).join(',')],
    queryFn: async () => {
      const response = await api.post<APIResponse<SectorRebalanceSuggestion[]>>(
        `/risk/sectors/rebalance?target_profile=${targetProfile}`,
        {
          positions,
          sector_map: sectorMap,
        }
      );
      return response.data;
    },
    enabled: options?.enabled !== false && positions.length > 0,
    staleTime: 5 * 60 * 1000,
  });
}

// ============================================
// Sector Utilities
// ============================================

/**
 * Get color for sector status
 */
export function getSectorStatusColor(status: SectorExposureItem['status']): string {
  switch (status) {
    case 'overweight': return 'text-amber-400';
    case 'underweight': return 'text-blue-400';
    case 'missing': return 'text-red-400';
    case 'neutral': return 'text-emerald-400';
    default: return 'text-slate-400';
  }
}

/**
 * Get badge color for sector status
 */
export function getSectorStatusBadge(status: SectorExposureItem['status']): string {
  switch (status) {
    case 'overweight': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
    case 'underweight': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    case 'missing': return 'bg-red-500/20 text-red-400 border-red-500/30';
    case 'neutral': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  }
}

/**
 * Get color for rebalance action
 */
export function getRebalanceActionColor(action: RebalanceAction): string {
  switch (action) {
    case 'buy': return 'text-emerald-400';
    case 'sell': return 'text-red-400';
    case 'hold': return 'text-slate-400';
    default: return 'text-slate-400';
  }
}

/**
 * Sector color palette for charts
 */
export const SECTOR_COLORS: Record<string, string> = {
  'Technology': '#8b5cf6',
  'Healthcare': '#22c55e',
  'Financials': '#3b82f6',
  'Consumer Discretionary': '#f97316',
  'Communication Services': '#ec4899',
  'Industrials': '#6366f1',
  'Consumer Staples': '#84cc16',
  'Energy': '#eab308',
  'Utilities': '#14b8a6',
  'Real Estate': '#a855f7',
  'Materials': '#f43f5e',
};


// ============================================
// Risk Metrics Types
// ============================================

export interface VaRResult {
  var_95: number;
  var_99: number;
  cvar_95: number;
  cvar_99: number;
  method: string;
  period_days: number;
  portfolio_value: number;
  var_95_amount: number;
  var_99_amount: number;
  cvar_95_amount: number;
  cvar_99_amount: number;
}

export interface BetaResult {
  beta: number;
  alpha: number;
  r_squared: number;
  correlation: number;
  interpretation: string;
}

export interface VolatilityResult {
  daily_volatility: number;
  annualized_volatility: number;
  downside_volatility: number;
  upside_volatility: number;
  volatility_skew: number;
  max_daily_loss: number;
  max_daily_gain: number;
}

export interface StressTestResult {
  scenario: string;
  scenario_name: string;
  description: string;
  market_return: number;
  estimated_portfolio_loss: number;
  estimated_loss_amount: number;
  recovery_estimate_days: number | null;
}

export type RiskLevel = 'low' | 'moderate' | 'high' | 'very_high';

export interface RiskMetricsSummary {
  var: VaRResult;
  beta: BetaResult;
  volatility: VolatilityResult;
  stress_tests: StressTestResult[];
  risk_score: number;
  risk_level: RiskLevel;
  calculated_at: string;
}

export interface StressScenarioInfo {
  id: string;
  name: string;
  description: string;
  market_return: number;
  duration_days: number;
}

// ============================================
// Risk Metrics Hooks
// ============================================

/**
 * Calculate Value at Risk
 */
export function useCalculateVaR() {
  return useMutation({
    mutationFn: async ({
      portfolioReturns,
      portfolioValue,
      method = 'historical',
    }: {
      portfolioReturns: number[];
      portfolioValue: number;
      method?: string;
    }) => {
      const response = await api.post<APIResponse<VaRResult>>(
        '/risk/metrics/var',
        {
          portfolio_returns: portfolioReturns,
          portfolio_value: portfolioValue,
          var_method: method,
        }
      );
      return response.data;
    },
  });
}

/**
 * Calculate Beta
 */
export function useCalculateBeta() {
  return useMutation({
    mutationFn: async ({
      portfolioReturns,
      benchmarkReturns,
      portfolioValue,
    }: {
      portfolioReturns: number[];
      benchmarkReturns?: number[];
      portfolioValue: number;
    }) => {
      const response = await api.post<APIResponse<BetaResult>>(
        '/risk/metrics/beta',
        {
          portfolio_returns: portfolioReturns,
          benchmark_returns: benchmarkReturns,
          portfolio_value: portfolioValue,
        }
      );
      return response.data;
    },
  });
}

/**
 * Calculate Volatility
 */
export function useCalculateVolatility() {
  return useMutation({
    mutationFn: async ({
      portfolioReturns,
      portfolioValue,
    }: {
      portfolioReturns: number[];
      portfolioValue: number;
    }) => {
      const response = await api.post<APIResponse<VolatilityResult>>(
        '/risk/metrics/volatility',
        {
          portfolio_returns: portfolioReturns,
          portfolio_value: portfolioValue,
        }
      );
      return response.data;
    },
  });
}

/**
 * Run stress tests
 */
export function useRunStressTests() {
  return useMutation({
    mutationFn: async ({
      portfolioBeta,
      portfolioValue,
      scenarios,
    }: {
      portfolioBeta: number;
      portfolioValue: number;
      scenarios?: string[];
    }) => {
      const response = await api.post<APIResponse<StressTestResult[]>>(
        '/risk/metrics/stress-test',
        {
          portfolio_beta: portfolioBeta,
          portfolio_value: portfolioValue,
          scenarios,
        }
      );
      return response.data;
    },
  });
}

/**
 * Run custom stress test
 */
export function useRunCustomStressTest() {
  return useMutation({
    mutationFn: async ({
      portfolioBeta,
      portfolioValue,
      marketDropPercent,
      scenarioName,
    }: {
      portfolioBeta: number;
      portfolioValue: number;
      marketDropPercent: number;
      scenarioName?: string;
    }) => {
      const response = await api.post<APIResponse<StressTestResult>>(
        '/risk/metrics/stress-test/custom',
        {
          portfolio_beta: portfolioBeta,
          portfolio_value: portfolioValue,
          market_drop_percent: marketDropPercent,
          scenario_name: scenarioName,
        }
      );
      return response.data;
    },
  });
}

/**
 * Calculate full risk metrics
 */
export function useCalculateFullRiskMetrics() {
  return useMutation({
    mutationFn: async ({
      portfolioReturns,
      benchmarkReturns,
      portfolioValue,
      varMethod = 'historical',
    }: {
      portfolioReturns: number[];
      benchmarkReturns?: number[];
      portfolioValue: number;
      varMethod?: string;
    }) => {
      const response = await api.post<APIResponse<RiskMetricsSummary>>(
        '/risk/metrics/full',
        {
          portfolio_returns: portfolioReturns,
          benchmark_returns: benchmarkReturns,
          portfolio_value: portfolioValue,
          var_method: varMethod,
        }
      );
      return response.data;
    },
  });
}

/**
 * Get available stress scenarios
 */
export function useStressScenarios() {
  return useQuery({
    queryKey: [...riskKeys.metrics(), 'scenarios'],
    queryFn: async () => {
      const response = await api.get<APIResponse<StressScenarioInfo[]>>(
        '/risk/metrics/scenarios'
      );
      return response.data;
    },
    staleTime: 24 * 60 * 60 * 1000, // 24 hours
  });
}

// ============================================
// Risk Metrics Utilities
// ============================================

/**
 * Get color for risk level
 */
export function getRiskLevelColor(level: RiskLevel): string {
  switch (level) {
    case 'low': return 'text-emerald-400';
    case 'moderate': return 'text-yellow-400';
    case 'high': return 'text-orange-400';
    case 'very_high': return 'text-red-400';
    default: return 'text-slate-400';
  }
}

/**
 * Get badge color for risk level
 */
export function getRiskLevelBadge(level: RiskLevel): string {
  switch (level) {
    case 'low': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    case 'moderate': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    case 'high': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    case 'very_high': return 'bg-red-500/20 text-red-400 border-red-500/30';
    default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  }
}

/**
 * Format percentage for display
 */
export function formatPercent(value: number, decimals: number = 2): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format currency amount
 */
export function formatAmount(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Get beta interpretation color
 */
export function getBetaColor(beta: number): string {
  if (beta >= 1.5) return 'text-red-400';
  if (beta >= 1.2) return 'text-orange-400';
  if (beta >= 0.8) return 'text-yellow-400';
  if (beta >= 0.5) return 'text-emerald-400';
  return 'text-blue-400';
}

