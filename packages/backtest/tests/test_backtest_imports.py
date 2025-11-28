"""Test that package imports work correctly."""


class TestPackageImports:
    """Test that all subpackages can be imported."""

    def test_import_maverick_backtest(self):
        """Test importing the main package."""
        import maverick_backtest

        assert maverick_backtest is not None

    def test_import_strategies(self):
        """Test importing strategies subpackage."""
        from maverick_backtest import strategies

        assert strategies is not None

    def test_import_engine(self):
        """Test importing engine subpackage."""
        from maverick_backtest import engine

        assert engine is not None


class TestMainExports:
    """Test that main package exports are available."""

    def test_export_vectorbt_engine(self):
        """Test VectorBTEngine export."""
        from maverick_backtest import VectorBTEngine

        assert VectorBTEngine is not None

    def test_export_strategy(self):
        """Test Strategy export."""
        from maverick_backtest import Strategy

        assert Strategy is not None

    def test_export_strategy_templates(self):
        """Test STRATEGY_TEMPLATES export."""
        from maverick_backtest import STRATEGY_TEMPLATES

        assert STRATEGY_TEMPLATES is not None
        assert isinstance(STRATEGY_TEMPLATES, dict)

    def test_export_utility_functions(self):
        """Test utility function exports."""
        from maverick_backtest import (
            get_strategy_info,
            get_strategy_template,
            list_available_strategies,
        )

        assert get_strategy_info is not None
        assert get_strategy_template is not None
        assert list_available_strategies is not None


class TestMLStrategyExports:
    """Test ML strategy exports from main package."""

    def test_export_feature_extractor(self):
        """Test FeatureExtractor export."""
        from maverick_backtest import FeatureExtractor

        assert FeatureExtractor is not None

    def test_export_ml_predictor(self):
        """Test MLPredictor export."""
        from maverick_backtest import MLPredictor

        assert MLPredictor is not None

    def test_export_adaptive_strategy(self):
        """Test AdaptiveStrategy export."""
        from maverick_backtest import AdaptiveStrategy

        assert AdaptiveStrategy is not None

    def test_export_online_learning_strategy(self):
        """Test OnlineLearningStrategy export."""
        from maverick_backtest import OnlineLearningStrategy

        assert OnlineLearningStrategy is not None

    def test_export_hybrid_adaptive_strategy(self):
        """Test HybridAdaptiveStrategy export."""
        from maverick_backtest import HybridAdaptiveStrategy

        assert HybridAdaptiveStrategy is not None

    def test_export_strategy_ensemble(self):
        """Test StrategyEnsemble export."""
        from maverick_backtest import StrategyEnsemble

        assert StrategyEnsemble is not None

    def test_export_risk_adjusted_ensemble(self):
        """Test RiskAdjustedEnsemble export."""
        from maverick_backtest import RiskAdjustedEnsemble

        assert RiskAdjustedEnsemble is not None

    def test_export_market_regime_detector(self):
        """Test MarketRegimeDetector export."""
        from maverick_backtest import MarketRegimeDetector

        assert MarketRegimeDetector is not None

    def test_export_regime_aware_strategy(self):
        """Test RegimeAwareStrategy export."""
        from maverick_backtest import RegimeAwareStrategy

        assert RegimeAwareStrategy is not None

    def test_export_adaptive_regime_strategy(self):
        """Test AdaptiveRegimeStrategy export."""
        from maverick_backtest import AdaptiveRegimeStrategy

        assert AdaptiveRegimeStrategy is not None


class TestAnalysisExports:
    """Test analysis module exports from main package."""

    def test_export_backtest_analyzer(self):
        """Test BacktestAnalyzer export."""
        from maverick_backtest import BacktestAnalyzer

        assert BacktestAnalyzer is not None

    def test_export_strategy_optimizer(self):
        """Test StrategyOptimizer export."""
        from maverick_backtest import StrategyOptimizer

        assert StrategyOptimizer is not None

    def test_export_convert_to_native(self):
        """Test convert_to_native export."""
        from maverick_backtest import convert_to_native

        assert convert_to_native is not None

    def test_import_analysis_subpackage(self):
        """Test importing analysis subpackage."""
        from maverick_backtest import analysis

        assert analysis is not None


