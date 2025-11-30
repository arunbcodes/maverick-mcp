"""
Maverick Crypto - Cryptocurrency data and analysis package.

A standalone, portable package for cryptocurrency data fetching,
technical analysis, and MCP tool integration.

Features:
    - Multi-provider support (yfinance, CoinGecko)
    - 24/7 market calendar handling
    - Technical analysis via pandas-ta
    - SQLAlchemy models for persistence
    - MCP tools for Claude Desktop

Example:
    >>> from maverick_crypto import CryptoDataProvider
    >>> provider = CryptoDataProvider()
    >>> btc = await provider.get_crypto_data("BTC", days=90)

Standalone Deployment:
    This package can be deployed independently or moved to a separate
    repository without dependencies on other maverick packages.
"""

from maverick_crypto.providers import CryptoDataProvider
from maverick_crypto.calendar import CryptoCalendarService
from maverick_crypto.models import Crypto, CryptoPriceCache

__version__ = "0.1.0"

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

