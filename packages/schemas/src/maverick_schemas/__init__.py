"""
Maverick Schemas Package.

Shared Pydantic models for MaverickMCP. This is a dependency-light leaf package
that other packages import from for consistent data models.

Features:
- Consistent API response envelopes
- Stock and market data models
- Technical analysis models
- Portfolio and position models
- Authentication models
"""

# Base models and types
from maverick_schemas.base import (
    MaverickBaseModel,
    TimestampMixin,
    Market,
    TimeInterval,
    Tier,
    AuthMethod,
    SentimentScore,
    TrendDirection,
    OrderSide,
    PositionStatus,
)

# Response envelopes
from maverick_schemas.responses import (
    APIResponse,
    PaginatedResponse,
    ErrorResponse,
    ResponseMeta,
    PaginationMeta,
    ErrorDetail,
)

# Stock models
from maverick_schemas.stock import (
    StockQuote,
    StockInfo,
    OHLCV,
    StockHistory,
    BatchQuoteRequest,
    BatchQuoteResponse,
)

# Technical analysis models
from maverick_schemas.technical import (
    RSIAnalysis,
    MACDAnalysis,
    BollingerBands,
    SupportResistance,
    MovingAverages,
    TechnicalSummary,
)

# Portfolio models
from maverick_schemas.portfolio import (
    Position,
    PositionCreate,
    PositionUpdate,
    Portfolio,
    PortfolioSummary,
    PortfolioPerformance,
    PortfolioAllocation,
    CorrelationMatrix,
)

# Screening models
from maverick_schemas.screening import (
    ScreeningStrategy,
    ScreeningResult,
    ScreeningFilter,
    MaverickStock,
    ScreeningResponse,
    MaverickScreeningResponse,
)

# Backtest models
from maverick_schemas.backtest import (
    StrategyType,
    JobStatus,
    StrategyConfig,
    BacktestRequest,
    BacktestResult,
    BacktestTrade,
    BacktestMetrics,
    BacktestJob,
    OptimizationResult,
    WalkForwardResult,
)

# Research models
from maverick_schemas.research import (
    ResearchDepth,
    SentimentAnalysis,
    NewsArticle,
    ResearchQuery,
    ResearchInsight,
    ResearchResult,
    EarningsTranscript,
    EarningsSummary,
)

# Auth models
from maverick_schemas.auth import (
    AuthenticatedUser,
    TokenResponse,
    LoginRequest,
    RefreshTokenRequest,
    APIKeyInfo,
    APIKeyCreate,
    APIKeyResponse,
    TokenBudget,
)

__all__ = [
    # Base
    "MaverickBaseModel",
    "TimestampMixin",
    "Market",
    "TimeInterval",
    "Tier",
    "AuthMethod",
    "SentimentScore",
    "TrendDirection",
    "OrderSide",
    "PositionStatus",
    # Responses
    "APIResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "ResponseMeta",
    "PaginationMeta",
    "ErrorDetail",
    # Stock
    "StockQuote",
    "StockInfo",
    "OHLCV",
    "StockHistory",
    "BatchQuoteRequest",
    "BatchQuoteResponse",
    # Technical
    "RSIAnalysis",
    "MACDAnalysis",
    "BollingerBands",
    "SupportResistance",
    "MovingAverages",
    "TechnicalSummary",
    # Portfolio
    "Position",
    "PositionCreate",
    "PositionUpdate",
    "Portfolio",
    "PortfolioSummary",
    "PortfolioPerformance",
    "PortfolioAllocation",
    "CorrelationMatrix",
    # Screening
    "ScreeningStrategy",
    "ScreeningResult",
    "ScreeningFilter",
    "MaverickStock",
    "ScreeningResponse",
    "MaverickScreeningResponse",
    # Backtest
    "StrategyType",
    "JobStatus",
    "StrategyConfig",
    "BacktestRequest",
    "BacktestResult",
    "BacktestTrade",
    "BacktestMetrics",
    "BacktestJob",
    "OptimizationResult",
    "WalkForwardResult",
    # Research
    "ResearchDepth",
    "SentimentAnalysis",
    "NewsArticle",
    "ResearchQuery",
    "ResearchInsight",
    "ResearchResult",
    "EarningsTranscript",
    "EarningsSummary",
    # Auth
    "AuthenticatedUser",
    "TokenResponse",
    "LoginRequest",
    "RefreshTokenRequest",
    "APIKeyInfo",
    "APIKeyCreate",
    "APIKeyResponse",
    "TokenBudget",
]

