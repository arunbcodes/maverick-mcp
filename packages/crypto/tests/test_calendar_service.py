"""Tests for CryptoCalendarService."""

from datetime import date, timedelta

import pytest


class TestMarketStatus:
    """Test market status methods."""
    
    def test_market_always_open(self, calendar_service):
        """Test crypto market is always reported as open."""
        assert calendar_service.is_market_open() is True
    
    def test_market_open_with_symbol(self, calendar_service):
        """Test market open with symbol parameter."""
        assert calendar_service.is_market_open("BTC-USD") is True
    
    def test_every_day_is_trading_day(self, calendar_service):
        """Test all days are trading days."""
        assert calendar_service.is_trading_day() is True
        assert calendar_service.is_trading_day(date.today()) is True
        
        # Weekend should also be trading day
        saturday = date(2024, 1, 6)  # A Saturday
        assert calendar_service.is_trading_day(saturday) is True


class TestTradingDays:
    """Test trading days calculation."""
    
    def test_get_trading_days_includes_all_days(self, calendar_service):
        """Test all calendar days are included."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        
        trading_days = calendar_service.get_trading_days(start, end)
        
        assert len(trading_days) == 31  # All days in January
    
    def test_get_trading_days_with_strings(self, calendar_service):
        """Test trading days with string dates."""
        trading_days = calendar_service.get_trading_days("2024-01-01", "2024-01-07")
        
        assert len(trading_days) == 7
    
    def test_trading_days_count(self, calendar_service):
        """Test trading days count is calendar days."""
        count = calendar_service.get_trading_days_count("2024-01-01", "2024-01-31")
        
        assert count == 31


class TestNextPreviousTradingDay:
    """Test next/previous trading day methods."""
    
    def test_next_trading_day_is_tomorrow(self, calendar_service):
        """Test next trading day is always tomorrow."""
        today = date.today()
        next_day = calendar_service.get_next_trading_day(today)
        
        assert next_day == today + timedelta(days=1)
    
    def test_previous_trading_day_is_yesterday(self, calendar_service):
        """Test previous trading day is always yesterday."""
        today = date.today()
        prev_day = calendar_service.get_previous_trading_day(today)
        
        assert prev_day == today - timedelta(days=1)


class TestMarketHours:
    """Test market hours methods."""
    
    def test_market_hours_24_7(self, calendar_service):
        """Test market hours show 24/7."""
        hours = calendar_service.get_market_hours()
        
        assert hours["is_24_7"] is True
        assert hours["open"] == "00:00"
        assert hours["close"] == "23:59"
    
    def test_market_status_always_open(self, calendar_service):
        """Test market status shows always open."""
        status = calendar_service.get_market_status()
        
        assert status["is_open"] is True
        assert status["status"] == "open"
        assert status["next_close"] is None


class TestVolatilityParameters:
    """Test crypto-specific volatility parameters."""
    
    def test_volatility_params_exist(self, calendar_service):
        """Test volatility parameters are returned."""
        params = calendar_service.get_volatility_parameters()
        
        assert "default_stop_loss" in params
        assert "rsi_overbought" in params
        assert "rsi_oversold" in params
    
    def test_crypto_thresholds_wider_than_stocks(self, calendar_service):
        """Test crypto thresholds are wider than typical stock values."""
        params = calendar_service.get_volatility_parameters()
        
        # Crypto stop loss should be wider than typical 5-7% for stocks
        assert params["default_stop_loss"] >= 0.10
        
        # RSI overbought should be higher (more tolerant of high RSI)
        assert params["rsi_overbought"] >= 70
        
        # RSI oversold should be lower (more tolerant of low RSI)
        assert params["rsi_oversold"] <= 30
    
    def test_adjust_for_crypto(self, calendar_service):
        """Test parameter adjustment for crypto."""
        stock_params = {
            "stop_loss": 0.05,
            "take_profit": 0.10,
            "position_size": 0.20,
            "rsi_overbought": 70,
        }
        
        crypto_params = calendar_service.adjust_for_crypto(stock_params)
        
        # Stop loss should be widened
        assert crypto_params["stop_loss"] > stock_params["stop_loss"]
        
        # Position size should be reduced
        assert crypto_params["position_size"] < stock_params["position_size"]

