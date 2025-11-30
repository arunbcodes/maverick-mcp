"""
Maverick Crypto - Cryptocurrency data and analysis package.

A standalone, portable package for cryptocurrency data fetching,
technical analysis, backtesting, and MCP tool integration.

Features:
    - Multi-provider support (yfinance, CoinGecko)
    - 24/7 market calendar handling
    - Technical analysis via pandas-ta
    - VectorBT-powered backtesting with crypto-specific strategies
    - SQLAlchemy models for persistence
    - MCP tools for Claude Desktop

Example:
    >>> from maverick_crypto import CryptoDataProvider
    >>> provider = CryptoDataProvider()
    >>> btc = await provider.get_crypto_data("BTC", days=90)
    
    >>> from maverick_crypto import CryptoBacktestEngine
    >>> engine = CryptoBacktestEngine()
    >>> result = await engine.run_backtest("BTC", "crypto_momentum", days=90)

Standalone Deployment:
    This package can be deployed independently or moved to a separate
    repository without dependencies on other maverick packages.
"""

from maverick_crypto.providers import CryptoDataProvider
from maverick_crypto.calendar import CryptoCalendarService
from maverick_crypto.models import Crypto, CryptoPriceCache

__version__ = "0.2.0"

__all__ = [
    # Providers
    "CryptoDataProvider",
    # Calendar
    "CryptoCalendarService",
    # Models
    "Crypto",
    "CryptoPriceCache",
    # Version
    "__version__",
]

# Lazy imports for optional backtesting components
def __getattr__(name: str):
    """Lazy import for optional components."""
    if name == "CryptoBacktestEngine":
        from maverick_crypto.backtesting import CryptoBacktestEngine
        return CryptoBacktestEngine
    if name in ("get_crypto_strategy", "list_crypto_strategies"):
        from maverick_crypto.backtesting import strategies
        return getattr(strategies, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

