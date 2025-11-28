"""
Database Models.

SQLAlchemy models for financial data storage and analysis.
"""

from maverick_data.models.backtest import (
    BacktestPortfolio,
    BacktestResult,
    BacktestTrade,
    OptimizationResult,
    WalkForwardTest,
)
from maverick_data.models.base import Base, TimestampMixin
from maverick_data.models.exchange_rate import ExchangeRate
from maverick_data.models.news import NewsArticle
from maverick_data.models.portfolio import PortfolioPosition, UserPortfolio
from maverick_data.models.price_cache import PriceCache
from maverick_data.models.screening import (
    MaverickBearStocks,
    MaverickStocks,
    SupplyDemandBreakoutStocks,
)
from maverick_data.models.stock import Stock
from maverick_data.models.technical import TechnicalCache

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # Core models
    "Stock",
    "PriceCache",
    "ExchangeRate",
    "NewsArticle",
    "TechnicalCache",
    # Screening models
    "MaverickStocks",
    "MaverickBearStocks",
    "SupplyDemandBreakoutStocks",
    # Backtest models
    "BacktestResult",
    "BacktestTrade",
    "OptimizationResult",
    "WalkForwardTest",
    "BacktestPortfolio",
    # Portfolio models
    "UserPortfolio",
    "PortfolioPosition",
]
