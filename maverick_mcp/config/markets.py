"""
Multi-market configuration for MaverickMCP.

This module provides a market registry pattern that supports multiple stock exchanges
(US, Indian NSE/BSE) with market-specific configurations including trading hours,
calendars, circuit breakers, and settlement cycles.
"""

from dataclasses import dataclass
from datetime import time
from enum import Enum
from typing import Any

import pandas_market_calendars as mcal

# Set up logging
import logging

logger = logging.getLogger("maverick_mcp.config.markets")


class Market(Enum):
    """Supported stock market exchanges."""

    US = "US"
    INDIA_NSE = "NSE"
    INDIA_BSE = "BSE"


@dataclass
class MarketConfig:
    """
    Configuration for a specific stock market.

    This class encapsulates all market-specific parameters needed for
    accurate data fetching, caching, and analysis across different exchanges.
    """

    name: str
    """Full name of the market/exchange"""

    country: str
    """ISO 3166-1 alpha-2 country code (e.g., 'US', 'IN')"""

    currency: str
    """ISO 4217 currency code (e.g., 'USD', 'INR')"""

    timezone: str
    """IANA timezone identifier (e.g., 'America/New_York', 'Asia/Kolkata')"""

    calendar_name: str
    """Calendar name for pandas_market_calendars"""

    symbol_suffix: str
    """Symbol suffix for yfinance (e.g., '' for US, '.NS' for NSE, '.BO' for BSE)"""

    trading_hours_start: time
    """Market opening time (local timezone)"""

    trading_hours_end: time
    """Market closing time (local timezone)"""

    circuit_breaker_percent: float
    """Circuit breaker limit percentage (e.g., 10.0 for India, 7.0 for US)"""

    settlement_cycle: str
    """Settlement cycle (e.g., 'T+1' for India, 'T+2' for US)"""

    min_tick_size: float
    """Minimum price movement (tick size)"""

    def get_calendar(self) -> Any:
        """
        Get market calendar instance.

        Returns:
            pandas_market_calendars calendar instance

        Raises:
            ValueError: If calendar not available for this market
        """
        try:
            return mcal.get_calendar(self.calendar_name)
        except Exception as e:
            logger.warning(
                f"Could not load calendar '{self.calendar_name}' for {self.name}: {e}"
            )
            # Fallback to NYSE calendar as default
            logger.info(f"Falling back to NYSE calendar for {self.name}")
            return mcal.get_calendar("NYSE")

    def format_symbol(self, base_symbol: str) -> str:
        """
        Format a base symbol for this market.

        Args:
            base_symbol: Base ticker symbol (e.g., 'RELIANCE', 'AAPL')

        Returns:
            Formatted symbol with appropriate suffix (e.g., 'RELIANCE.NS', 'AAPL')
        """
        # Remove any existing suffix
        clean_symbol = base_symbol.split(".")[0]
        return f"{clean_symbol}{self.symbol_suffix}"

    def strip_suffix(self, symbol: str) -> str:
        """
        Remove market suffix from symbol.

        Args:
            symbol: Full symbol with suffix (e.g., 'RELIANCE.NS')

        Returns:
            Base symbol without suffix (e.g., 'RELIANCE')
        """
        if self.symbol_suffix and symbol.endswith(self.symbol_suffix):
            return symbol[: -len(self.symbol_suffix)]
        return symbol


# Market configurations for supported exchanges
MARKET_CONFIGS = {
    Market.US: MarketConfig(
        name="United States Stock Market",
        country="US",
        currency="USD",
        timezone="America/New_York",
        calendar_name="NYSE",
        symbol_suffix="",
        trading_hours_start=time(9, 30),
        trading_hours_end=time(16, 0),
        circuit_breaker_percent=7.0,
        settlement_cycle="T+2",
        min_tick_size=0.01,
    ),
    Market.INDIA_NSE: MarketConfig(
        name="National Stock Exchange of India",
        country="IN",
        currency="INR",
        timezone="Asia/Kolkata",
        calendar_name="NSE",
        symbol_suffix=".NS",
        trading_hours_start=time(9, 15),
        trading_hours_end=time(15, 30),
        circuit_breaker_percent=10.0,
        settlement_cycle="T+1",
        min_tick_size=0.05,
    ),
    Market.INDIA_BSE: MarketConfig(
        name="Bombay Stock Exchange",
        country="IN",
        currency="INR",
        timezone="Asia/Kolkata",
        calendar_name="NSE",  # Use NSE calendar (same holidays as BSE)
        symbol_suffix=".BO",
        trading_hours_start=time(9, 15),
        trading_hours_end=time(15, 30),
        circuit_breaker_percent=10.0,
        settlement_cycle="T+1",
        min_tick_size=0.05,
    ),
}


def get_market_from_symbol(symbol: str) -> Market:
    """
    Determine market from symbol suffix.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'RELIANCE.NS', 'TCS.BO')

    Returns:
        Market enum corresponding to the symbol

    Examples:
        >>> get_market_from_symbol('AAPL')
        Market.US
        >>> get_market_from_symbol('RELIANCE.NS')
        Market.INDIA_NSE
        >>> get_market_from_symbol('SENSEX.BO')
        Market.INDIA_BSE
    """
    symbol_upper = symbol.upper()

    if symbol_upper.endswith(".NS"):
        return Market.INDIA_NSE
    elif symbol_upper.endswith(".BO"):
        return Market.INDIA_BSE
    else:
        return Market.US


def get_market_config(symbol: str) -> MarketConfig:
    """
    Get market configuration for a symbol.

    Args:
        symbol: Stock ticker symbol

    Returns:
        MarketConfig for the symbol's market

    Examples:
        >>> config = get_market_config('RELIANCE.NS')
        >>> config.currency
        'INR'
        >>> config.trading_hours_start
        time(9, 15)
    """
    market = get_market_from_symbol(symbol)
    return MARKET_CONFIGS[market]


def get_all_markets() -> list[Market]:
    """
    Get list of all supported markets.

    Returns:
        List of Market enums
    """
    return list(MARKET_CONFIGS.keys())


def get_markets_by_country(country_code: str) -> list[Market]:
    """
    Get all markets for a specific country.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g., 'US', 'IN')

    Returns:
        List of markets in the specified country
    """
    return [
        market
        for market, config in MARKET_CONFIGS.items()
        if config.country == country_code.upper()
    ]


def is_indian_market(symbol: str) -> bool:
    """
    Check if symbol belongs to Indian market (NSE or BSE).

    Args:
        symbol: Stock ticker symbol

    Returns:
        True if symbol is from NSE or BSE, False otherwise
    """
    market = get_market_from_symbol(symbol)
    return market in [Market.INDIA_NSE, Market.INDIA_BSE]


def is_us_market(symbol: str) -> bool:
    """
    Check if symbol belongs to US market.

    Args:
        symbol: Stock ticker symbol

    Returns:
        True if symbol is from US market, False otherwise
    """
    return get_market_from_symbol(symbol) == Market.US


# Export key classes and functions
__all__ = [
    "Market",
    "MarketConfig",
    "MARKET_CONFIGS",
    "get_market_from_symbol",
    "get_market_config",
    "get_all_markets",
    "get_markets_by_country",
    "is_indian_market",
    "is_us_market",
]

