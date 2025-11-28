"""
Maverick Data Package.

This package provides data access, caching, and persistence for Maverick stock analysis.
It includes database models, repositories, cache providers, data providers, and services.
"""

# Session management
from maverick_data.session import (
    close_async_db_connections,
    ensure_database_schema,
    get_async_db,
    get_db,
    get_session,
    init_db,
)

# Cache providers and utilities
from maverick_data.cache import (
    CACHE_VERSION,
    DEFAULT_TTL_SECONDS,
    CacheManager,
    MemoryCache,
    RedisCache,
    deserialize_data,
    ensure_timezone_naive,
    generate_cache_key,
    get_cache_manager,
    normalize_timezone,
    reset_cache_manager,
    serialize_data,
)

# Models
from maverick_data.models import (
    # Base
    Base,
    TimestampMixin,
    # Core models
    Stock,
    PriceCache,
    ExchangeRate,
    NewsArticle,
    TechnicalCache,
    # Screening models
    MaverickStocks,
    MaverickBearStocks,
    SupplyDemandBreakoutStocks,
    # Backtest models
    BacktestResult,
    BacktestTrade,
    OptimizationResult,
    WalkForwardTest,
    BacktestPortfolio,
    # Portfolio models
    UserPortfolio,
    PortfolioPosition,
)

# Repositories
from maverick_data.repositories import (
    StockRepository,
    PortfolioRepository,
    ScreeningRepository,
)

# Providers
from maverick_data.providers import (
    BaseStockProvider,
    YFinanceProvider,
)

# Services
from maverick_data.services import (
    MarketCalendarService,
)

__all__ = [
    # Session management
    "get_db",
    "get_async_db",
    "get_session",
    "init_db",
    "ensure_database_schema",
    "close_async_db_connections",
    # Cache providers
    "RedisCache",
    "MemoryCache",
    "CacheManager",
    "get_cache_manager",
    "reset_cache_manager",
    "generate_cache_key",
    "CACHE_VERSION",
    "DEFAULT_TTL_SECONDS",
    # Serialization
    "serialize_data",
    "deserialize_data",
    "normalize_timezone",
    "ensure_timezone_naive",
    # Base models
    "Base",
    "TimestampMixin",
    # Core models
    "Stock",
    "PriceCache",
    "ExchangeRate",
    "NewsArticle",
    "TechnicalCache",
    # Screening models
    "MaverickStocks",
    "MaverickBearStocks",
    "SupplyDemandBreakoutStocks",
    # Backtest models
    "BacktestResult",
    "BacktestTrade",
    "OptimizationResult",
    "WalkForwardTest",
    "BacktestPortfolio",
    # Portfolio models
    "UserPortfolio",
    "PortfolioPosition",
    # Repositories
    "StockRepository",
    "PortfolioRepository",
    "ScreeningRepository",
    # Providers
    "BaseStockProvider",
    "YFinanceProvider",
    # Services
    "MarketCalendarService",
]