class TestVisualizationExports:
    """Test visualization module exports."""

    def test_import_visualization_subpackage(self):
        """Test importing visualization subpackage."""
        from maverick_backtest import visualization

        assert visualization is not None

    def test_export_set_chart_style(self):
        """Test set_chart_style export."""
        from maverick_backtest import set_chart_style

        assert set_chart_style is not None

    def test_export_image_to_base64(self):
        """Test image_to_base64 export."""
        from maverick_backtest import image_to_base64

        assert image_to_base64 is not None

    def test_export_generate_equity_curve(self):
        """Test generate_equity_curve export."""
        from maverick_backtest import generate_equity_curve

        assert generate_equity_curve is not None

    def test_export_generate_trade_scatter(self):
        """Test generate_trade_scatter export."""
        from maverick_backtest import generate_trade_scatter

        assert generate_trade_scatter is not None

    def test_export_generate_optimization_heatmap(self):
        """Test generate_optimization_heatmap export."""
        from maverick_backtest import generate_optimization_heatmap

        assert generate_optimization_heatmap is not None

    def test_export_generate_portfolio_allocation(self):
        """Test generate_portfolio_allocation export."""
        from maverick_backtest import generate_portfolio_allocation

        assert generate_portfolio_allocation is not None

    def test_export_generate_strategy_comparison(self):
        """Test generate_strategy_comparison export."""
        from maverick_backtest import generate_strategy_comparison

        assert generate_strategy_comparison is not None

    def test_export_generate_performance_dashboard(self):
        """Test generate_performance_dashboard export."""
        from maverick_backtest import generate_performance_dashboard

        assert generate_performance_dashboard is not None

    def test_export_generate_returns_distribution(self):
        """Test generate_returns_distribution export."""
        from maverick_backtest import generate_returns_distribution

        assert generate_returns_distribution is not None

    def test_export_generate_rolling_metrics(self):
        """Test generate_rolling_metrics export."""
        from maverick_backtest import generate_rolling_metrics

        assert generate_rolling_metrics is not None


class TestPersistenceExports:
    """Test persistence module exports."""

    def test_import_persistence_subpackage(self):
        """Test importing persistence subpackage."""
        from maverick_backtest import persistence

        assert persistence is not None

    def test_export_backtest_result_protocol(self):
        """Test BacktestResultProtocol export."""
        from maverick_backtest import BacktestResultProtocol

        assert BacktestResultProtocol is not None

    def test_export_backtest_trade_protocol(self):
        """Test BacktestTradeProtocol export."""
        from maverick_backtest import BacktestTradeProtocol

        assert BacktestTradeProtocol is not None

    def test_export_optimization_result_protocol(self):
        """Test OptimizationResultProtocol export."""
        from maverick_backtest import OptimizationResultProtocol

        assert OptimizationResultProtocol is not None

    def test_export_walk_forward_test_protocol(self):
        """Test WalkForwardTestProtocol export."""
        from maverick_backtest import WalkForwardTestProtocol

        assert WalkForwardTestProtocol is not None

    def test_export_database_session_protocol(self):
        """Test DatabaseSessionProtocol export."""
        from maverick_backtest import DatabaseSessionProtocol

        assert DatabaseSessionProtocol is not None

    def test_export_backtest_persistence_repository(self):
        """Test BacktestPersistenceRepository export."""
        from maverick_backtest import BacktestPersistenceRepository

        assert BacktestPersistenceRepository is not None

    def test_export_backtest_persistence_error(self):
        """Test BacktestPersistenceError export."""
        from maverick_backtest import BacktestPersistenceError

        assert BacktestPersistenceError is not None
        # Test it's an exception
        assert issubclass(BacktestPersistenceError, Exception)

    def test_export_sqlalchemy_backtest_repository(self):
        """Test SQLAlchemyBacktestRepository export."""
        from maverick_backtest import SQLAlchemyBacktestRepository

        assert SQLAlchemyBacktestRepository is not None


