"""Tests for NewsArticle database model."""

import pytest
from datetime import datetime, UTC, timedelta
from decimal import Decimal

from maverick_mcp.data.models import NewsArticle, SessionLocal


class TestNewsArticleModel:
    """Test suite for NewsArticle model."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        self.session = SessionLocal()
        yield
        # Cleanup test data
        self.session.query(NewsArticle).filter(
            NewsArticle.source.in_(["test_source", "moneycontrol_test"])
        ).delete()
        self.session.commit()
        self.session.close()
    
    def test_store_new_article(self):
        """Test storing a new news article."""
        article = NewsArticle.store_article(
            self.session,
            title="Reliance Industries Q4 Earnings Beat Expectations",
            url="https://example.com/article1",
            source="test_source",
            published_date=datetime.now(UTC),
            summary="Reliance posts strong Q4 results",
            symbol="RELIANCE.NS",
            sentiment="bullish",
            sentiment_score=0.75
        )
        
        assert article is not None
        assert article.title == "Reliance Industries Q4 Earnings Beat Expectations"
        assert article.symbol == "RELIANCE.NS"
        assert article.sentiment == "bullish"
        assert float(article.sentiment_score) == 0.75
    
    def test_update_existing_article(self):
        """Test updating an existing article by URL."""
        # Create initial article
        url = "https://example.com/article2"
        article1 = NewsArticle.store_article(
            self.session,
            title="Original Title",
            url=url,
            source="test_source",
            published_date=datetime.now(UTC),
            summary="Original summary",
            sentiment="neutral"
        )
        
        article_id = article1.article_id
        
        # Update the same article
        article2 = NewsArticle.store_article(
            self.session,
            title="Updated Title",
            url=url,  # Same URL triggers update
            source="test_source",
            published_date=datetime.now(UTC),
            summary="Updated summary",
            sentiment="bullish",
            sentiment_score=0.80
        )
        
        # Should be the same article
        assert article2.article_id == article_id
        assert article2.title == "Updated Title"
        assert article2.summary == "Updated summary"
        assert article2.sentiment == "bullish"
    
    def test_get_recent_articles_no_filter(self):
        """Test retrieving recent articles without filters."""
        # Create test articles
        now = datetime.now(UTC)
        
        for i in range(3):
            NewsArticle.store_article(
                self.session,
                title=f"Test Article {i}",
                url=f"https://example.com/article_{i}",
                source="test_source",
                published_date=now - timedelta(days=i),
                summary=f"Summary {i}"
            )
        
        # Retrieve recent articles
        articles = NewsArticle.get_recent_articles(self.session, days_back=7)
        
        assert len(articles) >= 3
        # Should be ordered by published_date desc
        assert articles[0].published_date >= articles[1].published_date
    
    def test_get_recent_articles_by_symbol(self):
        """Test retrieving articles filtered by symbol."""
        now = datetime.now(UTC)
        
        # Create articles for different symbols
        NewsArticle.store_article(
            self.session,
            title="Reliance News",
            url="https://example.com/reliance",
            source="test_source",
            published_date=now,
            symbol="RELIANCE.NS"
        )
        
        NewsArticle.store_article(
            self.session,
            title="TCS News",
            url="https://example.com/tcs",
            source="test_source",
            published_date=now,
            symbol="TCS.NS"
        )
        
        # Filter by symbol
        reliance_articles = NewsArticle.get_recent_articles(
            self.session,
            symbol="RELIANCE.NS",
            days_back=1
        )
        
        assert len(reliance_articles) >= 1
        assert all(a.symbol == "RELIANCE.NS" for a in reliance_articles)
    
    def test_get_recent_articles_by_source(self):
        """Test retrieving articles filtered by source."""
        now = datetime.now(UTC)
        
        # Create articles from different sources
        NewsArticle.store_article(
            self.session,
            title="MoneyControl Article",
            url="https://example.com/mc1",
            source="moneycontrol_test",
            published_date=now
        )
        
        NewsArticle.store_article(
            self.session,
            title="Test Source Article",
            url="https://example.com/test1",
            source="test_source",
            published_date=now
        )
        
        # Filter by source
        mc_articles = NewsArticle.get_recent_articles(
            self.session,
            source="moneycontrol_test",
            days_back=1
        )
        
        assert len(mc_articles) >= 1
        assert all(a.source == "moneycontrol_test" for a in mc_articles)
    
    def test_get_sentiment_summary_with_articles(self):
        """Test sentiment summary calculation with articles."""
        now = datetime.now(UTC)
        symbol = "TESTSTOCK.NS"
        
        # Create articles with different sentiments
        NewsArticle.store_article(
            self.session,
            title="Bullish News 1",
            url="https://example.com/bull1",
            source="test_source",
            published_date=now,
            symbol=symbol,
            sentiment="bullish",
            sentiment_score=0.8
        )
        
        NewsArticle.store_article(
            self.session,
            title="Bullish News 2",
            url="https://example.com/bull2",
            source="test_source",
            published_date=now,
            symbol=symbol,
            sentiment="bullish",
            sentiment_score=0.6
        )
        
        NewsArticle.store_article(
            self.session,
            title="Bearish News",
            url="https://example.com/bear1",
            source="test_source",
            published_date=now,
            symbol=symbol,
            sentiment="bearish",
            sentiment_score=-0.5
        )
        
        # Get sentiment summary
        summary = NewsArticle.get_sentiment_summary(self.session, symbol, days_back=1)
        
        assert summary["total_articles"] == 3
        assert summary["bullish"] == 2
        assert summary["bearish"] == 1
        assert summary["neutral"] == 0
        assert summary["overall_sentiment"] == "bullish"
        assert -1.0 <= summary["average_score"] <= 1.0
    
    def test_get_sentiment_summary_no_articles(self):
        """Test sentiment summary when no articles exist."""
        summary = NewsArticle.get_sentiment_summary(
            self.session,
            "NONEXISTENT.NS",
            days_back=7
        )
        
        assert summary["total_articles"] == 0
        assert summary["overall_sentiment"] == "neutral"
        assert summary["average_score"] == 0.0
    
    def test_to_dict(self):
        """Test converting article to dictionary."""
        now = datetime.now(UTC)
        article = NewsArticle.store_article(
            self.session,
            title="Test Article",
            url="https://example.com/dict_test",
            source="test_source",
            published_date=now,
            summary="Test summary",
            symbol="TEST.NS",
            sentiment="neutral",
            sentiment_score=0.0,
            category="earnings",
            keywords=["earnings", "revenue", "profit"]
        )
        
        article_dict = article.to_dict()
        
        assert article_dict["title"] == "Test Article"
        assert article_dict["url"] == "https://example.com/dict_test"
        assert article_dict["source"] == "test_source"
        assert article_dict["symbol"] == "TEST.NS"
        assert article_dict["sentiment"] == "neutral"
        assert article_dict["category"] == "earnings"
        assert article_dict["keywords"] == ["earnings", "revenue", "profit"]
        assert "article_id" in article_dict
        assert "published_date" in article_dict
    
    def test_article_repr(self):
        """Test article string representation."""
        now = datetime.now(UTC)
        article = NewsArticle.store_article(
            self.session,
            title="Test Article for Repr" * 5,  # Long title
            url="https://example.com/repr_test",
            source="test_source",
            published_date=now,
            sentiment="bullish"
        )
        
        repr_str = repr(article)
        
        assert "NewsArticle" in repr_str
        assert "test_source" in repr_str
        assert "bullish" in repr_str
        # Title should be truncated in repr
        assert len(repr_str) < 200

