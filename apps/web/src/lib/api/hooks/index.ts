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
  useInvestmentThesis,
  useLazyInvestmentThesis,
} from './use-ai-screening';

// Alert hooks
export {
  alertKeys,
  useAlertRules,
  useAlerts,
  useUnreadAlertCount,
  useAlertPresets,
  useCreateAlertRule,
  useUpdateAlertRule,
  useDeleteAlertRule,
  useToggleAlertRule,
  useEnablePreset,
  useMarkAlertRead,
  useMarkAllAlertsRead,
  useDismissAlert,
  useAlertStream,
  type Alert,
  type AlertRule,
  type AlertType,
  type AlertPriority,
  type AlertStatus,
  type PresetRule,
} from './use-alerts';

// Watchlist hooks
export {
  watchlistKeys,
  useWatchlists,
  useWatchlist,
  useCreateWatchlist,
  useUpdateWatchlist,
  useDeleteWatchlist,
  useAddWatchlistItem,
  useAddWatchlistItemsBatch,
  useUpdateWatchlistItem,
  useRemoveWatchlistItem,
  useReorderWatchlistItems,
  useQuickAddToWatchlist,
  useIsWatching,
  type Watchlist,
  type WatchlistItem,
  type WatchlistSummary,
  type IsWatchingResponse,
} from './use-watchlists';

// Custom Screener hooks
export {
  customScreenerKeys,
  useCustomScreeners,
  useCustomScreener,
  useCreateCustomScreener,
  useUpdateCustomScreener,
  useDeleteCustomScreener,
  useDuplicateCustomScreener,
  useRunCustomScreener,
  useScreenerResults,
  useScreenerPresets,
  useCreateFromPreset,
  useFilterFields,
  FILTER_OPERATORS,
  type CustomScreener,
  type ScreenerSummary,
  type ScreenerResult,
  type PresetScreener,
  type FilterCondition,
  type FilterFieldMeta,
} from './use-custom-screeners';

// Thesis Tracking hooks
export {
  thesisKeys,
  useTheses,
  useThesis,
  useThesisForTicker,
  useCreateThesis,
  useUpdateThesis,
  useCloseThesis,
  useDeleteThesis,
  useAddMilestone,
  useUpdateMilestone,
  useAddDecision,
  useUpdateDecisionOutcome,
  useWinLossAnalysis,
  type InvestmentThesis,
  type ThesisSummary,
  type Milestone,
  type Decision,
  type ThesisStatus,
  type MilestoneStatus,
  type MilestoneType,
  type DecisionType,
  type WinLossAnalysis,
} from './use-thesis-tracking';

