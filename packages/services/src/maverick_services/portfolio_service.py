"""
Portfolio management service.

Provides portfolio operations: add/remove positions, calculate P&L, performance metrics.
"""

from datetime import date, datetime, UTC
from decimal import Decimal
from typing import Protocol

from maverick_schemas.portfolio import (
    Position,
    PositionCreate,
    Portfolio,
    PortfolioSummary,
)
from maverick_schemas.base import Market, PositionStatus
from maverick_services.exceptions import (
    PortfolioNotFoundError,
    PositionNotFoundError,
    StockNotFoundError,
)


class PortfolioRepository(Protocol):
    """Protocol for portfolio data access."""

    async def get_portfolio(self, user_id: str, name: str) -> dict | None:
        """Get portfolio by user and name."""
        ...

    async def get_positions(self, user_id: str, portfolio_name: str) -> list[dict]:
        """Get all positions for a portfolio."""
        ...

    async def get_position(self, user_id: str, ticker: str) -> dict | None:
        """Get single position."""
        ...

    async def create_position(self, user_id: str, position: dict) -> dict:
        """Create new position."""
        ...

    async def update_position(self, user_id: str, ticker: str, updates: dict) -> dict:
        """Update existing position."""
        ...

    async def delete_position(self, user_id: str, ticker: str) -> bool:
        """Delete position."""
        ...


class QuoteProvider(Protocol):
    """Protocol for getting current prices."""

    async def get_quote(self, ticker: str) -> dict:
        """Get current quote for ticker."""
        ...


def _to_decimal(value: float | int | str | None) -> Decimal | None:
    """Convert to Decimal."""
    if value is None:
        return None
    return Decimal(str(value))


def _detect_market(ticker: str) -> Market:
    """Detect market from ticker."""
    ticker_upper = ticker.upper()
    if ticker_upper.endswith(".NS"):
        return Market.NSE
    elif ticker_upper.endswith(".BO"):
        return Market.BSE
    return Market.US


