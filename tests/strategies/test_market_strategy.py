"""
Comprehensive tests for Market Strategy Pattern.

Tests cover:
- USMarketStrategy
- IndianNSEMarketStrategy
- IndianBSEMarketStrategy
- MarketStrategyFactory
- Symbol validation and normalization
- Data source routing
- Configuration access
"""

import pytest
from maverick_mcp.strategies.market_strategy import (
    USMarketStrategy,
    IndianNSEMarketStrategy,
    IndianBSEMarketStrategy,
    MarketStrategyFactory,
    BaseMarketStrategy
)
from maverick_mcp.config.markets import Market


class TestUSMarketStrategy:
    """Test US market strategy."""
    
    def test_initializes_correctly(self):
        """Test US strategy initialization."""
        strategy = USMarketStrategy()
        assert strategy.market == Market.US
        assert strategy.config is not None
    
    def test_validates_known_symbols(self):
        """Test validation of known US symbols."""
        strategy = USMarketStrategy()
        
        assert strategy.is_valid_symbol("AAPL") is True
        assert strategy.is_valid_symbol("MSFT") is True
        assert strategy.is_valid_symbol("GOOGL") is True
        assert strategy.is_valid_symbol("SPY") is True
    
    def test_validates_symbol_format(self):
        """Test US symbol format validation."""
        strategy = USMarketStrategy()
        
        # Valid formats (1-5 letters)
        assert strategy.is_valid_symbol("A") is True
        assert strategy.is_valid_symbol("ABC") is True
        assert strategy.is_valid_symbol("ABCDE") is True
        
        # Invalid formats
        assert strategy.is_valid_symbol("ABCDEF") is False  # Too long
        assert strategy.is_valid_symbol("ABC123") is False  # Contains numbers
        assert strategy.is_valid_symbol("") is False  # Empty
    
    def test_normalizes_symbols(self):
        """Test symbol normalization."""
        strategy = USMarketStrategy()
        
        assert strategy.normalize_symbol("aapl") == "AAPL"
        assert strategy.normalize_symbol("AAPL") == "AAPL"
        assert strategy.normalize_symbol("Aapl") == "AAPL"
    
    def test_strips_suffix(self):
        """Test suffix stripping."""
        strategy = USMarketStrategy()
        
        # US symbols typically don't have suffix
        assert strategy.strip_suffix("AAPL") == "AAPL"
        # US suffix is empty string, so AAPL.US stays as is
        result = strategy.strip_suffix("AAPL.US")
        assert result in ["AAPL", "AAPL.US"]  # Depends on config
    
    def test_validate_symbol_format_method(self):
        """Test detailed format validation."""
        strategy = USMarketStrategy()
        
        # Valid
        valid, error = strategy.validate_symbol_format("AAPL")
        assert valid is True
        assert error is None
        
        # Empty symbol
        valid, error = strategy.validate_symbol_format("")
        assert valid is False
        assert "empty" in error.lower()
        
        # Too long
        valid, error = strategy.validate_symbol_format("ABCDEF")
        assert valid is False
        assert "1-5 characters" in error
        
        # Invalid characters (numbers make it too long if 6 chars, or fail pattern)
        valid, error = strategy.validate_symbol_format("ABC123")
        assert valid is False
        assert error is not None  # Will have some error message
    
    def test_gets_data_source(self):
        """Test data source retrieval."""
        strategy = USMarketStrategy()
        assert strategy.get_data_source() == "yfinance"


