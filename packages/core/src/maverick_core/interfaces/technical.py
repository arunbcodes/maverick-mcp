"""
Technical analysis interfaces.

This module defines abstract interfaces for technical analysis operations.
"""

from typing import Any, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class ITechnicalAnalyzer(Protocol):
    """
    Interface for technical analysis.

    This interface defines the contract for calculating technical indicators
    and performing technical analysis on stock data.

    Implemented by: maverick-core (TechnicalAnalysisService)
    """

    def calculate_sma(
        self,
        data: pd.DataFrame,
        period: int = 20,
        column: str = "Close",
    ) -> pd.Series:
        """
        Calculate Simple Moving Average.

        Args:
            data: OHLCV DataFrame
            period: SMA period
            column: Column to calculate SMA on

        Returns:
            Series with SMA values
        """
        ...

    def calculate_ema(
        self,
        data: pd.DataFrame,
        period: int = 20,
        column: str = "Close",
    ) -> pd.Series:
        """
        Calculate Exponential Moving Average.

        Args:
            data: OHLCV DataFrame
            period: EMA period
            column: Column to calculate EMA on

        Returns:
            Series with EMA values
        """
        ...

    def calculate_rsi(
        self,
        data: pd.DataFrame,
        period: int = 14,
    ) -> pd.Series:
        """
        Calculate Relative Strength Index.

        Args:
            data: OHLCV DataFrame
            period: RSI period

        Returns:
            Series with RSI values (0-100)
        """
        ...

    def calculate_macd(
        self,
        data: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> dict[str, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            data: OHLCV DataFrame
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            Dictionary with:
            - macd: MACD line
            - signal: Signal line
            - histogram: MACD histogram
        """
        ...

    def calculate_bollinger_bands(
        self,
        data: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
    ) -> dict[str, pd.Series]:
        """
        Calculate Bollinger Bands.

        Args:
            data: OHLCV DataFrame
            period: Moving average period
            std_dev: Standard deviation multiplier

        Returns:
            Dictionary with:
            - upper: Upper band
            - middle: Middle band (SMA)
            - lower: Lower band
        """
        ...

    def calculate_atr(
        self,
        data: pd.DataFrame,
        period: int = 14,
    ) -> pd.Series:
        """
        Calculate Average True Range.

        Args:
            data: OHLCV DataFrame
            period: ATR period

        Returns:
            Series with ATR values
        """
        ...

    def calculate_support_resistance(
        self,
        data: pd.DataFrame,
        window: int = 20,
    ) -> dict[str, list[float]]:
        """
        Calculate support and resistance levels.

        Args:
            data: OHLCV DataFrame
            window: Window for finding pivots

        Returns:
            Dictionary with:
            - support: List of support levels (sorted descending)
            - resistance: List of resistance levels (sorted ascending)
        """
        ...

    def calculate_trend_strength(
        self,
        data: pd.DataFrame,
        short_period: int = 20,
        long_period: int = 50,
    ) -> dict[str, Any]:
        """
        Calculate trend strength indicators.

        Args:
            data: OHLCV DataFrame
            short_period: Short-term MA period
            long_period: Long-term MA period

        Returns:
            Dictionary with:
            - trend: "bullish", "bearish", or "neutral"
            - strength: Trend strength (0-100)
            - ma_alignment: MA alignment status
        """
        ...

    def get_full_analysis(
        self,
        data: pd.DataFrame,
    ) -> dict[str, Any]:
        """
        Get comprehensive technical analysis.

        Args:
            data: OHLCV DataFrame

        Returns:
            Dictionary with all indicators and signals:
            - rsi: RSI analysis
            - macd: MACD analysis
            - bollinger: Bollinger Bands analysis
            - support_resistance: Support/resistance levels
            - trend: Trend analysis
            - signals: Trading signals
            - summary: Overall analysis summary
        """
        ...

    def generate_signals(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Generate trading signals based on technical analysis.

        Args:
            data: OHLCV DataFrame

        Returns:
            DataFrame with signal columns:
            - signal: 1 (buy), -1 (sell), 0 (hold)
            - signal_strength: Signal confidence (0-100)
            - reason: Signal reasoning
        """
        ...
