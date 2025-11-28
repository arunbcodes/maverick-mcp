"""
Indian market data providers and utilities.

Supports NSE (.NS) and BSE (.BO) stock markets.
"""

from maverick_india.market.provider import (
    INDIAN_MARKET_CONFIG,
    IndianMarket,
    IndianMarketDataProvider,
    calculate_circuit_breaker_limits,
    fetch_bse_data,
    fetch_nse_data,
    format_indian_currency,
    get_nifty_sectors,
)
from maverick_india.market.screening import (
    get_maverick_bearish_india,
    get_maverick_bullish_india,
    get_nifty50_momentum,
    get_nifty_sector_rotation,
    get_smallcap_breakouts_india,
    get_value_picks_india,
)

__all__ = [
    # Provider
    "IndianMarket",
    "IndianMarketDataProvider",
    "INDIAN_MARKET_CONFIG",
    "calculate_circuit_breaker_limits",
    "format_indian_currency",
    "get_nifty_sectors",
    "fetch_nse_data",
    "fetch_bse_data",
    # Screening
    "get_maverick_bullish_india",
    "get_maverick_bearish_india",
    "get_nifty50_momentum",
    "get_nifty_sector_rotation",
    "get_value_picks_india",
    "get_smallcap_breakouts_india",
]
