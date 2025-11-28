"""
Maverick Core - Pure domain logic and interfaces for stock analysis.

This package contains:
- Domain entities and value objects (DDD patterns)
- Interface definitions (protocols) for all services
- Pure technical analysis functions
- Domain exceptions

Zero external dependencies on frameworks like SQLAlchemy, Redis, or LangChain.
"""

# Domain entities
from maverick_core.domain import Portfolio, Position

# Technical analysis functions
from maverick_core.technical import (
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_momentum,
    calculate_obv,
    calculate_rate_of_change,
    calculate_rsi,
    calculate_sma,
    calculate_stochastic,
    calculate_support_resistance,
    calculate_trend_strength,
    calculate_williams_r,
)

# Exceptions
from maverick_core.exceptions import (
    AgentError,
    BacktestError,
    CacheError,
    CircuitBreakerError,
    ConfigurationError,
    DatabaseError,
    DataProviderError,
    DataValidationError,
    LLMError,
    MaverickError,
    PersistenceError,
    RateLimitError,
    StockDataError,
    StrategyError,
    SymbolNotFoundError,
    TechnicalAnalysisError,
    ValidationError,
)

# Interfaces
from maverick_core.interfaces import (
    IBacktestEngine,
    ICacheKeyGenerator,
    ICacheProvider,
    IConfigProvider,
    ILLMProvider,
    IMarketCalendar,
    IPortfolioRepository,
    IRepository,
    IResearchAgent,
    IScreeningRepository,
    IStockDataFetcher,
    IStockRepository,
    IStockScreener,
    IStrategy,
    ITechnicalAnalyzer,
    TaskType,
)

__version__ = "0.1.0"

__all__ = [
    # Domain entities
    "Portfolio",
    "Position",
    # Technical Analysis Functions
    "calculate_sma",
    "calculate_ema",
    "calculate_rsi",
    "calculate_stochastic",
    "calculate_williams_r",
    "calculate_macd",
    "calculate_trend_strength",
    "calculate_bollinger_bands",
    "calculate_atr",
    "calculate_momentum",
    "calculate_rate_of_change",
    "calculate_obv",
    "calculate_support_resistance",
    # Interfaces - Stock Data
    "IStockDataFetcher",
    "IStockScreener",
    # Interfaces - Cache
    "ICacheProvider",
    "ICacheKeyGenerator",
    # Interfaces - Persistence
    "IRepository",
    "IStockRepository",
    "IPortfolioRepository",
    "IScreeningRepository",
    # Interfaces - Technical Analysis
    "ITechnicalAnalyzer",
    # Interfaces - Market Calendar
    "IMarketCalendar",
    # Interfaces - LLM
    "ILLMProvider",
    "IResearchAgent",
    "TaskType",
    # Interfaces - Backtest
    "IBacktestEngine",
    "IStrategy",
    # Interfaces - Config
    "IConfigProvider",
    # Exceptions
    "MaverickError",
    "ValidationError",
    "StockDataError",
    "SymbolNotFoundError",
    "DataProviderError",
    "DataValidationError",
    "TechnicalAnalysisError",
    "CacheError",
    "PersistenceError",
    "DatabaseError",
    "StrategyError",
    "LLMError",
    "AgentError",
    "BacktestError",
    "ConfigurationError",
    "RateLimitError",
    "CircuitBreakerError",
    # Version
    "__version__",
]
