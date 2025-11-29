"""
Maverick Data Services.

Business logic services for data operations.

Services:
    - MarketCalendarService: Trading days, market hours, holidays
    - StockCacheManager: Database-backed caching
    - StockDataFetcher: External data fetching (yfinance)
    - ScreeningService: Stock screening and recommendations
"""

from maverick_data.services.bulk_operations import (
    bulk_insert_price_data,
    bulk_insert_screening_data,
    get_latest_maverick_screening,
)
from maverick_data.services.market_calendar import MarketCalendarService
from maverick_data.services.screening import ScreeningService
from maverick_data.services.stock_cache import StockCacheManager
from maverick_data.services.stock_fetcher import StockDataFetcher

__all__ = [
    # Services
    "MarketCalendarService",
    "StockCacheManager",
    "StockDataFetcher",
    "ScreeningService",
    # Bulk operations
    "bulk_insert_price_data",
    "bulk_insert_screening_data",
    "get_latest_maverick_screening",
]
