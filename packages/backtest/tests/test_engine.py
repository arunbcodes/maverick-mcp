"""Tests for maverick-backtest engine."""

import pytest

from maverick_backtest.engine import IDataProvider, VectorBTEngine


class TestEngineImports:
    """Test that engine components can be imported."""

    def test_vectorbt_engine_import(self):
        """Test VectorBTEngine import."""
        assert VectorBTEngine is not None

    def test_data_provider_protocol_import(self):
        """Test IDataProvider protocol import."""
        assert IDataProvider is not None


class TestVectorBTEngine:
    """Test VectorBTEngine class."""

    def test_create_engine(self):
        """Test creating engine without providers."""
        engine = VectorBTEngine()
        assert engine is not None
        assert engine.data_provider is None
        assert engine.cache is None

    def test_engine_default_settings(self):
        """Test engine has correct default settings."""
        engine = VectorBTEngine()
        assert engine.enable_memory_optimization is True

    def test_engine_custom_settings(self):
        """Test engine accepts custom settings."""
        engine = VectorBTEngine(enable_memory_optimization=False)
        assert engine.enable_memory_optimization is False

    def test_engine_has_required_methods(self):
        """Test engine has all required interface methods."""
        engine = VectorBTEngine()

        # Core methods
        assert hasattr(engine, "run_backtest")
        assert hasattr(engine, "get_historical_data")
        assert hasattr(engine, "optimize_parameters")

        # Signal generation
        assert hasattr(engine, "_generate_signals")
        assert hasattr(engine, "_sma_crossover_signals")
        assert hasattr(engine, "_rsi_signals")
        assert hasattr(engine, "_macd_signals")
        assert hasattr(engine, "_bollinger_bands_signals")
        assert hasattr(engine, "_momentum_signals")

    def test_engine_signal_methods(self):
        """Test engine has all signal generation methods."""
        engine = VectorBTEngine()

        signal_methods = [
            "_sma_crossover_signals",
            "_rsi_signals",
            "_macd_signals",
            "_bollinger_bands_signals",
            "_momentum_signals",
            "_ema_crossover_signals",
            "_mean_reversion_signals",
            "_breakout_signals",
            "_volume_momentum_signals",
            "_online_learning_signals",
            "_regime_aware_signals",
            "_ensemble_signals",
        ]

        for method in signal_methods:
            assert hasattr(engine, method), f"Missing method: {method}"

    def test_engine_metric_methods(self):
        """Test engine has metric extraction methods."""
        engine = VectorBTEngine()

        assert hasattr(engine, "_extract_metrics")
        assert hasattr(engine, "_extract_trades")
        assert hasattr(engine, "_calculate_kelly")
        assert hasattr(engine, "_calculate_recovery_factor")
        assert hasattr(engine, "_calculate_risk_reward")
        assert hasattr(engine, "_get_metric_value")


class TestEngineUtilities:
    """Test VectorBTEngine utility methods."""

    def test_ensure_timezone_naive(self):
        """Test timezone handling utility."""
        import pandas as pd

        engine = VectorBTEngine()

        # Create timezone-aware DataFrame
        dates = pd.date_range("2024-01-01", periods=10, freq="D", tz="UTC")
        df = pd.DataFrame({"close": range(10)}, index=dates)

        # Should remove timezone
        result = engine._ensure_timezone_naive(df)
        assert result.index.tz is None

    def test_ensure_timezone_naive_already_naive(self):
        """Test timezone handling with already naive DataFrame."""
        import pandas as pd

        engine = VectorBTEngine()

        # Create timezone-naive DataFrame
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame({"close": range(10)}, index=dates)

        # Should not change anything
        result = engine._ensure_timezone_naive(df)
        assert result.index.tz is None


class TestEngineSignalGeneration:
    """Test signal generation methods."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return VectorBTEngine()

    @pytest.fixture
    def sample_data(self):
        """Create sample price data."""
        import pandas as pd

        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        # Create trending data with some noise
        prices = [100 + i * 0.5 + (i % 5) for i in range(100)]
        volumes = [1000000 + i * 10000 for i in range(100)]
        return pd.DataFrame({
            "close": prices,
            "volume": volumes,
        }, index=dates)

    def test_sma_crossover_signals(self, engine, sample_data):
        """Test SMA crossover signal generation."""
        params = {"fast_period": 5, "slow_period": 10}
        entries, exits = engine._sma_crossover_signals(
            sample_data["close"], params
        )

        assert len(entries) == len(sample_data)
        assert len(exits) == len(sample_data)

    def test_rsi_signals(self, engine, sample_data):
        """Test RSI signal generation."""
        params = {"period": 14, "oversold": 30, "overbought": 70}
        entries, exits = engine._rsi_signals(sample_data["close"], params)

        assert len(entries) == len(sample_data)
        assert len(exits) == len(sample_data)

    def test_macd_signals(self, engine, sample_data):
        """Test MACD signal generation."""
        params = {"fast_period": 12, "slow_period": 26, "signal_period": 9}
        entries, exits = engine._macd_signals(sample_data["close"], params)

        assert len(entries) == len(sample_data)
        assert len(exits) == len(sample_data)

    def test_bollinger_signals(self, engine, sample_data):
        """Test Bollinger Bands signal generation."""
        params = {"period": 20, "std_dev": 2}
        entries, exits = engine._bollinger_bands_signals(
            sample_data["close"], params
        )

        assert len(entries) == len(sample_data)
        assert len(exits) == len(sample_data)

    def test_momentum_signals(self, engine, sample_data):
        """Test momentum signal generation."""
        params = {"lookback": 20, "threshold": 0.05}
        entries, exits = engine._momentum_signals(sample_data["close"], params)

        assert len(entries) == len(sample_data)
        assert len(exits) == len(sample_data)

    def test_generate_signals_sma(self, engine, sample_data):
        """Test _generate_signals with sma_cross strategy."""
        params = {"fast_period": 5, "slow_period": 10}
        entries, exits = engine._generate_signals(sample_data, "sma_cross", params)

        assert len(entries) == len(sample_data)
        assert len(exits) == len(sample_data)

    def test_generate_signals_invalid_strategy(self, engine, sample_data):
        """Test _generate_signals with invalid strategy."""
        with pytest.raises(ValueError, match="Unknown strategy type"):
            engine._generate_signals(sample_data, "invalid_strategy", {})

    def test_generate_signals_missing_close_column(self, engine):
        """Test _generate_signals with missing close column."""
        import pandas as pd

        data = pd.DataFrame({"open": [1, 2, 3], "high": [1, 2, 3]})
        with pytest.raises(ValueError, match="Missing 'close' column"):
            engine._generate_signals(data, "sma_cross", {})
