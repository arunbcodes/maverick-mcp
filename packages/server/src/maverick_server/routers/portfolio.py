"""
Portfolio management router - thin wrapper around maverick-data.

All portfolio logic and persistence lives in maverick-data.
This router only defines MCP tool signatures and delegates.
"""

import logging
from datetime import date
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from maverick_core import Portfolio, Position
from maverick_data import (
    PortfolioRepository,
    YFinanceProvider,
    get_db,
)
from maverick_server.capabilities_integration import with_audit

logger = logging.getLogger(__name__)


def register_portfolio_tools(mcp: FastMCP) -> None:
    """Register portfolio management tools with MCP server."""

    @mcp.tool()
    @with_audit("portfolio_add_position")
    async def portfolio_add_position(
        ticker: str,
        shares: float,
        purchase_price: float,
        purchase_date: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: str = "default",
        portfolio_name: str = "My Portfolio",
    ) -> Dict[str, Any]:
        """Add a stock position to your portfolio.

        If the ticker already exists, it will average the cost basis.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            shares: Number of shares (supports fractional)
            purchase_price: Price per share at purchase
            purchase_date: Purchase date in YYYY-MM-DD format
            notes: Optional notes about this position
            user_id: User identifier (default: "default")
            portfolio_name: Portfolio name (default: "My Portfolio")

        Returns:
            Dictionary containing the updated position information
        """
        try:
            with next(get_db()) as db:
                repo = PortfolioRepository(db)

                # Get or create portfolio
                portfolio = repo.get_portfolio(user_id, portfolio_name)
                if portfolio is None:
                    portfolio = Portfolio(
                        portfolio_id=f"{user_id}_{portfolio_name}",
                        user_id=user_id,
                        name=portfolio_name,
                    )

                # Parse date
                parsed_date = None
                if purchase_date:
                    parsed_date = date.fromisoformat(purchase_date)

                # Add position (handles averaging)
                position = Position(
                    ticker=ticker.upper(),
                    shares=shares,
                    average_cost_basis=purchase_price,
                    purchase_date=parsed_date,
                    notes=notes,
                )
                portfolio.add_position(position)

                # Save
                repo.save_portfolio(portfolio)

                return {
                    "success": True,
                    "ticker": ticker.upper(),
                    "shares": portfolio.get_position(ticker.upper()).shares,
                    "average_cost_basis": portfolio.get_position(ticker.upper()).average_cost_basis,
                    "portfolio": portfolio_name,
                }
        except Exception as e:
            logger.error(f"Add position error: {e}")
            return {"error": str(e)}

    @mcp.tool()
    @with_audit("portfolio_get_my_portfolio")
    async def portfolio_get_my_portfolio(
        user_id: str = "default",
        portfolio_name: str = "My Portfolio",
        include_current_prices: bool = True,
    ) -> Dict[str, Any]:
        """Get your complete portfolio with all positions and performance.

        Args:
            user_id: User identifier (default: "default")
            portfolio_name: Portfolio name (default: "My Portfolio")
            include_current_prices: Fetch live prices for P&L (default: True)

        Returns:
            Dictionary containing portfolio with performance metrics
        """
        try:
            with next(get_db()) as db:
                repo = PortfolioRepository(db)
                portfolio = repo.get_portfolio(user_id, portfolio_name)

                if portfolio is None:
                    return {
                        "portfolio_name": portfolio_name,
                        "positions": [],
                        "total_invested": 0,
                        "message": "Portfolio not found or empty",
                    }

                positions = []
                total_invested = portfolio.get_total_invested()
                total_current_value = 0
                total_unrealized_pnl = 0

                # Get current prices if requested
                provider = YFinanceProvider() if include_current_prices else None

                for ticker in portfolio.get_tickers():
                    pos = portfolio.get_position(ticker)
                    pos_data = {
                        "ticker": ticker,
                        "shares": pos.shares,
                        "average_cost_basis": round(pos.average_cost_basis, 2),
                        "total_cost": round(pos.total_cost, 2),
                    }

                    if provider:
                        try:
                            current_price = await provider.get_current_price(ticker)
                            if current_price:
                                current_value = pos.shares * current_price
                                unrealized_pnl = current_value - pos.total_cost
                                pnl_percent = (unrealized_pnl / pos.total_cost) * 100

                                pos_data.update({
                                    "current_price": round(current_price, 2),
                                    "current_value": round(current_value, 2),
                                    "unrealized_pnl": round(unrealized_pnl, 2),
                                    "pnl_percent": round(pnl_percent, 2),
                                })

                                total_current_value += current_value
                                total_unrealized_pnl += unrealized_pnl
                        except Exception:
                            pass  # Skip price fetch errors

                    positions.append(pos_data)

                result = {
                    "portfolio_name": portfolio_name,
                    "position_count": len(positions),
                    "positions": positions,
                    "total_invested": round(total_invested, 2),
                }

                if include_current_prices and total_current_value > 0:
                    result.update({
                        "total_current_value": round(total_current_value, 2),
                        "total_unrealized_pnl": round(total_unrealized_pnl, 2),
                        "total_pnl_percent": round((total_unrealized_pnl / total_invested) * 100, 2),
                    })

                return result
        except Exception as e:
            logger.error(f"Get portfolio error: {e}")
            return {"error": str(e)}

    @mcp.tool()
    @with_audit("portfolio_remove_position")
    async def portfolio_remove_position(
        ticker: str,
        shares: Optional[float] = None,
        user_id: str = "default",
        portfolio_name: str = "My Portfolio",
    ) -> Dict[str, Any]:
        """Remove shares from a position in your portfolio.

        Args:
            ticker: Stock ticker symbol
            shares: Number of shares to remove (None = remove entire position)
            user_id: User identifier
            portfolio_name: Portfolio name

        Returns:
            Dictionary containing the updated or removed position
        """
        try:
            with next(get_db()) as db:
                repo = PortfolioRepository(db)
                portfolio = repo.get_portfolio(user_id, portfolio_name)

                if portfolio is None:
                    return {"error": f"Portfolio '{portfolio_name}' not found"}

                ticker = ticker.upper()
                position = portfolio.get_position(ticker)

                if position is None:
                    return {"error": f"Position {ticker} not found in portfolio"}

                if shares is None or shares >= position.shares:
                    # Remove entire position
                    portfolio.remove_position(ticker)
                    repo.save_portfolio(portfolio)
                    return {
                        "success": True,
                        "action": "removed",
                        "ticker": ticker,
                        "shares_removed": position.shares,
                    }
                else:
                    # Remove partial shares
                    position.remove_shares(shares)
                    repo.save_portfolio(portfolio)
                    return {
                        "success": True,
                        "action": "reduced",
                        "ticker": ticker,
                        "shares_removed": shares,
                        "shares_remaining": position.shares,
                    }
        except Exception as e:
            logger.error(f"Remove position error: {e}")
            return {"error": str(e)}

    @mcp.tool()
    @with_audit("portfolio_clear_portfolio")
    async def portfolio_clear_portfolio(
        user_id: str = "default",
        portfolio_name: str = "My Portfolio",
        confirm: bool = False,
    ) -> Dict[str, Any]:
        """Clear all positions from your portfolio.

        CAUTION: This removes all positions. Cannot be undone.

        Args:
            user_id: User identifier
            portfolio_name: Portfolio name
            confirm: Must be True to confirm deletion (safety check)

        Returns:
            Dictionary containing confirmation of cleared positions
        """
        if not confirm:
            return {
                "error": "Must set confirm=True to clear portfolio",
                "message": "This action cannot be undone",
            }

        try:
            with next(get_db()) as db:
                repo = PortfolioRepository(db)
                portfolio = repo.get_portfolio(user_id, portfolio_name)

                if portfolio is None:
                    return {"error": f"Portfolio '{portfolio_name}' not found"}

                position_count = len(portfolio.get_tickers())
                portfolio.clear_all_positions()
                repo.save_portfolio(portfolio)

                return {
                    "success": True,
                    "portfolio_name": portfolio_name,
                    "positions_cleared": position_count,
                }
        except Exception as e:
            logger.error(f"Clear portfolio error: {e}")
            return {"error": str(e)}

    logger.info("Registered portfolio tools")
