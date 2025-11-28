"""
Maverick India Package.

Indian market-specific functionality for Maverick stock analysis.
Supports NSE (.NS) and BSE (.BO) stocks.
"""

from maverick_india.market import (
    INDIAN_MARKET_CONFIG,
    IndianMarket,
    IndianMarketDataProvider,
    calculate_circuit_breaker_limits,
    fetch_bse_data,
    fetch_nse_data,
    format_indian_currency,
    get_maverick_bearish_india,
    get_maverick_bullish_india,
    get_nifty50_momentum,
    get_nifty_sector_rotation,
    get_nifty_sectors,
    get_smallcap_breakouts_india,
    get_value_picks_india,
)

__all__ = [
    # Market Provider
    "IndianMarket",
    "IndianMarketDataProvider",
    "INDIAN_MARKET_CONFIG",
    "calculate_circuit_breaker_limits",
    "format_indian_currency",
    "get_nifty_sectors",
    "fetch_nse_data",
    "fetch_bse_data",
    # Screening Strategies
    "get_maverick_bullish_india",
    "get_maverick_bearish_india",
    "get_nifty50_momentum",
    "get_nifty_sector_rotation",
    "get_value_picks_india",
    "get_smallcap_breakouts_india",
]
