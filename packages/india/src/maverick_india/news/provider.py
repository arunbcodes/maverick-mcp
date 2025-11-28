"""
Indian Financial News Provider.

Provides access to Indian financial news from multiple sources.

Enhanced implementation with real news sources:
- MoneyControl RSS feeds and web scraping
- Economic Times RSS feeds and web scraping
- Multi-source aggregation with deduplication
- Optional database persistence and caching
"""

import logging
from datetime import datetime
from typing import Any

from maverick_india.news.aggregator import MultiSourceNewsAggregator
from maverick_india.news.base_scraper import NewsArticleStore

logger = logging.getLogger(__name__)


class IndianNewsProvider:
    """
    Provider for Indian financial news.

    Enhanced implementation using real news sources:
    - MoneyControl (RSS + web scraping)
    - Economic Times (RSS + web scraping)
    - Multi-source aggregation with deduplication
    - Optional database-backed caching
    """

    def __init__(
        self,
        article_store: NewsArticleStore | None = None,
        cache_ttl: int = 1800,
    ):
        """
        Initialize Indian news provider.

        Args:
            article_store: Optional article store for persistence
            cache_ttl: Cache time-to-live in seconds (default: 30 min)
        """
        self.aggregator = MultiSourceNewsAggregator(
            article_store=article_store,
            cache_ttl=cache_ttl,
        )
        self.sources = ["MoneyControl", "Economic Times"]
        logger.info(
            "IndianNewsProvider initialized (enhanced mode with real news sources)"
        )

    def get_stock_news(
        self,
        symbol: str,
        limit: int = 10,
        days: int = 7,
    ) -> list[dict[str, Any]]:
        """
        Get news articles for a specific Indian stock from all sources.

        Args:
            symbol: Stock ticker symbol (e.g., "RELIANCE.NS")
            limit: Maximum number of articles
            days: Number of days to look back

        Returns:
            List of deduplicated news articles with sentiment
        """
        logger.info(f"Fetching real news for {symbol} from multiple sources")

        try:
            articles = self.aggregator.fetch_stock_news(
                symbol=symbol,
                limit=limit,
                days_back=days,
            )

            logger.info(f"Retrieved {len(articles)} real articles for {symbol}")
            return articles

        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []

    def get_market_news(
        self,
        category: str = "all",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Get general Indian market news from all sources.

        Args:
            category: News category (all, stocks, economy, policy)
            limit: Maximum number of articles

        Returns:
            List of deduplicated news articles
        """
        logger.info(f"Fetching real market news, category: {category}")

        try:
            articles = self.aggregator.fetch_latest_news(limit=limit)

            # Filter by category if specified
            if category != "all":
                articles = [a for a in articles if a.get("category") == category]

            logger.info(f"Retrieved {len(articles)} real market articles")
            return articles[:limit]

        except Exception as e:
            logger.error(f"Error fetching market news: {e}")
            return []

    def analyze_sentiment(
        self,
        symbol: str,
        period: str = "7d",
    ) -> dict[str, Any]:
        """
        Analyze news sentiment for a stock from all sources.

        Args:
            symbol: Stock ticker symbol
            period: Time period (7d, 30d, 90d)

        Returns:
            Sentiment analysis results with per-source statistics
        """
        logger.info(f"Analyzing sentiment for {symbol} (real news sources)")

        # Parse period
        days = 7 if period == "7d" else 30 if period == "30d" else 90

        try:
            # Get sentiment summary from aggregator
            sentiment_summary = self.aggregator.get_sentiment_summary(
                symbol, days_back=days
            )

            # Enhance with period and status fields
            sentiment_summary["period"] = period
            sentiment_summary["status"] = "success"
            sentiment_summary["timestamp"] = datetime.now().isoformat()
            sentiment_summary["note"] = (
                "Multi-source sentiment analysis with keyword matching. "
                "See Future Enhancements for advanced NLP."
            )

            return sentiment_summary

        except Exception as e:
            logger.error(f"Error analyzing sentiment for {symbol}: {e}")
            return {
                "symbol": symbol,
                "period": period,
                "error": str(e),
                "status": "error",
                "timestamp": datetime.now().isoformat(),
            }

    def get_trending_topics(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get trending topics in Indian financial news from all sources.

        Args:
            limit: Maximum number of topics

        Returns:
            List of trending topics with article counts and examples
        """
        logger.info("Fetching trending topics from real news sources")

        try:
            trending = self.aggregator.get_trending_topics(limit=limit)
            logger.info(f"Retrieved {len(trending)} trending topics")
            return trending

        except Exception as e:
            logger.error(f"Error fetching trending topics: {e}")
            return []


# Convenience functions


def get_indian_stock_news(
    symbol: str,
    limit: int = 10,
    article_store: NewsArticleStore | None = None,
) -> list[dict[str, Any]]:
    """
    Quick function to get real news for Indian stock from all sources.

    Args:
        symbol: Stock ticker symbol
        limit: Maximum articles
        article_store: Optional article store for persistence

    Returns:
        List of deduplicated news articles with sentiment
    """
    provider = IndianNewsProvider(article_store=article_store)
    return provider.get_stock_news(symbol, limit=limit)


def analyze_stock_sentiment(
    symbol: str,
    days_back: int = 7,
    article_store: NewsArticleStore | None = None,
) -> dict[str, Any]:
    """
    Quick function to analyze stock sentiment from all sources.

    Args:
        symbol: Stock ticker symbol
        days_back: Number of days to analyze
        article_store: Optional article store for persistence

    Returns:
        Sentiment analysis with per-source statistics
    """
    provider = IndianNewsProvider(article_store=article_store)
    period = f"{days_back}d"
    return provider.analyze_sentiment(symbol, period=period)


__all__ = [
    "IndianNewsProvider",
    "get_indian_stock_news",
    "analyze_stock_sentiment",
]
