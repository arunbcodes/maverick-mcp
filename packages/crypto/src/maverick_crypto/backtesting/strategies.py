"""
Cryptocurrency-specific trading strategies.

All strategies are adjusted for crypto's higher volatility:
- Wider stop losses (15% vs 5-7% for stocks)
- Adjusted RSI thresholds (75/25 vs 70/30)
- Wider Bollinger Bands (2.5 std vs 2.0)
- Smaller position sizes

Strategies:
    - CryptoMomentumStrategy: Trend-following with SMA crossover
    - CryptoMeanReversionStrategy: Buy oversold, sell overbought
    - CryptoBreakoutStrategy: Trade on volatility breakouts
    - CryptoRSIStrategy: RSI with crypto-adjusted thresholds
    - CryptoMACDStrategy: MACD with optimized parameters
    - CryptoBollingerStrategy: Bollinger Bands with wider bands
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

logger = logging.getLogger(__name__)


class CryptoStrategy(ABC):
    """
    Base class for cryptocurrency trading strategies.
    
    Provides common functionality and crypto-specific parameter defaults.
    All derived strategies automatically adjust for crypto volatility.
    """
    
    # Crypto-specific defaults (wider than stock defaults)
    DEFAULT_STOP_LOSS = 0.15  # 15% vs 5-7% for stocks
    DEFAULT_TAKE_PROFIT = 0.25  # 25% vs 10-15% for stocks
    DEFAULT_POSITION_SIZE = 0.10  # 10% of capital per trade
    
    def __init__(self, parameters: dict[str, Any] | None = None):
        """
        Initialize strategy with parameters.
        
        Args:
            parameters: Strategy-specific parameters
        """
        self.parameters = {**self.get_default_parameters(), **(parameters or {})}
    
    @abstractmethod
    def generate_signals(self, data: DataFrame) -> tuple[Series, Series]:
        """
        Generate entry and exit signals.
        
        Args:
            data: OHLCV DataFrame with columns: Open, High, Low, Close, Volume
            
        Returns:
            Tuple of (entry_signals, exit_signals) as boolean Series
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Strategy description."""
        pass
    
    @abstractmethod
    def get_default_parameters(self) -> dict[str, Any]:
        """Get default parameters for the strategy."""
        pass
    
    def to_dict(self) -> dict[str, Any]:
        """Convert strategy to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "default_parameters": self.get_default_parameters(),
            "asset_class": "crypto",
        }


class CryptoMomentumStrategy(CryptoStrategy):
    """
    Momentum strategy using SMA crossover.
    
    Entry: Fast SMA crosses above slow SMA (bullish momentum)
    Exit: Fast SMA crosses below slow SMA (bearish momentum)
    
    Crypto-adjusted: Uses shorter periods due to faster market cycles.
    """
    
    @property
    def name(self) -> str:
        return "crypto_momentum"
    
    @property
    def description(self) -> str:
        return "SMA crossover momentum strategy optimized for crypto volatility"
    
    def get_default_parameters(self) -> dict[str, Any]:
        return {
            "fast_period": 10,  # Shorter than stocks (typically 20)
            "slow_period": 30,  # Shorter than stocks (typically 50)
            "stop_loss": self.DEFAULT_STOP_LOSS,
            "take_profit": self.DEFAULT_TAKE_PROFIT,
        }
    
    def generate_signals(self, data: DataFrame) -> tuple[Series, Series]:
        """Generate momentum signals."""
        close = data["Close"] if "Close" in data.columns else data["close"]
        
        fast_period = self.parameters.get("fast_period", 10)
        slow_period = self.parameters.get("slow_period", 30)
        
        fast_sma = close.rolling(window=fast_period).mean()
        slow_sma = close.rolling(window=slow_period).mean()
        
        # Entry: fast crosses above slow
        entries = (fast_sma > slow_sma) & (fast_sma.shift(1) <= slow_sma.shift(1))
        
        # Exit: fast crosses below slow
        exits = (fast_sma < slow_sma) & (fast_sma.shift(1) >= slow_sma.shift(1))
        
        return entries.fillna(False), exits.fillna(False)


