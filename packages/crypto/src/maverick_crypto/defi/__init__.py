"""
Maverick Crypto DeFi Module.

Provides DeFi metrics including TVL, protocol data, and on-chain analytics.

Data Sources:
    - DefiLlama: TVL, protocol rankings, chain data (free, no API key)
    - CoinGecko: On-chain DEX data via GeckoTerminal
"""

from maverick_crypto.defi.defillama import (
    DefiLlamaProvider,
)
from maverick_crypto.defi.onchain import (
    OnChainProvider,
)

__all__ = [
    "DefiLlamaProvider",
    "OnChainProvider",
]