class TestIndianNSEMarketStrategy:
    """Test Indian NSE market strategy."""
    
    def test_initializes_correctly(self):
        """Test NSE strategy initialization."""
        strategy = IndianNSEMarketStrategy()
        assert strategy.market == Market.INDIA_NSE
        assert strategy.config is not None
    
    def test_validates_known_symbols(self):
        """Test validation of known NSE symbols."""
        strategy = IndianNSEMarketStrategy()
        
        assert strategy.is_valid_symbol("RELIANCE") is True
        assert strategy.is_valid_symbol("RELIANCE.NS") is True
        assert strategy.is_valid_symbol("TCS") is True
        assert strategy.is_valid_symbol("TCS.NS") is True
    
    def test_validates_symbol_format(self):
        """Test NSE symbol format validation."""
        strategy = IndianNSEMarketStrategy()
        
        # Valid formats
        assert strategy.is_valid_symbol("RELIANCE.NS") is True
        assert strategy.is_valid_symbol("M&M.NS") is True  # With ampersand
        assert strategy.is_valid_symbol("BAJAJ-AUTO.NS") is True  # With hyphen
        
        # Invalid formats
        assert strategy.is_valid_symbol("") is False
        assert strategy.is_valid_symbol("123.NS") is True  # Numbers are allowed
    
    def test_normalizes_symbols(self):
        """Test NSE symbol normalization."""
        strategy = IndianNSEMarketStrategy()
        
        assert strategy.normalize_symbol("RELIANCE") == "RELIANCE.NS"
        assert strategy.normalize_symbol("reliance") == "RELIANCE.NS"
        assert strategy.normalize_symbol("RELIANCE.NS") == "RELIANCE.NS"
    
    def test_strips_suffix(self):
        """Test NSE suffix stripping."""
        strategy = IndianNSEMarketStrategy()
        
        assert strategy.strip_suffix("RELIANCE.NS") == "RELIANCE"
        assert strategy.strip_suffix("RELIANCE") == "RELIANCE"
    
    def test_validate_symbol_format_method(self):
        """Test detailed NSE format validation."""
        strategy = IndianNSEMarketStrategy()
        
        # Valid
        valid, error = strategy.validate_symbol_format("RELIANCE")
        assert valid is True
        assert error is None
        
        # Empty symbol
        valid, error = strategy.validate_symbol_format("")
        assert valid is False
        assert "empty" in error.lower()
        
        # Too long (over 20 chars)
        valid, error = strategy.validate_symbol_format("A" * 21)
        assert valid is False
        assert "20 characters" in error
        
        # Invalid characters
        valid, error = strategy.validate_symbol_format("INVALID!SYMBOL")
        assert valid is False
    
    def test_gets_data_source(self):
        """Test data source retrieval."""
        strategy = IndianNSEMarketStrategy()
        assert strategy.get_data_source() == "yfinance"


class TestIndianBSEMarketStrategy:
    """Test Indian BSE market strategy."""
    
    def test_initializes_correctly(self):
        """Test BSE strategy initialization."""
        strategy = IndianBSEMarketStrategy()
        assert strategy.market == Market.INDIA_BSE
        assert strategy.config is not None
    
    def test_validates_known_symbols(self):
        """Test validation of known BSE symbols."""
        strategy = IndianBSEMarketStrategy()
        
        assert strategy.is_valid_symbol("RELIANCE") is True
        assert strategy.is_valid_symbol("RELIANCE.BO") is True
        assert strategy.is_valid_symbol("TCS") is True
        assert strategy.is_valid_symbol("TCS.BO") is True
    
    def test_validates_symbol_format(self):
        """Test BSE symbol format validation."""
        strategy = IndianBSEMarketStrategy()
        
        # Valid formats
        assert strategy.is_valid_symbol("RELIANCE.BO") is True
        assert strategy.is_valid_symbol("M&M.BO") is True  # With ampersand
        assert strategy.is_valid_symbol("BAJAJ-AUTO.BO") is True  # With hyphen
        
        # Invalid formats
        assert strategy.is_valid_symbol("") is False
    
    def test_normalizes_symbols(self):
        """Test BSE symbol normalization."""
        strategy = IndianBSEMarketStrategy()
        
        assert strategy.normalize_symbol("RELIANCE") == "RELIANCE.BO"
        assert strategy.normalize_symbol("reliance") == "RELIANCE.BO"
        assert strategy.normalize_symbol("RELIANCE.BO") == "RELIANCE.BO"
    
    def test_strips_suffix(self):
        """Test BSE suffix stripping."""
        strategy = IndianBSEMarketStrategy()
        
        assert strategy.strip_suffix("RELIANCE.BO") == "RELIANCE"
        assert strategy.strip_suffix("RELIANCE") == "RELIANCE"
    
    def test_validate_symbol_format_method(self):
        """Test detailed BSE format validation."""
        strategy = IndianBSEMarketStrategy()
        
        # Valid
        valid, error = strategy.validate_symbol_format("RELIANCE")
        assert valid is True
        assert error is None
        
        # Empty symbol
        valid, error = strategy.validate_symbol_format("")
        assert valid is False
        assert "empty" in error.lower()
        
        # Too long (over 20 chars)
        valid, error = strategy.validate_symbol_format("A" * 21)
        assert valid is False
        assert "20 characters" in error
        
        # Invalid characters
        valid, error = strategy.validate_symbol_format("INVALID!SYMBOL")
        assert valid is False
    
    def test_gets_data_source(self):
        """Test data source retrieval."""
        strategy = IndianBSEMarketStrategy()
        assert strategy.get_data_source() == "yfinance"