class CryptoMeanReversionStrategy(CryptoStrategy):
    """
    Mean reversion strategy using Bollinger Bands.
    
    Entry: Price touches lower band (oversold)
    Exit: Price touches upper band or middle band (mean reversion complete)
    
    Crypto-adjusted: Uses wider bands (2.5 std vs 2.0) for higher volatility.
    """
    
    @property
    def name(self) -> str:
        return "crypto_mean_reversion"
    
    @property
    def description(self) -> str:
        return "Mean reversion strategy using wider Bollinger Bands for crypto"
    
    def get_default_parameters(self) -> dict[str, Any]:
        return {
            "period": 20,
            "std_dev": 2.5,  # Wider than stocks (2.0)
            "exit_at_middle": True,  # Exit at middle band vs upper
            "stop_loss": self.DEFAULT_STOP_LOSS,
            "take_profit": self.DEFAULT_TAKE_PROFIT,
        }
    
    def generate_signals(self, data: DataFrame) -> tuple[Series, Series]:
        """Generate mean reversion signals."""
        close = data["Close"] if "Close" in data.columns else data["close"]
        
        period = self.parameters.get("period", 20)
        std_dev = self.parameters.get("std_dev", 2.5)
        exit_at_middle = self.parameters.get("exit_at_middle", True)
        
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        # Entry: Price below lower band (oversold)
        entries = close < lower
        
        # Exit: Price above middle or upper band
        if exit_at_middle:
            exits = close > middle
        else:
            exits = close > upper
        
        return entries.fillna(False), exits.fillna(False)


class CryptoBreakoutStrategy(CryptoStrategy):
    """
    Volatility breakout strategy.
    
    Entry: Price breaks above recent high with volume confirmation
    Exit: Price breaks below support or trailing stop hit
    
    Crypto-adjusted: Uses ATR-based stops for dynamic risk management.
    """
    
    @property
    def name(self) -> str:
        return "crypto_breakout"
    
    @property
    def description(self) -> str:
        return "Volatility breakout strategy with ATR-based risk management"
    
    def get_default_parameters(self) -> dict[str, Any]:
        return {
            "lookback": 20,
            "atr_period": 14,
            "atr_multiplier": 2.0,  # ATR stop multiplier
            "volume_threshold": 1.5,  # Volume must be 1.5x average
            "stop_loss": self.DEFAULT_STOP_LOSS,
            "take_profit": self.DEFAULT_TAKE_PROFIT,
        }
    
    def generate_signals(self, data: DataFrame) -> tuple[Series, Series]:
        """Generate breakout signals."""
        close = data["Close"] if "Close" in data.columns else data["close"]
        high = data["High"] if "High" in data.columns else data["high"]
        low = data["Low"] if "Low" in data.columns else data["low"]
        volume = data["Volume"] if "Volume" in data.columns else data.get("volume", pd.Series(1, index=data.index))
        
        lookback = self.parameters.get("lookback", 20)
        atr_period = self.parameters.get("atr_period", 14)
        volume_threshold = self.parameters.get("volume_threshold", 1.5)
        
        # Calculate ATR
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=atr_period).mean()
        
        # Recent high/low
        recent_high = high.rolling(window=lookback).max()
        recent_low = low.rolling(window=lookback).min()
        
        # Average volume
        avg_volume = volume.rolling(window=lookback).mean()
        
        # Entry: Price breaks above recent high with volume confirmation
        entries = (close > recent_high.shift(1)) & (volume > avg_volume * volume_threshold)
        
        # Exit: Price breaks below recent low
        exits = close < recent_low.shift(1)
        
        return entries.fillna(False), exits.fillna(False)


class CryptoRSIStrategy(CryptoStrategy):
    """
    RSI strategy with crypto-adjusted thresholds.
    
    Entry: RSI below oversold threshold (buy the dip)
    Exit: RSI above overbought threshold
    
    Crypto-adjusted: Uses 25/75 thresholds (vs 30/70 for stocks).
    """
    
    @property
    def name(self) -> str:
        return "crypto_rsi"
    
    @property
    def description(self) -> str:
        return "RSI strategy with crypto-adjusted overbought/oversold thresholds"
    
    def get_default_parameters(self) -> dict[str, Any]:
        return {
            "period": 14,
            "oversold": 25,  # Lower than stocks (30)
            "overbought": 75,  # Higher than stocks (70)
            "stop_loss": self.DEFAULT_STOP_LOSS,
            "take_profit": self.DEFAULT_TAKE_PROFIT,
        }
    
    def generate_signals(self, data: DataFrame) -> tuple[Series, Series]:
        """Generate RSI signals."""
        close = data["Close"] if "Close" in data.columns else data["close"]
        
        period = self.parameters.get("period", 14)
        oversold = self.parameters.get("oversold", 25)
        overbought = self.parameters.get("overbought", 75)
        
        # Calculate RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        
        # Entry: RSI crosses below oversold
        entries = (rsi < oversold) & (rsi.shift(1) >= oversold)
        
        # Exit: RSI crosses above overbought
        exits = (rsi > overbought) & (rsi.shift(1) <= overbought)
        
        return entries.fillna(False), exits.fillna(False)


