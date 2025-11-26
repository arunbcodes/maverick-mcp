"""
Maverick Core Interfaces.

This module defines Protocol-based interfaces for all Maverick services.
These interfaces enable loose coupling between packages and support
dependency injection patterns.

All interfaces use Python's Protocol for structural subtyping,
allowing implementations without explicit inheritance.
"""

from maverick_core.interfaces.stock_data import (
    IStockDataFetcher,
    IStockScreener,
)
from maverick_core.interfaces.cache import (
    ICacheProvider,
    ICacheKeyGenerator,
)
from maverick_core.interfaces.persistence import (
    IRepository,
    IStockRepository,
    IPortfolioRepository,
)
from maverick_core.interfaces.technical import (
    ITechnicalAnalyzer,
)
from maverick_core.interfaces.market_calendar import (
    IMarketCalendar,
)
from maverick_core.interfaces.llm import (
    ILLMProvider,
    IResearchAgent,
    TaskType,
)
from maverick_core.interfaces.backtest import (
    IBacktestEngine,
    IStrategy,
)
from maverick_core.interfaces.config import (
    IConfigProvider,
)

__all__ = [
    # Stock Data
    "IStockDataFetcher",
    "IStockScreener",
    # Cache
    "ICacheProvider",
    "ICacheKeyGenerator",
    # Persistence
    "IRepository",
    "IStockRepository",
    "IPortfolioRepository",
    # Technical Analysis
    "ITechnicalAnalyzer",
    # Market Calendar
    "IMarketCalendar",
    # LLM
    "ILLMProvider",
    "IResearchAgent",
    "TaskType",
    # Backtest
    "IBacktestEngine",
    "IStrategy",
    # Config
    "IConfigProvider",
]