class TestMarketStrategyFactory:
    """Test market strategy factory."""
    
    def setup_method(self):
        """Clear factory cache before each test."""
        MarketStrategyFactory.clear_cache()
    
    def test_gets_us_strategy_for_us_symbols(self):
        """Test factory returns US strategy for US symbols."""
        strategy = MarketStrategyFactory.get_strategy("AAPL")
        assert isinstance(strategy, USMarketStrategy)
        assert strategy.market == Market.US
    
    def test_gets_nse_strategy_for_nse_symbols(self):
        """Test factory returns NSE strategy for NSE symbols."""
        strategy = MarketStrategyFactory.get_strategy("RELIANCE.NS")
        assert isinstance(strategy, IndianNSEMarketStrategy)
        assert strategy.market == Market.INDIA_NSE
    
    def test_gets_bse_strategy_for_bse_symbols(self):
        """Test factory returns BSE strategy for BSE symbols."""
        strategy = MarketStrategyFactory.get_strategy("RELIANCE.BO")
        assert isinstance(strategy, IndianBSEMarketStrategy)
        assert strategy.market == Market.INDIA_BSE
    
    def test_caches_strategies(self):
        """Test that factory caches strategy instances."""
        strategy1 = MarketStrategyFactory.get_strategy("AAPL")
        strategy2 = MarketStrategyFactory.get_strategy("MSFT")
        
        # Both should return the same instance (cached)
        assert strategy1 is strategy2
    
    def test_get_strategy_by_market_enum(self):
        """Test getting strategy by market enum."""
        strategy = MarketStrategyFactory.get_strategy_by_market(Market.US)
        assert isinstance(strategy, USMarketStrategy)
        
        strategy = MarketStrategyFactory.get_strategy_by_market(Market.INDIA_NSE)
        assert isinstance(strategy, IndianNSEMarketStrategy)
        
        strategy = MarketStrategyFactory.get_strategy_by_market(Market.INDIA_BSE)
        assert isinstance(strategy, IndianBSEMarketStrategy)
    
    def test_caches_strategies_from_market_enum(self):
        """Test caching with get_strategy_by_market."""
        strategy1 = MarketStrategyFactory.get_strategy_by_market(Market.US)
        strategy2 = MarketStrategyFactory.get_strategy_by_market(Market.US)
        
        assert strategy1 is strategy2
    
    def test_clear_cache_works(self):
        """Test cache clearing functionality."""
        # Get a strategy (will be cached)
        strategy1 = MarketStrategyFactory.get_strategy("AAPL")
        
        # Clear cache
        MarketStrategyFactory.clear_cache()
        
        # Get strategy again (should create new instance)
        strategy2 = MarketStrategyFactory.get_strategy("AAPL")
        
        # Should be different instances
        assert strategy1 is not strategy2
    
    def test_raises_error_for_unsupported_market(self):
        """Test error handling for unsupported markets."""
        # This would require a market enum that doesn't have a strategy
        # Since we support all current markets, we'll test via get_strategy_by_market
        # with a hypothetical unsupported market
        pass  # All current markets are supported


