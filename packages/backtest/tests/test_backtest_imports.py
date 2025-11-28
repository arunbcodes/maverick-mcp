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
