"""Tests for maverick-backtest strategies."""

import pandas as pd
import pytest

from maverick_backtest.strategies import (
    STRATEGY_TEMPLATES,
    SimpleMovingAverageStrategy,
    Strategy,
    get_strategy_info,
    get_strategy_template,
    list_available_strategies,
)
from maverick_backtest.strategies.base import Strategy as BaseStrategy


class TestStrategyImports:
    """Test that strategy components can be imported."""

    def test_strategy_base_import(self):
        """Test Strategy base class import."""
        assert Strategy is not None
        assert BaseStrategy is not None

    def test_sma_strategy_import(self):
        """Test SimpleMovingAverageStrategy import."""
        assert SimpleMovingAverageStrategy is not None

    def test_strategy_templates_import(self):
        """Test STRATEGY_TEMPLATES import."""
        assert STRATEGY_TEMPLATES is not None
        assert isinstance(STRATEGY_TEMPLATES, dict)


class TestStrategyTemplates:
    """Test strategy template functionality."""

    def test_templates_contains_required_strategies(self):
        """Test templates contain all required strategies."""
        required = [
            "sma_cross",
            "rsi",
            "macd",
            "bollinger",
            "momentum",
            "ema_cross",
            "mean_reversion",
            "breakout",
        ]
        for strategy in required:
            assert strategy in STRATEGY_TEMPLATES, f"Missing strategy: {strategy}"

    def test_template_has_required_fields(self):
        """Test each template has required fields."""
        for name, template in STRATEGY_TEMPLATES.items():
            assert "name" in template, f"{name} missing 'name'"
            assert "description" in template, f"{name} missing 'description'"
            assert "parameters" in template, f"{name} missing 'parameters'"
            assert "optimization_ranges" in template, f"{name} missing 'optimization_ranges'"

    def test_get_strategy_template(self):
        """Test get_strategy_template function."""
        template = get_strategy_template("sma_cross")
        assert template is not None
        assert template["name"] == "SMA Crossover"

    def test_get_strategy_template_invalid(self):
        """Test get_strategy_template with invalid strategy."""
        with pytest.raises(ValueError):
            get_strategy_template("invalid_strategy")

    def test_list_available_strategies(self):
        """Test list_available_strategies function."""
        strategies = list_available_strategies()
        assert isinstance(strategies, list)
        assert len(strategies) > 0
        assert "sma_cross" in strategies
        assert "rsi" in strategies

    def test_get_strategy_info(self):
        """Test get_strategy_info function."""
        info = get_strategy_info("rsi")
        assert "type" in info
        assert "name" in info
        assert "description" in info
        assert "default_parameters" in info
        assert "optimization_ranges" in info
        assert info["type"] == "rsi"
        assert info["name"] == "RSI Mean Reversion"


class TestSimpleMovingAverageStrategy:
    """Test SimpleMovingAverageStrategy class."""

    def test_create_sma_strategy(self):
        """Test creating SMA strategy."""
        strategy = SimpleMovingAverageStrategy()
        assert strategy is not None
        assert strategy.fast_period == 10
        assert strategy.slow_period == 20

    def test_sma_strategy_custom_params(self):
        """Test SMA strategy with custom parameters."""
        strategy = SimpleMovingAverageStrategy(fast_period=5, slow_period=15)
        assert strategy.fast_period == 5
        assert strategy.slow_period == 15

    def test_sma_strategy_dict_params(self):
        """Test SMA strategy with dict parameters."""
        params = {"fast_period": 8, "slow_period": 25}
        strategy = SimpleMovingAverageStrategy(parameters=params)
        assert strategy.fast_period == 8
        assert strategy.slow_period == 25

    def test_sma_strategy_generate_signals(self):
        """Test SMA strategy signal generation."""
        strategy = SimpleMovingAverageStrategy(fast_period=5, slow_period=10)

        # Create sample data
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        prices = [100 + i * 0.5 for i in range(50)]  # Uptrend
        data = pd.DataFrame({"close": prices}, index=dates)

        entries, exits = strategy.generate_signals(data)

        assert len(entries) == 50
        assert len(exits) == 50
        assert entries.dtype == bool
        assert exits.dtype == bool

    def test_sma_strategy_get_parameters(self):
        """Test getting strategy parameters."""
        strategy = SimpleMovingAverageStrategy(fast_period=12, slow_period=26)
        params = strategy.get_parameters()

        assert params["fast_period"] == 12
        assert params["slow_period"] == 26


class TestStrategyBaseClass:
    """Test Strategy abstract base class."""

    def test_strategy_is_abstract(self):
        """Test Strategy is abstract and can't be instantiated directly."""
        # Strategy has abstract methods, so we can't instantiate it directly
        assert hasattr(Strategy, "generate_signals")
        assert hasattr(Strategy, "name")
        assert hasattr(Strategy, "description")

    def test_strategy_has_required_methods(self):
        """Test Strategy has required interface methods."""
        # Check abstract methods exist
        assert hasattr(Strategy, "generate_signals")
        assert hasattr(Strategy, "validate_parameters")
        assert hasattr(Strategy, "get_default_parameters")
        assert hasattr(Strategy, "to_dict")
