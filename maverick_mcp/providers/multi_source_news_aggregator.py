"""
Multi-Source News Aggregator

Aggregates financial news from multiple Indian sources (MoneyControl, Economic Times)
with deduplication and unified sentiment analysis.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

from maverick_mcp.providers.moneycontrol_scraper import MoneyControlScraper
from maverick_mcp.providers.economic_times_scraper import EconomicTimesScraper
from maverick_mcp.data.models import NewsArticle, SessionLocal

logger = logging.getLogger(__name__)


class MultiSourceNewsAggregator:
    """
    Aggregates news from multiple Indian financial news sources.
    
    Features:
    - Fetches from MoneyControl and Economic Times
    - Deduplicates articles by URL and similarity
    - Unified sentiment scoring across sources
    - Database-backed caching
    - Sorted by recency and relevance
    """
    
    def __init__(self, use_db: bool = True):
        """
        Initialize multi-source news aggregator.
        
        Args:
            use_db: Whether to use database storage and caching
        """
        self.use_db = use_db
        self.moneycontrol = MoneyControlScraper(use_db=use_db)
        self.economic_times = EconomicTimesScraper(use_db=use_db)
        logger.info("MultiSourceNewsAggregator initialized")
    
    def fetch_latest_news(
        self,
        limit: int = 20,
        sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch latest news from all or selected sources.
        
        Args:
            limit: Maximum number of articles
            sources: List of sources to fetch from (default: all)
                    Options: ["moneycontrol", "economictimes"]
            
        Returns:
            Deduplicated and sorted list of news articles
        """
        if sources is None:
            sources = ["moneycontrol", "economictimes"]
        
        all_articles = []
        
        # Fetch from MoneyControl
        if "moneycontrol" in sources:
            try:
                mc_articles = self.moneycontrol.fetch_latest_news(
                    category="latest",
                    limit=limit * 2  # Fetch more to account for dedup
                )
                all_articles.extend(mc_articles)
                logger.info(f"Fetched {len(mc_articles)} articles from MoneyControl")
            except Exception as e:
                logger.error(f"Error fetching from MoneyControl: {e}")
        
        # Fetch from Economic Times
        if "economictimes" in sources:
            try:
                et_articles = self.economic_times.fetch_latest_news(
                    category="markets",
                    limit=limit * 2
                )
                all_articles.extend(et_articles)
                logger.info(f"Fetched {len(et_articles)} articles from Economic Times")
            except Exception as e:
                logger.error(f"Error fetching from Economic Times: {e}")
        
        # Deduplicate articles
        deduped_articles = self._deduplicate_articles(all_articles)
        
        # Sort by published date (most recent first)
        sorted_articles = sorted(
            deduped_articles,
            key=lambda x: x.get("published_date", datetime.min),
            reverse=True
        )
        
        logger.info(f"Returning {len(sorted_articles[:limit])} deduplicated articles")
        return sorted_articles[:limit]
    
    def fetch_stock_news(
        self,
        symbol: str,
        limit: int = 10,
        days_back: int = 7,
        sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch news for a specific stock from all sources.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE.NS")
            limit: Maximum number of articles
            days_back: Number of days to look back
            sources: List of sources (default: all)
            
        Returns:
            Deduplicated and sorted list of stock-specific news
        """
        if sources is None:
            sources = ["moneycontrol", "economictimes"]
        
        # Check database first
        if self.use_db:
            db_articles = self._fetch_from_database(symbol, days_back, limit * 2)
            if len(db_articles) >= limit:
                logger.info(f"Found sufficient articles in database for {symbol}")
                return db_articles[:limit]
        
        all_articles = []
        
        # Fetch from MoneyControl
        if "moneycontrol" in sources:
            try:
                mc_articles = self.moneycontrol.fetch_stock_news(
                    symbol,
                    limit=limit * 2,
                    days_back=days_back
                )
                all_articles.extend(mc_articles)
                logger.info(f"Fetched {len(mc_articles)} MoneyControl articles for {symbol}")
            except Exception as e:
                logger.error(f"Error fetching from MoneyControl for {symbol}: {e}")
        
        # Fetch from Economic Times
        if "economictimes" in sources:
            try:
                et_articles = self.economic_times.fetch_stock_news(
                    symbol,
                    limit=limit * 2,
                    days_back=days_back
                )
                all_articles.extend(et_articles)
                logger.info(f"Fetched {len(et_articles)} ET articles for {symbol}")
            except Exception as e:
                logger.error(f"Error fetching from ET for {symbol}: {e}")
        
        # Deduplicate and sort
        deduped_articles = self._deduplicate_articles(all_articles)
        sorted_articles = sorted(
            deduped_articles,
            key=lambda x: x.get("published_date", datetime.min),
            reverse=True
        )
        
        logger.info(f"Returning {len(sorted_articles[:limit])} deduplicated articles for {symbol}")
        return sorted_articles[:limit]
    
    def get_sentiment_summary(
        self,
        symbol: str,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Get aggregated sentiment summary for a stock from all sources.
        
        Args:
            symbol: Stock symbol
            days_back: Number of days to analyze
            
        Returns:
            Sentiment summary with statistics
        """
        # Fetch articles from all sources
        articles = self.fetch_stock_news(symbol, limit=100, days_back=days_back)
        
        if not articles:
            return {
                "symbol": symbol,
                "total_articles": 0,
                "sentiment_distribution": {
                    "bullish": 0,
                    "bearish": 0,
                    "neutral": 0
                },
                "overall_sentiment": "neutral",
                "average_score": 0.0,
                "by_source": {}
            }
        
        # Calculate overall statistics
        sentiment_counts = defaultdict(int)
        scores = []
        by_source = defaultdict(lambda: {"count": 0, "bullish": 0, "bearish": 0, "neutral": 0})
        
        for article in articles:
            sentiment = article.get("sentiment", "neutral")
            sentiment_counts[sentiment] += 1
            
            if article.get("sentiment_score") is not None:
                scores.append(float(article["sentiment_score"]))
            
            source = article.get("source", "unknown")
            by_source[source]["count"] += 1
            by_source[source][sentiment] += 1
        
        # Calculate average score and overall sentiment
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        if sentiment_counts["bullish"] > sentiment_counts["bearish"]:
            overall = "bullish"
        elif sentiment_counts["bearish"] > sentiment_counts["bullish"]:
            overall = "bearish"
        else:
            overall = "neutral"
        
        return {
            "symbol": symbol,
            "total_articles": len(articles),
            "sentiment_distribution": {
                "bullish": sentiment_counts["bullish"],
                "bearish": sentiment_counts["bearish"],
                "neutral": sentiment_counts["neutral"]
            },
            "overall_sentiment": overall,
            "average_score": round(avg_score, 4),
            "by_source": dict(by_source),
            "period_days": days_back
        }
    
    def get_trending_topics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending topics across all news sources.
        
        Args:
            limit: Maximum number of topics
            
        Returns:
            List of trending topics with article counts
        """
        # Fetch recent articles
        articles = self.fetch_latest_news(limit=100)
        
        # Count keyword occurrences
        keyword_counts = defaultdict(int)
        keyword_articles = defaultdict(list)
        
        for article in articles:
            keywords = article.get("keywords", [])
            for keyword in keywords:
                keyword_counts[keyword] += 1
                if len(keyword_articles[keyword]) < 3:  # Store up to 3 example articles
                    keyword_articles[keyword].append(article["title"])
        
        # Sort by frequency
        sorted_keywords = sorted(
            keyword_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Format results
        trending = []
        for keyword, count in sorted_keywords[:limit]:
            trending.append({
                "topic": keyword,
                "article_count": count,
                "example_headlines": keyword_articles[keyword]
            })
        
        return trending
    
    # Helper methods
    
    def _deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate articles by URL and title similarity.
        
        Args:
            articles: List of articles
            
        Returns:
            Deduplicated list of articles
        """
        seen_urls: Set[str] = set()
        seen_titles: Set[str] = set()
        deduped = []
        
        for article in articles:
            url = article.get("url", "")
            title = article.get("title", "").lower().strip()
            
            # Check URL duplication
            if url and url in seen_urls:
                logger.debug(f"Skipping duplicate URL: {url}")
                continue
            
            # Check title similarity (exact match)
            if title and title in seen_titles:
                logger.debug(f"Skipping duplicate title: {title[:50]}...")
                continue
            
            # Add to seen sets
            if url:
                seen_urls.add(url)
            if title:
                seen_titles.add(title)
            
            deduped.append(article)
        
        removed_count = len(articles) - len(deduped)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate articles")
        
        return deduped
    
    def _fetch_from_database(
        self,
        symbol: str,
        days_back: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch articles from database across all sources."""
        try:
            session = SessionLocal()
            articles = NewsArticle.get_recent_articles(
                session,
                symbol=symbol,
                days_back=days_back,
                limit=limit
            )
            session.close()
            
            return [article.to_dict() for article in articles]
            
        except Exception as e:
            logger.error(f"Error fetching from database: {e}")
            return []


# Convenience functions

def get_aggregated_news(symbol: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Quick function to get aggregated news from all sources.
    
    Args:
        symbol: Stock symbol (optional, for stock-specific news)
        limit: Maximum articles
        
    Returns:
        Deduplicated list of news articles
    """
    aggregator = MultiSourceNewsAggregator()
    
    if symbol:
        return aggregator.fetch_stock_news(symbol, limit=limit)
    else:
        return aggregator.fetch_latest_news(limit=limit)


def get_stock_sentiment(symbol: str, days_back: int = 7) -> Dict[str, Any]:
    """
    Quick function to get sentiment summary for a stock.
    
    Args:
        symbol: Stock symbol
        days_back: Number of days to analyze
        
    Returns:
        Sentiment summary
    """
    aggregator = MultiSourceNewsAggregator()
    return aggregator.get_sentiment_summary(symbol, days_back=days_back)


__all__ = [
    "MultiSourceNewsAggregator",
    "get_aggregated_news",
    "get_stock_sentiment",
]