class PortfolioService:
    """
    Domain service for portfolio management.

    Handles position tracking, P&L calculations, and portfolio analytics.
    """

    def __init__(
        self,
        repository: PortfolioRepository,
        quote_provider: QuoteProvider | None = None,
    ):
        """
        Initialize portfolio service.

        Args:
            repository: Portfolio data repository
            quote_provider: Optional provider for current prices
        """
        self._repository = repository
        self._quote_provider = quote_provider

    async def get_portfolio(
        self,
        user_id: str,
        portfolio_name: str = "My Portfolio",
        include_prices: bool = True,
    ) -> Portfolio:
        """
        Get complete portfolio with positions.

        Args:
            user_id: User identifier
            portfolio_name: Portfolio name
            include_prices: Whether to fetch current prices

        Returns:
            Portfolio with positions and summary
        """
        positions_data = await self._repository.get_positions(user_id, portfolio_name)

        if not positions_data:
            # Return empty portfolio
            return Portfolio(
                name=portfolio_name,
                user_id=user_id,
                positions=[],
                summary=PortfolioSummary(
                    total_value=Decimal("0"),
                    total_cost=Decimal("0"),
                    total_pnl=Decimal("0"),
                    total_pnl_percent=Decimal("0"),
                    position_count=0,
                    last_updated=datetime.now(UTC),
                ),
            )

        # Convert to Position objects
        positions = []
        total_value = Decimal("0")
        total_cost = Decimal("0")
        winning = 0
        losing = 0

        for pos_data in positions_data:
            position = Position(
                id=pos_data.get("id"),
                ticker=pos_data["ticker"],
                shares=_to_decimal(pos_data["shares"]),
                avg_cost=_to_decimal(pos_data["avg_cost"]),
                total_cost=_to_decimal(pos_data["total_cost"]),
                market=_detect_market(pos_data["ticker"]),
                status=PositionStatus.OPEN,
                first_purchase_date=pos_data.get("first_purchase_date"),
                notes=pos_data.get("notes"),
            )

            # Fetch current price if requested and provider available
            if include_prices and self._quote_provider:
                try:
                    quote = await self._quote_provider.get_quote(position.ticker)
                    current_price = _to_decimal(quote.get("price"))
                    if current_price and position.shares:
                        position.current_price = current_price
                        position.current_value = current_price * position.shares
                        position.unrealized_pnl = position.current_value - position.total_cost
                        if position.total_cost and position.total_cost > 0:
                            position.unrealized_pnl_percent = (
                                position.unrealized_pnl / position.total_cost * 100
                            )

                        total_value += position.current_value
                        if position.unrealized_pnl > 0:
                            winning += 1
                        elif position.unrealized_pnl < 0:
                            losing += 1
                except Exception:
                    # Skip price lookup on error
                    pass

            total_cost += position.total_cost or Decimal("0")
            positions.append(position)

        # Calculate summary
        total_pnl = total_value - total_cost if total_value else Decimal("0")
        total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else Decimal("0")

        summary = PortfolioSummary(
            total_value=total_value,
            total_cost=total_cost,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            position_count=len(positions),
            winning_positions=winning,
            losing_positions=losing,
            last_updated=datetime.now(UTC),
        )

        return Portfolio(
            name=portfolio_name,
            user_id=user_id,
            positions=positions,
            summary=summary,
            updated_at=datetime.now(UTC),
        )

    async def add_position(
        self,
        user_id: str,
        position: PositionCreate,
        portfolio_name: str = "My Portfolio",
    ) -> Position:
        """
        Add or update a position.

        If position already exists, averages the cost basis.

        Args:
            user_id: User identifier
            position: Position to add
            portfolio_name: Portfolio name

        Returns:
            Created or updated Position
        """
        existing = await self._repository.get_position(user_id, position.ticker)

        if existing:
            # Average into existing position
            existing_shares = Decimal(str(existing["shares"]))
            existing_cost = Decimal(str(existing["total_cost"]))

            new_shares = existing_shares + position.shares
            new_total_cost = existing_cost + (position.shares * position.purchase_price)
            new_avg_cost = new_total_cost / new_shares

            updated = await self._repository.update_position(
                user_id,
                position.ticker,
                {
                    "shares": float(new_shares),
                    "avg_cost": float(new_avg_cost),
                    "total_cost": float(new_total_cost),
                },
            )

            return Position(
                id=updated.get("id"),
                ticker=position.ticker.upper(),
                shares=new_shares,
                avg_cost=new_avg_cost,
                total_cost=new_total_cost,
                market=_detect_market(position.ticker),
                notes=position.notes,
            )
        else:
            # Create new position
            total_cost = position.shares * position.purchase_price

            created = await self._repository.create_position(
                user_id,
                {
                    "ticker": position.ticker.upper(),
                    "shares": float(position.shares),
                    "avg_cost": float(position.purchase_price),
                    "total_cost": float(total_cost),
                    "portfolio_name": portfolio_name,
                    "first_purchase_date": position.purchase_date or date.today(),
                    "notes": position.notes,
                },
            )

            return Position(
                id=created.get("id"),
                ticker=position.ticker.upper(),
                shares=position.shares,
                avg_cost=position.purchase_price,
                total_cost=total_cost,
                market=_detect_market(position.ticker),
                first_purchase_date=position.purchase_date,
                notes=position.notes,
            )

    async def remove_position(
        self,
        user_id: str,
        ticker: str,
        shares: Decimal | None = None,
    ) -> Position | None:
        """
        Remove shares from a position or close entirely.

        Args:
            user_id: User identifier
            ticker: Stock ticker
            shares: Shares to remove (None = remove all)

        Returns:
            Updated or removed Position

        Raises:
            PositionNotFoundError: If position doesn't exist
        """
        existing = await self._repository.get_position(user_id, ticker)

        if not existing:
            raise PositionNotFoundError(ticker, user_id)

        existing_shares = Decimal(str(existing["shares"]))

        if shares is None or shares >= existing_shares:
            # Remove entire position
            await self._repository.delete_position(user_id, ticker)
            return None
        else:
            # Partial removal
            new_shares = existing_shares - shares
            avg_cost = Decimal(str(existing["avg_cost"]))
            new_total_cost = new_shares * avg_cost

            updated = await self._repository.update_position(
                user_id,
                ticker,
                {
                    "shares": float(new_shares),
                    "total_cost": float(new_total_cost),
                },
            )

            return Position(
                id=updated.get("id"),
                ticker=ticker.upper(),
                shares=new_shares,
                avg_cost=avg_cost,
                total_cost=new_total_cost,
            )


__all__ = ["PortfolioService"]

