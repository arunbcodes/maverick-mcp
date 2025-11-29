"""
Maverick Data Providers.

Data provider implementations for fetching stock, market, and macro data.

Providers:
    - BaseStockProvider: Abstract base class for stock data providers
    - YFinanceProvider: Yahoo Finance data provider (async)
    - StockDataProvider: Full-featured provider with caching (sync)
    - YFinancePool: Thread-safe connection pooling for yfinance
    - MarketDataProvider: Market indices, gainers, losers, sectors
    - MacroDataProvider: Macroeconomic data from FRED API
"""

from maverick_data.providers.base import BaseStockProvider
from maverick_data.providers.macro_data import MacroDataProvider
from maverick_data.providers.market_data import (
    MARKET_INDICES,
    SECTOR_ETFS,
    MarketDataProvider,
)
from maverick_data.providers.stock_data import (
    EnhancedStockDataProvider,
    StockDataProvider,
)
from maverick_data.providers.yfinance_pool import (
    YFinancePool,
    cleanup_yfinance_pool,
    get_yfinance_pool,
)
from maverick_data.providers.yfinance_provider import YFinanceProvider

__all__ = [
    # Stock providers
    "BaseStockProvider",
    "YFinanceProvider",
    "StockDataProvider",
    "EnhancedStockDataProvider",
    # Connection pooling
    "YFinancePool",
    "get_yfinance_pool",
    "cleanup_yfinance_pool",
    # Market data
    "MarketDataProvider",
    "MARKET_INDICES",
    "SECTOR_ETFS",
    # Macro data
    "MacroDataProvider",
]
