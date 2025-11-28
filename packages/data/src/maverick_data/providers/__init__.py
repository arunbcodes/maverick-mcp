"""
Maverick Data Providers.

Data provider implementations for fetching stock, market, and macro data.

Providers:
    - BaseStockProvider: Abstract base class for stock data providers
    - YFinanceProvider: Yahoo Finance data provider
    - MarketDataProvider: Market indices, gainers, losers, sectors
    - MacroDataProvider: Macroeconomic data from FRED API
"""

from maverick_data.providers.base import BaseStockProvider
from maverick_data.providers.yfinance_provider import YFinanceProvider
from maverick_data.providers.market_data import (
    MarketDataProvider,
    MARKET_INDICES,
    SECTOR_ETFS,
)
from maverick_data.providers.macro_data import MacroDataProvider

__all__ = [
    # Stock providers
    "BaseStockProvider",
    "YFinanceProvider",
    # Market data
    "MarketDataProvider",
    "MARKET_INDICES",
    "SECTOR_ETFS",
    # Macro data
    "MacroDataProvider",
]
