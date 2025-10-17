"""
Indian Stock Market Data Provider

This module provides data fetching functionality specific to Indian stock markets (NSE and BSE).
It extends the base stock data provider with market-specific features and validations.
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime, date, timedelta

import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from maverick_mcp.config.markets import Market, MarketConfig, get_market_config, MARKET_CONFIGS
from maverick_mcp.providers.stock_data import EnhancedStockDataProvider
from maverick_mcp.data.models import Stock

logger = logging.getLogger(__name__)


class IndianMarketDataProvider(EnhancedStockDataProvider):
    """
    Data provider specialized for Indian stock markets (NSE and BSE).
    
    Features:
    - NSE and BSE symbol validation
    - Market-specific trading calendar
    - Currency conversion support (INR)
    - Indian market hours handling
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize Indian Market Data Provider.
        
        Args:
            db_session: Optional database session for caching
        """
        super().__init__(db_session)
        self.nse_config = MARKET_CONFIGS[Market.INDIA_NSE]
        self.bse_config = MARKET_CONFIGS[Market.INDIA_BSE]
        logger.info("IndianMarketDataProvider initialized")
    
    def validate_indian_symbol(self, symbol: str) -> tuple[bool, Optional[Market], Optional[str]]:
        """
        Validate if a symbol is a valid Indian market symbol.
        
        Args:
            symbol: Stock ticker symbol to validate
            
        Returns:
            Tuple of (is_valid, market, error_message)
        """
        symbol_upper = symbol.upper()
        
        # Check if it's an NSE symbol
        if symbol_upper.endswith('.NS'):
            base_symbol = symbol_upper[:-3]
            if len(base_symbol) < 1:
                return False, None, "NSE symbol too short"
            if len(base_symbol) > 10:
                return False, None, "NSE symbol too long (max 10 characters)"
            return True, Market.INDIA_NSE, None
        
        # Check if it's a BSE symbol
        elif symbol_upper.endswith('.BO'):
            base_symbol = symbol_upper[:-3]
            if len(base_symbol) < 1:
                return False, None, "BSE symbol too short"
            if len(base_symbol) > 10:
                return False, None, "BSE symbol too long (max 10 characters)"
            return True, Market.INDIA_BSE, None
        
        else:
            return False, None, "Not an Indian market symbol (must end with .NS or .BO)"
    
    def format_nse_symbol(self, base_symbol: str) -> str:
        """
        Format a base symbol as an NSE symbol.
        
        Args:
            base_symbol: Base stock symbol (e.g., "RELIANCE")
            
        Returns:
            Formatted NSE symbol (e.g., "RELIANCE.NS")
        """
        base_symbol = base_symbol.upper().strip()
        if base_symbol.endswith('.NS'):
            return base_symbol
        return f"{base_symbol}.NS"
    
    def format_bse_symbol(self, base_symbol: str) -> str:
        """
        Format a base symbol as a BSE symbol.
        
        Args:
            base_symbol: Base stock symbol (e.g., "RELIANCE")
            
        Returns:
            Formatted BSE symbol (e.g., "RELIANCE.BO")
        """
        base_symbol = base_symbol.upper().strip()
        if base_symbol.endswith('.BO'):
            return base_symbol
        return f"{base_symbol}.BO"
    
    def get_nse_stock_data(
        self,
        base_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Fetch stock data for an NSE-listed stock.
        
        Args:
            base_symbol: Base stock symbol (without .NS suffix)
            start_date: Start date for data (YYYY-MM-DD)
            end_date: End date for data (YYYY-MM-DD)
            period: Alternative to start/end dates (e.g., "1mo", "1y")
            interval: Data interval (1d, 1wk, 1mo)
            
        Returns:
            DataFrame with stock data
        """
        symbol = self.format_nse_symbol(base_symbol)
        logger.info(f"Fetching NSE data for {symbol}")
        
        is_valid, market, error = self.validate_indian_symbol(symbol)
        if not is_valid:
            raise ValueError(f"Invalid NSE symbol: {error}")
        
        return self.get_stock_data(symbol, start_date, end_date, period, interval)
    
    def get_bse_stock_data(
        self,
        base_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Fetch stock data for a BSE-listed stock.
        
        Args:
            base_symbol: Base stock symbol (without .BO suffix)
            start_date: Start date for data (YYYY-MM-DD)
            end_date: End date for data (YYYY-MM-DD)
            period: Alternative to start/end dates (e.g., "1mo", "1y")
            interval: Data interval (1d, 1wk, 1mo)
            
        Returns:
            DataFrame with stock data
        """
        symbol = self.format_bse_symbol(base_symbol)
        logger.info(f"Fetching BSE data for {symbol}")
        
        is_valid, market, error = self.validate_indian_symbol(symbol)
        if not is_valid:
            raise ValueError(f"Invalid BSE symbol: {error}")
        
        return self.get_stock_data(symbol, start_date, end_date, period, interval)
    
    def get_stock_info(self, symbol: str) -> Dict:
        """
        Get detailed information about an Indian stock.
        
        Args:
            symbol: Stock ticker symbol (with .NS or .BO suffix)
            
        Returns:
            Dictionary with stock information
        """
        is_valid, market, error = self.validate_indian_symbol(symbol)
        if not is_valid:
            raise ValueError(f"Invalid Indian stock symbol: {error}")
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Add market-specific information
            config = get_market_config(symbol)
            info['market'] = market.value
            info['market_name'] = config.name
            info['currency'] = config.currency
            info['timezone'] = config.timezone
            info['trading_hours'] = f"{config.trading_hours_start} - {config.trading_hours_end}"
            
            logger.info(f"Retrieved info for {symbol}")
            return info
            
        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            raise
    
    def search_indian_stocks(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for Indian stocks by name or symbol.
        
        Args:
            query: Search query (company name or symbol)
            limit: Maximum number of results
            
        Returns:
            List of matching stocks
        """
        # This would typically query a database or API
        # For now, return basic structure
        logger.info(f"Searching for Indian stocks matching: {query}")
        
        # TODO: Implement actual search functionality
        # This could query:
        # 1. Local database of Indian stocks
        # 2. NSE/BSE API
        # 3. yfinance search
        
        results = []
        # Placeholder - would be replaced with actual search
        return results
    
    def get_nifty50_constituents(self) -> List[str]:
        """
        Get list of Nifty 50 constituent symbols.
        
        Returns:
            List of NSE symbols for Nifty 50 stocks
        """
        # Nifty 50 major constituents as of 2024
        nifty50 = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
            "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "BAJFINANCE",
            "KOTAKBANK", "LT", "HCLTECH", "ASIANPAINT", "AXISBANK",
            "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND",
            "WIPRO", "BAJAJFINSV", "TECHM", "POWERGRID", "NTPC",
            "M&M", "ONGC", "TATAMOTORS", "JSWSTEEL", "INDUSINDBK",
            "ADANIENT", "ADANIPORTS", "TATASTEEL", "COALINDIA", "HINDALCO",
            "GRASIM", "DIVISLAB", "DRREDDY", "CIPLA", "APOLLOHOSP",
            "EICHERMOT", "BRITANNIA", "BPCL", "HEROMOTOCO", "TATACONSUM",
            "SBILIFE", "BAJAJ-AUTO", "HDFCLIFE", "IOC", "UPL"
        ]
        return [self.format_nse_symbol(symbol) for symbol in nifty50]
    
    def get_sensex_constituents(self) -> List[str]:
        """
        Get list of Sensex (BSE 30) constituent symbols.
        
        Returns:
            List of BSE symbols for Sensex stocks
        """
        # Sensex major constituents (using NSE symbols as they're more commonly used)
        sensex = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
            "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "BAJFINANCE",
            "KOTAKBANK", "LT", "ASIANPAINT", "AXISBANK", "MARUTI",
            "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "WIPRO",
            "BAJAJFINSV", "TECHM", "POWERGRID", "NTPC", "M&M",
            "TATAMOTORS", "JSWSTEEL", "INDUSINDBK", "TATASTEEL", "HINDALCO"
        ]
        # Return as NSE symbols (more commonly used than BSE)
        return [self.format_nse_symbol(symbol) for symbol in sensex]
    
    def get_indian_market_status(self) -> Dict[str, any]:
        """
        Get current Indian market status (open/closed).
        
        Returns:
            Dictionary with market status information
        """
        now = datetime.now(tz=pd.Timestamp.now(tz=self.nse_config.timezone).tzinfo)
        current_date = now.date()
        
        # Use BSE calendar (same as NSE for holidays)
        calendar = self.nse_config.get_calendar()
        schedule = calendar.schedule(start_date=current_date, end_date=current_date)
        
        is_trading_day = len(schedule) > 0
        
        if is_trading_day:
            trading_start = schedule.iloc[0]['market_open'].time()
            trading_end = schedule.iloc[0]['market_close'].time()
            current_time = now.time()
            
            is_open = trading_start <= current_time <= trading_end
            status = "OPEN" if is_open else "CLOSED"
        else:
            is_open = False
            status = "HOLIDAY"
            trading_start = self.nse_config.trading_hours_start
            trading_end = self.nse_config.trading_hours_end
        
        return {
            "status": status,
            "is_open": is_open,
            "is_trading_day": is_trading_day,
            "current_time": now.strftime("%H:%M:%S"),
            "market_open": trading_start.strftime("%H:%M") if is_trading_day else None,
            "market_close": trading_end.strftime("%H:%M") if is_trading_day else None,
            "timezone": self.nse_config.timezone,
            "date": current_date.isoformat()
        }


# Convenience functions for quick access
def fetch_nse_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = "1mo"
) -> pd.DataFrame:
    """
    Quick function to fetch NSE stock data.
    
    Args:
        symbol: Base stock symbol (without .NS)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        period: Period (if dates not provided)
        
    Returns:
        DataFrame with stock data
    """
    provider = IndianMarketDataProvider()
    return provider.get_nse_stock_data(symbol, start_date, end_date, period)


def fetch_bse_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = "1mo"
) -> pd.DataFrame:
    """
    Quick function to fetch BSE stock data.
    
    Args:
        symbol: Base stock symbol (without .BO)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        period: Period (if dates not provided)
        
    Returns:
        DataFrame with stock data
    """
    provider = IndianMarketDataProvider()
    return provider.get_bse_stock_data(symbol, start_date, end_date, period)


__all__ = [
    "IndianMarketDataProvider",
    "fetch_nse_data",
    "fetch_bse_data",
]

