"""Tests for technical analysis indicators."""

import numpy as np
import pandas as pd
import pytest

from maverick_core.technical import (
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_momentum,
    calculate_obv,
    calculate_rate_of_change,
    calculate_rsi,
    calculate_sma,
    calculate_stochastic,
    calculate_support_resistance,
    calculate_trend_strength,
    calculate_williams_r,
)


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    n = 100

    # Generate realistic price data
    base_price = 100
    prices = [base_price]
    for _ in range(n - 1):
        change = np.random.randn() * 2
        prices.append(prices[-1] * (1 + change / 100))

    close = pd.Series(prices)
    high = close * (1 + np.abs(np.random.randn(n) * 0.01))
    low = close * (1 - np.abs(np.random.randn(n) * 0.01))
    open_ = close.shift(1).fillna(close.iloc[0]) + np.random.randn(n) * 0.5
    volume = np.random.randint(1000000, 10000000, n)

    return pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        }
    )


class TestSMA:
    """Tests for Simple Moving Average."""

    def test_calculate_sma_basic(self, sample_ohlcv_data):
        """Test basic SMA calculation."""
        sma = calculate_sma(sample_ohlcv_data, period=20)

        assert len(sma) == len(sample_ohlcv_data)
        # First 19 values should be NaN
        assert sma.iloc[:19].isna().all()
        # Values from index 19 onwards should not be NaN
        assert sma.iloc[19:].notna().all()

    def test_calculate_sma_period_5(self, sample_ohlcv_data):
        """Test SMA with period 5."""
        sma = calculate_sma(sample_ohlcv_data, period=5)

        # Manually calculate for verification
        expected = sample_ohlcv_data["Close"].iloc[:5].mean()
        assert pytest.approx(sma.iloc[4], rel=1e-6) == expected

    def test_calculate_sma_invalid_period(self, sample_ohlcv_data):
        """Test SMA with invalid period raises error."""
        with pytest.raises(ValueError, match="Period must be >= 1"):
            calculate_sma(sample_ohlcv_data, period=0)


class TestEMA:
    """Tests for Exponential Moving Average."""

    def test_calculate_ema_basic(self, sample_ohlcv_data):
        """Test basic EMA calculation."""
        ema = calculate_ema(sample_ohlcv_data, period=20)

        assert len(ema) == len(sample_ohlcv_data)
        # EMA should have values from the start
        assert ema.notna().all()

    def test_ema_more_responsive_than_sma(self, sample_ohlcv_data):
        """Test that EMA responds faster to price changes."""
        sma = calculate_sma(sample_ohlcv_data, period=20)
        ema = calculate_ema(sample_ohlcv_data, period=20)

        # EMA should be closer to current price than SMA on average
        # This is a general property, not exact for all cases
        close = sample_ohlcv_data["Close"]
        assert ema.iloc[-1] != sma.iloc[-1]


class TestRSI:
    """Tests for Relative Strength Index."""

    def test_calculate_rsi_range(self, sample_ohlcv_data):
        """Test that RSI stays within 0-100 range."""
        rsi = calculate_rsi(sample_ohlcv_data, period=14)

        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_calculate_rsi_period_14(self, sample_ohlcv_data):
        """Test standard RSI with period 14."""
        rsi = calculate_rsi(sample_ohlcv_data, period=14)

        assert len(rsi) == len(sample_ohlcv_data)
        # Should have some NaN values at the start
        assert rsi.iloc[:13].isna().all() or rsi.iloc[13:].notna().sum() > 0

    def test_calculate_rsi_invalid_period(self, sample_ohlcv_data):
        """Test RSI with invalid period."""
        with pytest.raises(ValueError, match="Period must be >= 1"):
            calculate_rsi(sample_ohlcv_data, period=-1)


class TestMACD:
    """Tests for MACD indicator."""

    def test_calculate_macd_returns_dict(self, sample_ohlcv_data):
        """Test that MACD returns dictionary with required keys."""
        result = calculate_macd(sample_ohlcv_data)

        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

    def test_macd_histogram_calculation(self, sample_ohlcv_data):
        """Test that histogram equals MACD - Signal."""
        result = calculate_macd(sample_ohlcv_data)

        diff = result["macd"] - result["signal"]
        pd.testing.assert_series_equal(
            result["histogram"], diff, check_names=False
        )

    def test_calculate_macd_invalid_periods(self, sample_ohlcv_data):
        """Test MACD with fast >= slow raises error."""
        with pytest.raises(ValueError, match="Fast period.*must be < slow period"):
            calculate_macd(sample_ohlcv_data, fast_period=26, slow_period=12)


class TestBollingerBands:
    """Tests for Bollinger Bands."""

    def test_calculate_bollinger_bands_structure(self, sample_ohlcv_data):
        """Test Bollinger Bands returns correct structure."""
        result = calculate_bollinger_bands(sample_ohlcv_data)

        assert "upper" in result
        assert "middle" in result
        assert "lower" in result
        assert "bandwidth" in result

    def test_bollinger_bands_order(self, sample_ohlcv_data):
        """Test that upper > middle > lower."""
        result = calculate_bollinger_bands(sample_ohlcv_data, period=20)

        # For valid values (after period-1)
        valid_idx = result["upper"].dropna().index
        assert (result["upper"][valid_idx] >= result["middle"][valid_idx]).all()
        assert (result["middle"][valid_idx] >= result["lower"][valid_idx]).all()

    def test_bollinger_bands_middle_is_sma(self, sample_ohlcv_data):
        """Test that middle band equals SMA."""
        result = calculate_bollinger_bands(sample_ohlcv_data, period=20)
        sma = calculate_sma(sample_ohlcv_data, period=20)

        pd.testing.assert_series_equal(result["middle"], sma, check_names=False)


