"""
Backtesting router - thin wrapper around maverick-backtest.

All backtesting logic lives in maverick-backtest.
This router only defines MCP tool signatures and delegates.

Note: Requires maverick-backtest optional dependency.
"""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from maverick_server.capabilities_integration import with_audit

logger = logging.getLogger(__name__)

# Check if maverick-backtest is available
try:
    from maverick_backtest import (
        VectorBTEngine,
        list_available_strategies,
        StrategyParser,
    )
    BACKTEST_AVAILABLE = True
except ImportError:
    BACKTEST_AVAILABLE = False
    logger.warning("maverick-backtest not installed - backtesting tools disabled")


def register_backtesting_tools(mcp: FastMCP) -> None:
    """Register backtesting tools with MCP server.

    Only registers tools if maverick-backtest is installed.
    """
    if not BACKTEST_AVAILABLE:
        logger.info("Skipping backtesting tools - maverick-backtest not available")
        return

    @mcp.tool()
    @with_audit("backtest_run")
    async def backtest_run(
        symbol: str,
        strategy: str = "sma_cross",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_capital: float = 10000,
        fast_period: Optional[int] = None,
        slow_period: Optional[int] = None,
        period: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run a VectorBT backtest with specified strategy.

        Args:
            symbol: Stock symbol to backtest
            strategy: Strategy type (sma_cross, rsi, macd, bollinger, momentum)
            start_date: Start date (YYYY-MM-DD), defaults to 1 year ago
            end_date: End date (YYYY-MM-DD), defaults to today
            initial_capital: Starting capital for backtest
            fast_period: Fast period for SMA cross (default: 10)
            slow_period: Slow period for SMA cross (default: 20)
            period: Period for single-period indicators

        Returns:
            Comprehensive backtest results including metrics and trades
        """
        try:
            engine = VectorBTEngine()

            # Build parameters
            params = {}
            if fast_period:
                params["fast_period"] = fast_period
            if slow_period:
                params["slow_period"] = slow_period
            if period:
                params["period"] = period

            result = await engine.run_backtest(
                symbol=symbol,
                strategy=strategy,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                **params,
            )

            return {
                "symbol": symbol,
                "strategy": strategy,
                "metrics": {
                    "total_return": result.get("total_return"),
                    "sharpe_ratio": result.get("sharpe_ratio"),
                    "max_drawdown": result.get("max_drawdown"),
                    "win_rate": result.get("win_rate"),
                    "total_trades": result.get("total_trades"),
                },
                "period": {
                    "start": result.get("start_date"),
                    "end": result.get("end_date"),
                },
                "initial_capital": initial_capital,
                "final_value": result.get("final_value"),
            }
        except Exception as e:
            logger.error(f"Backtest error for {symbol}: {e}")
            return {"error": str(e)}

    @mcp.tool()
    @with_audit("backtest_compare_strategies")
    async def backtest_compare_strategies(
        symbol: str,
        strategies: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compare multiple strategies on the same symbol.

        Args:
            symbol: Stock symbol
            strategies: List of strategy types (defaults to all)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Comparison results with rankings
        """
        try:
            engine = VectorBTEngine()

            if strategies is None:
                strategies = ["sma_cross", "rsi", "macd", "bollinger"]

            results = []
            for strategy in strategies:
                try:
                    result = await engine.run_backtest(
                        symbol=symbol,
                        strategy=strategy,
                        start_date=start_date,
                        end_date=end_date,
                    )
                    results.append({
                        "strategy": strategy,
                        "total_return": result.get("total_return"),
                        "sharpe_ratio": result.get("sharpe_ratio"),
                        "max_drawdown": result.get("max_drawdown"),
                        "win_rate": result.get("win_rate"),
                    })
                except Exception as e:
                    results.append({
                        "strategy": strategy,
                        "error": str(e),
                    })

            # Sort by Sharpe ratio
            valid_results = [r for r in results if "error" not in r]
            valid_results.sort(key=lambda x: x.get("sharpe_ratio", 0) or 0, reverse=True)

            return {
                "symbol": symbol,
                "strategies_compared": len(strategies),
                "ranking": valid_results,
                "best_strategy": valid_results[0]["strategy"] if valid_results else None,
                "all_results": results,
            }
        except Exception as e:
            logger.error(f"Strategy comparison error for {symbol}: {e}")
            return {"error": str(e)}

    @mcp.tool()
    @with_audit("backtest_list_strategies")
    async def backtest_list_strategies() -> Dict[str, Any]:
        """List all available VectorBT strategies.

        Returns:
            Dictionary of available strategies and their information
        """
        try:
            strategies = list_available_strategies()

            return {
                "total_strategies": len(strategies),
                "strategies": [
                    {
                        "name": s.name,
                        "description": s.description,
                        "category": s.category,
                        "parameters": s.parameters,
                    }
                    for s in strategies
                ],
            }
        except Exception as e:
            logger.error(f"List strategies error: {e}")
            return {"error": str(e)}

    @mcp.tool()
    @with_audit("backtest_parse_strategy")
    async def backtest_parse_strategy(description: str) -> Dict[str, Any]:
        """Parse natural language strategy description into parameters.

        Args:
            description: Natural language description of trading strategy

        Returns:
            Parsed strategy configuration

        Examples:
            "Buy when RSI is below 30 and sell when above 70"
            "Use 10-day and 20-day moving average crossover"
        """
        try:
            parser = StrategyParser()
            result = parser.parse(description)

            return {
                "input": description,
                "parsed_strategy": result.strategy_type,
                "parameters": result.parameters,
                "confidence": result.confidence,
            }
        except Exception as e:
            logger.error(f"Strategy parsing error: {e}")
            return {"error": str(e)}

    logger.info("Registered backtesting tools")
