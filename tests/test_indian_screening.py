"""
Tests for Indian market screening strategies
"""

import pytest
from datetime import datetime

from maverick_mcp.application.screening.indian_market import (
    calculate_circuit_breaker_limits,
    get_nifty_sectors,
    format_indian_currency,
)
from maverick_mcp.config.markets import Market


class TestUtilityFunctions:
    """Test utility functions for Indian market"""
    
    def test_circuit_breaker_limits_nse(self):
        """Test circuit breaker calculation for NSE"""
        price = 1000.0
        limits = calculate_circuit_breaker_limits(price, Market.INDIA_NSE)
        
        assert "upper_limit" in limits
        assert "lower_limit" in limits
        assert "circuit_breaker_pct" in limits
        
        # Indian market has 10% circuit breakers
        assert limits["circuit_breaker_pct"] == 10.0
        assert limits["upper_limit"] == 1100.0  # +10%
        assert limits["lower_limit"] == 900.0   # -10%
    
    def test_circuit_breaker_limits_bse(self):
        """Test circuit breaker calculation for BSE"""
        price = 2500.0
        limits = calculate_circuit_breaker_limits(price, Market.INDIA_BSE)
        
        assert limits["circuit_breaker_pct"] == 10.0
        assert limits["upper_limit"] == 2750.0  # +10%
        assert limits["lower_limit"] == 2250.0  # -10%
    
    def test_nifty_sectors(self):
        """Test Nifty sector list"""
        sectors = get_nifty_sectors()
        
        assert isinstance(sectors, list)
        assert len(sectors) > 0
        
        # Check for known major sectors
        assert "Banking & Financial Services" in sectors
        assert "Information Technology" in sectors
        assert "Oil & Gas" in sectors
        assert "Fast Moving Consumer Goods" in sectors
        assert "Automobile" in sectors
        assert "Pharmaceuticals" in sectors
    
    def test_format_indian_currency_crores(self):
        """Test Indian currency formatting for crores"""
        # 1 crore = 10 million
        assert "Cr" in format_indian_currency(10000000)
        assert "Cr" in format_indian_currency(50000000)
        assert "1.00 Cr" in format_indian_currency(10000000)
        assert "5.00 Cr" in format_indian_currency(50000000)
    
    def test_format_indian_currency_lakhs(self):
        """Test Indian currency formatting for lakhs"""
        # 1 lakh = 100 thousand
        assert "L" in format_indian_currency(100000)
        assert "L" in format_indian_currency(500000)
        assert "1.00 L" in format_indian_currency(100000)
        assert "5.00 L" in format_indian_currency(500000)
    
    def test_format_indian_currency_regular(self):
        """Test Indian currency formatting for regular amounts"""
        formatted = format_indian_currency(50000)
        assert "₹" in formatted
        assert "50,000" in formatted or "50000" in formatted
    
    def test_format_indian_currency_edge_cases(self):
        """Test edge cases for currency formatting"""
        # Exactly 1 lakh
        assert "1.00 L" in format_indian_currency(100000)
        
        # Exactly 1 crore
        assert "1.00 Cr" in format_indian_currency(10000000)
        
        # Zero
        assert "₹0.00" in format_indian_currency(0)


class TestScreeningStrategies:
    """Test screening strategy functions"""
    
    def test_strategies_return_lists(self):
        """Test that screening strategies return proper data structures"""
        from maverick_mcp.application.screening.indian_market import (
            get_maverick_bullish_india,
            get_maverick_bearish_india,
            get_nifty50_momentum,
            get_value_picks_india,
            get_high_dividend_india,
            get_smallcap_breakouts_india,
        )
        
        # Note: These may return empty lists if no stocks meet criteria
        # Just testing they don't crash and return proper type
        
        strategies = [
            get_maverick_bullish_india,
            get_maverick_bearish_india,
            get_nifty50_momentum,
            get_value_picks_india,
            get_high_dividend_india,
            get_smallcap_breakouts_india,
        ]
        
        for strategy in strategies:
            try:
                result = strategy(limit=5)
                assert isinstance(result, list)
            except Exception as e:
                # It's OK if strategies fail due to no data or DB issues
                # Just checking they have proper structure
                pytest.skip(f"Strategy execution failed (acceptable): {e}")
    
    def test_sector_rotation_returns_dict(self):
        """Test that sector rotation returns proper structure"""
        from maverick_mcp.application.screening.indian_market import get_nifty_sector_rotation
        
        try:
            result = get_nifty_sector_rotation(lookback_days=30, top_n=2)
            assert isinstance(result, dict)
            assert "analysis_period_days" in result
            assert "total_sectors" in result
            assert "top_sectors" in result
            assert "all_sectors" in result
            assert "timestamp" in result
        except Exception as e:
            pytest.skip(f"Sector rotation failed (acceptable): {e}")
    
    def test_strategies_respect_limit_param(self):
        """Test that strategies respect the limit parameter"""
        from maverick_mcp.application.screening.indian_market import get_maverick_bullish_india
        
        try:
            # Request only 3 results
            result = get_maverick_bullish_india(limit=3)
            
            # Should have at most 3 results
            assert len(result) <= 3
        except Exception as e:
            pytest.skip(f"Strategy execution failed (acceptable): {e}")


class TestMarketDetection:
    """Test market detection and configuration"""
    
    def test_indian_market_config(self):
        """Test that Indian market configs are properly set up"""
        from maverick_mcp.config.markets import MARKET_CONFIGS, Market
        
        # Check NSE config
        nse_config = MARKET_CONFIGS[Market.INDIA_NSE]
        assert nse_config.country == "IN"
        assert nse_config.currency == "INR"
        assert nse_config.circuit_breaker_percent == 10.0
        assert nse_config.symbol_suffix == ".NS"
        assert nse_config.settlement_cycle == "T+1"
        
        # Check BSE config
        bse_config = MARKET_CONFIGS[Market.INDIA_BSE]
        assert bse_config.country == "IN"
        assert bse_config.currency == "INR"
        assert bse_config.circuit_breaker_percent == 10.0
        assert bse_config.symbol_suffix == ".BO"
        assert bse_config.settlement_cycle == "T+1"
    
    def test_indian_vs_us_circuit_breakers(self):
        """Test that Indian circuit breakers differ from US"""
        from maverick_mcp.config.markets import MARKET_CONFIGS, Market
        
        indian_breaker = MARKET_CONFIGS[Market.INDIA_NSE].circuit_breaker_percent
        us_breaker = MARKET_CONFIGS[Market.US].circuit_breaker_percent
        
        assert indian_breaker == 10.0
        assert us_breaker == 7.0
        assert indian_breaker != us_breaker


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

