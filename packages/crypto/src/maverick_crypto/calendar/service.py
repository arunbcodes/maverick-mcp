"""
Cryptocurrency Market Calendar Service.

Handles the unique characteristics of crypto markets:
- 24/7/365 trading (no market hours, no holidays)
- No circuit breakers (can swing 50%+ in a day)
- All days are trading days

This service provides a consistent interface with stock market
calendars while accounting for crypto-specific behavior.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class CryptoCalendarService:
    """
    Cryptocurrency market calendar service.
    
    Unlike traditional stock markets, crypto markets operate 24/7/365.
    This service provides compatibility with stock market calendar
    interfaces while correctly handling crypto's always-open nature.
    
    Key Differences from Stock Markets:
        - No market hours (always open)
        - No holidays (trading every day)
        - No weekends off
        - No circuit breakers
        - Higher volatility tolerance
    
    Example:
        >>> calendar = CryptoCalendarService()
        >>> calendar.is_market_open()  # Always True
        True
        >>> calendar.get_trading_days("2024-01-01", "2024-01-31")
        # Returns all 31 days
    """
    
    # Crypto-specific volatility thresholds (vs stock defaults)
    DEFAULT_VOLATILITY_THRESHOLD = 0.10  # 10% (vs 2-3% for stocks)
    DEFAULT_STOP_LOSS = 0.15  # 15% (vs 5-7% for stocks)
    
    def __init__(self, timezone_str: str = "UTC"):
        """
        Initialize the crypto calendar service.
        
        Args:
            timezone_str: Timezone for market operations (default: UTC)
        """
        self.timezone_str = timezone_str
        logger.debug(f"CryptoCalendarService initialized with timezone: {timezone_str}")
    
    def is_market_open(self, symbol: str | None = None) -> bool:
        """
        Check if the crypto market is open.
        
        Crypto markets are ALWAYS open - 24/7/365.
        
        Args:
            symbol: Optional symbol (ignored, all crypto markets same)
            
        Returns:
            Always True
        """
        return True
    
    def is_trading_day(self, check_date: date | str | None = None) -> bool:
        """
        Check if a given date is a trading day.
        
        For crypto, every day is a trading day.
        
        Args:
            check_date: Date to check (default: today)
            
        Returns:
            Always True
        """
        return True
    
    def get_trading_days(
        self,
        start_date: date | str,
        end_date: date | str,
    ) -> list[date]:
        """
        Get all trading days in a date range.
        
        For crypto, this returns ALL days in the range (no weekends/holidays excluded).
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of all dates in range (inclusive)
        """
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        
        # Generate all dates in range
        dates = pd.date_range(start=start_date, end=end_date, freq="D")
        return [d.date() for d in dates]
    
    def get_trading_days_count(
        self,
        start_date: date | str,
        end_date: date | str,
    ) -> int:
        """
        Get count of trading days between two dates.
        
        For crypto, this is simply the number of calendar days.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Number of days (inclusive)
        """
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        
        return (end_date - start_date).days + 1
    
    def get_market_hours(self) -> dict[str, Any]:
        """
        Get crypto market hours (24/7).
        
        Returns:
            Dictionary with market hours info
        """
        return {
            "open": "00:00",
            "close": "23:59",
            "timezone": self.timezone_str,
            "is_24_7": True,
            "has_pre_market": False,
            "has_after_hours": False,
            "description": "Crypto markets operate 24/7/365",
        }
    
    def get_next_trading_day(self, from_date: date | str | None = None) -> date:
        """
        Get the next trading day.
        
        For crypto, this is always the next calendar day.
        
        Args:
            from_date: Starting date (default: today)
            
        Returns:
            Next trading day (tomorrow)
        """
        if from_date is None:
            from_date = date.today()
        elif isinstance(from_date, str):
            from_date = date.fromisoformat(from_date)
        
        return from_date + timedelta(days=1)
    
    def get_previous_trading_day(self, from_date: date | str | None = None) -> date:
        """
        Get the previous trading day.
        
        For crypto, this is always yesterday.
        
        Args:
            from_date: Starting date (default: today)
            
        Returns:
            Previous trading day (yesterday)
        """
        if from_date is None:
            from_date = date.today()
        elif isinstance(from_date, str):
            from_date = date.fromisoformat(from_date)
        
        return from_date - timedelta(days=1)
    
    def get_market_status(self) -> dict[str, Any]:
        """
        Get current crypto market status.
        
        Returns:
            Dictionary with market status
        """
        now = datetime.now(timezone.utc)
        return {
            "is_open": True,
            "status": "open",
            "message": "Crypto markets are always open",
            "current_time": now.isoformat(),
            "timezone": self.timezone_str,
            "next_close": None,  # Never closes
            "next_open": None,  # Never opens (always open)
        }
    
    def get_volatility_parameters(self) -> dict[str, float]:
        """
        Get crypto-specific volatility parameters.
        
        Crypto is significantly more volatile than stocks,
        so risk parameters should be adjusted accordingly.
        
        Returns:
            Dictionary with volatility parameters
        """
        return {
            "default_stop_loss": self.DEFAULT_STOP_LOSS,  # 15% vs 5-7% for stocks
            "default_take_profit": 0.25,  # 25% vs 10-15% for stocks
            "volatility_threshold": self.DEFAULT_VOLATILITY_THRESHOLD,  # 10% vs 2-3%
            "position_size_multiplier": 0.5,  # Smaller positions due to volatility
            "max_drawdown_tolerance": 0.30,  # 30% vs 15-20% for stocks
            "rsi_overbought": 75,  # Higher threshold for crypto
            "rsi_oversold": 25,  # Lower threshold for crypto
            "bollinger_std": 2.5,  # Wider bands for crypto
        }
    
    def adjust_for_crypto(self, stock_parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Adjust stock trading parameters for crypto.
        
        Takes standard stock trading parameters and adjusts them
        for crypto's higher volatility.
        
        Args:
            stock_parameters: Parameters calibrated for stocks
            
        Returns:
            Parameters adjusted for crypto
        """
        crypto_params = stock_parameters.copy()
        volatility_params = self.get_volatility_parameters()
        
        # Widen stop loss
        if "stop_loss" in crypto_params:
            crypto_params["stop_loss"] = max(
                crypto_params["stop_loss"] * 2,
                volatility_params["default_stop_loss"],
            )
        
        # Widen take profit
        if "take_profit" in crypto_params:
            crypto_params["take_profit"] = max(
                crypto_params["take_profit"] * 1.5,
                volatility_params["default_take_profit"],
            )
        
        # Reduce position size
        if "position_size" in crypto_params:
            crypto_params["position_size"] *= volatility_params["position_size_multiplier"]
        
        # Adjust RSI thresholds
        if "rsi_overbought" in crypto_params:
            crypto_params["rsi_overbought"] = volatility_params["rsi_overbought"]
        if "rsi_oversold" in crypto_params:
            crypto_params["rsi_oversold"] = volatility_params["rsi_oversold"]
        
        return crypto_params

