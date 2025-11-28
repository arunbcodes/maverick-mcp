"""
Indian Financial News.

News aggregation from MoneyControl, Economic Times, and other Indian sources.
Provides RSS feed parsing, sentiment analysis, and multi-source aggregation.
"""

from maverick_india.news.aggregator import (
    MultiSourceNewsAggregator,
    get_aggregated_news,
    get_stock_sentiment,
)
from maverick_india.news.base_scraper import BaseNewsScraper, NewsArticleStore
from maverick_india.news.economic_times import (
    EconomicTimesScraper,
    fetch_economic_times_news,
)
from maverick_india.news.moneycontrol import (
    MoneyControlScraper,
    fetch_moneycontrol_news,
)
from maverick_india.news.provider import (
    IndianNewsProvider,
    analyze_stock_sentiment,
    get_indian_stock_news,
)
from maverick_india.news.symbol_mapping import IndianStockSymbolMapper

__all__ = [
    # Base classes and protocols
    "BaseNewsScraper",
    "NewsArticleStore",
    # Symbol mapping
    "IndianStockSymbolMapper",
    # Scrapers
    "MoneyControlScraper",
    "EconomicTimesScraper",
    # Aggregator
    "MultiSourceNewsAggregator",
    # High-level provider
    "IndianNewsProvider",
    # Convenience functions
    "fetch_moneycontrol_news",
    "fetch_economic_times_news",
    "get_aggregated_news",
    "get_stock_sentiment",
    "get_indian_stock_news",
    "analyze_stock_sentiment",
]
