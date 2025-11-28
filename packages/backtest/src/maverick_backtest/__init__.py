"""
Maverick Backtest Package.

Backtesting engine and strategies for Maverick stock analysis.
Uses VectorBT for high-performance vectorized backtesting.

Modules:
    - engine: VectorBT-based backtesting engine
    - strategies: Trading strategies (traditional and ML-based)
    - analysis: Performance analysis and optimization
    - visualization: Chart generation for backtest results
    - persistence: Database persistence for backtest results
    - batch: Parallel batch processing for multiple backtests
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

# Visualization
from maverick_backtest.visualization import (
    generate_equity_curve,
    generate_optimization_heatmap,
    generate_performance_dashboard,
    generate_portfolio_allocation,
    generate_returns_distribution,
    generate_rolling_metrics,
    generate_strategy_comparison,
    generate_trade_scatter,
    image_to_base64,
    set_chart_style,
)

# Persistence
from maverick_backtest.persistence import (
    BacktestPersistenceError,
    BacktestPersistenceRepository,
    BacktestResultProtocol,
    BacktestTradeProtocol,
    DatabaseSessionProtocol,
    OptimizationResultProtocol,
    SQLAlchemyBacktestRepository,
    WalkForwardTestProtocol,
)

# Batch Processing
from maverick_backtest.batch import (
    BacktestEngineProtocol,
    BatchProcessor,
    CacheManagerProtocol,
    ExecutionContext,
    ExecutionResult,
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
    # Visualization
    "set_chart_style",
    "image_to_base64",
    "generate_equity_curve",
    "generate_trade_scatter",
    "generate_optimization_heatmap",
    "generate_portfolio_allocation",
    "generate_strategy_comparison",
    "generate_performance_dashboard",
    "generate_returns_distribution",
    "generate_rolling_metrics",
    # Persistence
    "BacktestResultProtocol",
    "BacktestTradeProtocol",
    "OptimizationResultProtocol",
    "WalkForwardTestProtocol",
    "DatabaseSessionProtocol",
    "BacktestPersistenceRepository",
    "BacktestPersistenceError",
    "SQLAlchemyBacktestRepository",
    # Batch Processing
    "ExecutionContext",
    "ExecutionResult",
    "BatchProcessor",
    "CacheManagerProtocol",
    "BacktestEngineProtocol",
]
