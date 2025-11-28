"""
Market Data Provider.

Provides market-wide data including top gainers, losers, market indices,
sector performance, and earnings calendar.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pandas as pd
import requests
import yfinance as yf
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


# Market indices - standard references
MARKET_INDICES = {
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "NASDAQ",
    "^RUT": "Russell 2000",
    "^VIX": "VIX",
    "^TNX": "10Y Treasury",
}

# Sector ETFs - standard references
SECTOR_ETFS = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financials": "XLF",
    "Consumer Discretionary": "XLY",
    "Industrials": "XLI",
    "Energy": "XLE",
    "Utilities": "XLU",
    "Materials": "XLB",
    "Consumer Staples": "XLP",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
}


def _get_finviz_movers(mover_type: str = "gainers", limit: int = 50) -> list[str]:
    """
    Get market movers using finvizfinance screener.

    Args:
        mover_type: Type of movers to get ("gainers", "losers", "active")
        limit: Maximum number of stocks to return

    Returns:
        List of ticker symbols
    """
    try:
        from finvizfinance.screener.overview import Overview

        foverview = Overview()

        # Set up filters based on mover type
        if mover_type == "gainers":
            filters_dict = {
                "Change": "Up 5%",
                "Average Volume": "Over 1M",
                "Price": "Over $5",
            }
        elif mover_type == "losers":
            filters_dict = {
                "Change": "Down 5%",
                "Average Volume": "Over 1M",
                "Price": "Over $5",
            }
        elif mover_type == "active":
            filters_dict = {
                "Average Volume": "Over 20M",
                "Price": "Over $5",
            }
        else:
            filters_dict = {
                "Average Volume": "Over 10M",
                "Market Cap.": "Large (>10bln)",
                "Price": "Over $10",
            }

        foverview.set_filter(filters_dict=filters_dict)
        df = foverview.screener_view()

        if df is not None and not df.empty:
            if mover_type == "gainers" and "Change" in df.columns:
                df = df.sort_values("Change", ascending=False)
            elif mover_type == "losers" and "Change" in df.columns:
                df = df.sort_values("Change", ascending=True)
            elif mover_type == "active" and "Volume" in df.columns:
                df = df.sort_values("Volume", ascending=False)

            if "Ticker" in df.columns:
                return list(df["Ticker"].head(limit).tolist())

        logger.debug(f"No finviz data available for {mover_type}")
        return []

    except ImportError:
        logger.warning("finvizfinance not installed")
        return []
    except Exception as e:
        logger.debug(f"Error fetching finviz movers: {e}")
        return []


def _get_finviz_stock_data(symbols: list[str]) -> list[dict[str, Any]]:
    """
    Get stock data for symbols using yfinance.

    Args:
        symbols: List of ticker symbols

    Returns:
        List of dictionaries with stock data
    """
    results = []

    for symbol in symbols[:20]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if info and "currentPrice" in info:
                price = info.get("currentPrice", 0)
                prev_close = info.get("previousClose", price)
                change = price - prev_close if prev_close else 0
                change_percent = (change / prev_close * 100) if prev_close else 0
                volume = info.get("volume", 0)

                results.append(
                    {
                        "symbol": symbol,
                        "price": round(price, 2),
                        "change": round(change, 2),
                        "change_percent": round(change_percent, 2),
                        "volume": volume,
                    }
                )
        except Exception as e:
            logger.debug(f"Error fetching data for {symbol}: {e}")
            continue

    return results


class MarketDataProvider:
    """
    Provider for market-wide data.

    Provides market indices, top gainers/losers, sector performance,
    and earnings calendar data.

    Features:
    - Market summary with major indices
    - Top gainers and losers
    - Most active stocks by volume
    - Sector performance (via sector ETFs)
    - Earnings calendar
    - Async support for parallel fetching
    """

    def __init__(self):
        """Initialize market data provider."""
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=10, pool_maxsize=10
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.info("MarketDataProvider initialized")

    async def _run_in_executor(self, func, *args) -> Any:
        """Run a blocking function in an executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

    def _fetch_data(
        self, url: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Fetch data from an API with retry logic.

        Args:
            url: API endpoint URL
            params: Optional query parameters

        Returns:
            JSON response as dictionary
        """
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=(5, 30),
                headers={"User-Agent": "Maverick-Data/1.0"},
            )
            response.raise_for_status()
            result = response.json()
            return result if isinstance(result, dict) else {}
        except requests.Timeout:
            logger.error(f"Timeout error fetching data from {url}")
            return {}
        except requests.HTTPError as e:
            logger.error(f"HTTP error fetching data from {url}: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Unknown error fetching data from {url}: {str(e)}")
            return {}

    def get_market_summary(self) -> dict[str, Any]:
        """
        Get a summary of major market indices.

        Returns:
            Dictionary with market summary data
        """
        try:
            data = {}
            for index, name in MARKET_INDICES.items():
                ticker = yf.Ticker(index)
                history = ticker.history(period="2d")

                if history.empty:
                    continue

                prev_close = (
                    history["Close"].iloc[0]
                    if len(history) > 1
                    else history["Close"].iloc[0]
                )
                current = history["Close"].iloc[-1]
                change = current - prev_close
                change_percent = (change / prev_close) * 100 if prev_close != 0 else 0

                data[index] = {
                    "name": name,
                    "symbol": index,
                    "price": round(current, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                }

            return data
        except Exception as e:
            logger.error(f"Error fetching market summary: {str(e)}")
            return {}

    def get_top_gainers(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get top gaining stocks in the market.

        Args:
            limit: Maximum number of stocks to return

        Returns:
            List of dictionaries with stock data
        """
        try:
            # Try to get gainers from finvizfinance
            symbols = _get_finviz_movers("gainers", limit=limit * 2)

            if symbols:
                results = _get_finviz_stock_data(symbols[:limit])
                if results:
                    results.sort(key=lambda x: x["change_percent"], reverse=True)
                    return results[:limit]

            # Fallback to yfinance with active stocks
            if not symbols:
                symbols = _get_finviz_movers("active", limit=50)

            if not symbols:
                logger.warning("No symbols available for gainers calculation")
                return []

            # Fetch data using yfinance batch
            results = []
            batch_str = " ".join(symbols[:50])

            data = yf.download(
                batch_str,
                period="2d",
                group_by="ticker",
                threads=True,
                progress=False,
            )

            if data is None or data.empty:
                logger.warning("No data available from yfinance")
                return []

            for symbol in symbols[:50]:
                try:
                    if len(symbols) == 1:
                        ticker_data = data
                    else:
                        if symbol not in data.columns.get_level_values(0):
                            continue
                        ticker_data = data[symbol]

                    if len(ticker_data) < 2:
                        continue

                    prev_close = ticker_data["Close"].iloc[0]
                    current = ticker_data["Close"].iloc[-1]

                    if pd.isna(prev_close) or pd.isna(current) or prev_close == 0:
                        continue

                    change = current - prev_close
                    change_percent = (change / prev_close) * 100
                    volume = ticker_data["Volume"].iloc[-1]

                    if pd.notna(change_percent) and pd.notna(volume):
                        results.append(
                            {
                                "symbol": symbol,
                                "price": round(current, 2),
                                "change": round(change, 2),
                                "change_percent": round(change_percent, 2),
                                "volume": int(volume),
                            }
                        )
                except Exception as e:
                    logger.debug(f"Error processing {symbol}: {str(e)}")
                    continue

            results.sort(key=lambda x: x["change_percent"], reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Error fetching top gainers: {str(e)}")
            return []

    def get_top_losers(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get top losing stocks in the market.

        Args:
            limit: Maximum number of stocks to return

        Returns:
            List of dictionaries with stock data
        """
        try:
            # Try to get losers from finvizfinance
            symbols = _get_finviz_movers("losers", limit=limit * 2)

            if symbols:
                results = _get_finviz_stock_data(symbols[:limit])
                if results:
                    results.sort(key=lambda x: x["change_percent"])
                    return results[:limit]

            # Fallback to yfinance with active stocks
            if not symbols:
                symbols = _get_finviz_movers("active", limit=50)

            if not symbols:
                logger.warning("No symbols available for losers calculation")
                return []

            # Fetch data using yfinance batch
            results = []
            batch_str = " ".join(symbols[:50])

            data = yf.download(
                batch_str,
                period="2d",
                group_by="ticker",
                threads=True,
                progress=False,
            )

            if data is None or data.empty:
                logger.warning("No data available from yfinance")
                return []

            for symbol in symbols[:50]:
                try:
                    if len(symbols) == 1:
                        ticker_data = data
                    else:
                        if symbol not in data.columns.get_level_values(0):
                            continue
                        ticker_data = data[symbol]

                    if len(ticker_data) < 2:
                        continue

                    prev_close = ticker_data["Close"].iloc[0]
                    current = ticker_data["Close"].iloc[-1]

                    if pd.isna(prev_close) or pd.isna(current) or prev_close == 0:
                        continue

                    change = current - prev_close
                    change_percent = (change / prev_close) * 100
                    volume = ticker_data["Volume"].iloc[-1]

                    if pd.notna(change_percent) and pd.notna(volume):
                        results.append(
                            {
                                "symbol": symbol,
                                "price": round(current, 2),
                                "change": round(change, 2),
                                "change_percent": round(change_percent, 2),
                                "volume": int(volume),
                            }
                        )
                except Exception as e:
                    logger.debug(f"Error processing {symbol}: {str(e)}")
                    continue

            results.sort(key=lambda x: x["change_percent"])
            return results[:limit]

        except Exception as e:
            logger.error(f"Error fetching top losers: {str(e)}")
            return []

    def get_most_active(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get most active stocks by volume.

        Args:
            limit: Maximum number of stocks to return

        Returns:
            List of dictionaries with stock data
        """
        try:
            symbols = _get_finviz_movers("active", limit=limit * 2)

            if symbols:
                results = _get_finviz_stock_data(symbols[:limit])
                if results:
                    results.sort(key=lambda x: x["volume"], reverse=True)
                    return results[:limit]

            if not symbols:
                logger.warning("No most active stocks data available")
                return []

            # Fetch data using yfinance batch
            batch_str = " ".join(symbols[: limit * 2])

            data = yf.download(
                batch_str,
                period="2d",
                group_by="ticker",
                threads=True,
                progress=False,
            )

            if data is None or data.empty:
                logger.warning("No data available from yfinance")
                return []

            results = []
            for symbol in symbols[: limit * 2]:
                try:
                    if len(symbols) == 1:
                        ticker_data = data
                    else:
                        if symbol not in data.columns.get_level_values(0):
                            continue
                        ticker_data = data[symbol]

                    if len(ticker_data) < 2:
                        continue

                    prev_close = ticker_data["Close"].iloc[0]
                    current = ticker_data["Close"].iloc[-1]
                    volume = ticker_data["Volume"].iloc[-1]

                    if (
                        pd.isna(prev_close)
                        or pd.isna(current)
                        or pd.isna(volume)
                        or prev_close == 0
                    ):
                        continue

                    change = current - prev_close
                    change_percent = (change / prev_close) * 100

                    if pd.notna(change_percent) and pd.notna(volume):
                        results.append(
                            {
                                "symbol": symbol,
                                "price": round(current, 2),
                                "change": round(change, 2),
                                "change_percent": round(change_percent, 2),
                                "volume": int(volume),
                            }
                        )
                except Exception as e:
                    logger.debug(f"Error processing {symbol}: {str(e)}")
                    continue

            results.sort(key=lambda x: x["volume"], reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Error fetching most active stocks: {str(e)}")
            return []

    def get_sector_performance(self) -> dict[str, float]:
        """
        Get sector performance data.

        Returns:
            Dictionary mapping sector names to performance percentages
        """
        try:
            results = {}
            for sector, etf in SECTOR_ETFS.items():
                try:
                    data = yf.Ticker(etf)
                    hist = data.history(period="2d")

                    if len(hist) < 2:
                        continue

                    prev_close = hist["Close"].iloc[0]
                    current = hist["Close"].iloc[-1]
                    change_percent = ((current - prev_close) / prev_close) * 100

                    results[sector] = round(change_percent, 2)
                except Exception as e:
                    logger.debug(f"Error processing sector {sector}: {str(e)}")
                    continue

            return results

        except Exception as e:
            logger.error(f"Error fetching sector performance: {str(e)}")
            return {}

    def get_earnings_calendar(
        self, days: int = 7, symbols: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get upcoming earnings announcements.

        Args:
            days: Number of days to look ahead
            symbols: Optional list of symbols to check

        Returns:
            List of dictionaries with earnings data
        """
        try:
            # Get stocks to check
            if symbols:
                check_stocks = symbols[:50]
            else:
                # Get active stocks to check
                check_stocks = _get_finviz_movers("active", limit=50)

            results = []
            today = datetime.now(UTC).date()
            end_date = today + timedelta(days=days)

            for ticker in check_stocks:
                try:
                    data = yf.Ticker(ticker)

                    if hasattr(data, "calendar") and data.calendar is not None:
                        try:
                            calendar = data.calendar
                            if "Earnings Date" in calendar.index:
                                earnings_date = calendar.loc["Earnings Date"]

                                if hasattr(earnings_date, "date"):
                                    earnings_date = earnings_date.date()
                                elif isinstance(earnings_date, str):
                                    earnings_date = datetime.strptime(
                                        earnings_date, "%Y-%m-%d"
                                    ).date()
                                else:
                                    continue

                                if today <= earnings_date <= end_date:
                                    results.append(
                                        {
                                            "ticker": ticker,
                                            "name": data.info.get("shortName", ticker),
                                            "earnings_date": earnings_date.strftime(
                                                "%Y-%m-%d"
                                            ),
                                            "eps_estimate": float(
                                                calendar.loc["EPS Estimate"]
                                            )
                                            if "EPS Estimate" in calendar.index
                                            else None,
                                        }
                                    )
                        except Exception as e:
                            logger.debug(
                                f"Error parsing calendar for {ticker}: {str(e)}"
                            )
                            continue
                except Exception as e:
                    logger.debug(f"Error fetching data for {ticker}: {str(e)}")
                    continue

            results.sort(key=lambda x: x["earnings_date"])
            return results

        except Exception as e:
            logger.error(f"Error fetching earnings calendar: {str(e)}")
            return []

    # Async versions

    async def get_market_summary_async(self) -> dict[str, Any]:
        """Get market summary (async version)."""
        result = await self._run_in_executor(self.get_market_summary)
        return cast(dict[str, Any], result)

    async def get_top_gainers_async(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top gainers (async version)."""
        result = await self._run_in_executor(self.get_top_gainers, limit)
        return cast(list[dict[str, Any]], result)

    async def get_top_losers_async(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top losers (async version)."""
        result = await self._run_in_executor(self.get_top_losers, limit)
        return cast(list[dict[str, Any]], result)

    async def get_most_active_async(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most active stocks (async version)."""
        result = await self._run_in_executor(self.get_most_active, limit)
        return cast(list[dict[str, Any]], result)

    async def get_sector_performance_async(self) -> dict[str, float]:
        """Get sector performance (async version)."""
        result = await self._run_in_executor(self.get_sector_performance)
        return cast(dict[str, float], result)

    async def get_market_overview_async(self) -> dict[str, Any]:
        """
        Get comprehensive market overview (async version).

        Uses concurrent execution for better performance.
        """
        tasks = [
            self.get_market_summary_async(),
            self.get_top_gainers_async(5),
            self.get_top_losers_async(5),
            self.get_sector_performance_async(),
        ]

        summary, gainers, losers, sectors = await asyncio.gather(*tasks)

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "market_summary": summary,
            "top_gainers": gainers,
            "top_losers": losers,
            "sector_performance": sectors,
        }

    def get_market_overview(self) -> dict[str, Any]:
        """
        Get comprehensive market overview.

        Returns:
            Dictionary with market overview data
        """
        summary = self.get_market_summary()
        gainers = self.get_top_gainers(5)
        losers = self.get_top_losers(5)
        sectors = self.get_sector_performance()

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "market_summary": summary,
            "top_gainers": gainers,
            "top_losers": losers,
            "sector_performance": sectors,
        }


__all__ = [
    "MarketDataProvider",
    "MARKET_INDICES",
    "SECTOR_ETFS",
]
