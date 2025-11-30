"""
Maverick Crypto Data Providers.

Multi-provider support for cryptocurrency data fetching.

Providers:
    - CryptoDataProvider: Primary provider using yfinance (default)
    - CoinGeckoProvider: Optional provider for broader coverage (6000+ coins)
"""

from maverick_crypto.providers.crypto_provider import CryptoDataProvider

__all__ = [
    "CryptoDataProvider",
]

# Optional CoinGecko provider
try:
    from maverick_crypto.providers.coingecko_provider import CoinGeckoProvider
    __all__.append("CoinGeckoProvider")
except ImportError:
    # pycoingecko not installed
    pass

