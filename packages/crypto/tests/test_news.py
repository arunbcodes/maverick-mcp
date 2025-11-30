"""Tests for crypto news module."""

import pytest
from datetime import datetime


class TestSentimentAnalyzer:
    """Test CryptoSentimentAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create sentiment analyzer."""
        from maverick_crypto.news import CryptoSentimentAnalyzer
        return CryptoSentimentAnalyzer()
    
    def test_bullish_headline(self, analyzer):
        """Test bullish headline detection."""
        result = analyzer.analyze("Bitcoin surges past $100k as ETF demand soars")
        
        assert result.score.value >= 4  # Bullish or very bullish
        assert result.confidence > 0.5
        assert len(result.keywords_found) > 0
    
    def test_bearish_headline(self, analyzer):
        """Test bearish headline detection."""
        result = analyzer.analyze("Crypto exchange hacked, millions lost in exploit")
        
        assert result.score.value <= 2  # Bearish or very bearish
        assert result.confidence > 0.5
    
    def test_neutral_headline(self, analyzer):
        """Test neutral headline detection."""
        result = analyzer.analyze("Blockchain technology explained in simple terms")
        
        assert result.score.value == 3  # Neutral
    
    def test_very_bullish_keywords(self, analyzer):
        """Test very bullish keywords."""
        result = analyzer.analyze("Bitcoin hits all-time high as institutional adoption accelerates")
        
        assert result.score.value == 5  # Very bullish
        assert "all-time high" in " ".join(result.keywords_found).lower() or "institutional adoption" in " ".join(result.keywords_found).lower()
    
    def test_very_bearish_keywords(self, analyzer):
        """Test very bearish keywords."""
        result = analyzer.analyze("Major rug pull scam causes crypto crash, investors face capitulation")
        
        assert result.score.value == 1  # Very bearish
    
    def test_empty_text(self, analyzer):
        """Test empty text handling."""
        result = analyzer.analyze("")
        
        assert result.score.value == 3  # Neutral
        assert result.confidence == 0.0
    
    def test_batch_analysis(self, analyzer):
        """Test batch analysis."""
        headlines = [
            "Bitcoin surges to new highs",
            "Crypto market crashes hard",
            "New blockchain update released",
        ]
        
        result = analyzer.analyze_batch(headlines)
        
        assert "overall_score" in result
        assert "distribution" in result
        assert result["analyzed_count"] == 3
    
    def test_market_sentiment(self, analyzer):
        """Test market sentiment analysis."""
        articles = [
            {"title": "Bitcoin rallies on positive news"},
            {"title": "ETH gains momentum"},
            {"title": "Crypto adoption grows"},
        ]
        
        result = analyzer.get_market_sentiment(articles)
        
        assert "sentiment" in result
        assert "score" in result
        assert "interpretation" in result


class TestSentimentScore:
    """Test SentimentScore enum."""
    
    def test_score_values(self):
        """Test score values."""
        from maverick_crypto.news import SentimentScore
        
        assert SentimentScore.VERY_BULLISH.value == 5
        assert SentimentScore.BULLISH.value == 4
        assert SentimentScore.NEUTRAL.value == 3
        assert SentimentScore.BEARISH.value == 2
        assert SentimentScore.VERY_BEARISH.value == 1
    
    def test_score_labels(self):
        """Test score labels."""
        from maverick_crypto.news import SentimentScore
        
        assert SentimentScore.VERY_BULLISH.label == "very bullish"
        assert SentimentScore.NEUTRAL.label == "neutral"


class TestNewsArticle:
    """Test NewsArticle dataclass."""
    
    def test_article_creation(self):
        """Test creating news article."""
        from maverick_crypto.news.providers import NewsArticle
        
        article = NewsArticle(
            title="Test Article",
            url="https://example.com",
            source="Test Source",
            published_at=datetime.now(),
            sentiment="bullish",
        )
        
        assert article.title == "Test Article"
        assert article.sentiment == "bullish"
    
    def test_article_to_dict(self):
        """Test article to_dict method."""
        from maverick_crypto.news.providers import NewsArticle
        
        article = NewsArticle(
            title="Test",
            url="https://example.com",
            source="Source",
            published_at=datetime.now(),
        )
        
        d = article.to_dict()
        
        assert d["title"] == "Test"
        assert d["url"] == "https://example.com"
        assert "published_at" in d


class TestCryptoPanicProvider:
    """Test CryptoPanic provider."""
    
    @pytest.fixture
    def provider(self):
        """Create provider."""
        from maverick_crypto.news import CryptoPanicProvider
        return CryptoPanicProvider()
    
    def test_provider_initialization(self, provider):
        """Test provider initializes correctly."""
        assert provider.base_url is not None
    
    def test_calculate_sentiment_bullish(self, provider):
        """Test bullish sentiment calculation."""
        votes = {"positive": 10, "negative": 2}
        sentiment = provider._calculate_sentiment(votes)
        
        assert sentiment == "bullish"
    
    def test_calculate_sentiment_bearish(self, provider):
        """Test bearish sentiment calculation."""
        votes = {"positive": 2, "negative": 10}
        sentiment = provider._calculate_sentiment(votes)
        
        assert sentiment == "bearish"
    
    def test_calculate_sentiment_neutral(self, provider):
        """Test neutral sentiment calculation."""
        votes = {"positive": 5, "negative": 5}
        sentiment = provider._calculate_sentiment(votes)
        
        assert sentiment == "neutral"
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_news(self, provider):
        """Test fetching news (external API)."""
        articles = await provider.get_news(limit=5)
        
        # May return empty if API unavailable
        assert isinstance(articles, list)


class TestNewsAggregator:
    """Test news aggregator."""
    
    @pytest.fixture
    def aggregator(self):
        """Create aggregator."""
        from maverick_crypto.news import NewsAggregator
        return NewsAggregator()
    
    def test_aggregator_initialization(self, aggregator):
        """Test aggregator initializes correctly."""
        assert aggregator.cryptopanic is not None
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_all_news(self, aggregator):
        """Test fetching news from all sources."""
        news = await aggregator.get_all_news(limit=5)
        
        assert isinstance(news, list)
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_news_summary(self, aggregator):
        """Test news summary."""
        summary = await aggregator.get_news_summary()
        
        assert "total_articles" in summary
        assert "overall_sentiment" in summary


class TestNewsImports:
    """Test news module imports."""
    
    def test_import_providers(self):
        """Test provider imports."""
        from maverick_crypto.news import CryptoPanicProvider, NewsAggregator
        assert CryptoPanicProvider is not None
        assert NewsAggregator is not None
    
    def test_import_sentiment(self):
        """Test sentiment imports."""
        from maverick_crypto.news import CryptoSentimentAnalyzer, SentimentScore
        assert CryptoSentimentAnalyzer is not None
        assert SentimentScore is not None

