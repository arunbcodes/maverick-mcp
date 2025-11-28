"""
Backtesting Strategies.

Trading strategies for backtesting including:
- SMA/EMA crossover
- RSI-based strategies
- MACD strategies
- Bollinger Bands strategies
- ML-based adaptive strategies
"""

from maverick_backtest.strategies.base import Strategy
from maverick_backtest.strategies.ml import (
    AdaptiveRegimeStrategy,
    AdaptiveStrategy,
    FeatureExtractor,
    HybridAdaptiveStrategy,
    MarketRegimeDetector,
    MLPredictor,
    OnlineLearningStrategy,
    RegimeAwareStrategy,
    RiskAdjustedEnsemble,
    StrategyEnsemble,
)
from maverick_backtest.strategies.templates import (
    STRATEGY_TEMPLATES,
    SimpleMovingAverageStrategy,
    get_strategy_info,
    get_strategy_template,
    list_available_strategies,
)

__all__ = [
    # Base
    "Strategy",
    # Templates
    "SimpleMovingAverageStrategy",
    "STRATEGY_TEMPLATES",
    "get_strategy_template",
    "list_available_strategies",
    "get_strategy_info",
    # ML Strategies
    "FeatureExtractor",
    "MLPredictor",
    "AdaptiveStrategy",
    "OnlineLearningStrategy",
    "HybridAdaptiveStrategy",
    "StrategyEnsemble",
    "RiskAdjustedEnsemble",
    "MarketRegimeDetector",
    "RegimeAwareStrategy",
    "AdaptiveRegimeStrategy",
]
