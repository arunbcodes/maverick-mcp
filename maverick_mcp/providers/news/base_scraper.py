"""
Base News Scraper - Abstract base class for financial news scrapers.

Provides common functionality for RSS feed parsing, sentiment analysis,
database persistence, and caching. Specific news sources only need to
implement source-specific methods.
"""

import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional, Set
from time import struct_time

import requests
import feedparser
from bs4 import BeautifulSoup
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ratelimit import limits, sleep_and_retry

from maverick_mcp.data.models import NewsArticle, SessionLocal

logger = logging.getLogger(__name__)


class BaseNewsScraper(ABC):
    """
    Abstract base class for financial news scrapers.
    
    Provides common functionality:
    - RSS feed parsing
    - Web scraping with rate limiting and retry logic
    - Sentiment analysis (keyword-based)
    - Database persistence
    - Caching
    
    Subclasses must implement:
    - get_rss_feeds(): Return RSS feed URLs
    - get_source_name(): Return source identifier
    - extract_article_content(): Extract content from parsed HTML
    """
    
    # Shared sentiment keywords across all scrapers
    BULLISH_KEYWORDS = [
        "surge", "rally", "gain", "profit", "growth", "beat", "outperform",
        "bullish", "positive", "upgrade", "buy", "strong", "record", "high",
        "revenue", "earnings beat", "expansion", "momentum", "soar", "jump",
        "rise", "advance", "climb", "spike"
    ]
    
    BEARISH_KEYWORDS = [
        "fall", "drop", "loss", "decline", "bearish", "negative", "downgrade",
        "sell", "weak", "miss", "disappoint", "concern", "warning", "low",
        "deficit", "debt", "lawsuit", "penalty", "slump", "plunge", "tumble",
        "slide", "crash", "collapse"
    ]
    
    # Shared financial terms for keyword extraction
    FINANCIAL_TERMS = [
        "earnings", "revenue", "profit", "loss", "growth", "decline",
        "merger", "acquisition", "ipo", "dividend", "buyback", "split",
        "expansion", "investment", "debt", "equity", "bond", "rating",
        "quarterly", "annual", "forecast", "guidance", "restructuring"
    ]
    
    def __init__(
        self,
        use_db: bool = True,
        cache_ttl: int = 1800,
        user_agent: str | None = None,
        db_session = None
    ):
        """
        Initialize news scraper.
        
        Args:
            use_db: Whether to store articles in database
            cache_ttl: Cache time-to-live in seconds (default: 30 min)
            user_agent: Custom user agent string
            db_session: Optional database session (for testing)
        """
        self.use_db = use_db
        self.cache = TTLCache(maxsize=100, ttl=cache_ttl)
        self.session = requests.Session()
        self._db_session = db_session
        
        # Setup session with user agent
        self.user_agent = user_agent or "MaverickMCP/1.0 (Financial News Aggregator)"
        self.session.headers.update({
            "User-Agent": self.user_agent
        })
        
        logger.info(
            f"{self.__class__.__name__} initialized "
            f"(DB: {use_db}, Cache TTL: {cache_ttl}s, Source: {self.get_source_name()})"
        )
    
    # Abstract methods - must be implemented by subclasses
    
    @abstractmethod
    def get_rss_feeds(self) -> Dict[str, str]:
        """
        Return RSS feed URLs for this news source.
        
        Returns:
            Dictionary mapping category names to RSS feed URLs
            Example: {"latest": "https://example.com/rss/latest.xml"}
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """
        Return source identifier for this news source.
        
        Returns:
            Lowercase source name (e.g., "moneycontrol", "economictimes")
        """
        pass
    
    @abstractmethod
    def extract_article_content(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """
        Extract full article content from parsed HTML.
        
        This is source-specific as each news site has different HTML structure.
        
        Args:
            soup: BeautifulSoup object with parsed HTML
            url: Article URL (for logging)
            
        Returns:
            Extracted article content or None if extraction fails
        """
        pass
    
    # Common implementation methods
    
    def fetch_latest_news(
        self,
        category: str = "latest",
        limit: int = 20,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch latest news from RSS feed.
        
        Args:
            category: News category
            limit: Maximum number of articles
            use_cache: Whether to use cached results
            
        Returns:
            List of news articles
        """
        cache_key = f"news_{self.get_source_name()}_{category}_{limit}"
        
        if use_cache and cache_key in self.cache:
            logger.debug(f"Returning cached news for {category} from {self.get_source_name()}")
            return self.cache[cache_key]
        
        try:
            rss_feeds = self.get_rss_feeds()
            feed_url = rss_feeds.get(category, list(rss_feeds.values())[0])
            logger.info(f"Fetching RSS feed: {feed_url}")
            
            # Parse RSS feed
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                logger.warning(f"No entries found in {category} feed from {self.get_source_name()}")
                return []
            
            articles = []
            for entry in feed.entries[:limit]:
                article = self._parse_rss_entry(entry, category)
                if article:
                    articles.append(article)
                    
                    # Store in database if enabled
                    if self.use_db:
                        self._store_article_in_db(article)
            
            logger.info(f"Fetched {len(articles)} articles from {category} ({self.get_source_name()})")
            
            # Cache results
            self.cache[cache_key] = articles
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching news from {category} ({self.get_source_name()}): {e}")
            return []
    
    def fetch_stock_news(
        self,
        symbol: str,
        limit: int = 10,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Fetch news for a specific stock.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE.NS")
            limit: Maximum number of articles
            days_back: Number of days to look back
            
        Returns:
            List of news articles for the stock
        """
        cache_key = f"stock_{self.get_source_name()}_{symbol}_{limit}_{days_back}"
        
        if cache_key in self.cache:
            logger.debug(f"Returning cached news for {symbol} from {self.get_source_name()}")
            return self.cache[cache_key]
        
        # Extract base symbol
        base_symbol = symbol.replace('.NS', '').replace('.BO', '').upper()
        company_name = self._get_company_name(base_symbol)
        
        # Check database first
        if self.use_db:
            db_articles = self._fetch_from_database(symbol, days_back, limit)
            if db_articles:
                logger.info(
                    f"Found {len(db_articles)} articles in database for {symbol} "
                    f"from {self.get_source_name()}"
                )
                self.cache[cache_key] = db_articles
                return db_articles
        
        # Fetch from RSS and filter
        categories = self._get_stock_related_categories()
        all_articles = []
        for category in categories:
            articles = self.fetch_latest_news(category, limit=50, use_cache=False)
            all_articles.extend(articles)
        
        # Filter articles mentioning the stock
        stock_articles = []
        for article in all_articles:
            if self._mentions_stock(article, base_symbol, company_name):
                article["symbol"] = symbol
                article["company_name"] = company_name
                stock_articles.append(article)
                
                if len(stock_articles) >= limit:
                    break
        
        logger.info(f"Found {len(stock_articles)} articles for {symbol} from {self.get_source_name()}")
        self.cache[cache_key] = stock_articles
        return stock_articles
    
    @sleep_and_retry
    @limits(calls=10, period=60)  # 10 calls per minute
    @retry(
        retry=retry_if_exception_type((requests.RequestException, requests.Timeout)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def scrape_article_content(self, url: str) -> Optional[str]:
        """
        Scrape full article content from URL with rate limiting and retry logic.
        
        Args:
            url: Article URL
            
        Returns:
            Article content or None if scraping fails
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Call subclass-specific extraction method
            content = self.extract_article_content(soup, url)
            
            if content:
                return content[:5000]  # Limit content length
            
            logger.warning(f"Could not extract content from {url} ({self.get_source_name()})")
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error scraping article {url}: {e}")
            raise  # Let retry decorator handle it
        except Exception as e:
            logger.error(f"Unexpected error scraping article {url}: {e}")
            return None
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of article text using keyword matching.
        
        Args:
            text: Article text (title + summary + content)
            
        Returns:
            Sentiment analysis result
        """
        text_lower = text.lower()
        
        # Count bullish and bearish keywords
        bullish_count = sum(1 for keyword in self.BULLISH_KEYWORDS if keyword in text_lower)
        bearish_count = sum(1 for keyword in self.BEARISH_KEYWORDS if keyword in text_lower)
        
        # Calculate sentiment score (-1 to 1)
        total_keywords = bullish_count + bearish_count
        if total_keywords == 0:
            sentiment_score = 0.0
            sentiment = "neutral"
            confidence = 0.5
        else:
            sentiment_score = (bullish_count - bearish_count) / total_keywords
            confidence = min(total_keywords / 10, 1.0)  # More keywords = higher confidence
            
            if sentiment_score > 0.2:
                sentiment = "bullish"
            elif sentiment_score < -0.2:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "sentiment_score": round(sentiment_score, 4),
            "confidence": round(confidence, 4),
            "bullish_keywords": bullish_count,
            "bearish_keywords": bearish_count
        }
    
    # Helper methods
    
    def _parse_rss_entry(self, entry: Any, category: str) -> Optional[Dict[str, Any]]:
        """Parse RSS feed entry into article dict."""
        try:
            # Extract published date
            published_date = None
            if hasattr(entry, 'published_parsed'):
                if isinstance(entry.published_parsed, struct_time):
                    published_date = datetime(*entry.published_parsed[:6], tzinfo=UTC)
            
            if not published_date:
                published_date = datetime.now(UTC)
            
            # Extract title and summary
            title = entry.get('title', '').strip()
            summary = entry.get('summary', '') or entry.get('description', '')
            summary = BeautifulSoup(summary, 'html.parser').get_text().strip()
            url = entry.get('link', '').strip()
            
            if not title or not url:
                return None
            
            # Analyze sentiment
            text_for_sentiment = f"{title} {summary}"
            sentiment_data = self.analyze_sentiment(text_for_sentiment)
            
            article = {
                "title": title,
                "url": url,
                "source": self.get_source_name(),
                "published_date": published_date,
                "summary": summary[:500] if summary else None,
                "category": category,
                "sentiment": sentiment_data["sentiment"],
                "sentiment_score": sentiment_data["sentiment_score"],
                "confidence": sentiment_data["confidence"],
                "keywords": self._extract_keywords(title, summary)
            }
            
            return article
            
        except Exception as e:
            logger.error(f"Error parsing RSS entry from {self.get_source_name()}: {e}")
            return None
    
    def _store_article_in_db(self, article: Dict[str, Any]) -> None:
        """Store article in database using NewsArticle model."""
        try:
            session = self._db_session or SessionLocal()
            
            try:
                NewsArticle.store_article(
                    session,
                    title=article["title"],
                    url=article["url"],
                    source=article["source"],
                    published_date=article["published_date"],
                    summary=article.get("summary"),
                    symbol=article.get("symbol"),
                    company_name=article.get("company_name"),
                    sentiment=article.get("sentiment"),
                    sentiment_score=article.get("sentiment_score"),
                    confidence=article.get("confidence"),
                    category=article.get("category"),
                    keywords=article.get("keywords")
                )
                
                logger.debug(f"Stored article in DB: {article['title'][:50]}...")
                
            finally:
                if not self._db_session:
                    session.close()
            
        except Exception as e:
            logger.error(f"Error storing article in DB ({self.get_source_name()}): {e}")
            # Don't raise - storage failure shouldn't break news fetching
    
    def _fetch_from_database(
        self,
        symbol: str,
        days_back: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch articles from database."""
        try:
            session = self._db_session or SessionLocal()
            
            try:
                articles = NewsArticle.get_recent_articles(
                    session,
                    symbol=symbol,
                    source=self.get_source_name(),
                    days_back=days_back,
                    limit=limit
                )
                
                return [article.to_dict() for article in articles]
                
            finally:
                if not self._db_session:
                    session.close()
            
        except Exception as e:
            logger.error(f"Error fetching from database ({self.get_source_name()}): {e}")
            return []
    
    def _mentions_stock(
        self,
        article: Dict[str, Any],
        symbol: str,
        company_name: Optional[str]
    ) -> bool:
        """Check if article mentions the stock."""
        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
        
        # Check for symbol mention
        if symbol.lower() in text:
            return True
        
        # Check for company name mention
        if company_name and company_name.lower() in text:
            return True
        
        return False
    
    def _get_company_name(self, symbol: str) -> Optional[str]:
        """
        Get company name from symbol.
        
        Override this in subclass for source-specific mappings,
        or use a centralized symbol mapper.
        """
        # Import here to avoid circular dependency
        from maverick_mcp.utils.symbol_mapping import IndianStockSymbolMapper
        return IndianStockSymbolMapper.get_company_name(symbol)
    
    def _extract_keywords(self, title: str, summary: str) -> List[str]:
        """Extract keywords from title and summary."""
        text = f"{title} {summary}".lower()
        
        keywords = []
        for term in self.FINANCIAL_TERMS:
            if term in text:
                keywords.append(term)
        
        return keywords[:10]  # Limit to 10 keywords
    
    def _get_stock_related_categories(self) -> List[str]:
        """
        Get categories that typically contain stock-specific news.
        
        Override in subclass if needed.
        """
        rss_feeds = self.get_rss_feeds()
        # Return all categories by default
        return list(rss_feeds.keys())


__all__ = ["BaseNewsScraper"]

