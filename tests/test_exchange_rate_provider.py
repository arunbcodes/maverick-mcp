"""
Tests for Exchange Rate Provider

Tests real-time currency conversion with multiple fallback sources.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from maverick_mcp.providers.exchange_rate import (
    ExchangeRateProvider,
    ExchangeRateSource,
    get_exchange_rate,
    convert_currency,
)


class TestExchangeRateProvider:
    """Test ExchangeRateProvider functionality"""
    
    def test_initialization(self):
        """Test provider initializes correctly"""
        provider = ExchangeRateProvider()
        
        assert provider is not None
        assert provider.cache is not None
        assert provider.default_usd_inr_rate > 0
    
    def test_initialization_with_api_key(self):
        """Test provider initializes with API key"""
        provider = ExchangeRateProvider(api_key="test_key_123")
        
        assert provider.api_key == "test_key_123"
    
    def test_same_currency_rate(self):
        """Test rate for same currency returns 1.0"""
        provider = ExchangeRateProvider()
        
        result = provider.get_rate("USD", "USD")
        
        assert result["rate"] == 1.0
        assert result["source"] == "same_currency"
        assert result["from_currency"] == "USD"
        assert result["to_currency"] == "USD"
    
    def test_rate_caching(self):
        """Test that rates are cached"""
        provider = ExchangeRateProvider()
        
        # Mock the API call
        with patch.object(provider, '_fetch_from_exchange_rate_api') as mock_api:
            mock_api.return_value = {
                "from_currency": "USD",
                "to_currency": "INR",
                "rate": 83.5,
                "source": "exchangerate-api",
                "timestamp": datetime.now().isoformat(),
                "cached": False
            }
            
            # First call should hit API
            result1 = provider.get_rate("USD", "INR")
            assert result1["cached"] == False
            assert mock_api.call_count == 1
            
            # Second call should use cache
            result2 = provider.get_rate("USD", "INR")
            assert result2["cached"] == True
            assert mock_api.call_count == 1  # Not called again
    
    def test_approximate_rate_usd_to_inr(self):
        """Test approximate rate for USD to INR"""
        provider = ExchangeRateProvider(api_key=None, use_fallback=False)
        
        result = provider.get_rate("USD", "INR")
        
        assert result["rate"] == provider.default_usd_inr_rate
        assert result["source"] == ExchangeRateSource.APPROXIMATE.value
        assert "warning" in result
    
    def test_approximate_rate_inr_to_usd(self):
        """Test approximate rate for INR to USD"""
        provider = ExchangeRateProvider(api_key=None, use_fallback=False)
        
        result = provider.get_rate("INR", "USD")
        
        expected_rate = 1.0 / provider.default_usd_inr_rate
        assert abs(result["rate"] - expected_rate) < 0.001
        assert result["source"] == ExchangeRateSource.APPROXIMATE.value
    
    def test_exchange_rate_api_success(self):
        """Test successful Exchange Rate API call"""
        provider = ExchangeRateProvider(api_key="test_key")
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": "success",
            "conversion_rate": 83.25,
            "time_last_update_utc": "2024-01-01 00:00:00",
            "time_next_update_utc": "2024-01-02 00:00:00"
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            result = provider.get_rate("USD", "INR")
            
            assert result["rate"] == 83.25
            assert result["source"] == ExchangeRateSource.EXCHANGE_RATE_API.value
            assert result["from_currency"] == "USD"
            assert result["to_currency"] == "INR"
    
    def test_exchange_rate_api_failure_fallback(self):
        """Test fallback when Exchange Rate API fails"""
        provider = ExchangeRateProvider(api_key="test_key", use_fallback=True)
        
        # Mock API failure
        with patch('requests.get', side_effect=Exception("API Error")):
            # Mock Yahoo Finance success
            with patch.object(provider, '_fetch_from_yahoo_finance') as mock_yahoo:
                mock_yahoo.return_value = {
                    "from_currency": "USD",
                    "to_currency": "INR",
                    "rate": 83.10,
                    "source": ExchangeRateSource.YAHOO_FINANCE.value,
                    "timestamp": datetime.now().isoformat(),
                    "cached": False
                }
                
                result = provider.get_rate("USD", "INR")
                
                assert result["rate"] == 83.10
                assert result["source"] == ExchangeRateSource.YAHOO_FINANCE.value
                assert mock_yahoo.called
    
    def test_force_refresh_bypasses_cache(self):
        """Test force_refresh bypasses cache"""
        provider = ExchangeRateProvider(api_key="test_key")
        
        with patch.object(provider, '_fetch_from_exchange_rate_api') as mock_api:
            mock_api.return_value = {
                "from_currency": "USD",
                "to_currency": "INR",
                "rate": 83.5,
                "source": "exchangerate-api",
                "timestamp": datetime.now().isoformat(),
                "cached": False
            }
            
            # First call
            provider.get_rate("USD", "INR")
            assert mock_api.call_count == 1
            
            # Second call with force_refresh
            provider.get_rate("USD", "INR", force_refresh=True)
            assert mock_api.call_count == 2  # Called again
    
    def test_supported_currencies(self):
        """Test getting list of supported currencies"""
        provider = ExchangeRateProvider()
        
        currencies = provider.get_supported_currencies()
        
        assert isinstance(currencies, list)
        assert len(currencies) > 0
        assert "USD" in currencies
        assert "INR" in currencies
        assert "EUR" in currencies
    
    def test_is_rate_stale(self):
        """Test rate staleness detection"""
        provider = ExchangeRateProvider()
        
        # Fresh rate
        fresh_rate = {
            "timestamp": datetime.now().isoformat()
        }
        assert provider.is_rate_stale(fresh_rate, max_age_hours=24) == False
        
        # Old rate (no timestamp)
        old_rate = {}
        assert provider.is_rate_stale(old_rate) == True


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_get_exchange_rate_function(self):
        """Test get_exchange_rate convenience function"""
        with patch('maverick_mcp.providers.exchange_rate.ExchangeRateProvider') as mock_provider_class:
            mock_provider = Mock()
            mock_provider.get_rate.return_value = {"rate": 83.5}
            mock_provider_class.return_value = mock_provider
            
            rate = get_exchange_rate("USD", "INR")
            
            assert rate == 83.5
            mock_provider.get_rate.assert_called_once_with("USD", "INR")
    
    def test_convert_currency_function(self):
        """Test convert_currency convenience function"""
        with patch('maverick_mcp.providers.exchange_rate.get_exchange_rate') as mock_get_rate:
            mock_get_rate.return_value = 83.0
            
            converted = convert_currency(100, "USD", "INR")
            
            assert converted == 8300.0
            mock_get_rate.assert_called_once_with("USD", "INR", None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