class CryptoMACDStrategy(CryptoStrategy):
    """
    MACD strategy optimized for crypto.
    
    Entry: MACD line crosses above signal line
    Exit: MACD line crosses below signal line
    
    Crypto-adjusted: Uses faster periods for quicker signal generation.
    """
    
    @property
    def name(self) -> str:
        return "crypto_macd"
    
    @property
    def description(self) -> str:
        return "MACD crossover strategy with faster parameters for crypto"
    
    def get_default_parameters(self) -> dict[str, Any]:
        return {
            "fast_period": 8,  # Faster than standard (12)
            "slow_period": 21,  # Faster than standard (26)
            "signal_period": 9,
            "stop_loss": self.DEFAULT_STOP_LOSS,
            "take_profit": self.DEFAULT_TAKE_PROFIT,
        }
    
    def generate_signals(self, data: DataFrame) -> tuple[Series, Series]:
        """Generate MACD signals."""
        close = data["Close"] if "Close" in data.columns else data["close"]
        
        fast = self.parameters.get("fast_period", 8)
        slow = self.parameters.get("slow_period", 21)
        signal_period = self.parameters.get("signal_period", 9)
        
        # Calculate EMAs
        fast_ema = close.ewm(span=fast, adjust=False).mean()
        slow_ema = close.ewm(span=slow, adjust=False).mean()
        
        # MACD line
        macd_line = fast_ema - slow_ema
        
        # Signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # Entry: MACD crosses above signal
        entries = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
        
        # Exit: MACD crosses below signal
        exits = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))
        
        return entries.fillna(False), exits.fillna(False)


class CryptoBollingerStrategy(CryptoStrategy):
    """
    Bollinger Bands strategy with crypto adjustments.
    
    Entry: Price touches lower band
    Exit: Price touches upper band
    
    Crypto-adjusted: Uses wider bands (2.5 std) and shorter period.
    """
    
    @property
    def name(self) -> str:
        return "crypto_bollinger"
    
    @property
    def description(self) -> str:
        return "Bollinger Bands strategy with wider bands for crypto volatility"
    
    def get_default_parameters(self) -> dict[str, Any]:
        return {
            "period": 20,
            "std_dev": 2.5,  # Wider than stocks (2.0)
            "stop_loss": self.DEFAULT_STOP_LOSS,
            "take_profit": self.DEFAULT_TAKE_PROFIT,
        }
    
    def generate_signals(self, data: DataFrame) -> tuple[Series, Series]:
        """Generate Bollinger Band signals."""
        close = data["Close"] if "Close" in data.columns else data["close"]
        
        period = self.parameters.get("period", 20)
        std_dev = self.parameters.get("std_dev", 2.5)
        
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        # Entry: Price crosses below lower band
        entries = (close < lower) & (close.shift(1) >= lower.shift(1))
        
        # Exit: Price crosses above upper band
        exits = (close > upper) & (close.shift(1) <= upper.shift(1))
        
        return entries.fillna(False), exits.fillna(False)


# Strategy registry
CRYPTO_STRATEGIES = {
    "crypto_momentum": CryptoMomentumStrategy,
    "crypto_mean_reversion": CryptoMeanReversionStrategy,
    "crypto_breakout": CryptoBreakoutStrategy,
    "crypto_rsi": CryptoRSIStrategy,
    "crypto_macd": CryptoMACDStrategy,
    "crypto_bollinger": CryptoBollingerStrategy,
}


def get_crypto_strategy(
    strategy_name: str,
    parameters: dict[str, Any] | None = None,
) -> CryptoStrategy:
    """
    Get a crypto strategy by name.
    
    Args:
        strategy_name: Name of the strategy
        parameters: Optional strategy parameters
        
    Returns:
        Initialized strategy instance
        
    Raises:
        ValueError: If strategy name is unknown
    """
    if strategy_name not in CRYPTO_STRATEGIES:
        available = ", ".join(CRYPTO_STRATEGIES.keys())
        raise ValueError(f"Unknown strategy: {strategy_name}. Available: {available}")
    
    return CRYPTO_STRATEGIES[strategy_name](parameters)


def list_crypto_strategies() -> list[dict[str, Any]]:
    """
    List all available crypto strategies.
    
    Returns:
        List of strategy information dictionaries
    """
    strategies = []
    for name, strategy_class in CRYPTO_STRATEGIES.items():
        instance = strategy_class()
        strategies.append({
            "name": name,
            "description": instance.description,
            "default_parameters": instance.get_default_parameters(),
        })
    return strategies

