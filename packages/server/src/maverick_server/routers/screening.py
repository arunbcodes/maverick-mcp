"""
Stock screening router - thin wrapper around maverick-data.

All screening logic and database access lives in maverick-data.
This router only defines MCP tool signatures and delegates.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from maverick_data import (
    MaverickStocks,
    MaverickBearStocks,
    SupplyDemandBreakoutStocks,
    ScreeningRepository,
    get_db,
)

if TYPE_CHECKING:
    from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_screening_tools(mcp: FastMCP) -> None:
    """Register stock screening tools with MCP server."""

    @mcp.tool()
    async def screening_get_maverick_stocks(limit: int = 20) -> dict[str, Any]:
        """Get top Maverick stocks from the screening results.

        The Maverick screening strategy identifies stocks with:
        - High momentum strength
        - Technical patterns (Cup & Handle, consolidation, etc.)
        - Strong combined scores

        Args:
            limit: Maximum number of stocks to return (default: 20)

        Returns:
            Dictionary containing Maverick stock screening results
        """
        try:
            with next(get_db()) as db:
                stocks = (
                    db.query(MaverickStocks)
                    .order_by(MaverickStocks.combined_score.desc())
                    .limit(limit)
                    .all()
                )

                return {
                    "strategy": "maverick_bullish",
                    "count": len(stocks),
                    "stocks": [
                        {
                            "ticker": s.ticker,
                            "combined_score": s.combined_score,
                            "momentum_score": s.momentum_score,
                            "pattern": s.pattern,
                            "sector": s.sector,
                        }
                        for s in stocks
                    ],
                }
        except Exception as e:
            logger.error(f"Maverick screening error: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def screening_get_maverick_bear_stocks(limit: int = 20) -> dict[str, Any]:
        """Get top Maverick Bear stocks from the screening results.

        The Maverick Bear screening identifies stocks with:
        - Weak momentum strength
        - Bearish technical patterns
        - High bear scores

        Args:
            limit: Maximum number of stocks to return (default: 20)

        Returns:
            Dictionary containing Maverick Bear stock screening results
        """
        try:
            with next(get_db()) as db:
                stocks = (
                    db.query(MaverickBearStocks)
                    .order_by(MaverickBearStocks.bear_score.desc())
                    .limit(limit)
                    .all()
                )

                return {
                    "strategy": "maverick_bearish",
                    "count": len(stocks),
                    "stocks": [
                        {
                            "ticker": s.ticker,
                            "bear_score": s.bear_score,
                            "pattern": s.pattern,
                            "sector": s.sector,
                        }
                        for s in stocks
                    ],
                }
        except Exception as e:
            logger.error(f"Maverick Bear screening error: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def screening_get_supply_demand_breakouts(
        limit: int = 20,
        filter_moving_averages: bool = False,
    ) -> dict[str, Any]:
        """Get stocks showing supply/demand breakout patterns.

        This screening identifies stocks in the demand expansion phase with:
        - Price above all major moving averages
        - Moving averages in proper alignment (50 > 150 > 200)
        - Strong momentum strength

        Args:
            limit: Maximum number of stocks to return (default: 20)
            filter_moving_averages: If True, only return stocks above all MAs

        Returns:
            Dictionary containing supply/demand breakout screening results
        """
        try:
            with next(get_db()) as db:
                query = db.query(SupplyDemandBreakoutStocks)

                if filter_moving_averages:
                    query = query.filter(
                        SupplyDemandBreakoutStocks.above_all_mas == True  # noqa: E712
                    )

                stocks = (
                    query.order_by(SupplyDemandBreakoutStocks.breakout_score.desc())
                    .limit(limit)
                    .all()
                )

                return {
                    "strategy": "supply_demand_breakout",
                    "count": len(stocks),
                    "filter_applied": filter_moving_averages,
                    "stocks": [
                        {
                            "ticker": s.ticker,
                            "breakout_score": s.breakout_score,
                            "above_all_mas": s.above_all_mas,
                            "sector": s.sector,
                        }
                        for s in stocks
                    ],
                }
        except Exception as e:
            logger.error(f"Supply/demand breakout screening error: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def screening_get_all_recommendations() -> dict[str, Any]:
        """Get comprehensive screening results from all strategies.

        Returns the top stocks from each screening strategy:
        - Maverick Bullish: High momentum growth stocks
        - Maverick Bearish: Weak stocks for short opportunities
        - Supply/Demand Breakouts: Stocks breaking out from accumulation

        Returns:
            Dictionary containing all screening results organized by strategy
        """
        try:
            with next(get_db()) as db:
                repo = ScreeningRepository(db)

                maverick = repo.get_latest_screening("maverick", limit=10)
                bear = repo.get_latest_screening("maverick_bear", limit=10)
                breakout = repo.get_latest_screening("supply_demand", limit=10)

                return {
                    "maverick_bullish": {
                        "count": len(maverick),
                        "stocks": [s.to_dict() for s in maverick],
                    },
                    "maverick_bearish": {
                        "count": len(bear),
                        "stocks": [s.to_dict() for s in bear],
                    },
                    "supply_demand_breakouts": {
                        "count": len(breakout),
                        "stocks": [s.to_dict() for s in breakout],
                    },
                }
        except Exception as e:
            logger.error(f"All recommendations error: {e}")
            return {"error": str(e)}

    logger.info("Registered screening tools")
