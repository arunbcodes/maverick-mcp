"""
Economic Times News Scraper

Fetches financial news from Economic Times using RSS feeds and web scraping.
Stores articles in database with sentiment analysis.
"""

import logging
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional

import requests
import feedparser
from bs4 import BeautifulSoup
from cachetools import TTLCache

from maverick_mcp.data.models import NewsArticle, SessionLocal

logger = logging.getLogger(__name__)


class EconomicTimesScraper:
    """
    Scraper for Economic Times financial news.
    
    Features:
    - RSS feed parsing for latest news
    - Web scraping for full article content
    - Market and stock-specific news
    - Database persistence via NewsArticle model
    - Caching to reduce API calls
    """
    
    # Economic Times RSS feeds
    RSS_FEEDS = {
        "markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "stocks": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
        "companies": "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms",
        "economy": "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
        "policy": "https://economictimes.indiatimes.com/news/economy/policy/rssfeeds/1111525242.cms",
    }
    
    # Sentiment keywords (inherited from MoneyControl approach)
    BULLISH_KEYWORDS = [
        "surge", "rally", "gain", "profit", "growth", "beat", "outperform",
        "bullish", "positive", "upgrade", "buy", "strong", "record", "high",
        "revenue", "earnings beat", "expansion", "momentum", "soar", "jump"
    ]
    
    BEARISH_KEYWORDS = [
        "fall", "drop", "loss", "decline", "bearish", "negative", "downgrade",
        "sell", "weak", "miss", "disappoint", "concern", "warning", "low",
        "deficit", "debt", "lawsuit", "penalty", "slump", "plunge"
    ]
    
    def __init__(self, use_db: bool = True, cache_ttl: int = 1800):
        """
        Initialize Economic Times scraper.
        
        Args:
            use_db: Whether to store articles in database
            cache_ttl: Cache time-to-live in seconds (default: 30 min)
        """
        self.use_db = use_db
        self.cache = TTLCache(maxsize=100, ttl=cache_ttl)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        logger.info(f"EconomicTimesScraper initialized (DB: {use_db}, Cache TTL: {cache_ttl}s)")
    
    def fetch_latest_news(
        self,
        category: str = "markets",
        limit: int = 20,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch latest news from Economic Times RSS feed.
        
        Args:
            category: News category (markets, stocks, companies, economy, policy)
            limit: Maximum number of articles
            use_cache: Whether to use cached results
            
        Returns:
            List of news articles
        """
        cache_key = f"et_news_{category}_{limit}"
        
        if use_cache and cache_key in self.cache:
            logger.debug(f"Returning cached ET news for {category}")
            return self.cache[cache_key]
        
        try:
            feed_url = self.RSS_FEEDS.get(category, self.RSS_FEEDS["markets"])
            logger.info(f"Fetching ET RSS feed: {feed_url}")
            
            # Parse RSS feed
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                logger.warning(f"No entries found in ET {category} feed")
                return []
            
            articles = []
            for entry in feed.entries[:limit]:
                article = self._parse_rss_entry(entry, category)
                if article:
                    articles.append(article)
                    
                    # Store in database if enabled
                    if self.use_db:
                        self._store_article_in_db(article)
            
            logger.info(f"Fetched {len(articles)} ET articles from {category}")
            
            # Cache results
            self.cache[cache_key] = articles
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching ET news from {category}: {e}")
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
        cache_key = f"et_stock_{symbol}_{limit}_{days_back}"
        
        if cache_key in self.cache:
            logger.debug(f"Returning cached ET news for {symbol}")
            return self.cache[cache_key]
        
        # Extract base symbol
        base_symbol = symbol.replace('.NS', '').replace('.BO', '').upper()
        company_name = self._get_company_name(base_symbol)
        
        # Check database first
        if self.use_db:
            db_articles = self._fetch_from_database(symbol, days_back, limit)
            if db_articles:
                logger.info(f"Found {len(db_articles)} ET articles in database for {symbol}")
                self.cache[cache_key] = db_articles
                return db_articles
        
        # Fetch from RSS and filter
        all_articles = []
        for category in ["stocks", "markets", "companies"]:
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
        
        logger.info(f"Found {len(stock_articles)} ET articles for {symbol}")
        self.cache[cache_key] = stock_articles
        return stock_articles
    
    def scrape_article_content(self, url: str) -> Optional[str]:
        """
        Scrape full article content from Economic Times.
        
        Args:
            url: Article URL
            
        Returns:
            Article content or None if scraping fails
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find article content (ET structure)
            content_div = soup.find('div', {'class': 'artText'})
            if not content_div:
                content_div = soup.find('div', {'class': 'article-content'})
            if not content_div:
                content_div = soup.find('article')
            
            if content_div:
                # Extract text from paragraphs
                paragraphs = content_div.find_all('p')
                content = ' '.join([p.get_text().strip() for p in paragraphs])
                return content[:5000]  # Limit content length
            
            logger.warning(f"Could not extract content from ET: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error scraping ET article {url}: {e}")
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
            confidence = min(total_keywords / 10, 1.0)
            
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
                from time import struct_time
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
                "source": "economictimes",
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
            logger.error(f"Error parsing ET RSS entry: {e}")
            return None
    
    def _store_article_in_db(self, article: Dict[str, Any]) -> None:
        """Store article in database using NewsArticle model."""
        try:
            session = SessionLocal()
            
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
            
            session.close()
            logger.debug(f"Stored ET article in DB: {article['title'][:50]}...")
            
        except Exception as e:
            logger.error(f"Error storing ET article in DB: {e}")
    
    def _fetch_from_database(
        self,
        symbol: str,
        days_back: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch articles from database."""
        try:
            session = SessionLocal()
            articles = NewsArticle.get_recent_articles(
                session,
                symbol=symbol,
                source="economictimes",
                days_back=days_back,
                limit=limit
            )
            session.close()
            
            return [article.to_dict() for article in articles]
            
        except Exception as e:
            logger.error(f"Error fetching ET articles from database: {e}")
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
        """Get company name from symbol."""
        # Reuse mapping from MoneyControl
        symbol_map = {
            "RELIANCE": "Reliance Industries",
            "TCS": "Tata Consultancy Services",
            "INFY": "Infosys",
            "HDFCBANK": "HDFC Bank",
            "ITC": "ITC",
            "SBIN": "State Bank of India",
            "BHARTIARTL": "Bharti Airtel",
            "ICICIBANK": "ICICI Bank",
            "HINDUNILVR": "Hindustan Unilever",
            "LT": "Larsen & Toubro",
            "WIPRO": "Wipro",
            "AXISBANK": "Axis Bank",
            "KOTAKBANK": "Kotak Mahindra Bank",
            "MARUTI": "Maruti Suzuki",
            "TATASTEEL": "Tata Steel"
        }
        
        return symbol_map.get(symbol.upper())
    
    def _extract_keywords(self, title: str, summary: str) -> List[str]:
        """Extract keywords from title and summary."""
        text = f"{title} {summary}".lower()
        
        # Financial terms for keyword extraction
        keywords = []
        financial_terms = [
            "earnings", "revenue", "profit", "loss", "growth", "decline",
            "merger", "acquisition", "ipo", "dividend", "buyback", "split",
            "expansion", "investment", "debt", "equity", "bond", "rating",
            "quarterly", "annual", "forecast", "guidance", "restructuring"
        ]
        
        for term in financial_terms:
            if term in text:
                keywords.append(term)
        
        return keywords[:10]


# Convenience function
def fetch_economic_times_news(symbol: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Quick function to fetch Economic Times news.
    
    Args:
        symbol: Stock symbol (optional, for stock-specific news)
        limit: Maximum articles
        
    Returns:
        List of news articles
    """
    scraper = EconomicTimesScraper()
    
    if symbol:
        return scraper.fetch_stock_news(symbol, limit=limit)
    else:
        return scraper.fetch_latest_news(limit=limit)


__all__ = [
    "EconomicTimesScraper",
    "fetch_economic_times_news",
]

