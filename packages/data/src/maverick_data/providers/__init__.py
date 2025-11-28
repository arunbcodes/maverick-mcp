"""
Maverick Data Providers.

Data provider implementations for fetching stock data from various sources.
These providers implement the IStockDataFetcher interface from maverick-core.
"""

from maverick_data.providers.base import BaseStockProvider
from maverick_data.providers.yfinance_provider import YFinanceProvider

__all__ = [
    "BaseStockProvider",
    "YFinanceProvider",
]
