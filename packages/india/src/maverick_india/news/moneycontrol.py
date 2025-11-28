"""
MoneyControl News Scraper.

Fetches financial news from MoneyControl using RSS feeds and web scraping.
Extends BaseNewsScraper with MoneyControl-specific implementations.
"""

import logging

from bs4 import BeautifulSoup

from maverick_india.news.base_scraper import BaseNewsScraper, NewsArticleStore

logger = logging.getLogger(__name__)


class MoneyControlScraper(BaseNewsScraper):
    """
    Scraper for MoneyControl financial news.

    Extends BaseNewsScraper with MoneyControl-specific:
    - RSS feed URLs
    - HTML content extraction
    """

    # MoneyControl RSS feeds
    RSS_FEEDS = {
        "latest": "https://www.moneycontrol.com/rss/latestnews.xml",
        "stocks": "https://www.moneycontrol.com/rss/marketreports.xml",
        "economy": "https://www.moneycontrol.com/rss/economy.xml",
        "companies": "https://www.moneycontrol.com/rss/business.xml",
    }

    def __init__(
        self,
        article_store: NewsArticleStore | None = None,
        cache_ttl: int = 1800,
        user_agent: str | None = None,
    ):
        """
        Initialize MoneyControl scraper.

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
        """Return MoneyControl RSS feed URLs."""
        return self.RSS_FEEDS

    def get_source_name(self) -> str:
        """Return source identifier."""
        return "moneycontrol"

    def extract_article_content(self, soup: BeautifulSoup, url: str) -> str | None:
        """
        Extract article content from MoneyControl HTML.

        Args:
            soup: Parsed HTML
            url: Article URL (for logging)

        Returns:
            Extracted article content or None
        """
        # Try MoneyControl-specific content selectors
        content_div = soup.find("div", {"class": "content_wrapper"})
        if not content_div:
            content_div = soup.find("div", {"class": "article-text"})
        if not content_div:
            content_div = soup.find("article")

        if content_div:
            # Extract text from paragraphs
            paragraphs = content_div.find_all("p")
            content = " ".join([p.get_text().strip() for p in paragraphs])
            return content

        return None


# Convenience function
def fetch_moneycontrol_news(
    symbol: str | None = None,
    limit: int = 10,
    article_store: NewsArticleStore | None = None,
) -> list[dict]:
    """
    Quick function to fetch MoneyControl news.

    Args:
        symbol: Stock symbol (optional, for stock-specific news)
        limit: Maximum articles
        article_store: Optional article store for persistence

    Returns:
        List of news articles
    """
    scraper = MoneyControlScraper(article_store=article_store)

    if symbol:
        return scraper.fetch_stock_news(symbol, limit=limit)
    else:
        return scraper.fetch_latest_news(limit=limit)


__all__ = [
    "MoneyControlScraper",
    "fetch_moneycontrol_news",
]
