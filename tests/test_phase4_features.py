"""
Tests for Phase 4 Features

Covers:
- Currency conversion
- Market comparison
- Indian news provider  
- RBI data provider integration
"""

import pytest
from datetime import datetime


class TestCurrencyConverter:
    """Test currency conversion functionality"""
    
    def test_currency_converter_initialization(self):
        """Test that CurrencyConverter initializes correctly"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter()
        assert converter is not None
        assert converter.default_usd_inr_rate > 0
    
    def test_inr_to_usd_conversion(self):
        """Test converting INR to USD"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter()
        result = converter.convert(100, "INR", "USD")
        
        assert result > 0
        assert result < 100  # INR is less valuable than USD
        assert isinstance(result, float)
    
    def test_usd_to_inr_conversion(self):
        """Test converting USD to INR"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter()
        result = converter.convert(100, "USD", "INR")
        
        assert result > 100  # Should get more INR for USD
        assert isinstance(result, float)
    
    def test_same_currency_conversion(self):
        """Test converting same currency returns same amount"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter()
        result = converter.convert(100, "USD", "USD")
        
        assert result == 100.0
    
    def test_get_exchange_rate(self):
        """Test getting exchange rate"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter()
        rate = converter.get_exchange_rate("USD", "INR")
        
        assert rate > 0
        assert isinstance(rate, float)
    
    def test_convert_currency_function(self):
        """Test convenience function"""
        from maverick_mcp.utils.currency_converter import convert_currency
        
        result = convert_currency(1000, "INR", "USD")
        assert result > 0


class TestMarketComparison:
    """Test market comparison functionality"""
    
    def test_analyzer_initialization(self):
        """Test that MarketComparisonAnalyzer initializes correctly"""
        from maverick_mcp.analysis.market_comparison import MarketComparisonAnalyzer
        
        analyzer = MarketComparisonAnalyzer()
        assert analyzer is not None
        assert analyzer.us_provider is not None
        assert analyzer.indian_provider is not None
        assert analyzer.currency_converter is not None
    
    def test_calculate_correlation(self):
        """Test correlation calculation with sample data"""
        import pandas as pd
        from maverick_mcp.analysis.market_comparison import MarketComparisonAnalyzer
        
        analyzer = MarketComparisonAnalyzer()
        
        # Create sample data
        series1 = pd.Series([100, 102, 105, 103, 107])
        series2 = pd.Series([200, 204, 210, 206, 214])
        
        correlation = analyzer._calculate_correlation(series1, series2)
        
        assert -1 <= correlation <= 1
        assert isinstance(correlation, float)
    
    def test_compare_us_indian_markets_function(self):
        """Test convenience function for market comparison"""
        from maverick_mcp.analysis.market_comparison import compare_us_indian_markets
        
        # This is a smoke test - it may fail if network is unavailable
        result = compare_us_indian_markets("1m")
        assert result is not None
        assert isinstance(result, dict)


class TestIndianNewsProvider:
    """Test Indian news provider functionality"""
    
    def test_provider_initialization(self):
        """Test that IndianNewsProvider initializes correctly"""
        from maverick_mcp.providers.indian_news import IndianNewsProvider
        
        provider = IndianNewsProvider()
        assert provider is not None
        assert len(provider.sources) > 0
    
    def test_get_stock_news(self):
        """Test getting stock news (placeholder data)"""
        from maverick_mcp.providers.indian_news import IndianNewsProvider
        
        provider = IndianNewsProvider()
        news = provider.get_stock_news("RELIANCE.NS", limit=5)
        
        assert isinstance(news, list)
        assert len(news) <= 5
        
        if news:
            article = news[0]
            assert "title" in article
            assert "source" in article
            assert "sentiment" in article
    
    def test_get_market_news(self):
        """Test getting market news (placeholder data)"""
        from maverick_mcp.providers.indian_news import IndianNewsProvider
        
        provider = IndianNewsProvider()
        news = provider.get_market_news(category="all", limit=10)
        
        assert isinstance(news, list)
        assert len(news) <= 10
    
    def test_analyze_sentiment(self):
        """Test sentiment analysis"""
        from maverick_mcp.providers.indian_news import IndianNewsProvider
        
        provider = IndianNewsProvider()
        sentiment = provider.analyze_sentiment("TCS.NS")
        
        assert isinstance(sentiment, dict)
        assert "symbol" in sentiment
        assert "sentiment_score" in sentiment
        
        if "sentiment_score" in sentiment:
            score = sentiment["sentiment_score"]
            assert -1 <= score <= 1
    
    def test_get_trending_topics(self):
        """Test getting trending topics"""
        from maverick_mcp.providers.indian_news import IndianNewsProvider
        
        provider = IndianNewsProvider()
        topics = provider.get_trending_topics(limit=5)
        
        assert isinstance(topics, list)
        assert len(topics) <= 5
    
    def test_classify_sentiment(self):
        """Test sentiment classification"""
        from maverick_mcp.providers.indian_news import IndianNewsProvider
        
        provider = IndianNewsProvider()
        
        assert provider._classify_sentiment(0.5) == "bullish"
        assert provider._classify_sentiment(-0.5) == "bearish"
        assert provider._classify_sentiment(0.1) == "neutral"


class TestRBIDataProvider:
    """Test RBI data provider functionality"""
    
    def test_provider_initialization(self):
        """Test that RBIDataProvider initializes correctly"""
        from maverick_mcp.providers.rbi_data import RBIDataProvider
        
        provider = RBIDataProvider()
        assert provider is not None
        assert provider.cache is not None
    
    def test_get_policy_rates(self):
        """Test getting RBI policy rates"""
        from maverick_mcp.providers.rbi_data import RBIDataProvider
        
        provider = RBIDataProvider()
        rates = provider.get_policy_rates()
        
        assert isinstance(rates, dict)
        assert "repo_rate" in rates
        assert rates["repo_rate"] > 0
    
    def test_get_gdp_growth(self):
        """Test getting GDP growth data"""
        from maverick_mcp.providers.rbi_data import RBIDataProvider
        
        provider = RBIDataProvider()
        gdp = provider.get_gdp_growth()
        
        assert isinstance(gdp, dict)
        # May return error if World Bank API is unreachable
        assert "status" in gdp or "current" in gdp
    
    def test_get_forex_reserves(self):
        """Test getting forex reserves"""
        from maverick_mcp.providers.rbi_data import RBIDataProvider
        
        provider = RBIDataProvider()
        reserves = provider.get_forex_reserves()
        
        assert isinstance(reserves, dict)
        # May return error if API is unreachable
        assert "status" in reserves or "total_reserves_usd" in reserves
    
    def test_get_economic_calendar(self):
        """Test getting economic calendar"""
        from maverick_mcp.providers.rbi_data import RBIDataProvider
        
        provider = RBIDataProvider()
        calendar = provider.get_economic_calendar(days_ahead=30)
        
        assert isinstance(calendar, list)
        
        if calendar:
            event = calendar[0]
            assert "date" in event
            assert "event" in event
            assert "importance" in event
    
    def test_get_all_indicators(self):
        """Test getting all indicators at once"""
        from maverick_mcp.providers.rbi_data import RBIDataProvider
        
        provider = RBIDataProvider()
        indicators = provider.get_all_indicators()
        
        assert isinstance(indicators, dict)
        assert "policy_rates" in indicators
        assert "gdp_growth" in indicators
        assert "forex_reserves" in indicators
        assert "economic_calendar" in indicators
    
    def test_parse_period(self):
        """Test period parsing helper"""
        from maverick_mcp.providers.rbi_data import RBIDataProvider
        
        provider = RBIDataProvider()
        
        assert provider._parse_period("1m") == 30
        assert provider._parse_period("3m") == 90
        assert provider._parse_period("1y") == 365
        assert provider._parse_period("5y") == 1825


class TestPhase4Integration:
    """Integration tests for Phase 4 features"""
    
    def test_all_providers_work_together(self):
        """Test that all Phase 4 providers can be used together"""
        from maverick_mcp.providers.rbi_data import RBIDataProvider
        from maverick_mcp.providers.indian_news import IndianNewsProvider
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        # Initialize all providers
        rbi = RBIDataProvider()
        news = IndianNewsProvider()
        converter = CurrencyConverter()
        
        # Test basic operations
        rates = rbi.get_policy_rates()
        articles = news.get_market_news(limit=5)
        conversion = converter.convert(1000, "INR", "USD")
        
        assert rates is not None
        assert isinstance(articles, list)
        assert conversion > 0
    
    def test_cross_provider_data_flow(self):
        """Test using data from one provider in another"""
        from maverick_mcp.providers.rbi_data import RBIDataProvider
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        rbi = RBIDataProvider()
        converter = CurrencyConverter()
        
        # Get forex reserves (in USD)
        reserves = rbi.get_forex_reserves()
        
        # Convert to INR if available
        if "total_reserves_usd" in reserves:
            usd_amount = reserves["total_reserves_usd"]
            inr_amount = converter.convert(usd_amount, "USD", "INR")
            assert inr_amount > usd_amount


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

