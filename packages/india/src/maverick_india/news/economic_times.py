"""
Economic Times News Scraper.

Fetches financial news from Economic Times using RSS feeds and web scraping.
Extends BaseNewsScraper with Economic Times-specific implementations.
"""

import logging

from bs4 import BeautifulSoup

from maverick_india.news.base_scraper import BaseNewsScraper, NewsArticleStore

logger = logging.getLogger(__name__)


class EconomicTimesScraper(BaseNewsScraper):
    """
    Scraper for Economic Times financial news.

    Extends BaseNewsScraper with Economic Times-specific:
    - RSS feed URLs
    - HTML content extraction
    """

    # Economic Times RSS feeds
    RSS_FEEDS = {
        "markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "stocks": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
        "companies": "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms",
        "economy": "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
        "policy": "https://economictimes.indiatimes.com/news/economy/policy/rssfeeds/1111525242.cms",
    }

    def __init__(
        self,
        article_store: NewsArticleStore | None = None,
        cache_ttl: int = 1800,
        user_agent: str | None = None,
    ):
        """
        Initialize Economic Times scraper.

        Args:
            article_store: Optional article store for persistence
            cache_ttl: Cache time-to-live in seconds (default: 30 min)
            user_agent: Custom user agent string
        """
        super().__init__(
            article_store=article_store,
            cache_ttl=cache_ttl,
            user_agent=user_agent,
        )

    # Implement abstract methods from BaseNewsScraper

    def get_rss_feeds(self) -> dict[str, str]:
        """Return Economic Times RSS feed URLs."""
        return self.RSS_FEEDS

    def get_source_name(self) -> str:
        """Return source identifier."""
        return "economictimes"

    def extract_article_content(self, soup: BeautifulSoup, url: str) -> str | None:
        """
        Extract article content from Economic Times HTML.

        Args:
            soup: Parsed HTML
            url: Article URL (for logging)

        Returns:
            Extracted article content or None
        """
        # Try Economic Times-specific content selectors
        content_div = soup.find("div", {"class": "artText"})
        if not content_div:
            content_div = soup.find("div", {"class": "article-content"})
        if not content_div:
            content_div = soup.find("article")

        if content_div:
            # Extract text from paragraphs
            paragraphs = content_div.find_all("p")
            content = " ".join([p.get_text().strip() for p in paragraphs])
            return content

        return None

    def _get_stock_related_categories(self) -> list[str]:
        """
        Override to return ET-specific categories for stock news.

        Returns:
            List of categories that typically contain stock-specific news
        """
        return ["stocks", "markets", "companies"]


# Convenience function
def fetch_economic_times_news(
    symbol: str | None = None,
    limit: int = 10,
    article_store: NewsArticleStore | None = None,
) -> list[dict]:
    """
    Quick function to fetch Economic Times news.

    Args:
        symbol: Stock symbol (optional, for stock-specific news)
        limit: Maximum articles
        article_store: Optional article store for persistence

    Returns:
        List of news articles
    """
    scraper = EconomicTimesScraper(article_store=article_store)

    if symbol:
        return scraper.fetch_stock_news(symbol, limit=limit)
    else:
        return scraper.fetch_latest_news(limit=limit)


__all__ = [
    "EconomicTimesScraper",
    "fetch_economic_times_news",
]
