"""
Pure technical analysis indicator functions.

All functions in this module are pure - they take data and return computed values
without side effects. No external dependencies beyond numpy/pandas.

These functions implement standard technical analysis formulas and can be used
by any package that needs technical indicator calculations.
"""

from typing import Any

import numpy as np
import pandas as pd


def calculate_sma(
    data: pd.DataFrame,
    period: int = 20,
    column: str = "Close",
) -> pd.Series:
    """
    Calculate Simple Moving Average.

    SMA = Sum(Close[i], i=0..n-1) / n

    Args:
        data: OHLCV DataFrame with at least the specified column
        period: Number of periods to average
        column: Column name to calculate SMA on

    Returns:
        Series with SMA values, NaN for insufficient data

    Raises:
        KeyError: If column doesn't exist in DataFrame
        ValueError: If period < 1
    """
    if period < 1:
        raise ValueError(f"Period must be >= 1, got {period}")

    return data[column].rolling(window=period).mean()


def calculate_ema(
    data: pd.DataFrame,
    period: int = 20,
    column: str = "Close",
) -> pd.Series:
    """
    Calculate Exponential Moving Average.

    EMA uses an exponentially weighted multiplier:
    Multiplier = 2 / (period + 1)
    EMA[t] = Close[t] * Multiplier + EMA[t-1] * (1 - Multiplier)

    Args:
        data: OHLCV DataFrame with at least the specified column
        period: EMA period (span)
        column: Column name to calculate EMA on

    Returns:
        Series with EMA values

    Raises:
        KeyError: If column doesn't exist in DataFrame
        ValueError: If period < 1
    """
    if period < 1:
        raise ValueError(f"Period must be >= 1, got {period}")

    return data[column].ewm(span=period, adjust=False).mean()


def calculate_rsi(
    data: pd.DataFrame,
    period: int = 14,
    column: str = "Close",
) -> pd.Series:
    """
    Calculate Relative Strength Index.

    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss

    Uses Wilder's smoothing method (exponential moving average).

    Args:
        data: OHLCV DataFrame with at least the specified column
        period: RSI calculation period

    Returns:
        Series with RSI values (0-100 range)

    Raises:
        ValueError: If period < 1
    """
    if period < 1:
        raise ValueError(f"Period must be >= 1, got {period}")

    # Calculate price changes
    delta = data[column].diff()

    # Separate gains and losses
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)

    # Calculate average gains and losses using Wilder's smoothing
    avg_gain = gains.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Handle division by zero (when avg_loss is 0)
    rsi = rsi.replace([np.inf, -np.inf], 100)

    return rsi


def calculate_macd(
    data: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    column: str = "Close",
) -> dict[str, pd.Series]:
    """
    Calculate Moving Average Convergence Divergence.

    MACD Line = Fast EMA - Slow EMA
    Signal Line = EMA of MACD Line
    Histogram = MACD Line - Signal Line

    Args:
        data: OHLCV DataFrame
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line EMA period (default 9)
        column: Column to calculate MACD on

    Returns:
        Dictionary with 'macd', 'signal', and 'histogram' Series

    Raises:
        ValueError: If fast_period >= slow_period or any period < 1
    """
    if fast_period < 1 or slow_period < 1 or signal_period < 1:
        raise ValueError("All periods must be >= 1")
    if fast_period >= slow_period:
        raise ValueError(f"Fast period ({fast_period}) must be < slow period ({slow_period})")

    # Calculate EMAs
    fast_ema = calculate_ema(data, fast_period, column)
    slow_ema = calculate_ema(data, slow_period, column)

    # MACD line
    macd_line = fast_ema - slow_ema

    # Signal line (EMA of MACD)
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

    # Histogram
    histogram = macd_line - signal_line

    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram,
    }


def calculate_bollinger_bands(
    data: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0,
    column: str = "Close",
) -> dict[str, pd.Series]:
    """
    Calculate Bollinger Bands.

    Middle Band = SMA(period)
    Upper Band = Middle Band + (std_dev * Standard Deviation)
    Lower Band = Middle Band - (std_dev * Standard Deviation)

    Args:
        data: OHLCV DataFrame
        period: Moving average period
        std_dev: Standard deviation multiplier
        column: Column to calculate bands on

    Returns:
        Dictionary with 'upper', 'middle', 'lower', and 'bandwidth' Series

    Raises:
        ValueError: If period < 1 or std_dev < 0
    """
    if period < 1:
        raise ValueError(f"Period must be >= 1, got {period}")
    if std_dev < 0:
        raise ValueError(f"Standard deviation must be >= 0, got {std_dev}")

    # Middle band (SMA)
    middle = calculate_sma(data, period, column)

    # Standard deviation
    rolling_std = data[column].rolling(window=period).std()

    # Upper and lower bands
    upper = middle + (std_dev * rolling_std)
    lower = middle - (std_dev * rolling_std)

    # Bandwidth (measures volatility)
    bandwidth = (upper - lower) / middle * 100

    return {
        "upper": upper,
        "middle": middle,
        "lower": lower,
        "bandwidth": bandwidth,
    }