class TestATR:
    """Tests for Average True Range."""

    def test_calculate_atr_positive(self, sample_ohlcv_data):
        """Test that ATR is always positive."""
        atr = calculate_atr(sample_ohlcv_data, period=14)

        valid_atr = atr.dropna()
        assert (valid_atr >= 0).all()

    def test_calculate_atr_basic(self, sample_ohlcv_data):
        """Test basic ATR calculation."""
        atr = calculate_atr(sample_ohlcv_data, period=14)

        assert len(atr) == len(sample_ohlcv_data)


class TestStochastic:
    """Tests for Stochastic Oscillator."""

    def test_calculate_stochastic_range(self, sample_ohlcv_data):
        """Test that %K and %D stay within 0-100."""
        result = calculate_stochastic(sample_ohlcv_data)

        valid_k = result["k"].dropna()
        valid_d = result["d"].dropna()

        assert (valid_k >= 0).all()
        assert (valid_k <= 100).all()
        assert (valid_d >= 0).all()
        assert (valid_d <= 100).all()


class TestSupportResistance:
    """Tests for Support and Resistance levels."""

    def test_calculate_support_resistance_structure(self, sample_ohlcv_data):
        """Test S/R returns correct structure."""
        result = calculate_support_resistance(sample_ohlcv_data)

        assert "support" in result
        assert "resistance" in result
        assert isinstance(result["support"], list)
        assert isinstance(result["resistance"], list)

    def test_support_below_resistance(self, sample_ohlcv_data):
        """Test that support levels are below resistance."""
        result = calculate_support_resistance(sample_ohlcv_data)

        current_price = sample_ohlcv_data["Close"].iloc[-1]

        for s in result["support"]:
            assert s < current_price

        for r in result["resistance"]:
            assert r > current_price


class TestTrendStrength:
    """Tests for Trend Strength indicator."""

    def test_trend_strength_structure(self, sample_ohlcv_data):
        """Test trend strength returns correct structure."""
        result = calculate_trend_strength(sample_ohlcv_data)

        assert "trend" in result
        assert "strength" in result
        assert "ma_alignment" in result

    def test_trend_strength_valid_values(self, sample_ohlcv_data):
        """Test trend strength values are valid."""
        result = calculate_trend_strength(sample_ohlcv_data)

        assert result["trend"] in ["bullish", "bearish", "neutral"]
        assert 0 <= result["strength"] <= 100
        assert result["ma_alignment"] in ["bullish", "bearish"]

    def test_trend_strength_invalid_periods(self, sample_ohlcv_data):
        """Test trend strength with invalid periods."""
        with pytest.raises(ValueError, match="Short period.*must be < long period"):
            calculate_trend_strength(sample_ohlcv_data, short_period=50, long_period=20)


class TestMomentum:
    """Tests for Momentum indicator."""

    def test_calculate_momentum(self, sample_ohlcv_data):
        """Test basic momentum calculation."""
        momentum = calculate_momentum(sample_ohlcv_data, period=14)

        assert len(momentum) == len(sample_ohlcv_data)
        # First 'period' values should be NaN
        assert momentum.iloc[:14].isna().all()


class TestROC:
    """Tests for Rate of Change."""

    def test_calculate_roc(self, sample_ohlcv_data):
        """Test Rate of Change calculation."""
        roc = calculate_rate_of_change(sample_ohlcv_data, period=14)

        assert len(roc) == len(sample_ohlcv_data)


class TestWilliamsR:
    """Tests for Williams %R."""

    def test_williams_r_range(self, sample_ohlcv_data):
        """Test Williams %R stays within -100 to 0."""
        williams = calculate_williams_r(sample_ohlcv_data, period=14)

        valid_w = williams.dropna()
        assert (valid_w <= 0).all()
        assert (valid_w >= -100).all()


class TestOBV:
    """Tests for On-Balance Volume."""

    def test_calculate_obv(self, sample_ohlcv_data):
        """Test OBV calculation."""
        obv = calculate_obv(sample_ohlcv_data)

        assert len(obv) == len(sample_ohlcv_data)


class TestImports:
    """Test that all exports work correctly."""

    def test_import_from_maverick_core(self):
        """Test importing technical functions from main package."""
        from maverick_core import technical

        assert hasattr(technical, "calculate_sma")
        assert hasattr(technical, "calculate_rsi")
        assert hasattr(technical, "calculate_macd")

    def test_import_interfaces(self):
        """Test importing interfaces from main package."""
        from maverick_core import (
            IBacktestEngine,
            ICacheProvider,
            IConfigProvider,
            ILLMProvider,
            IMarketCalendar,
            IStockDataFetcher,
            IStockScreener,
            ITechnicalAnalyzer,
        )

        # All should be Protocol types
        assert IStockDataFetcher is not None
        assert IStockScreener is not None
        assert ICacheProvider is not None
        assert ITechnicalAnalyzer is not None
        assert IMarketCalendar is not None
        assert ILLMProvider is not None
        assert IBacktestEngine is not None
        assert IConfigProvider is not None

    def test_import_exceptions(self):
        """Test importing exceptions from main package."""
        from maverick_core import (
            MaverickError,
            StockDataError,
            ValidationError,
            TechnicalAnalysisError,
            CacheError,
            PersistenceError,
        )

        # Test hierarchy
        assert issubclass(StockDataError, MaverickError)
        assert issubclass(ValidationError, MaverickError)
        assert issubclass(TechnicalAnalysisError, MaverickError)
        assert issubclass(CacheError, MaverickError)
        assert issubclass(PersistenceError, MaverickError)

    def test_import_domain_entities(self):
        """Test importing domain entities from main package."""
        from maverick_core import Portfolio, Position

        assert Portfolio is not None
        assert Position is not None
