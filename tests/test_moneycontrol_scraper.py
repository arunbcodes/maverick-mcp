"""Tests for MoneyControl scraper."""

import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch, MagicMock

from maverick_mcp.providers.moneycontrol_scraper import MoneyControlScraper, fetch_moneycontrol_news


class TestMoneyControlScraper:
    """Test suite for MoneyControl scraper."""
    
    @pytest.fixture
    def scraper(self):
        """Create scraper instance without database."""
        return MoneyControlScraper(use_db=False, cache_ttl=60)
    
    def test_initialization(self, scraper):
        """Test scraper initialization."""
        assert scraper.use_db is False
        assert scraper.cache.ttl == 60
        assert scraper.session is not None
        assert "User-Agent" in scraper.session.headers
    
    def test_sentiment_analysis_bullish(self, scraper):
        """Test sentiment analysis with bullish text."""
        text = "Company reports record profit and strong revenue growth. Earnings beat expectations."
        
        result = scraper.analyze_sentiment(text)
        
        assert result["sentiment"] == "bullish"
        assert result["sentiment_score"] > 0
        assert result["bullish_keywords"] > 0
        assert 0 <= result["confidence"] <= 1
    
    def test_sentiment_analysis_bearish(self, scraper):
        """Test sentiment analysis with bearish text."""
        text = "Stock falls sharply on disappointing earnings. Company faces loss and decline in revenue."
        
        result = scraper.analyze_sentiment(text)
        
        assert result["sentiment"] == "bearish"
        assert result["sentiment_score"] < 0
        assert result["bearish_keywords"] > 0
        assert 0 <= result["confidence"] <= 1
    
    def test_sentiment_analysis_neutral(self, scraper):
        """Test sentiment analysis with neutral text."""
        text = "Company announces quarterly results. Market remains stable."
        
        result = scraper.analyze_sentiment(text)
        
        assert result["sentiment"] == "neutral"
        assert -0.2 <= result["sentiment_score"] <= 0.2
        assert 0 <= result["confidence"] <= 1
    
    def test_extract_keywords(self, scraper):
        """Test keyword extraction."""
        title = "Company Reports Strong Earnings"
        summary = "Revenue growth exceeds expectations with profit margin expansion"
        
        keywords = scraper._extract_keywords(title, summary)
        
        assert isinstance(keywords, list)
        assert "earnings" in keywords
        assert "revenue" in keywords
        assert "profit" in keywords
        assert "growth" in keywords
        assert len(keywords) <= 10
    
    def test_get_company_name(self, scraper):
        """Test company name mapping."""
        assert scraper._get_company_name("RELIANCE") == "Reliance Industries"
        assert scraper._get_company_name("TCS") == "Tata Consultancy Services"
        assert scraper._get_company_name("INFY") == "Infosys"
        assert scraper._get_company_name("UNKNOWN") is None
    
    def test_mentions_stock_by_symbol(self, scraper):
        """Test stock mention detection by symbol."""
        article = {
            "title": "RELIANCE announces Q4 results",
            "summary": "Strong performance in petrochemicals"
        }
        
        assert scraper._mentions_stock(article, "RELIANCE", None) is True
        assert scraper._mentions_stock(article, "TCS", None) is False
    
    def test_mentions_stock_by_company_name(self, scraper):
        """Test stock mention detection by company name."""
        article = {
            "title": "Reliance Industries posts record profit",
            "summary": "Company beats market expectations"
        }
        
        assert scraper._mentions_stock(article, "REL", "Reliance Industries") is True
        assert scraper._mentions_stock(article, "TCS", "Tata Consultancy Services") is False
    
    @patch('maverick_mcp.providers.moneycontrol_scraper.feedparser')
    def test_fetch_latest_news_success(self, mock_feedparser, scraper):
        """Test fetching latest news from RSS feed."""
        # Mock RSS feed response
        mock_entry = Mock()
        mock_entry.title = "Test Article Title"
        mock_entry.link = "https://www.moneycontrol.com/article1"
        mock_entry.summary = "Test article summary"
        mock_entry.published_parsed = (2025, 10, 19, 12, 0, 0, 0, 0, 0)
        
        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_feedparser.parse.return_value = mock_feed
        
        articles = scraper.fetch_latest_news(category="latest", limit=1)
        
        assert len(articles) == 1
        assert articles[0]["title"] == "Test Article Title"
        assert articles[0]["source"] == "moneycontrol"
        assert "sentiment" in articles[0]
        assert "sentiment_score" in articles[0]
    
    @patch('maverick_mcp.providers.moneycontrol_scraper.feedparser')
    def test_fetch_latest_news_caching(self, mock_feedparser, scraper):
        """Test that news fetching uses cache."""
        mock_feed = Mock()
        mock_feed.entries = []
        mock_feedparser.parse.return_value = mock_feed
        
        # First call
        scraper.fetch_latest_news(category="latest", limit=10)
        assert mock_feedparser.parse.call_count == 1
        
        # Second call should use cache
        scraper.fetch_latest_news(category="latest", limit=10, use_cache=True)
        assert mock_feedparser.parse.call_count == 1  # Still 1, not 2
    
    @patch('maverick_mcp.providers.moneycontrol_scraper.feedparser')
    def test_fetch_latest_news_no_cache(self, mock_feedparser, scraper):
        """Test that caching can be disabled."""
        mock_feed = Mock()
        mock_feed.entries = []
        mock_feedparser.parse.return_value = mock_feed
        
        # Two calls without cache
        scraper.fetch_latest_news(category="latest", limit=10, use_cache=False)
        scraper.fetch_latest_news(category="latest", limit=10, use_cache=False)
        
        assert mock_feedparser.parse.call_count == 2
    
    @patch('maverick_mcp.providers.moneycontrol_scraper.feedparser')
    def test_fetch_latest_news_empty_feed(self, mock_feedparser, scraper):
        """Test handling of empty RSS feed."""
        mock_feed = Mock()
        mock_feed.entries = []
        mock_feedparser.parse.return_value = mock_feed
        
        articles = scraper.fetch_latest_news()
        
        assert articles == []
    
    @patch('maverick_mcp.providers.moneycontrol_scraper.feedparser')
    def test_fetch_latest_news_error_handling(self, mock_feedparser, scraper):
        """Test error handling when RSS parsing fails."""
        mock_feedparser.parse.side_effect = Exception("Network error")
        
        articles = scraper.fetch_latest_news()
        
        assert articles == []  # Should return empty list on error
    
    @patch.object(MoneyControlScraper, 'fetch_latest_news')
    def test_fetch_stock_news(self, mock_fetch_latest, scraper):
        """Test fetching stock-specific news."""
        # Mock general news that mentions Reliance
        mock_articles = [
            {
                "title": "Reliance Industries announces expansion",
                "summary": "New petrochemical plant",
                "url": "https://example.com/1"
            },
            {
                "title": "TCS wins major contract",
                "summary": "IT services growth",
                "url": "https://example.com/2"
            },
            {
                "title": "Reliance posts strong Q4",
                "summary": "Revenue beats estimates",
                "url": "https://example.com/3"
            }
        ]
        mock_fetch_latest.return_value = mock_articles
        
        articles = scraper.fetch_stock_news("RELIANCE.NS", limit=2)
        
        # Should filter and return only Reliance articles
        assert len(articles) <= 2
        assert all("RELIANCE" in a["title"] or "Reliance" in a["title"] for a in articles)
        assert all(a["symbol"] == "RELIANCE.NS" for a in articles)
    
    @patch('maverick_mcp.providers.moneycontrol_scraper.requests.Session')
    def test_scrape_article_content_success(self, mock_session_class, scraper):
        """Test successful article content scraping."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <html>
            <div class="content_wrapper">
                <p>First paragraph of article.</p>
                <p>Second paragraph with more details.</p>
            </div>
        </html>
        """
        
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        scraper.session = mock_session
        
        content = scraper.scrape_article_content("https://example.com/article")
        
        assert content is not None
        assert "First paragraph" in content
        assert "Second paragraph" in content
    
    @patch('maverick_mcp.providers.moneycontrol_scraper.requests.Session')
    def test_scrape_article_content_failure(self, mock_session_class, scraper):
        """Test article scraping failure handling."""
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Network error")
        scraper.session = mock_session
        
        content = scraper.scrape_article_content("https://example.com/article")
        
        assert content is None
    
    def test_parse_rss_entry(self, scraper):
        """Test RSS entry parsing."""
        mock_entry = Mock()
        mock_entry.title = "Test Article"
        mock_entry.link = "https://example.com/test"
        mock_entry.summary = "Test summary"
        mock_entry.published_parsed = (2025, 10, 19, 12, 0, 0, 0, 0, 0)
        
        article = scraper._parse_rss_entry(mock_entry, "stocks")
        
        assert article is not None
        assert article["title"] == "Test Article"
        assert article["url"] == "https://example.com/test"
        assert article["source"] == "moneycontrol"
        assert article["category"] == "stocks"
        assert "sentiment" in article
        assert "keywords" in article
    
    def test_convenience_function(self):
        """Test convenience function for fetching news."""
        with patch.object(MoneyControlScraper, 'fetch_latest_news', return_value=[]):
            articles = fetch_moneycontrol_news(limit=5)
            assert isinstance(articles, list)
        
        with patch.object(MoneyControlScraper, 'fetch_stock_news', return_value=[]):
            articles = fetch_moneycontrol_news(symbol="RELIANCE.NS", limit=5)
            assert isinstance(articles, list)

