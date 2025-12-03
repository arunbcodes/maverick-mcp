"""
Technical analysis service.

Provides RSI, MACD, Bollinger Bands, and other technical indicators.
"""

from decimal import Decimal
from typing import Protocol

import pandas as pd

from maverick_schemas.technical import (
    RSIAnalysis,
    MACDAnalysis,
    BollingerBands,
    SupportResistance,
    MovingAverages,
    TechnicalSummary,
)
from maverick_schemas.base import TrendDirection
from maverick_services.exceptions import StockNotFoundError, InsufficientDataError


class StockDataProvider(Protocol):
    """Protocol for stock data providers."""

    async def get_stock_data(
        self,
        ticker: str,
        start_date: str | None = None,
        end_date: str | None = None,
        period: str | None = None,
    ) -> pd.DataFrame:
        """Fetch stock data."""
        ...


def _to_decimal(value: float | int | None) -> Decimal | None:
    """Convert to Decimal, handling None and NaN."""
    if value is None:
        return None
    if pd.isna(value):
        return None
    return Decimal(str(round(value, 4)))


def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def _calculate_macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD indicator."""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _calculate_bollinger(
    prices: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower


class TechnicalService:
    """
    Domain service for technical analysis.

    Provides RSI, MACD, Bollinger Bands, support/resistance,
    and comprehensive technical summaries.
    """

    def __init__(self, provider: StockDataProvider):
        """
        Initialize technical service.

        Args:
            provider: Stock data provider
        """
        self._provider = provider

    async def get_rsi(
        self,
        ticker: str,
        period: int = 14,
        days: int = 365,
    ) -> RSIAnalysis:
        """
        Calculate RSI for a stock.

        Args:
            ticker: Stock ticker symbol
            period: RSI period (default 14)
            days: Days of historical data

        Returns:
            RSIAnalysis with current RSI and interpretation
        """
        df = await self._provider.get_stock_data(ticker, period=f"{days}d")

        if df is None or df.empty:
            raise StockNotFoundError(ticker)

        if len(df) < period + 1:
            raise InsufficientDataError(ticker, period + 1, len(df))

        rsi = _calculate_rsi(df["Close"], period)
        current_rsi = float(rsi.iloc[-1])

        # Determine signal
        if current_rsi < 30:
            signal = "oversold"
            strength = "strong" if current_rsi < 20 else "moderate"
        elif current_rsi > 70:
            signal = "overbought"
            strength = "strong" if current_rsi > 80 else "moderate"
        else:
            signal = "neutral"
            strength = "weak"

        # Count days in overbought/oversold
        days_oversold = int((rsi.tail(30) < 30).sum())
        days_overbought = int((rsi.tail(30) > 70).sum())

        return RSIAnalysis(
            ticker=ticker.upper(),
            current_rsi=_to_decimal(current_rsi),
            period=period,
            signal=signal,
            strength=strength,
            rsi_high=_to_decimal(rsi.tail(30).max()),
            rsi_low=_to_decimal(rsi.tail(30).min()),
            days_oversold=days_oversold,
            days_overbought=days_overbought,
        )

    async def get_macd(
        self,
        ticker: str,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        days: int = 365,
    ) -> MACDAnalysis:
        """
        Calculate MACD for a stock.

        Args:
            ticker: Stock ticker symbol
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            days: Days of historical data

        Returns:
            MACDAnalysis with MACD values and interpretation
        """
        df = await self._provider.get_stock_data(ticker, period=f"{days}d")

        if df is None or df.empty:
            raise StockNotFoundError(ticker)

        min_required = slow_period + signal_period
        if len(df) < min_required:
            raise InsufficientDataError(ticker, min_required, len(df))

        macd_line, signal_line, histogram = _calculate_macd(
            df["Close"], fast_period, slow_period, signal_period
        )

        current_macd = float(macd_line.iloc[-1])
        current_signal = float(signal_line.iloc[-1])
        current_hist = float(histogram.iloc[-1])
        prev_hist = float(histogram.iloc[-2])

        # Determine signal
        if current_macd > current_signal:
            if macd_line.iloc[-2] <= signal_line.iloc[-2]:
                signal = "bullish_crossover"
            else:
                signal = "bullish"
        else:
            if macd_line.iloc[-2] >= signal_line.iloc[-2]:
                signal = "bearish_crossover"
            else:
                signal = "bearish"

        # Determine trend
        if current_macd > 0 and current_hist > prev_hist:
            trend = TrendDirection.STRONG_UP
        elif current_macd > 0:
            trend = TrendDirection.UP
        elif current_macd < 0 and current_hist < prev_hist:
            trend = TrendDirection.STRONG_DOWN
        elif current_macd < 0:
            trend = TrendDirection.DOWN
        else:
            trend = TrendDirection.SIDEWAYS

        # Histogram direction
        hist_direction = "expanding" if abs(current_hist) > abs(prev_hist) else "contracting"

        return MACDAnalysis(
            ticker=ticker.upper(),
            macd_line=_to_decimal(current_macd),
            signal_line=_to_decimal(current_signal),
            histogram=_to_decimal(current_hist),
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            signal=signal,
            trend=trend,
            histogram_direction=hist_direction,
        )

    async def get_bollinger(
        self,
        ticker: str,
        period: int = 20,
        std_dev: float = 2.0,
        days: int = 365,
    ) -> BollingerBands:
        """
        Calculate Bollinger Bands for a stock.

        Args:
            ticker: Stock ticker symbol
            period: SMA period
            std_dev: Standard deviations
            days: Days of historical data

        Returns:
            BollingerBands with band values and interpretation
        """
        df = await self._provider.get_stock_data(ticker, period=f"{days}d")

        if df is None or df.empty:
            raise StockNotFoundError(ticker)

        if len(df) < period:
            raise InsufficientDataError(ticker, period, len(df))

        upper, middle, lower = _calculate_bollinger(df["Close"], period, std_dev)

        current_price = float(df["Close"].iloc[-1])
        current_upper = float(upper.iloc[-1])
        current_middle = float(middle.iloc[-1])
        current_lower = float(lower.iloc[-1])

        # Calculate %B
        percent_b = (current_price - current_lower) / (current_upper - current_lower)

        # Calculate bandwidth
        bandwidth = (current_upper - current_lower) / current_middle * 100

        # Determine signal
        if bandwidth < 10:  # Squeeze
            signal = "squeeze"
        elif current_price > current_upper:
            signal = "breakout_up"
        elif current_price < current_lower:
            signal = "breakout_down"
        else:
            signal = "mean_reversion"

        # Determine position
        if current_price > current_upper:
            position = "above_upper"
        elif current_price > current_middle:
            position = "upper_half"
        elif current_price > current_lower:
            position = "lower_half"
        else:
            position = "below_lower"

        return BollingerBands(
            ticker=ticker.upper(),
            upper_band=_to_decimal(current_upper),
            middle_band=_to_decimal(current_middle),
            lower_band=_to_decimal(current_lower),
            current_price=_to_decimal(current_price),
            percent_b=_to_decimal(percent_b),
            bandwidth=_to_decimal(bandwidth),
            period=period,
            std_dev=_to_decimal(std_dev),
            signal=signal,
            position=position,
        )

    async def get_moving_averages(
        self,
        ticker: str,
        days: int = 365,
    ) -> MovingAverages:
        """
        Calculate moving averages for a stock.

        Args:
            ticker: Stock ticker symbol
            days: Days of historical data

        Returns:
            MovingAverages with SMA and EMA values
        """
        df = await self._provider.get_stock_data(ticker, period=f"{days}d")

        if df is None or df.empty:
            raise StockNotFoundError(ticker)

        prices = df["Close"]
        current_price = float(prices.iloc[-1])

        # Calculate SMAs
        sma_20 = prices.rolling(20).mean().iloc[-1] if len(prices) >= 20 else None
        sma_50 = prices.rolling(50).mean().iloc[-1] if len(prices) >= 50 else None
        sma_100 = prices.rolling(100).mean().iloc[-1] if len(prices) >= 100 else None
        sma_200 = prices.rolling(200).mean().iloc[-1] if len(prices) >= 200 else None

        # Calculate EMAs
        ema_12 = prices.ewm(span=12).mean().iloc[-1] if len(prices) >= 12 else None
        ema_26 = prices.ewm(span=26).mean().iloc[-1] if len(prices) >= 26 else None
        ema_50 = prices.ewm(span=50).mean().iloc[-1] if len(prices) >= 50 else None

        # Golden/Death cross
        golden_cross = False
        death_cross = False
        if sma_50 and sma_200:
            golden_cross = sma_50 > sma_200
            death_cross = sma_50 < sma_200

        return MovingAverages(
            ticker=ticker.upper(),
            current_price=_to_decimal(current_price),
            sma_20=_to_decimal(sma_20),
            sma_50=_to_decimal(sma_50),
            sma_100=_to_decimal(sma_100),
            sma_200=_to_decimal(sma_200),
            ema_12=_to_decimal(ema_12),
            ema_26=_to_decimal(ema_26),
            ema_50=_to_decimal(ema_50),
            above_sma_20=current_price > sma_20 if sma_20 else False,
            above_sma_50=current_price > sma_50 if sma_50 else False,
            above_sma_200=current_price > sma_200 if sma_200 else False,
            golden_cross=golden_cross,
            death_cross=death_cross,
        )

    async def get_summary(
        self,
        ticker: str,
        days: int = 365,
    ) -> TechnicalSummary:
        """
        Get comprehensive technical analysis summary.

        Args:
            ticker: Stock ticker symbol
            days: Days of historical data

        Returns:
            TechnicalSummary with all indicators and recommendation
        """
        # Fetch all indicators
        rsi = await self.get_rsi(ticker, days=days)
        macd = await self.get_macd(ticker, days=days)
        bollinger = await self.get_bollinger(ticker, days=days)
        moving_averages = await self.get_moving_averages(ticker, days=days)

        # Count signals
        buy_signals = 0
        sell_signals = 0
        neutral_signals = 0

        # RSI signals
        if rsi.signal == "oversold":
            buy_signals += 1
        elif rsi.signal == "overbought":
            sell_signals += 1
        else:
            neutral_signals += 1

        # MACD signals
        if "bullish" in macd.signal:
            buy_signals += 1
        elif "bearish" in macd.signal:
            sell_signals += 1
        else:
            neutral_signals += 1

        # Moving average signals
        if moving_averages.above_sma_50 and moving_averages.above_sma_200:
            buy_signals += 1
        elif not moving_averages.above_sma_50 and not moving_averages.above_sma_200:
            sell_signals += 1
        else:
            neutral_signals += 1

        # Overall trend
        trend = macd.trend

        # Calculate trend strength
        total_signals = buy_signals + sell_signals + neutral_signals
        if buy_signals > sell_signals:
            trend_strength = Decimal(str((buy_signals / total_signals) * 100))
        elif sell_signals > buy_signals:
            trend_strength = Decimal(str((sell_signals / total_signals) * 100))
        else:
            trend_strength = Decimal("50")

        # Recommendation
        if buy_signals >= 3:
            recommendation = "strong_buy"
        elif buy_signals >= 2:
            recommendation = "buy"
        elif sell_signals >= 3:
            recommendation = "strong_sell"
        elif sell_signals >= 2:
            recommendation = "sell"
        else:
            recommendation = "hold"

        # Confidence
        confidence = abs(buy_signals - sell_signals) / total_signals * 100

        return TechnicalSummary(
            ticker=ticker.upper(),
            rsi=rsi,
            macd=macd,
            bollinger=bollinger,
            moving_averages=moving_averages,
            trend=trend,
            trend_strength=trend_strength,
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            neutral_signals=neutral_signals,
            recommendation=recommendation,
            confidence=_to_decimal(confidence),
        )


__all__ = ["TechnicalService"]

