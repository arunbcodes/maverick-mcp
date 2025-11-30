"""
Maverick Crypto Backtesting Module.

Provides cryptocurrency-specific backtesting with VectorBT integration.
All strategies are adjusted for crypto's higher volatility.
"""

from maverick_crypto.backtesting.engine import CryptoBacktestEngine
from maverick_crypto.backtesting.strategies import (
    CryptoMomentumStrategy,
    CryptoMeanReversionStrategy,
    CryptoBreakoutStrategy,
    CryptoRSIStrategy,
    CryptoMACDStrategy,
    CryptoBollingerStrategy,
    get_crypto_strategy,
    list_crypto_strategies,
)

__all__ = [
    "CryptoBacktestEngine",
    "CryptoMomentumStrategy",
    "CryptoMeanReversionStrategy",
    "CryptoBreakoutStrategy",
    "CryptoRSIStrategy",
    "CryptoMACDStrategy",
    "CryptoBollingerStrategy",
    "get_crypto_strategy",
    "list_crypto_strategies",
]

