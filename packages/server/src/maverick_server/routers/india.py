"""
Indian market router - thin wrapper around maverick-india.

All Indian market logic lives in maverick-india.
This router only defines MCP tool signatures and delegates.

Note: Requires maverick-india optional dependency.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Check if maverick-india is available
try:
    from maverick_india import (
        IndianMarketProvider,
        IndianMarketScreener,
        IndianNewsProvider,
        EconomicIndicatorsProvider,
        CurrencyConverter,
    )
    INDIA_AVAILABLE = True
except ImportError:
    INDIA_AVAILABLE = False
    logger.warning("maverick-india not installed - India market tools disabled")


def register_india_tools(mcp: FastMCP) -> None:
    """Register Indian market tools with MCP server.

    Only registers tools if maverick-india is installed.
    """
    if not INDIA_AVAILABLE:
        logger.info("Skipping India tools - maverick-india not available")
        return

    @mcp.tool()
    async def india_get_market_overview() -> dict[str, Any]:
        """Get comprehensive overview of Indian stock market.

        Includes market status, trading hours, and major indices.

        Returns:
            Dictionary with Indian market overview
        """
        try:
            provider = IndianMarketProvider()
            overview = await provider.get_market_overview()

            return {
                "market_status": overview.get("status"),
                "trading_hours": overview.get("trading_hours"),
                "nifty_50": overview.get("nifty_50"),
                "sensex": overview.get("sensex"),
                "tracked_stocks": overview.get("tracked_stocks", 0),
            }
        except Exception as e:
            logger.error(f"India market overview error: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def india_get_recommendations(
        strategy: str = "bullish",
        limit: int = 20,
    ) -> dict[str, Any]:
        """Get stock recommendations for Indian market (NSE/BSE).

        Available strategies:
        - bullish: Maverick bullish strategy for Indian market
        - bearish: Bearish/short opportunities
        - momentum: Nifty 50 momentum plays
        - value: Value investing picks (P/E < 20, dividend > 2%)
        - dividend: High dividend yield stocks
        - smallcap: Small-cap breakout opportunities

        Args:
            strategy: Screening strategy to use
            limit: Maximum number of recommendations

        Returns:
            Dictionary with recommendations
        """
        try:
            screener = IndianMarketScreener()
            results = await screener.screen(strategy=strategy, limit=limit)

            return {
                "strategy": strategy,
                "count": len(results),
                "recommendations": results,
            }
        except Exception as e:
            logger.error(f"India recommendations error: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def india_get_economic_indicators() -> dict[str, Any]:
        """Get current Indian economic indicators from RBI.

        Includes RBI policy rates, GDP growth, inflation, and forex reserves.

        Returns:
            Dictionary with comprehensive economic data
        """
        try:
            provider = EconomicIndicatorsProvider()
            indicators = await provider.get_indicators()

            return {
                "rbi_rates": indicators.get("rbi_rates", {}),
                "gdp_growth": indicators.get("gdp_growth"),
                "inflation": indicators.get("inflation"),
                "forex_reserves": indicators.get("forex_reserves"),
                "economic_calendar": indicators.get("calendar", []),
            }
        except Exception as e:
            logger.error(f"Economic indicators error: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def india_get_stock_news(
        symbol: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Get news articles for an Indian stock with sentiment.

        Args:
            symbol: Stock ticker symbol (e.g., "RELIANCE.NS")
            limit: Maximum number of articles

        Returns:
            Dictionary with news articles and sentiment
        """
        try:
            provider = IndianNewsProvider()
            news = await provider.get_stock_news(symbol=symbol, limit=limit)

            return {
                "symbol": symbol,
                "article_count": len(news.get("articles", [])),
                "articles": news.get("articles", []),
                "overall_sentiment": news.get("sentiment", "neutral"),
            }
        except Exception as e:
            logger.error(f"India stock news error for {symbol}: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def india_convert_currency(
        amount: float,
        from_currency: str = "INR",
        to_currency: str = "USD",
    ) -> dict[str, Any]:
        """Convert amount between currencies.

        Args:
            amount: Amount to convert
            from_currency: Source currency (INR, USD, EUR, GBP, etc.)
            to_currency: Target currency

        Returns:
            Dictionary with conversion result
        """
        try:
            converter = CurrencyConverter()
            result = await converter.convert(
                amount=amount,
                from_currency=from_currency,
                to_currency=to_currency,
            )

            return {
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "converted_amount": result.get("converted"),
                "exchange_rate": result.get("rate"),
                "rate_source": result.get("source", "approximate"),
            }
        except Exception as e:
            logger.error(f"Currency conversion error: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def india_analyze_nifty_sectors() -> dict[str, Any]:
        """Analyze Nifty 50 sector rotation and performance.

        Returns sector rankings and top performing stocks.

        Returns:
            Dictionary with sector analysis
        """
        try:
            screener = IndianMarketScreener()
            analysis = await screener.analyze_sectors()

            return {
                "sector_rankings": analysis.get("rankings", []),
                "top_performers": analysis.get("top_performers", {}),
                "sector_rotation": analysis.get("rotation", "neutral"),
            }
        except Exception as e:
            logger.error(f"Nifty sector analysis error: {e}")
            return {"error": str(e)}

    logger.info("Registered India market tools")
