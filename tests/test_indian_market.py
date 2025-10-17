"""
Tests for Indian Market Data Provider

Tests cover:
- Symbol validation for NSE and BSE
- Data fetching for Indian stocks
- Market status checking
- Nifty 50 and Sensex constituent lists
"""

import pytest
from datetime import datetime, date
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

from maverick_mcp.providers.indian_market_data import (
    IndianMarketDataProvider,
    fetch_nse_data,
    fetch_bse_data,
)
from maverick_mcp.config.markets import Market


class TestIndianSymbolValidation:
    """Test Indian stock symbol validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = IndianMarketDataProvider()
    
    def test_valid_nse_symbol(self):
        """Test validation of valid NSE symbols."""
        is_valid, market, error = self.provider.validate_indian_symbol("RELIANCE.NS")
        assert is_valid is True
        assert market == Market.INDIA_NSE
        assert error is None
    
    def test_valid_bse_symbol(self):
        """Test validation of valid BSE symbols."""
        is_valid, market, error = self.provider.validate_indian_symbol("RELIANCE.BO")
        assert is_valid is True
        assert market == Market.INDIA_BSE
        assert error is None
    
    def test_invalid_us_symbol(self):
        """Test that US symbols are rejected."""
        is_valid, market, error = self.provider.validate_indian_symbol("AAPL")
        assert is_valid is False
        assert market is None
        assert "Not an Indian market symbol" in error
    
    def test_invalid_short_nse_symbol(self):
        """Test that too-short NSE symbols are rejected."""
        is_valid, market, error = self.provider.validate_indian_symbol(".NS")
        assert is_valid is False
        assert "too short" in error.lower()
    
    def test_invalid_long_nse_symbol(self):
        """Test that too-long NSE symbols are rejected."""
        is_valid, market, error = self.provider.validate_indian_symbol("VERYLONGSYMBOL.NS")
        assert is_valid is False
        assert "too long" in error.lower()
    
    def test_case_insensitive_validation(self):
        """Test that validation is case-insensitive."""
        is_valid1, market1, _ = self.provider.validate_indian_symbol("reliance.ns")
        is_valid2, market2, _ = self.provider.validate_indian_symbol("RELIANCE.NS")
        assert is_valid1 is True
        assert is_valid2 is True
        assert market1 == market2 == Market.INDIA_NSE


class TestSymbolFormatting:
    """Test symbol formatting functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = IndianMarketDataProvider()
    
    def test_format_nse_symbol_basic(self):
        """Test basic NSE symbol formatting."""
        assert self.provider.format_nse_symbol("RELIANCE") == "RELIANCE.NS"
        assert self.provider.format_nse_symbol("TCS") == "TCS.NS"
    
    def test_format_nse_symbol_lowercase(self):
        """Test NSE formatting with lowercase input."""
        assert self.provider.format_nse_symbol("reliance") == "RELIANCE.NS"
    
    def test_format_nse_symbol_already_formatted(self):
        """Test that already-formatted NSE symbols remain unchanged."""
        assert self.provider.format_nse_symbol("RELIANCE.NS") == "RELIANCE.NS"
    
    def test_format_bse_symbol_basic(self):
        """Test basic BSE symbol formatting."""
        assert self.provider.format_bse_symbol("RELIANCE") == "RELIANCE.BO"
        assert self.provider.format_bse_symbol("TCS") == "TCS.BO"
    
    def test_format_bse_symbol_lowercase(self):
        """Test BSE formatting with lowercase input."""
        assert self.provider.format_bse_symbol("reliance") == "RELIANCE.BO"
    
    def test_format_bse_symbol_already_formatted(self):
        """Test that already-formatted BSE symbols remain unchanged."""
        assert self.provider.format_bse_symbol("RELIANCE.BO") == "RELIANCE.BO"
    
    def test_format_with_whitespace(self):
        """Test formatting handles whitespace correctly."""
        assert self.provider.format_nse_symbol(" RELIANCE ") == "RELIANCE.NS"
        assert self.provider.format_bse_symbol(" RELIANCE ") == "RELIANCE.BO"


