"""
Maverick Crypto Data Providers.

Multi-provider support for cryptocurrency data fetching.

Providers:
    - CryptoDataProvider: Primary provider using yfinance (default)
    - CoinGeckoProvider: Optional provider for broader coverage (6000+ coins)
    - FearGreedProvider: Crypto Fear & Greed Index (always available)
"""

from maverick_crypto.providers.crypto_provider import CryptoDataProvider

__all__ = [
    "CryptoDataProvider",
]

# Optional CoinGecko provider
try:
    from maverick_crypto.providers.coingecko_provider import (
        CoinGeckoProvider,
        FearGreedProvider,
        HAS_COINGECKO,
    )
    __all__.extend(["CoinGeckoProvider", "FearGreedProvider", "HAS_COINGECKO"])
except ImportError:
    # pycoingecko not installed, but FearGreedProvider doesn't need it
    HAS_COINGECKO = False
    CoinGeckoProvider = None
    
    # FearGreedProvider can still work (only needs httpx)
    try:
        from maverick_crypto.providers.coingecko_provider import FearGreedProvider
        __all__.append("FearGreedProvider")
    except ImportError:
        FearGreedProvider = None

