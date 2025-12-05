/**
 * API Hooks - Re-export all hooks from a single entry point
 */

// Stock hooks
export {
  stockKeys,
  useStockQuote,
  useStockQuotes,
  useStockInfo,
  useStockHistory,
  useTechnicalIndicators,
  useStockSearch,
  usePrefetchStockQuote,
} from './use-stocks';

// Portfolio hooks
export {
  portfolioKeys,
  usePortfolioSummary,
  usePortfolio,
  usePositions,
  usePosition,
  useAddPosition,
  useUpdatePosition,
  useRemovePosition,
  useBatchUpdatePositions,
  useOptimisticPositionUpdate,
  usePortfolioPerformance,
} from './use-portfolio';

// Screening hooks
export {
  screeningKeys,
  useMaverickStocks,
  useMaverickBearStocks,
  useBreakoutStocks,
  useAllScreeningStrategies,
  useFilteredScreening,
  useScreeningByStrategy,
  useAvailableSectors,
  useStockRiskScore,
} from './use-screening';

// SSE hooks
export {
  usePriceStream,
  usePortfolioStream,
  useSSEManager,
} from './use-sse';

// API Key hooks
export {
  apiKeyKeys,
  useAPIKeys,
  useCreateAPIKey,
  useRevokeAPIKey,
} from './use-api-keys';

// AI Screening hooks
export {
  aiScreeningKeys,
  useStockExplanation,
  useLazyStockExplanation,
  useBatchExplanations,
  useAIUsageStats,
  useStockExplanationWithStatus,
} from './use-ai-screening';

