"""
Crypto News Providers.

Multiple news sources for cryptocurrency news aggregation.

Sources:
    - CryptoPanic: Free crypto news aggregator (no API key for basic use)
    - RSS feeds: Major crypto publications
    - NewsData.io: General news API
"""

from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Represents a news article."""
    
    title: str
    url: str
    source: str
    published_at: datetime | None
    summary: str | None = None
    sentiment: str | None = None  # bullish, bearish, neutral
    votes: dict[str, int] | None = None  # Community votes
    currencies: list[str] | None = None  # Related cryptocurrencies
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "summary": self.summary,
            "sentiment": self.sentiment,
            "votes": self.votes,
            "currencies": self.currencies,
        }


class CryptoPanicProvider:
    """
    CryptoPanic news provider.
    
    CryptoPanic is a news aggregator that collects crypto news from
    multiple sources and provides community-driven sentiment voting.
    
    API Documentation: https://cryptopanic.com/developers/api/
    
    Free tier:
        - Public feed: No API key required
        - Rate limit: ~100 requests/hour
        
    With API key:
        - More endpoints (trending, votes data)
        - Higher rate limits
        
    Example:
        >>> provider = CryptoPanicProvider()
        >>> news = await provider.get_news(currencies=["BTC", "ETH"])
    """
    
    BASE_URL = "https://cryptopanic.com/api/v1"
    PUBLIC_URL = "https://cryptopanic.com/api/free/v1"
    
    # RSS feeds for crypto publications (backup)
    RSS_FEEDS = {
        "cointelegraph": "https://cointelegraph.com/rss",
        "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "decrypt": "https://decrypt.co/feed",
        "theblock": "https://www.theblock.co/rss.xml",
    }
    
    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ):
        """
        Initialize CryptoPanic provider.

        Args:
            api_key: Optional API key for premium features
            timeout: Request timeout
            http_client: Optional shared HTTP client (recommended for connection reuse)
        """
        self.api_key = api_key
        self.timeout = timeout
        self._http_client = http_client
        self._owns_client = http_client is None

        # Use authenticated or public endpoint
        if api_key:
            self.base_url = self.BASE_URL
        else:
            self.base_url = self.PUBLIC_URL

        logger.info(f"CryptoPanicProvider initialized (API key: {'yes' if api_key else 'no'})")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client if owned by this instance."""
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def _request(self, endpoint: str, params: dict | None = None) -> dict | None:
        """Make async HTTP request using shared client."""
        url = f"{self.base_url}/{endpoint}"

        params = params or {}
        if self.api_key:
            params["auth_token"] = self.api_key

        try:
            client = await self._get_client()
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from CryptoPanic: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching from CryptoPanic: {e}")
            return None
    
    async def get_news(
        self,
        currencies: list[str] | None = None,
        filter_type: str | None = None,
        kind: str = "news",
        limit: int = 20,
    ) -> list[NewsArticle]:
        """
        Get crypto news articles.
        
        Args:
            currencies: Filter by currency symbols (e.g., ["BTC", "ETH"])
            filter_type: Filter type ("rising", "hot", "bullish", "bearish", "important")
            kind: Content type ("news", "media", "all")
            limit: Maximum number of results
            
        Returns:
            List of NewsArticle objects
        """
        logger.info(f"Fetching crypto news (currencies: {currencies})")
        
        params = {
            "kind": kind,
        }
        
        if currencies:
            params["currencies"] = ",".join(currencies)
        if filter_type:
            params["filter"] = filter_type
        
        # Try CryptoPanic API
        result = await self._request("posts/", params)
        
        if result and "results" in result:
            articles = []
            for item in result["results"][:limit]:
                # Determine sentiment from votes
                votes = item.get("votes", {})
                sentiment = self._calculate_sentiment(votes)
                
                # Extract currencies mentioned
                curr_list = [c.get("code") for c in item.get("currencies", [])]
                
                articles.append(NewsArticle(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    source=item.get("source", {}).get("title", "Unknown"),
                    published_at=self._parse_date(item.get("published_at")),
                    summary=item.get("title"),  # CryptoPanic doesn't provide summary
                    sentiment=sentiment,
                    votes=votes,
                    currencies=curr_list,
                ))
            
            return articles
        
        # Fallback to RSS feeds
        logger.info("Falling back to RSS feeds")
        return await self._fetch_rss_news(currencies, limit)
    
    def _calculate_sentiment(self, votes: dict) -> str:
        """Calculate sentiment from community votes."""
        if not votes:
            return "neutral"
        
        positive = votes.get("positive", 0) + votes.get("liked", 0)
        negative = votes.get("negative", 0) + votes.get("disliked", 0)
        
        if positive > negative * 1.5:
            return "bullish"
        elif negative > positive * 1.5:
            return "bearish"
        else:
            return "neutral"
    
    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse date string to datetime."""
        if not date_str:
            return None
        try:
            # CryptoPanic uses ISO format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None
    
    async def _fetch_rss_news(
        self,
        currencies: list[str] | None = None,
        limit: int = 20,
    ) -> list[NewsArticle]:
        """Fetch news from RSS feeds as fallback."""
        articles = []
        client = await self._get_client()

        for source, feed_url in self.RSS_FEEDS.items():
            try:
                response = await client.get(feed_url)
                response.raise_for_status()

                # Parse RSS XML
                root = ET.fromstring(response.text)

                for item in root.findall(".//item")[:10]:
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")
                    description = item.findtext("description", "")

                    # Filter by currency if specified
                    if currencies:
                        title_lower = title.lower()
                        if not any(c.lower() in title_lower for c in currencies):
                            continue

                    articles.append(NewsArticle(
                        title=title,
                        url=link,
                        source=source,
                        published_at=self._parse_rss_date(pub_date),
                        summary=description[:200] if description else None,
                        sentiment="neutral",
                    ))

            except Exception as e:
                logger.warning(f"Failed to fetch RSS from {source}: {e}")
        
        # Sort by date and limit
        articles.sort(key=lambda x: x.published_at or datetime.min, reverse=True)
        return articles[:limit]
    
    def _parse_rss_date(self, date_str: str) -> datetime | None:
        """Parse RSS date format."""
        if not date_str:
            return None
        try:
            # Common RSS date formats
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            return None
    
    async def get_trending(self, limit: int = 10) -> list[NewsArticle]:
        """
        Get trending crypto news.
        
        Returns news articles sorted by engagement/votes.
        """
        return await self.get_news(filter_type="hot", limit=limit)
    
    async def get_bullish_news(self, limit: int = 10) -> list[NewsArticle]:
        """Get news with bullish sentiment."""
        return await self.get_news(filter_type="bullish", limit=limit)
    
    async def get_bearish_news(self, limit: int = 10) -> list[NewsArticle]:
        """Get news with bearish sentiment."""
        return await self.get_news(filter_type="bearish", limit=limit)


class NewsAggregator:
    """
    Aggregates news from multiple crypto news sources.
    
    Combines CryptoPanic, RSS feeds, and other sources
    for comprehensive crypto news coverage.
    
    Example:
        >>> aggregator = NewsAggregator()
        >>> news = await aggregator.get_all_news(["BTC"])
    """
    
    def __init__(self, cryptopanic_key: str | None = None):
        """
        Initialize news aggregator.
        
        Args:
            cryptopanic_key: Optional CryptoPanic API key
        """
        self.cryptopanic = CryptoPanicProvider(api_key=cryptopanic_key)
    
    async def get_all_news(
        self,
        currencies: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Get news from all sources.
        
        Args:
            currencies: Filter by cryptocurrency symbols
            limit: Maximum articles to return
            
        Returns:
            List of news articles from all sources
        """
        articles = await self.cryptopanic.get_news(
            currencies=currencies,
            limit=limit,
        )
        
        return [a.to_dict() for a in articles]
    
    async def get_news_summary(
        self,
        currencies: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get news summary with sentiment breakdown.
        
        Args:
            currencies: Filter by cryptocurrency symbols
            
        Returns:
            Summary with article counts by sentiment
        """
        articles = await self.cryptopanic.get_news(currencies=currencies, limit=50)
        
        sentiment_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
        for article in articles:
            sentiment = article.sentiment or "neutral"
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Calculate overall sentiment
        total = len(articles)
        if total == 0:
            overall = "neutral"
        elif sentiment_counts["bullish"] > sentiment_counts["bearish"] * 1.5:
            overall = "bullish"
        elif sentiment_counts["bearish"] > sentiment_counts["bullish"] * 1.5:
            overall = "bearish"
        else:
            overall = "neutral"
        
        return {
            "total_articles": total,
            "sentiment_breakdown": sentiment_counts,
            "overall_sentiment": overall,
            "currencies": currencies,
            "top_articles": [a.to_dict() for a in articles[:5]],
            "timestamp": datetime.now().isoformat(),
        }

