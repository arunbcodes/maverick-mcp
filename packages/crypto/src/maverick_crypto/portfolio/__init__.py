"""
Maverick Crypto Portfolio Module.

Provides mixed portfolio optimization for stocks + crypto.
Enables correlation analysis and efficient frontier optimization.
"""

from maverick_crypto.portfolio.mixed_portfolio import (
    MixedPortfolioService,
    AssetType,
    PortfolioAsset,
)
from maverick_crypto.portfolio.optimizer import (
    PortfolioOptimizer,
    OptimizationObjective,
)
from maverick_crypto.portfolio.correlation import (
    CorrelationAnalyzer,
)

__all__ = [
    "MixedPortfolioService",
    "AssetType",
    "PortfolioAsset",
    "PortfolioOptimizer",
    "OptimizationObjective",
    "CorrelationAnalyzer",
]

