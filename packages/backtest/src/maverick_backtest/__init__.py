"""
Maverick Backtest Package.

Backtesting engine and strategies for Maverick stock analysis.
Uses VectorBT for high-performance vectorized backtesting.
"""

# Engine
from maverick_backtest.engine import IDataProvider, VectorBTEngine

# Strategies
from maverick_backtest.strategies import (
    STRATEGY_TEMPLATES,
    AdaptiveRegimeStrategy,
    AdaptiveStrategy,
    FeatureExtractor,
    HybridAdaptiveStrategy,
    MarketRegimeDetector,
    MLPredictor,
    OnlineLearningStrategy,
    RegimeAwareStrategy,
    RiskAdjustedEnsemble,
    SimpleMovingAverageStrategy,
    Strategy,
    StrategyEnsemble,
    get_strategy_info,
    get_strategy_template,
    list_available_strategies,
)

# Analysis
from maverick_backtest.analysis import (
    BacktestAnalyzer,
    StrategyOptimizer,
    convert_to_native,
)

__all__ = [
    # Engine
    "VectorBTEngine",
    "IDataProvider",
    # Strategies - Base
    "Strategy",
    "SimpleMovingAverageStrategy",
    "STRATEGY_TEMPLATES",
    "get_strategy_template",
    "list_available_strategies",
    "get_strategy_info",
    # Strategies - ML
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
    # Analysis
    "BacktestAnalyzer",
    "StrategyOptimizer",
    "convert_to_native",
]