def calculate_atr(
    data: pd.DataFrame,
    period: int = 14,
) -> pd.Series:
    """
    Calculate Average True Range.

    True Range = max(
        High - Low,
        abs(High - Previous Close),
        abs(Low - Previous Close)
    )
    ATR = Wilder's Moving Average of True Range

    Args:
        data: OHLCV DataFrame with High, Low, Close columns
        period: ATR period

    Returns:
        Series with ATR values

    Raises:
        ValueError: If period < 1
        KeyError: If required columns are missing
    """
    if period < 1:
        raise ValueError(f"Period must be >= 1, got {period}")

    high = data["High"]
    low = data["Low"]
    close = data["Close"]

    # Calculate True Range components
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    # True Range is the maximum of the three
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # ATR using Wilder's smoothing
    atr = true_range.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    return atr


def calculate_stochastic(
    data: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3,
) -> dict[str, pd.Series]:
    """
    Calculate Stochastic Oscillator.

    %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
    %D = SMA of %K

    Args:
        data: OHLCV DataFrame
        k_period: Period for %K calculation
        d_period: Period for %D smoothing

    Returns:
        Dictionary with 'k' and 'd' Series

    Raises:
        ValueError: If periods < 1
    """
    if k_period < 1 or d_period < 1:
        raise ValueError("All periods must be >= 1")

    # Lowest low and highest high over K period
    lowest_low = data["Low"].rolling(window=k_period).min()
    highest_high = data["High"].rolling(window=k_period).max()

    # %K
    k = ((data["Close"] - lowest_low) / (highest_high - lowest_low)) * 100

    # %D (SMA of %K)
    d = k.rolling(window=d_period).mean()

    return {
        "k": k,
        "d": d,
    }


def calculate_support_resistance(
    data: pd.DataFrame,
    window: int = 20,
    threshold: float = 0.02,
) -> dict[str, list[float]]:
    """
    Calculate support and resistance levels from pivot points.

    Uses local minima and maxima to identify support/resistance zones.

    Args:
        data: OHLCV DataFrame
        window: Window size for finding local extrema
        threshold: Minimum price distance threshold (as fraction)

    Returns:
        Dictionary with 'support' and 'resistance' lists (sorted)

    Raises:
        ValueError: If window < 1
    """
    if window < 1:
        raise ValueError(f"Window must be >= 1, got {window}")

    close = data["Close"]
    high = data["High"]
    low = data["Low"]

    # Find local minima (support levels)
    support_levels = []
    for i in range(window, len(low) - window):
        if low.iloc[i] == low.iloc[i - window : i + window + 1].min():
            support_levels.append(float(low.iloc[i]))

    # Find local maxima (resistance levels)
    resistance_levels = []
    for i in range(window, len(high) - window):
        if high.iloc[i] == high.iloc[i - window : i + window + 1].max():
            resistance_levels.append(float(high.iloc[i]))

    # Filter out levels too close together
    current_price = float(close.iloc[-1])

    def filter_levels(levels: list[float], min_distance: float) -> list[float]:
        if not levels:
            return []

        filtered = []
        levels = sorted(levels)
        prev = levels[0]
        filtered.append(prev)

        for level in levels[1:]:
            if abs(level - prev) / prev > min_distance:
                filtered.append(level)
                prev = level

        return filtered

    support_filtered = filter_levels(support_levels, threshold)
    resistance_filtered = filter_levels(resistance_levels, threshold)

    # Return only recent/relevant levels (within 20% of current price)
    support_relevant = [s for s in support_filtered if s < current_price and s > current_price * 0.8]
    resistance_relevant = [r for r in resistance_filtered if r > current_price and r < current_price * 1.2]

    return {
        "support": sorted(support_relevant, reverse=True),
        "resistance": sorted(resistance_relevant),
    }


