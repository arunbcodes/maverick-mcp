"""Machine learning enhanced trading strategies."""

from maverick_backtest.strategies.ml.adaptive import (
    AdaptiveStrategy,
    HybridAdaptiveStrategy,
    OnlineLearningStrategy,
)
from maverick_backtest.strategies.ml.ensemble import (
    RiskAdjustedEnsemble,
    StrategyEnsemble,
)
from maverick_backtest.strategies.ml.feature_engineering import (
    FeatureExtractor,
    MLPredictor,
)
from maverick_backtest.strategies.ml.regime_aware import (
    AdaptiveRegimeStrategy,
    MarketRegimeDetector,
    RegimeAwareStrategy,
)

__all__ = [
    # Feature engineering
    "FeatureExtractor",
    "MLPredictor",
    # Adaptive strategies
    "AdaptiveStrategy",
    "OnlineLearningStrategy",
    "HybridAdaptiveStrategy",
    # Ensemble strategies
    "StrategyEnsemble",
    "RiskAdjustedEnsemble",
    # Regime-aware strategies
    "MarketRegimeDetector",
    "RegimeAwareStrategy",
    "AdaptiveRegimeStrategy",
]
