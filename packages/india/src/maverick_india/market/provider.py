"""
Indian Stock Market Data Provider.

Provides data fetching functionality specific to Indian stock markets (NSE and BSE).
Extends base providers with market-specific features and validations.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Optional

import pandas as pd
import yfinance as yf

from maverick_data import YFinanceProvider, MarketCalendarService, MARKET_CONFIGS

logger = logging.getLogger(__name__)


class IndianMarket(Enum):
    """Indian stock market identifiers."""

    NSE = "NSE"
    BSE = "BSE"


# Indian market configuration with circuit breaker limits
INDIAN_MARKET_CONFIG = {
    IndianMarket.NSE: {
        "suffix": ".NS",
        "name": "National Stock Exchange",
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "trading_hours_start": "09:15",
        "trading_hours_end": "15:30",
        "circuit_breaker_percent": 10,  # 10% vs 7% in US
    },
    IndianMarket.BSE: {
        "suffix": ".BO",
        "name": "Bombay Stock Exchange",
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "trading_hours_start": "09:15",
        "trading_hours_end": "15:30",
        "circuit_breaker_percent": 10,
    },
}


class IndianMarketDataProvider(YFinanceProvider):
    """
    Data provider specialized for Indian stock markets (NSE and BSE).

    Features:
    - NSE and BSE symbol validation
    - Market-specific trading calendar
    - Currency conversion support (INR)
    - Indian market hours handling
    - Circuit breaker calculations
    """

    def __init__(self):
        """Initialize Indian Market Data Provider."""
        super().__init__()
        self._calendar = MarketCalendarService()
        logger.info("IndianMarketDataProvider initialized")

    def validate_indian_symbol(
        self, symbol: str
    ) -> tuple[bool, Optional[IndianMarket], Optional[str]]:
        """
        Validate if a symbol is a valid Indian market symbol.

        Args:
            symbol: Stock ticker symbol to validate

        Returns:
            Tuple of (is_valid, market, error_message)
        """
        symbol_upper = symbol.upper()

        # Check if it's an NSE symbol
        if symbol_upper.endswith(".NS"):
            base_symbol = symbol_upper[:-3]
            if len(base_symbol) < 1:
                return False, None, "NSE symbol too short"
            if len(base_symbol) > 10:
                return False, None, "NSE symbol too long (max 10 characters)"
            return True, IndianMarket.NSE, None

        # Check if it's a BSE symbol
        elif symbol_upper.endswith(".BO"):
            base_symbol = symbol_upper[:-3]
            if len(base_symbol) < 1:
                return False, None, "BSE symbol too short"
            if len(base_symbol) > 10:
                return False, None, "BSE symbol too long (max 10 characters)"
            return True, IndianMarket.BSE, None

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
        if base_symbol.endswith(".NS"):
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
        if base_symbol.endswith(".BO"):
            return base_symbol
        return f"{base_symbol}.BO"

    def get_nse_stock_data(
        self,
        base_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch stock data for an NSE-listed stock.

        Args:
            base_symbol: Base stock symbol (without .NS suffix)
            start_date: Start date for data (YYYY-MM-DD)
            end_date: End date for data (YYYY-MM-DD)
            period: Alternative to start/end dates (e.g., "1mo", "1y")

        Returns:
            DataFrame with stock data
        """
        symbol = self.format_nse_symbol(base_symbol)
        logger.info(f"Fetching NSE data for {symbol}")

        is_valid, market, error = self.validate_indian_symbol(symbol)
        if not is_valid:
            raise ValueError(f"Invalid NSE symbol: {error}")

        return self.fetch_data(symbol, start_date, end_date, period)

    def get_bse_stock_data(
        self,
        base_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch stock data for a BSE-listed stock.

        Args:
            base_symbol: Base stock symbol (without .BO suffix)
            start_date: Start date for data (YYYY-MM-DD)
            end_date: End date for data (YYYY-MM-DD)
            period: Alternative to start/end dates (e.g., "1mo", "1y")

        Returns:
            DataFrame with stock data
        """
        symbol = self.format_bse_symbol(base_symbol)
        logger.info(f"Fetching BSE data for {symbol}")

        is_valid, market, error = self.validate_indian_symbol(symbol)
        if not is_valid:
            raise ValueError(f"Invalid BSE symbol: {error}")

        return self.fetch_data(symbol, start_date, end_date, period)

    def get_stock_info(self, symbol: str) -> dict:
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
            if market:
                config = INDIAN_MARKET_CONFIG[market]
                info["market"] = market.value
                info["market_name"] = config["name"]
                info["currency"] = config["currency"]
                info["timezone"] = config["timezone"]
                info["trading_hours"] = (
                    f"{config['trading_hours_start']} - {config['trading_hours_end']}"
                )
                info["circuit_breaker_pct"] = config["circuit_breaker_percent"]

            logger.info(f"Retrieved info for {symbol}")
            return info

        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            raise

    def get_nifty50_constituents(self) -> list[str]:
        """
        Get list of Nifty 50 constituent symbols.

        Returns:
            List of NSE symbols for Nifty 50 stocks
        """
        # Nifty 50 major constituents as of 2024
        nifty50 = [
            "RELIANCE",
            "TCS",
            "HDFCBANK",
            "INFY",
            "ICICIBANK",
            "HINDUNILVR",
            "ITC",
            "SBIN",
            "BHARTIARTL",
            "BAJFINANCE",
            "KOTAKBANK",
            "LT",
            "HCLTECH",
            "ASIANPAINT",
            "AXISBANK",
            "MARUTI",
            "SUNPHARMA",
            "TITAN",
            "ULTRACEMCO",
            "NESTLEIND",
            "WIPRO",
            "BAJAJFINSV",
            "TECHM",
            "POWERGRID",
            "NTPC",
            "M&M",
            "ONGC",
            "TATAMOTORS",
            "JSWSTEEL",
            "INDUSINDBK",
            "ADANIENT",
            "ADANIPORTS",
            "TATASTEEL",
            "COALINDIA",
            "HINDALCO",
            "GRASIM",
            "DIVISLAB",
            "DRREDDY",
            "CIPLA",
            "APOLLOHOSP",
            "EICHERMOT",
            "BRITANNIA",
            "BPCL",
            "HEROMOTOCO",
            "TATACONSUM",
            "SBILIFE",
            "BAJAJ-AUTO",
            "HDFCLIFE",
            "IOC",
            "UPL",
        ]
        return [self.format_nse_symbol(symbol) for symbol in nifty50]

    def get_sensex_constituents(self) -> list[str]:
        """
        Get list of Sensex (BSE 30) constituent symbols.

        Returns:
            List of NSE symbols for Sensex stocks (NSE symbols are more commonly used)
        """
        sensex = [
            "RELIANCE",
            "TCS",
            "HDFCBANK",
            "INFY",
            "ICICIBANK",
            "HINDUNILVR",
            "ITC",
            "SBIN",
            "BHARTIARTL",
            "BAJFINANCE",
            "KOTAKBANK",
            "LT",
            "ASIANPAINT",
            "AXISBANK",
            "MARUTI",
            "SUNPHARMA",
            "TITAN",
            "ULTRACEMCO",
            "NESTLEIND",
            "WIPRO",
            "BAJAJFINSV",
            "TECHM",
            "POWERGRID",
            "NTPC",
            "M&M",
            "TATAMOTORS",
            "JSWSTEEL",
            "INDUSINDBK",
            "TATASTEEL",
            "HINDALCO",
        ]
        return [self.format_nse_symbol(symbol) for symbol in sensex]

    def get_indian_market_status(self) -> dict:
        """
        Get current Indian market status (open/closed).

        Returns:
            Dictionary with market status information
        """
        import pytz

        tz = pytz.timezone("Asia/Kolkata")
        now = datetime.now(tz)
        current_date = now.date()

        is_trading_day = self._calendar.is_trading_day(current_date, "NSE")

        if is_trading_day:
            is_open = self._calendar.is_market_open(now, "NSE")
            status = "OPEN" if is_open else "CLOSED"
        else:
            is_open = False
            status = "HOLIDAY"

        return {
            "status": status,
            "is_open": is_open,
            "is_trading_day": is_trading_day,
            "current_time": now.strftime("%H:%M:%S"),
            "timezone": "Asia/Kolkata",
            "date": current_date.isoformat(),
        }


def calculate_circuit_breaker_limits(
    current_price: float, market: IndianMarket = IndianMarket.NSE
) -> dict[str, float]:
    """
    Calculate circuit breaker limits for Indian stocks.

    Indian market has 10% circuit breakers (vs 7% in US).

    Args:
        current_price: Current stock price
        market: Market (NSE or BSE)

    Returns:
        Dict with upper_limit, lower_limit, and circuit_breaker_pct
    """
    config = INDIAN_MARKET_CONFIG.get(market, INDIAN_MARKET_CONFIG[IndianMarket.NSE])
    breaker_pct = config["circuit_breaker_percent"] / 100

    return {
        "upper_limit": current_price * (1 + breaker_pct),
        "lower_limit": current_price * (1 - breaker_pct),
        "circuit_breaker_pct": config["circuit_breaker_percent"],
    }


def format_indian_currency(amount: float) -> str:
    """
    Format amount in Indian numbering system (lakhs and crores).

    Args:
        amount: Amount in rupees

    Returns:
        Formatted string (e.g., "₹1.5 Cr", "₹50 L")
    """
    if amount >= 10000000:  # 1 crore = 10 million
        crores = amount / 10000000
        return f"₹{crores:.2f} Cr"
    elif amount >= 100000:  # 1 lakh = 100 thousand
        lakhs = amount / 100000
        return f"₹{lakhs:.2f} L"
    else:
        return f"₹{amount:,.2f}"


def get_nifty_sectors() -> list[str]:
    """
    Get list of Nifty sectors.

    Returns:
        List of sector names used in Nifty indices
    """
    return [
        "Banking & Financial Services",
        "Information Technology",
        "Oil & Gas",
        "Fast Moving Consumer Goods",
        "Automobile",
        "Pharmaceuticals",
        "Metals & Mining",
        "Infrastructure",
        "Telecom",
        "Power",
        "Consumer Durables",
        "Cement",
        "Real Estate",
        "Media & Entertainment",
    ]


# Convenience functions for quick access
def fetch_nse_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = "1mo",
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
    period: Optional[str] = "1mo",
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
    "IndianMarket",
    "IndianMarketDataProvider",
    "INDIAN_MARKET_CONFIG",
    "calculate_circuit_breaker_limits",
    "format_indian_currency",
    "get_nifty_sectors",
    "fetch_nse_data",
    "fetch_bse_data",
]