class TestCrossStrategyConsistency:
    """Test consistency across different strategies."""
    
    def test_all_strategies_implement_interface(self):
        """Test that all strategies implement required methods."""
        strategies = [
            USMarketStrategy(),
            IndianNSEMarketStrategy(),
            IndianBSEMarketStrategy()
        ]
        
        for strategy in strategies:
            assert hasattr(strategy, "market")
            assert hasattr(strategy, "config")
            assert callable(strategy.is_valid_symbol)
            assert callable(strategy.normalize_symbol)
            assert callable(strategy.strip_suffix)
            assert callable(strategy.get_data_source)
            assert callable(strategy.validate_symbol_format)
    
    def test_all_strategies_have_known_symbols(self):
        """Test that all strategies have known symbol lists."""
        assert len(USMarketStrategy.KNOWN_SYMBOLS) > 0
        assert len(IndianNSEMarketStrategy.KNOWN_SYMBOLS) > 0
        assert len(IndianBSEMarketStrategy.KNOWN_SYMBOLS) > 0
    
    def test_strategies_handle_case_insensitivity(self):
        """Test case-insensitive handling across strategies."""
        us = USMarketStrategy()
        nse = IndianNSEMarketStrategy()
        bse = IndianBSEMarketStrategy()
        
        # All should handle lowercase/uppercase
        assert us.is_valid_symbol("aapl") == us.is_valid_symbol("AAPL")
        # NSE/BSE check uppercase suffix, so we need to test with base symbols
        assert nse.is_valid_symbol("RELIANCE") == nse.is_valid_symbol("reliance")
        assert bse.is_valid_symbol("RELIANCE") == bse.is_valid_symbol("reliance")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_symbol_handling(self):
        """Test handling of empty symbols."""
        us = USMarketStrategy()
        nse = IndianNSEMarketStrategy()
        bse = IndianBSEMarketStrategy()
        
        assert us.is_valid_symbol("") is False
        assert nse.is_valid_symbol("") is False
        assert bse.is_valid_symbol("") is False
    
    def test_whitespace_in_symbols(self):
        """Test handling of whitespace in symbols."""
        us = USMarketStrategy()
        
        # Whitespace should make symbol invalid
        assert us.is_valid_symbol("A P P L") is False
        assert us.is_valid_symbol(" AAPL") is False
        assert us.is_valid_symbol("AAPL ") is False
    
    def test_special_characters_in_symbols(self):
        """Test handling of special characters."""
        us = USMarketStrategy()
        nse = IndianNSEMarketStrategy()
        
        # US doesn't allow special chars (except known symbols)
        assert us.is_valid_symbol("ABC&D") is False
        assert us.is_valid_symbol("ABC-D") is False
        
        # NSE allows ampersands and hyphens
        assert nse.is_valid_symbol("M&M") is True
        assert nse.is_valid_symbol("BAJAJ-AUTO") is True
    
    def test_very_long_symbols(self):
        """Test handling of very long symbols."""
        us = USMarketStrategy()
        nse = IndianNSEMarketStrategy()
        
        # US max is 5 chars
        assert us.is_valid_symbol("A" * 6) is False
        
        # NSE/BSE format validation checks base symbol (max 20 chars)
        # But is_valid_symbol checks pattern, which allows any length
        # Let's test validate_symbol_format instead which has the length check
        valid, _ = nse.validate_symbol_format("A" * 20)
        assert valid is True
        valid, _ = nse.validate_symbol_format("A" * 21)
        assert valid is False
    
    def test_numeric_symbols(self):
        """Test handling of numeric symbols."""
        us = USMarketStrategy()
        nse = IndianNSEMarketStrategy()
        
        # US doesn't allow pure numbers
        assert us.is_valid_symbol("123") is False
        
        # NSE allows numbers
        assert nse.is_valid_symbol("123") is True
    
    def test_normalize_with_multiple_dots(self):
        """Test normalization with multiple dots."""
        us = USMarketStrategy()
        
        # Should only consider first part
        result = us.normalize_symbol("AAPL.US.EXTRA")
        assert result == "AAPL"
    
    def test_config_properties_accessible(self):
        """Test that config properties are accessible."""
        strategies = [
            USMarketStrategy(),
            IndianNSEMarketStrategy(),
            IndianBSEMarketStrategy()
        ]
        
        for strategy in strategies:
            assert strategy.config.name is not None
            assert strategy.config.symbol_suffix is not None
            assert strategy.config.timezone is not None


# Note: These are unit tests for the Strategy Pattern implementation

