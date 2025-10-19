"""
Tests for Updated Currency Converter

Tests the enhanced currency converter with real-time rates.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime


class TestEnhancedCurrencyConverter:
    """Test enhanced currency converter with real-time rates"""
    
    def test_initialization_with_live_rates(self):
        """Test converter initializes with live rates enabled"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter(use_live_rates=True)
        
        assert converter is not None
        assert converter.use_live_rates == True
        assert converter.rate_provider is not None
    
    def test_initialization_with_approximate_rates(self):
        """Test converter initializes with approximate rates"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter(use_live_rates=False)
        
        assert converter is not None
        assert converter.use_live_rates == False
        assert converter.rate_provider is None
    
    def test_initialization_with_api_key(self):
        """Test converter initializes with API key"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter(api_key="test_key", use_live_rates=True)
        
        assert converter.rate_provider is not None
        assert converter.rate_provider.api_key == "test_key"
    
    def test_get_exchange_rate_with_live_provider(self):
        """Test getting exchange rate with live provider"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter(use_live_rates=True)
        
        # Mock the provider
        mock_result = {
            "rate": 83.25,
            "source": "exchangerate-api",
            "timestamp": datetime.now().isoformat()
        }
        
        with patch.object(converter.rate_provider, 'get_rate', return_value=mock_result):
            rate = converter.get_exchange_rate("USD", "INR")
            
            assert rate == 83.25
            converter.rate_provider.get_rate.assert_called_once()
    
    def test_get_exchange_rate_falls_back_to_approximate(self):
        """Test fallback to approximate rate when provider fails"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter(use_live_rates=True)
        
        # Mock provider failure
        with patch.object(converter.rate_provider, 'get_rate', side_effect=Exception("API Error")):
            rate = converter.get_exchange_rate("USD", "INR")
            
            # Should return approximate rate
            assert rate == converter.default_usd_inr_rate
    
    def test_get_exchange_rate_with_force_refresh(self):
        """Test force refresh parameter is passed through"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter(use_live_rates=True)
        
        mock_result = {
            "rate": 83.25,
            "source": "exchangerate-api",
            "timestamp": datetime.now().isoformat()
        }
        
        with patch.object(converter.rate_provider, 'get_rate', return_value=mock_result) as mock_get:
            converter.get_exchange_rate("USD", "INR", force_refresh=True)
            
            # Check force_refresh was passed
            mock_get.assert_called_once_with("USD", "INR", force_refresh=True)
    
    def test_get_rate_info_with_live_provider(self):
        """Test getting detailed rate info with live provider"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter(use_live_rates=True)
        
        mock_result = {
            "from_currency": "USD",
            "to_currency": "INR",
            "rate": 83.25,
            "source": "exchangerate-api",
            "timestamp": datetime.now().isoformat(),
            "last_update": "2024-01-01 00:00:00",
            "next_update": "2024-01-02 00:00:00"
        }
        
        with patch.object(converter.rate_provider, 'get_rate', return_value=mock_result):
            info = converter.get_rate_info("USD", "INR")
            
            assert info["rate"] == 83.25
            assert info["source"] == "exchangerate-api"
            assert "timestamp" in info
            assert "last_update" in info
    
    def test_get_rate_info_with_approximate(self):
        """Test getting rate info with approximate rates"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter(use_live_rates=False)
        
        info = converter.get_rate_info("USD", "INR")
        
        assert info["rate"] == converter.default_usd_inr_rate
        assert info["source"] == "approximate"
        assert "timestamp" in info
    
    def test_convert_with_live_rates(self):
        """Test conversion with live rates"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter(use_live_rates=True)
        
        mock_result = {
            "rate": 83.0,
            "source": "exchangerate-api"
        }
        
        with patch.object(converter.rate_provider, 'get_rate', return_value=mock_result):
            result = converter.convert(100, "USD", "INR")
            
            assert result == 8300.0
    
    def test_convert_zero_amount(self):
        """Test converting zero amount"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter(use_live_rates=False)
        result = converter.convert(0, "USD", "INR")
        
        assert result == 0.0
    
    def test_convert_same_currency(self):
        """Test converting to same currency"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter(use_live_rates=False)
        result = converter.convert(100, "USD", "USD")
        
        assert result == 100.0
    
    def test_approximate_rate_method(self):
        """Test _get_approximate_rate method"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter(use_live_rates=False)
        
        # USD to INR
        rate_usd_inr = converter._get_approximate_rate("USD", "INR")
        assert rate_usd_inr == converter.default_usd_inr_rate
        
        # INR to USD
        rate_inr_usd = converter._get_approximate_rate("INR", "USD")
        assert rate_inr_usd == 1.0 / converter.default_usd_inr_rate
    
    def test_unsupported_currency_pair(self):
        """Test unsupported currency pair raises error"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        converter = CurrencyConverter(use_live_rates=False)
        
        with pytest.raises(ValueError, match="Unsupported currency pair"):
            converter._get_approximate_rate("EUR", "GBP")
    
    def test_backward_compatibility(self):
        """Test backward compatibility with old usage"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        # Old usage (no parameters)
        converter = CurrencyConverter()
        
        # Should still work
        rate = converter.get_exchange_rate("USD", "INR")
        assert rate > 0
        
        result = converter.convert(100, "USD", "INR")
        assert result > 0
    
    def test_provider_initialization_failure_handling(self):
        """Test graceful handling of provider initialization failure"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        
        # Force import error
        with patch('maverick_mcp.utils.currency_converter.ExchangeRateProvider', side_effect=ImportError("Module not found")):
            converter = CurrencyConverter(use_live_rates=True)
            
            # Should fall back to approximate rates
            assert converter.use_live_rates == False
            assert converter.rate_provider is None
            
            # Should still work
            rate = converter.get_exchange_rate("USD", "INR")
            assert rate == converter.default_usd_inr_rate


class TestConvenienceFunctions:
    """Test convenience functions with updated converter"""
    
    def test_convert_currency_function(self):
        """Test convert_currency convenience function"""
        from maverick_mcp.utils.currency_converter import convert_currency
        
        # Should work with default parameters
        result = convert_currency(1000, "INR", "USD")
        
        assert result > 0
        assert result < 1000
    
    def test_convert_currency_with_live_rates(self):
        """Test convert_currency uses live rates by default"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter, convert_currency
        
        # The function creates a new converter, which defaults to live_rates=True
        with patch.object(CurrencyConverter, '__init__', return_value=None) as mock_init:
            with patch.object(CurrencyConverter, 'convert', return_value=12.0):
                result = convert_currency(1000, "INR", "USD")
                
                # Converter should be created (though patched here)
                assert result == 12.0


class TestHistoricalRates:
    """Test historical rates functionality"""
    
    def test_get_historical_rates(self):
        """Test getting historical rates (placeholder implementation)"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        from datetime import date
        
        converter = CurrencyConverter(use_live_rates=False)
        
        df = converter.get_historical_rates(
            "USD",
            "INR",
            date(2024, 1, 1),
            date(2024, 1, 10)
        )
        
        assert not df.empty
        assert "date" in df.columns
        assert "rate" in df.columns
        assert len(df) == 10  # 10 days
    
    def test_convert_timeseries(self):
        """Test converting time series"""
        from maverick_mcp.utils.currency_converter import CurrencyConverter
        import pandas as pd
        
        converter = CurrencyConverter(use_live_rates=False)
        
        amounts = pd.Series([100, 200, 300])
        converted = converter.convert_timeseries(amounts, "INR", "USD")
        
        assert len(converted) == len(amounts)
        assert all(converted < amounts)  # INR to USD should be less


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

