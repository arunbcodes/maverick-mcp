"""
Technical analysis router - thin wrapper around maverick-core.

All business logic lives in maverick-core. This router only:
1. Defines MCP tool signatures
2. Fetches data via maverick-data
3. Delegates analysis to maverick-core functions
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from maverick_core import (
    calculate_bollinger_bands,
    calculate_macd,
    calculate_rsi,
    calculate_support_resistance,
)
from maverick_data import YFinanceProvider

if TYPE_CHECKING:
    from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_technical_tools(mcp: FastMCP) -> None:
    """Register technical analysis tools with MCP server."""

    @mcp.tool()
    async def technical_get_rsi_analysis(
        ticker: str,
        period: int = 14,
        days: int = 365,
    ) -> dict[str, Any]:
        """Get RSI analysis for a given ticker.

        Args:
            ticker: Stock ticker symbol
            period: RSI period (default: 14)
            days: Number of days of historical data to analyze

        Returns:
            Dictionary containing RSI analysis
        """
        try:
            provider = YFinanceProvider()
            df = await provider.get_stock_data(ticker, days=days)

            if df.empty:
                return {"error": f"No data found for {ticker}"}

            rsi_series = calculate_rsi(df["Close"], period=period)
            current_rsi = float(rsi_series.iloc[-1])

            # Determine signal
            if current_rsi < 30:
                signal = "oversold"
            elif current_rsi > 70:
                signal = "overbought"
            else:
                signal = "neutral"

            return {
                "ticker": ticker,
                "current_rsi": round(current_rsi, 2),
                "period": period,
                "signal": signal,
                "analysis": f"RSI({period}) is {current_rsi:.2f} - {signal}",
            }
        except Exception as e:
            logger.error(f"RSI analysis error for {ticker}: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def technical_get_macd_analysis(
        ticker: str,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        days: int = 365,
    ) -> dict[str, Any]:
        """Get MACD analysis for a given ticker.

        Args:
            ticker: Stock ticker symbol
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line period (default: 9)
            days: Number of days of historical data

        Returns:
            Dictionary containing MACD analysis
        """
        try:
            provider = YFinanceProvider()
            df = await provider.get_stock_data(ticker, days=days)

            if df.empty:
                return {"error": f"No data found for {ticker}"}

            macd_result = calculate_macd(
                df["Close"],
                fast_period=fast_period,
                slow_period=slow_period,
                signal_period=signal_period,
            )

            macd_line = float(macd_result["macd"].iloc[-1])
            signal_line = float(macd_result["signal"].iloc[-1])
            histogram = float(macd_result["histogram"].iloc[-1])

            # Determine signal
            if macd_line > signal_line:
                signal = "bullish"
            else:
                signal = "bearish"

            return {
                "ticker": ticker,
                "macd_line": round(macd_line, 4),
                "signal_line": round(signal_line, 4),
                "histogram": round(histogram, 4),
                "signal": signal,
                "parameters": {
                    "fast": fast_period,
                    "slow": slow_period,
                    "signal": signal_period,
                },
            }
        except Exception as e:
            logger.error(f"MACD analysis error for {ticker}: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def technical_get_support_resistance(
        ticker: str,
        days: int = 365,
    ) -> dict[str, Any]:
        """Get support and resistance levels for a given ticker.

        Args:
            ticker: Stock ticker symbol
            days: Number of days of historical data

        Returns:
            Dictionary containing support and resistance levels
        """
        try:
            provider = YFinanceProvider()
            df = await provider.get_stock_data(ticker, days=days)

            if df.empty:
                return {"error": f"No data found for {ticker}"}

            levels = calculate_support_resistance(
                df["High"], df["Low"], df["Close"]
            )

            current_price = float(df["Close"].iloc[-1])

            return {
                "ticker": ticker,
                "current_price": round(current_price, 2),
                "support_levels": [round(s, 2) for s in levels.get("support", [])],
                "resistance_levels": [round(r, 2) for r in levels.get("resistance", [])],
            }
        except Exception as e:
            logger.error(f"Support/resistance error for {ticker}: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def technical_get_bollinger_bands(
        ticker: str,
        period: int = 20,
        std_dev: float = 2.0,
        days: int = 365,
    ) -> dict[str, Any]:
        """Get Bollinger Bands analysis for a given ticker.

        Args:
            ticker: Stock ticker symbol
            period: Moving average period (default: 20)
            std_dev: Standard deviation multiplier (default: 2.0)
            days: Number of days of historical data

        Returns:
            Dictionary containing Bollinger Bands analysis
        """
        try:
            provider = YFinanceProvider()
            df = await provider.get_stock_data(ticker, days=days)

            if df.empty:
                return {"error": f"No data found for {ticker}"}

            bb = calculate_bollinger_bands(df["Close"], period=period, std_dev=std_dev)

            current_price = float(df["Close"].iloc[-1])
            upper = float(bb["upper"].iloc[-1])
            middle = float(bb["middle"].iloc[-1])
            lower = float(bb["lower"].iloc[-1])

            # Determine position
            if current_price > upper:
                position = "above_upper"
            elif current_price < lower:
                position = "below_lower"
            else:
                position = "within_bands"

            return {
                "ticker": ticker,
                "current_price": round(current_price, 2),
                "upper_band": round(upper, 2),
                "middle_band": round(middle, 2),
                "lower_band": round(lower, 2),
                "position": position,
                "bandwidth": round((upper - lower) / middle * 100, 2),
            }
        except Exception as e:
            logger.error(f"Bollinger Bands error for {ticker}: {e}")
            return {"error": str(e)}

    logger.info("Registered technical analysis tools")