class TestBatchExports:
    """Test batch processing module exports."""

    def test_import_batch_subpackage(self):
        """Test importing batch subpackage."""
        from maverick_backtest import batch

        assert batch is not None

    def test_export_execution_context(self):
        """Test ExecutionContext export."""
        from maverick_backtest import ExecutionContext

        assert ExecutionContext is not None

    def test_export_execution_result(self):
        """Test ExecutionResult export."""
        from maverick_backtest import ExecutionResult

        assert ExecutionResult is not None

    def test_export_batch_processor(self):
        """Test BatchProcessor export."""
        from maverick_backtest import BatchProcessor

        assert BatchProcessor is not None

    def test_export_cache_manager_protocol(self):
        """Test CacheManagerProtocol export."""
        from maverick_backtest import CacheManagerProtocol

        assert CacheManagerProtocol is not None

    def test_export_backtest_engine_protocol(self):
        """Test BacktestEngineProtocol export."""
        from maverick_backtest import BacktestEngineProtocol

        assert BacktestEngineProtocol is not None

    def test_execution_context_init(self):
        """Test ExecutionContext can be instantiated."""
        from maverick_backtest import ExecutionContext

        ctx = ExecutionContext(
            strategy_id="test_strategy",
            symbol="AAPL",
            strategy_type="sma_cross",
            parameters={"fast": 10, "slow": 20},
            start_date="2024-01-01",
            end_date="2024-12-31",
        )
        assert ctx is not None
        assert ctx.symbol == "AAPL"
        assert ctx.strategy_type == "sma_cross"
        assert ctx.initial_capital == 10000.0  # default

    def test_execution_result_init(self):
        """Test ExecutionResult can be instantiated."""
        from maverick_backtest import ExecutionContext, ExecutionResult

        ctx = ExecutionContext(
            strategy_id="test",
            symbol="AAPL",
            strategy_type="sma_cross",
            parameters={},
            start_date="2024-01-01",
            end_date="2024-12-31",
        )
        result = ExecutionResult(
            context=ctx,
            success=True,
            result={"metrics": {"sharpe_ratio": 1.5}},
        )
        assert result is not None
        assert result.success is True
        assert result.error is None


class TestAllExports:
    """Test that __all__ exports are complete."""

    def test_all_exports_importable(self):
        """Test all items in __all__ can be imported."""
        import maverick_backtest

        for name in maverick_backtest.__all__:
            assert hasattr(maverick_backtest, name), f"Missing export: {name}"

    def test_visualization_exports_in_all(self):
        """Test visualization exports are in __all__."""
        import maverick_backtest

        viz_exports = [
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
        ]
        for name in viz_exports:
            assert name in maverick_backtest.__all__, f"Missing in __all__: {name}"

    def test_persistence_exports_in_all(self):
        """Test persistence exports are in __all__."""
        import maverick_backtest

        persistence_exports = [
            "BacktestResultProtocol",
            "BacktestTradeProtocol",
            "OptimizationResultProtocol",
            "WalkForwardTestProtocol",
            "DatabaseSessionProtocol",
            "BacktestPersistenceRepository",
            "BacktestPersistenceError",
            "SQLAlchemyBacktestRepository",
        ]
        for name in persistence_exports:
            assert name in maverick_backtest.__all__, f"Missing in __all__: {name}"

    def test_batch_exports_in_all(self):
        """Test batch exports are in __all__."""
        import maverick_backtest

        batch_exports = [
            "ExecutionContext",
            "ExecutionResult",
            "BatchProcessor",
            "CacheManagerProtocol",
            "BacktestEngineProtocol",
        ]
        for name in batch_exports:
            assert name in maverick_backtest.__all__, f"Missing in __all__: {name}"
