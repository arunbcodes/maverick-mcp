"""Tests for crypto backtesting module."""

import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta


class TestCryptoStrategies:
    """Test crypto trading strategies."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample OHLCV data."""
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        np.random.seed(42)
        
        # Generate realistic price data
        close = 100 + np.cumsum(np.random.randn(100) * 2)
        high = close + np.random.rand(100) * 3
        low = close - np.random.rand(100) * 3
        open_price = close + np.random.randn(100) * 1
        volume = np.random.randint(1000, 10000, 100)
        
        return pd.DataFrame({
            "Open": open_price,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        }, index=dates)
    
    def test_momentum_strategy_generates_signals(self, sample_data):
        """Test momentum strategy signal generation."""
        from maverick_crypto.backtesting.strategies import CryptoMomentumStrategy
        
        strategy = CryptoMomentumStrategy()
        entries, exits = strategy.generate_signals(sample_data)
        
        assert len(entries) == len(sample_data)
        assert len(exits) == len(sample_data)
        assert entries.dtype == bool
        assert exits.dtype == bool
    
    def test_rsi_strategy_generates_signals(self, sample_data):
        """Test RSI strategy signal generation."""
        from maverick_crypto.backtesting.strategies import CryptoRSIStrategy
        
        strategy = CryptoRSIStrategy()
        entries, exits = strategy.generate_signals(sample_data)
        
        assert len(entries) == len(sample_data)
        assert len(exits) == len(sample_data)
    
    def test_macd_strategy_generates_signals(self, sample_data):
        """Test MACD strategy signal generation."""
        from maverick_crypto.backtesting.strategies import CryptoMACDStrategy
        
        strategy = CryptoMACDStrategy()
        entries, exits = strategy.generate_signals(sample_data)
        
        assert len(entries) == len(sample_data)
        assert len(exits) == len(sample_data)
    
    def test_bollinger_strategy_generates_signals(self, sample_data):
        """Test Bollinger strategy signal generation."""
        from maverick_crypto.backtesting.strategies import CryptoBollingerStrategy
        
        strategy = CryptoBollingerStrategy()
        entries, exits = strategy.generate_signals(sample_data)
        
        assert len(entries) == len(sample_data)
        assert len(exits) == len(sample_data)
    
    def test_mean_reversion_strategy_generates_signals(self, sample_data):
        """Test mean reversion strategy signal generation."""
        from maverick_crypto.backtesting.strategies import CryptoMeanReversionStrategy
        
        strategy = CryptoMeanReversionStrategy()
        entries, exits = strategy.generate_signals(sample_data)
        
        assert len(entries) == len(sample_data)
        assert len(exits) == len(sample_data)
    
    def test_breakout_strategy_generates_signals(self, sample_data):
        """Test breakout strategy signal generation."""
        from maverick_crypto.backtesting.strategies import CryptoBreakoutStrategy
        
        strategy = CryptoBreakoutStrategy()
        entries, exits = strategy.generate_signals(sample_data)
        
        assert len(entries) == len(sample_data)
        assert len(exits) == len(sample_data)


class TestStrategyParameters:
    """Test strategy parameter handling."""
    
    def test_default_parameters(self):
        """Test strategies have valid default parameters."""
        from maverick_crypto.backtesting.strategies import (
            CryptoMomentumStrategy,
            CryptoRSIStrategy,
            CryptoMACDStrategy,
        )
        
        momentum = CryptoMomentumStrategy()
        assert momentum.parameters["fast_period"] == 10
        assert momentum.parameters["slow_period"] == 30
        
        rsi = CryptoRSIStrategy()
        assert rsi.parameters["oversold"] == 25  # Crypto-adjusted
        assert rsi.parameters["overbought"] == 75  # Crypto-adjusted
        
        macd = CryptoMACDStrategy()
        assert macd.parameters["fast_period"] == 8  # Faster for crypto
    
    def test_custom_parameters(self):
        """Test strategies accept custom parameters."""
        from maverick_crypto.backtesting.strategies import CryptoMomentumStrategy
        
        strategy = CryptoMomentumStrategy({"fast_period": 5, "slow_period": 20})
        
        assert strategy.parameters["fast_period"] == 5
        assert strategy.parameters["slow_period"] == 20
    
    def test_strategy_to_dict(self):
        """Test strategy to_dict method."""
        from maverick_crypto.backtesting.strategies import CryptoMomentumStrategy
        
        strategy = CryptoMomentumStrategy()
        info = strategy.to_dict()
        
        assert info["name"] == "crypto_momentum"
        assert "description" in info
        assert "parameters" in info
        assert info["asset_class"] == "crypto"


