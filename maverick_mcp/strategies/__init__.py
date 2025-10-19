"""
Market strategies for MaverickMCP.

Implements the Strategy pattern to encapsulate market-specific behavior
for different stock exchanges (US, Indian NSE/BSE, Crypto, etc.).
"""

from maverick_mcp.strategies.market_strategy import (
    IMarketStrategy,
    BaseMarketStrategy,
    USMarketStrategy,
    IndianNSEMarketStrategy,
    IndianBSEMarketStrategy,
    MarketStrategyFactory,
)

__all__ = [
    "IMarketStrategy",
    "BaseMarketStrategy",
    "USMarketStrategy",
    "IndianNSEMarketStrategy",
    "IndianBSEMarketStrategy",
    "MarketStrategyFactory",
]

