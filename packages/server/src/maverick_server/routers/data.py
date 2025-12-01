"""
Data operations router - thin wrapper around maverick-data.

All data fetching and caching lives in maverick-data.
This router only defines MCP tool signatures and delegates.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from maverick_data import (
    YFinanceProvider,
    CacheManager,
    get_cache_manager,
    Stock,
    get_db,
)

logger = logging.getLogger(__name__)


def register_data_tools(mcp: FastMCP) -> None:
    """Register data operation tools with MCP server."""

    @mcp.tool()
    async def data_fetch_stock_data(
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch historical stock data for a given ticker.

        Uses intelligent caching to minimize API calls.

        Args:
            ticker: Stock ticker symbol (e.g., AAPL, MSFT)
            start_date: Start date in YYYY-MM-DD format (default: 1 year ago)
            end_date: End date in YYYY-MM-DD format (default: today)

        Returns:
            Dictionary containing the stock data
        """
        try:
            provider = YFinanceProvider()
            df = await provider.get_stock_data(
                ticker,
                start_date=start_date,
                end_date=end_date,
            )

            if df.empty:
                return {"error": f"No data found for {ticker}"}

            # Convert to serializable format
            return {
                "ticker": ticker,
                "data_points": len(df),
                "date_range": {
                    "start": str(df.index[0].date()),
                    "end": str(df.index[-1].date()),
                },
                "latest": {
                    "date": str(df.index[-1].date()),
                    "open": round(float(df["Open"].iloc[-1]), 2),
                    "high": round(float(df["High"].iloc[-1]), 2),
                    "low": round(float(df["Low"].iloc[-1]), 2),
                    "close": round(float(df["Close"].iloc[-1]), 2),
                    "volume": int(df["Volume"].iloc[-1]),
                },
            }
        except Exception as e:
            logger.error(f"Fetch stock data error for {ticker}: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def data_fetch_stock_data_batch(
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch historical data for multiple tickers.

        More efficient than calling fetch_stock_data multiple times.

        Args:
            tickers: List of ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with ticker symbols as keys
        """
        try:
            provider = YFinanceProvider()

            async def fetch_single_ticker(ticker: str) -> tuple[str, dict]:
                """Fetch data for a single ticker."""
                try:
                    df = await provider.get_stock_data(
                        ticker,
                        start_date=start_date,
                        end_date=end_date,
                    )

                    if not df.empty:
                        return ticker, {
                            "data_points": len(df),
                            "latest_close": round(float(df["Close"].iloc[-1]), 2),
                            "latest_date": str(df.index[-1].date()),
                        }
                    else:
                        return ticker, {"error": "No data found"}
                except Exception as e:
                    return ticker, {"error": str(e)}

            # Fetch all tickers in parallel
            ticker_results = await asyncio.gather(
                *[fetch_single_ticker(t) for t in tickers]
            )

            results = {ticker: result for ticker, result in ticker_results}

            return {
                "tickers_requested": len(tickers),
                "tickers_successful": len([r for r in results.values() if "error" not in r]),
                "results": results,
            }
        except Exception as e:
            logger.error(f"Batch fetch error: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def data_get_stock_info(ticker: str) -> Dict[str, Any]:
        """Get detailed fundamental information about a stock.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary containing detailed stock information
        """
        try:
            provider = YFinanceProvider()
            info = await provider.get_stock_info(ticker)

            if not info:
                return {"error": f"No info found for {ticker}"}

            return {
                "ticker": ticker,
                "name": info.get("longName", info.get("shortName", ticker)),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "average_volume": info.get("averageVolume"),
            }
        except Exception as e:
            logger.error(f"Get stock info error for {ticker}: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def data_get_chart_links(ticker: str) -> Dict[str, Any]:
        """Provide links to various financial charting websites.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary containing links to chart providers
        """
        ticker_clean = ticker.upper().replace(".", "-")

        return {
            "ticker": ticker,
            "chart_links": {
                "tradingview": f"https://www.tradingview.com/chart/?symbol={ticker_clean}",
                "finviz": f"https://finviz.com/quote.ashx?t={ticker_clean}",
                "yahoo_finance": f"https://finance.yahoo.com/quote/{ticker}",
                "stockcharts": f"https://stockcharts.com/h-sc/ui?s={ticker_clean}",
                "google_finance": f"https://www.google.com/finance/quote/{ticker_clean}:NASDAQ",
            },
        }

    @mcp.tool()
    async def data_clear_cache(ticker: Optional[str] = None) -> Dict[str, Any]:
        """Clear cached data for a specific ticker or all tickers.

        Args:
            ticker: Specific ticker to clear (None to clear all)

        Returns:
            Dictionary with cache clearing status
        """
        try:
            cache = get_cache_manager()

            if ticker:
                # Clear specific ticker cache
                pattern = f"*{ticker.upper()}*"
                cleared = await cache.clear_pattern(pattern)
                return {
                    "success": True,
                    "ticker": ticker.upper(),
                    "keys_cleared": cleared,
                }
            else:
                # Clear all cache
                cleared = await cache.clear_all()
                return {
                    "success": True,
                    "message": "All cache cleared",
                    "keys_cleared": cleared,
                }
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return {"error": str(e)}

    logger.info("Registered data tools")