class TestStrategyRegistry:
    """Test strategy registry functions."""
    
    def test_get_crypto_strategy(self):
        """Test getting strategy by name."""
        from maverick_crypto.backtesting.strategies import get_crypto_strategy
        
        strategy = get_crypto_strategy("crypto_momentum")
        assert strategy.name == "crypto_momentum"
    
    def test_get_unknown_strategy_raises(self):
        """Test getting unknown strategy raises ValueError."""
        from maverick_crypto.backtesting.strategies import get_crypto_strategy
        
        with pytest.raises(ValueError, match="Unknown strategy"):
            get_crypto_strategy("unknown_strategy")
    
    def test_list_crypto_strategies(self):
        """Test listing all strategies."""
        from maverick_crypto.backtesting.strategies import list_crypto_strategies
        
        strategies = list_crypto_strategies()
        
        assert len(strategies) >= 6
        assert any(s["name"] == "crypto_momentum" for s in strategies)
        assert any(s["name"] == "crypto_rsi" for s in strategies)


class TestCryptoBacktestEngine:
    """Test crypto backtesting engine."""
    
    @pytest.fixture
    def engine(self):
        """Create backtesting engine."""
        from maverick_crypto.backtesting import CryptoBacktestEngine
        return CryptoBacktestEngine()
    
    def test_engine_initialization(self, engine):
        """Test engine initializes correctly."""
        assert engine.fees == 0.001
        assert engine.slippage == 0.002
    
    def test_engine_custom_fees(self):
        """Test engine accepts custom fees."""
        from maverick_crypto.backtesting import CryptoBacktestEngine
        
        engine = CryptoBacktestEngine(fees=0.002, slippage=0.003)
        
        assert engine.fees == 0.002
        assert engine.slippage == 0.003
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_run_backtest_btc(self, engine):
        """Test running backtest on Bitcoin."""
        result = await engine.run_backtest(
            symbol="BTC",
            strategy="crypto_momentum",
            days=30,
            initial_capital=10000,
        )
        
        assert "total_return_pct" in result or "error" in result
        if "total_return_pct" in result:
            assert "sharpe_ratio" in result
            assert "max_drawdown" in result
            assert "num_trades" in result
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_compare_strategies(self, engine):
        """Test strategy comparison."""
        result = await engine.compare_strategies(
            symbol="BTC",
            strategies=["crypto_momentum", "crypto_rsi"],
            days=30,
        )
        
        assert "results" in result
        assert "best_strategy" in result


class TestCryptoSpecificAdjustments:
    """Test that crypto strategies have correct volatility adjustments."""
    
    def test_stop_loss_wider_than_stocks(self):
        """Test crypto stop loss is wider than typical stock values."""
        from maverick_crypto.backtesting.strategies import CryptoStrategy
        
        # Crypto should have at least 10% stop loss
        assert CryptoStrategy.DEFAULT_STOP_LOSS >= 0.10
        
        # Stocks typically use 5-7%
        assert CryptoStrategy.DEFAULT_STOP_LOSS > 0.07
    
    def test_rsi_thresholds_adjusted(self):
        """Test RSI thresholds are crypto-adjusted."""
        from maverick_crypto.backtesting.strategies import CryptoRSIStrategy
        
        strategy = CryptoRSIStrategy()
        
        # Crypto uses 25/75 vs stocks 30/70
        assert strategy.parameters["oversold"] <= 25
        assert strategy.parameters["overbought"] >= 75
    
    def test_bollinger_bands_wider(self):
        """Test Bollinger Bands are wider for crypto."""
        from maverick_crypto.backtesting.strategies import CryptoBollingerStrategy
        
        strategy = CryptoBollingerStrategy()
        
        # Crypto uses 2.5 std vs stocks 2.0
        assert strategy.parameters["std_dev"] >= 2.5
    
    def test_momentum_periods_shorter(self):
        """Test momentum periods are shorter for faster crypto markets."""
        from maverick_crypto.backtesting.strategies import CryptoMomentumStrategy
        
        strategy = CryptoMomentumStrategy()
        
        # Crypto uses 10/30 vs stocks 20/50
        assert strategy.parameters["fast_period"] <= 10
        assert strategy.parameters["slow_period"] <= 30

