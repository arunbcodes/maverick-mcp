/**
 * API Types - Matching backend Pydantic schemas
 * 
 * These types mirror the schemas in packages/schemas/
 */

// --- Base Types ---

export type Tier = 'free' | 'pro' | 'premium' | 'enterprise';

export type AuthMethod = 'cookie' | 'jwt' | 'api_key' | 'unknown';

// --- API Response Wrapper ---

export interface APIResponse<T> {
  success: boolean;
  data: T;
  meta: ResponseMeta;
}

export interface ResponseMeta {
  request_id: string;
  timestamp: string;
  version?: string;
  pagination?: PaginationMeta;
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface APIError {
  detail: string;
  error_code?: string;
}

// --- Auth Types ---

export interface User {
  user_id: string;
  email: string;
  tier: Tier;
  email_verified?: boolean;
  created_at?: string;
  last_login_at?: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  tier: Tier;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface APIKeyInfo {
  key_id: string;
  key_prefix: string;
  name: string;
  tier: Tier;
  rate_limit: number | null;
  last_used_at: string | null;
  created_at: string;
  expires_at: string | null;
}

export interface APIKeyCreateRequest {
  name: string;
  expires_in_days?: number;
}

export interface APIKeyCreateResponse {
  key: string;
  key_id: string;
  key_prefix: string;
  name: string;
  tier: Tier;
  created_at: string;
  expires_at: string | null;
}

// --- Stock Types ---

export interface StockQuote {
  ticker: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap?: number;
  name?: string;
  exchange?: string;
  currency?: string;
  timestamp: string;
}

export interface StockInfo {
  ticker: string;
  name: string;
  sector?: string;
  industry?: string;
  market_cap?: number;
  pe_ratio?: number;
  dividend_yield?: number;
  fifty_two_week_high?: number;
  fifty_two_week_low?: number;
  avg_volume?: number;
  description?: string;
}

export interface OHLCV {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adj_close?: number;
}

export interface HistoricalData {
  ticker: string;
  data: OHLCV[];
  start_date: string;
  end_date: string;
}

// --- Portfolio Types ---

export interface Portfolio {
  portfolio_id: string;
  name: string;
  description?: string;
  positions: Position[];
  total_value: number;
  total_cost: number;
  total_gain: number;
  total_gain_percent: number;
  day_change: number;
  day_change_percent: number;
  created_at: string;
  updated_at: string;
}

export interface Position {
  position_id: string;
  ticker: string;
  shares: number;
  avg_cost: number;
  current_price?: number;
  market_value?: number;
  cost_basis: number;
  gain: number;
  gain_percent: number;
  day_change?: number;
  day_change_percent?: number;
  weight?: number;
  name?: string;
  created_at: string;
  updated_at: string;
}

export interface AddPositionRequest {
  ticker: string;
  shares: number;
  purchase_price: number;
  purchase_date?: string;
  notes?: string;
}

export interface UpdatePositionRequest {
  shares?: number;
  avg_cost?: number;
  notes?: string;
}

export interface PortfolioSummary {
  total_value: number;
  total_cost: number;
  total_gain: number;
  total_gain_percent: number;
  day_change: number;
  day_change_percent: number;
  positions_count: number;
  top_performers: Position[];
  worst_performers: Position[];
}

// --- Portfolio Performance Types ---

export type PerformancePeriod = '7d' | '30d' | '90d' | '1y' | 'ytd' | 'all';

export interface PerformanceDataPoint {
  date: string;
  portfolio_value: number;
  daily_return: number | null;
  cumulative_return: number | null;
  benchmark_value: number | null;
  benchmark_return: number | null;
}

export interface PortfolioPerformanceChart {
  period: string;
  start_date: string;
  end_date: string;
  total_return: number;
  total_return_value: number;
  benchmark_return: number | null;
  alpha: number | null;
  volatility: number | null;
  sharpe_ratio: number | null;
  max_drawdown: number | null;
  max_drawdown_date: string | null;
  data: PerformanceDataPoint[];
}

// --- Technical Analysis Types ---

export interface TechnicalIndicators {
  ticker: string;
  rsi?: RSIData;
  macd?: MACDData;
  bollinger?: BollingerData;
  moving_averages?: MovingAveragesData;
  support_resistance?: SupportResistance;
}

export interface RSIData {
  value: number;
  signal: 'oversold' | 'neutral' | 'overbought';
  period: number;
}

export interface MACDData {
  macd_line: number;
  signal_line: number;
  histogram: number;
  signal: 'bullish' | 'neutral' | 'bearish';
}

export interface BollingerData {
  upper: number;
  middle: number;
  lower: number;
  bandwidth: number;
  percent_b: number;
}

export interface MovingAveragesData {
  sma_20: number;
  sma_50: number;
  sma_200: number;
  ema_12: number;
  ema_26: number;
  trend: 'bullish' | 'neutral' | 'bearish';
}

export interface SupportResistance {
  support_levels: number[];
  resistance_levels: number[];
  current_price: number;
}

// --- Screening Types ---

export interface ScreeningResult {
  ticker: string;
  name: string;
  price: number;
  change_percent: number;
  volume: number;
  market_cap?: number;
  sector?: string;
  score: number;
  signals: string[];
  momentum_rating?: string;
  pattern?: string;
}

export interface ScreeningResponse {
  strategy: string;
  results: ScreeningResult[];
  total_count: number;
  timestamp: string;
}

export interface ScreeningFilters {
  min_price?: number;
  max_price?: number;
  min_volume?: number;
  min_market_cap?: number;
  sectors?: string[];
  min_momentum_score?: number;
}

// --- SSE Types ---

export interface PriceUpdate {
  ticker: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
}

export interface SSEMessage<T = unknown> {
  event: string;
  data: T;
}

// --- Chart Types (for Recharts) ---

export interface ChartDataPoint {
  date: string;
  value: number;
  [key: string]: string | number;
}

export interface PortfolioChartData {
  history: ChartDataPoint[];
  benchmark?: ChartDataPoint[];
}

// --- AI Screening Types ---

export type InvestorPersona = 'conservative' | 'moderate' | 'aggressive';

export type ConfidenceLevel = 'high' | 'medium' | 'low';

export interface StockExplanation {
  ticker: string;
  strategy: string;
  summary: string;
  technical_setup: string;
  key_signals: string[];
  support_resistance: string | null;
  risk_factors: string[];
  confidence: ConfidenceLevel;
  persona: InvestorPersona | null;
  generated_at: string;
  cached: boolean;
  model_used: string | null;
}

export interface BatchExplanationRequest {
  tickers: string[];
  strategy?: string;
  persona?: InvestorPersona;
}

export interface AIUsageStats {
  user_id: string;
  date: string;
  explanations_used: number;
  explanations_limit: number;
  remaining: number;
}

// --- Investment Thesis Types ---

export type ThesisRating = 'strong_buy' | 'buy' | 'hold' | 'sell' | 'strong_sell';

export type RiskLevel = 'low' | 'moderate' | 'high' | 'very_high';

export interface ThesisSection {
  title: string;
  content: string;
  bullet_points: string[];
}

export interface InvestmentThesis {
  ticker: string;
  company_name: string | null;
  generated_at: string;
  persona: InvestorPersona | null;
  
  // Summary
  summary: string;
  rating: ThesisRating;
  risk_level: RiskLevel;
  confidence: number;
  
  // Sections
  technical_setup: ThesisSection;
  fundamental_story: ThesisSection;
  catalysts: ThesisSection;
  risks: ThesisSection;
  
  // Price targets
  current_price: string | null;
  price_target: string | null;
  stop_loss: string | null;
  upside_percent: number | null;
  
  // Additional
  peer_comparison: string[];
  data_sources: string[];
  
  // Meta
  cached: boolean;
  model_used: string | null;
}