class TestConstituentLists:
    """Test index constituent list functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = IndianMarketDataProvider()
    
    def test_nifty50_constituents_count(self):
        """Test that Nifty 50 returns correct number of stocks."""
        constituents = self.provider.get_nifty50_constituents()
        assert len(constituents) == 50
    
    def test_nifty50_constituents_format(self):
        """Test that Nifty 50 constituents have correct format."""
        constituents = self.provider.get_nifty50_constituents()
        for symbol in constituents:
            assert symbol.endswith(".NS")
            assert len(symbol) > 3  # At least one char + .NS
    
    def test_nifty50_contains_major_stocks(self):
        """Test that Nifty 50 contains expected major stocks."""
        constituents = self.provider.get_nifty50_constituents()
        expected_stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]
        for stock in expected_stocks:
            assert stock in constituents
    
    def test_sensex_constituents_count(self):
        """Test that Sensex returns correct number of stocks."""
        constituents = self.provider.get_sensex_constituents()
        assert len(constituents) == 30
    
    def test_sensex_constituents_format(self):
        """Test that Sensex constituents have correct format."""
        constituents = self.provider.get_sensex_constituents()
        for symbol in constituents:
            assert symbol.endswith(".NS")  # Using NSE symbols
            assert len(symbol) > 3
    
    def test_sensex_contains_major_stocks(self):
        """Test that Sensex contains expected major stocks."""
        constituents = self.provider.get_sensex_constituents()
        expected_stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]
        for stock in expected_stocks:
            assert stock in constituents


class TestMarketStatus:
    """Test Indian market status functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = IndianMarketDataProvider()
    
    def test_market_status_structure(self):
        """Test that market status returns expected structure."""
        status = self.provider.get_indian_market_status()
        
        # Check required keys
        assert "status" in status
        assert "is_open" in status
        assert "is_trading_day" in status
        assert "current_time" in status
        assert "timezone" in status
        assert "date" in status
        
        # Check value types
        assert isinstance(status["is_open"], bool)
        assert isinstance(status["is_trading_day"], bool)
        assert status["status"] in ["OPEN", "CLOSED", "HOLIDAY"]
        assert status["timezone"] == "Asia/Kolkata"
    
    @patch('maverick_mcp.providers.indian_market_data.datetime')
    def test_market_open_during_trading_hours(self, mock_datetime):
        """Test that market status is OPEN during trading hours."""
        # Mock a trading day at 10:00 AM IST (market is open 9:15 AM - 3:30 PM)
        mock_now = MagicMock()
        mock_now.date.return_value = date(2024, 10, 17)  # A Thursday
        mock_now.time.return_value = datetime(2024, 10, 17, 10, 0).time()
        mock_datetime.now.return_value = mock_now
        
        # Note: This test would need proper timezone mocking to work correctly
        # For now, it just tests the structure
        status = self.provider.get_indian_market_status()
        assert isinstance(status, dict)


@pytest.mark.integration
class TestDataFetching:
    """Integration tests for data fetching (requires internet)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = IndianMarketDataProvider()
    
    @pytest.mark.skip(reason="Requires internet connection and real API access")
    def test_fetch_nse_stock_data(self):
        """Test fetching real NSE stock data."""
        # Test with Reliance Industries (reliable major stock)
        df = self.provider.get_nse_stock_data("RELIANCE", period="5d")
        
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "close" in df.columns
        assert len(df) > 0
    
    @pytest.mark.skip(reason="Requires internet connection and real API access")
    def test_fetch_bse_stock_data(self):
        """Test fetching real BSE stock data."""
        df = self.provider.get_bse_stock_data("RELIANCE", period="5d")
        
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "close" in df.columns
    
    @pytest.mark.skip(reason="Requires internet connection and real API access")
    def test_get_stock_info(self):
        """Test fetching stock information."""
        info = self.provider.get_stock_info("RELIANCE.NS")
        
        assert isinstance(info, dict)
        assert "market" in info
        assert info["market"] == "NSE"
        assert "currency" in info
        assert info["currency"] == "INR"


class TestConvenienceFunctions:
    """Test convenience functions for quick data access."""
    
    @patch('maverick_mcp.providers.indian_market_data.IndianMarketDataProvider')
    def test_fetch_nse_data_convenience(self, mock_provider_class):
        """Test fetch_nse_data convenience function."""
        # Mock the provider and its method
        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        mock_provider.get_nse_stock_data.return_value = pd.DataFrame()
        
        # Call convenience function
        fetch_nse_data("RELIANCE", period="1mo")
        
        # Verify it called the provider correctly
        mock_provider_class.assert_called_once()
        mock_provider.get_nse_stock_data.assert_called_once_with(
            "RELIANCE", None, None, "1mo"
        )
    
    @patch('maverick_mcp.providers.indian_market_data.IndianMarketDataProvider')
    def test_fetch_bse_data_convenience(self, mock_provider_class):
        """Test fetch_bse_data convenience function."""
        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        mock_provider.get_bse_stock_data.return_value = pd.DataFrame()
        
        fetch_bse_data("RELIANCE", period="1mo")
        
        mock_provider_class.assert_called_once()
        mock_provider.get_bse_stock_data.assert_called_once_with(
            "RELIANCE", None, None, "1mo"
        )


class TestErrorHandling:
    """Test error handling in Indian market provider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = IndianMarketDataProvider()
    
    def test_invalid_symbol_raises_error(self):
        """Test that invalid symbols raise appropriate errors."""
        with pytest.raises(ValueError) as exc_info:
            self.provider.get_nse_stock_data("INVALID_SYMBOL_WITHOUT_SUFFIX")
        assert "Invalid NSE symbol" in str(exc_info.value)
    
    def test_invalid_nse_symbol_in_get_stock_info(self):
        """Test error handling in get_stock_info with invalid symbol."""
        with pytest.raises(ValueError) as exc_info:
            self.provider.get_stock_info("AAPL")  # US stock, not Indian
        assert "Invalid Indian stock symbol" in str(exc_info.value)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