def calculate_trend_strength(
    data: pd.DataFrame,
    short_period: int = 20,
    long_period: int = 50,
) -> dict[str, Any]:
    """
    Calculate trend strength indicators.

    Uses moving average alignment and price position to determine trend.

    Args:
        data: OHLCV DataFrame
        short_period: Short-term MA period
        long_period: Long-term MA period

    Returns:
        Dictionary with:
        - trend: "bullish", "bearish", or "neutral"
        - strength: Trend strength score (0-100)
        - ma_alignment: MA alignment status
        - price_vs_ma: Price position relative to MAs

    Raises:
        ValueError: If short_period >= long_period
    """
    if short_period >= long_period:
        raise ValueError(f"Short period ({short_period}) must be < long period ({long_period})")

    close = data["Close"]
    current_price = float(close.iloc[-1])

    # Calculate MAs
    sma_short = calculate_sma(data, short_period)
    sma_long = calculate_sma(data, long_period)

    short_val = float(sma_short.iloc[-1])
    long_val = float(sma_long.iloc[-1])

    # Determine trend based on MA alignment
    ma_bullish = short_val > long_val
    price_above_short = current_price > short_val
    price_above_long = current_price > long_val

    # Calculate strength (0-100)
    strength = 0

    if ma_bullish:
        strength += 30
    else:
        strength -= 30

    if price_above_short:
        strength += 25
    else:
        strength -= 25

    if price_above_long:
        strength += 25
    else:
        strength -= 25

    # Add momentum component
    momentum = (current_price - close.iloc[-5]) / close.iloc[-5] * 100
    if momentum > 0:
        strength += min(20, momentum * 4)
    else:
        strength -= min(20, abs(momentum) * 4)

    # Normalize to 0-100
    strength = max(0, min(100, strength + 50))

    # Determine trend
    if strength >= 60:
        trend = "bullish"
    elif strength <= 40:
        trend = "bearish"
    else:
        trend = "neutral"

    return {
        "trend": trend,
        "strength": round(strength, 2),
        "ma_alignment": "bullish" if ma_bullish else "bearish",
        "price_vs_ma": {
            "above_short_ma": price_above_short,
            "above_long_ma": price_above_long,
        },
        "short_ma": round(short_val, 2),
        "long_ma": round(long_val, 2),
    }


def calculate_momentum(
    data: pd.DataFrame,
    period: int = 14,
    column: str = "Close",
) -> pd.Series:
    """
    Calculate Momentum indicator.

    Momentum = Close[t] - Close[t-period]

    Args:
        data: OHLCV DataFrame
        period: Lookback period
        column: Column to calculate momentum on

    Returns:
        Series with momentum values

    Raises:
        ValueError: If period < 1
    """
    if period < 1:
        raise ValueError(f"Period must be >= 1, got {period}")

    return data[column] - data[column].shift(period)


def calculate_rate_of_change(
    data: pd.DataFrame,
    period: int = 14,
    column: str = "Close",
) -> pd.Series:
    """
    Calculate Rate of Change (ROC).

    ROC = ((Close[t] - Close[t-period]) / Close[t-period]) * 100

    Args:
        data: OHLCV DataFrame
        period: Lookback period
        column: Column to calculate ROC on

    Returns:
        Series with ROC values (percentage)

    Raises:
        ValueError: If period < 1
    """
    if period < 1:
        raise ValueError(f"Period must be >= 1, got {period}")

    return data[column].pct_change(periods=period) * 100


def calculate_williams_r(
    data: pd.DataFrame,
    period: int = 14,
) -> pd.Series:
    """
    Calculate Williams %R.

    %R = (Highest High - Close) / (Highest High - Lowest Low) * -100

    Args:
        data: OHLCV DataFrame
        period: Lookback period

    Returns:
        Series with Williams %R values (-100 to 0)

    Raises:
        ValueError: If period < 1
    """
    if period < 1:
        raise ValueError(f"Period must be >= 1, got {period}")

    highest_high = data["High"].rolling(window=period).max()
    lowest_low = data["Low"].rolling(window=period).min()

    williams_r = ((highest_high - data["Close"]) / (highest_high - lowest_low)) * -100

    return williams_r


def calculate_obv(data: pd.DataFrame) -> pd.Series:
    """
    Calculate On-Balance Volume (OBV).

    OBV is a cumulative total of volume:
    - Add volume on up days
    - Subtract volume on down days

    Args:
        data: OHLCV DataFrame with Close and Volume columns

    Returns:
        Series with OBV values
    """
    close = data["Close"]
    volume = data["Volume"]

    # Direction of price change
    direction = np.sign(close.diff())

    # OBV is cumulative sum of volume * direction
    obv = (volume * direction).cumsum()

    return obv


__all__ = [
    "calculate_sma",
    "calculate_ema",
    "calculate_rsi",
    "calculate_macd",
    "calculate_bollinger_bands",
    "calculate_atr",
    "calculate_stochastic",
    "calculate_support_resistance",
    "calculate_trend_strength",
    "calculate_momentum",
    "calculate_rate_of_change",
    "calculate_williams_r",
    "calculate_obv",
]
