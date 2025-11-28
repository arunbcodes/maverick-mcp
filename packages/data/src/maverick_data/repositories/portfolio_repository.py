"""
Portfolio Repository Implementation.

Implements IPortfolioRepository interface for portfolio persistence operations.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from maverick_data.models import UserPortfolio, PortfolioPosition
from maverick_data.session import get_async_db

logger = logging.getLogger(__name__)


class PortfolioRepository:
    """
    Repository for portfolio persistence operations.

    Implements IPortfolioRepository interface to provide CRUD operations
    for user portfolios and their positions.

    Features:
    - Async operations for better performance
    - Position management with cost basis tracking
    - Multi-portfolio support per user
    - Automatic cost basis averaging
    """

    def __init__(self, session: AsyncSession | None = None):
        """
        Initialize repository with optional session.

        Args:
            session: Optional AsyncSession for dependency injection.
                    If None, sessions will be created per-operation.
        """
        self._session = session

    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if self._session:
            return self._session
        async for session in get_async_db():
            return session
        raise RuntimeError("Failed to get database session")

    async def get_portfolio(
        self,
        user_id: str,
        portfolio_name: str,
    ) -> dict[str, Any] | None:
        """
        Get portfolio by user and name.

        Args:
            user_id: User identifier
            portfolio_name: Portfolio name

        Returns:
            Portfolio data or None if not found
        """
        session = await self._get_session()

        try:
            result = await session.execute(
                select(UserPortfolio)
                .where(UserPortfolio.user_id == user_id)
                .where(UserPortfolio.name == portfolio_name)
            )
            portfolio = result.scalar_one_or_none()

            if portfolio:
                return self._portfolio_to_dict(portfolio)
            return None
        except Exception as e:
            logger.error(f"Error getting portfolio {portfolio_name} for user {user_id}: {e}")
            return None

    async def get_portfolio_by_id(self, portfolio_id: str) -> dict[str, Any] | None:
        """
        Get portfolio by ID.

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            Portfolio data or None if not found
        """
        session = await self._get_session()

        try:
            portfolio_uuid = uuid.UUID(portfolio_id)
            result = await session.execute(
                select(UserPortfolio).where(UserPortfolio.id == portfolio_uuid)
            )
            portfolio = result.scalar_one_or_none()

            if portfolio:
                return self._portfolio_to_dict(portfolio)
            return None
        except Exception as e:
            logger.error(f"Error getting portfolio by ID {portfolio_id}: {e}")
            return None

    async def save_portfolio(self, portfolio: dict[str, Any]) -> dict[str, Any]:
        """
        Save portfolio (create or update).

        Args:
            portfolio: Portfolio data dictionary

        Returns:
            Saved portfolio data
        """
        session = await self._get_session()

        try:
            user_id = portfolio.get("user_id", "default")
            name = portfolio.get("name", "My Portfolio")
            portfolio_id = portfolio.get("id")

            if portfolio_id:
                # Update existing portfolio
                portfolio_uuid = uuid.UUID(portfolio_id)
                result = await session.execute(
                    select(UserPortfolio).where(UserPortfolio.id == portfolio_uuid)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.name = name
                    existing.user_id = user_id
                else:
                    # ID provided but not found, create new
                    existing = UserPortfolio(
                        id=portfolio_uuid,
                        user_id=user_id,
                        name=name,
                    )
                    session.add(existing)
            else:
                # Check if portfolio with same name exists
                result = await session.execute(
                    select(UserPortfolio)
                    .where(UserPortfolio.user_id == user_id)
                    .where(UserPortfolio.name == name)
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    existing = UserPortfolio(
                        user_id=user_id,
                        name=name,
                    )
                    session.add(existing)

            await session.commit()
            await session.refresh(existing)
            return self._portfolio_to_dict(existing)

        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving portfolio: {e}")
            raise

    async def get_positions(
        self,
        portfolio_id: str,
    ) -> list[dict[str, Any]]:
        """
        Get all positions in portfolio.

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            List of position data dictionaries
        """
        session = await self._get_session()

        try:
            portfolio_uuid = uuid.UUID(portfolio_id)
            result = await session.execute(
                select(PortfolioPosition)
                .where(PortfolioPosition.portfolio_id == portfolio_uuid)
                .order_by(PortfolioPosition.ticker)
            )
            positions = result.scalars().all()
            return [self._position_to_dict(p) for p in positions]
        except Exception as e:
            logger.error(f"Error getting positions for portfolio {portfolio_id}: {e}")
            return []

    async def get_position(
        self,
        portfolio_id: str,
        symbol: str,
    ) -> dict[str, Any] | None:
        """
        Get specific position in portfolio.

        Args:
            portfolio_id: Portfolio identifier
            symbol: Stock ticker

        Returns:
            Position data or None if not found
        """
        session = await self._get_session()
        symbol = symbol.upper()

        try:
            portfolio_uuid = uuid.UUID(portfolio_id)
            result = await session.execute(
                select(PortfolioPosition)
                .where(PortfolioPosition.portfolio_id == portfolio_uuid)
                .where(PortfolioPosition.ticker == symbol)
            )
            position = result.scalar_one_or_none()

            if position:
                return self._position_to_dict(position)
            return None
        except Exception as e:
            logger.error(f"Error getting position {symbol} in portfolio {portfolio_id}: {e}")
            return None

    async def save_position(self, position: dict[str, Any]) -> dict[str, Any]:
        """
        Save position (create or update with cost basis averaging).

        Args:
            position: Position data dictionary with:
                - portfolio_id: Portfolio identifier
                - ticker: Stock symbol
                - shares: Number of shares
                - purchase_price: Price per share
                - purchase_date: Optional date (defaults to today)
                - notes: Optional notes

        Returns:
            Saved position data
        """
        session = await self._get_session()

        try:
            portfolio_uuid = uuid.UUID(position["portfolio_id"])
            ticker = position["ticker"].upper()
            new_shares = Decimal(str(position["shares"]))
            new_price = Decimal(str(position["purchase_price"]))
            purchase_date = position.get("purchase_date")

            if purchase_date and isinstance(purchase_date, str):
                purchase_date = datetime.fromisoformat(purchase_date.replace("Z", "+00:00"))
            elif not purchase_date:
                purchase_date = datetime.now(UTC)

            notes = position.get("notes")

            # Check for existing position
            result = await session.execute(
                select(PortfolioPosition)
                .where(PortfolioPosition.portfolio_id == portfolio_uuid)
                .where(PortfolioPosition.ticker == ticker)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Calculate new average cost basis
                existing_total = existing.shares * existing.average_cost_basis
                new_total = new_shares * new_price
                combined_shares = existing.shares + new_shares

                if combined_shares > 0:
                    new_avg_cost = (existing_total + new_total) / combined_shares
                else:
                    new_avg_cost = Decimal("0")

                existing.shares = combined_shares
                existing.average_cost_basis = new_avg_cost
                existing.total_cost = combined_shares * new_avg_cost
                if notes:
                    existing.notes = notes
                # Keep earliest purchase date
                if purchase_date < existing.purchase_date:
                    existing.purchase_date = purchase_date

                await session.commit()
                await session.refresh(existing)
                return self._position_to_dict(existing)
            else:
                # Create new position
                new_position = PortfolioPosition(
                    portfolio_id=portfolio_uuid,
                    ticker=ticker,
                    shares=new_shares,
                    average_cost_basis=new_price,
                    total_cost=new_shares * new_price,
                    purchase_date=purchase_date,
                    notes=notes,
                )
                session.add(new_position)
                await session.commit()
                await session.refresh(new_position)
                return self._position_to_dict(new_position)

        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving position: {e}")
            raise

    async def update_position_shares(
        self,
        portfolio_id: str,
        symbol: str,
        shares_delta: float,
    ) -> dict[str, Any] | None:
        """
        Update position shares (add or remove).

        Args:
            portfolio_id: Portfolio identifier
            symbol: Stock ticker
            shares_delta: Change in shares (negative to remove)

        Returns:
            Updated position data or None if position removed
        """
        session = await self._get_session()
        symbol = symbol.upper()

        try:
            portfolio_uuid = uuid.UUID(portfolio_id)
            result = await session.execute(
                select(PortfolioPosition)
                .where(PortfolioPosition.portfolio_id == portfolio_uuid)
                .where(PortfolioPosition.ticker == symbol)
            )
            position = result.scalar_one_or_none()

            if not position:
                logger.warning(f"Position {symbol} not found in portfolio {portfolio_id}")
                return None

            new_shares = position.shares + Decimal(str(shares_delta))

            if new_shares <= 0:
                # Remove position entirely
                await session.delete(position)
                await session.commit()
                logger.info(f"Removed position {symbol} from portfolio {portfolio_id}")
                return None
            else:
                # Update shares and total cost
                position.shares = new_shares
                position.total_cost = new_shares * position.average_cost_basis
                await session.commit()
                await session.refresh(position)
                return self._position_to_dict(position)

        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating position shares: {e}")
            raise

    async def delete_position(
        self,
        portfolio_id: str,
        symbol: str,
    ) -> bool:
        """
        Delete position from portfolio.

        Args:
            portfolio_id: Portfolio identifier
            symbol: Stock ticker

        Returns:
            True if deleted, False if not found
        """
        session = await self._get_session()
        symbol = symbol.upper()

        try:
            portfolio_uuid = uuid.UUID(portfolio_id)
            result = await session.execute(
                delete(PortfolioPosition)
                .where(PortfolioPosition.portfolio_id == portfolio_uuid)
                .where(PortfolioPosition.ticker == symbol)
            )
            await session.commit()

            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted position {symbol} from portfolio {portfolio_id}")
            return deleted
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting position {symbol}: {e}")
            return False

    async def get_user_portfolios(
        self,
        user_id: str,
    ) -> list[dict[str, Any]]:
        """
        Get all portfolios for user.

        Args:
            user_id: User identifier

        Returns:
            List of portfolio data dictionaries
        """
        session = await self._get_session()

        try:
            result = await session.execute(
                select(UserPortfolio)
                .where(UserPortfolio.user_id == user_id)
                .order_by(UserPortfolio.name)
            )
            portfolios = result.scalars().all()
            return [self._portfolio_to_dict(p) for p in portfolios]
        except Exception as e:
            logger.error(f"Error getting portfolios for user {user_id}: {e}")
            return []

    async def clear_portfolio(
        self,
        portfolio_id: str,
    ) -> bool:
        """
        Clear all positions from portfolio.

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            True if cleared successfully
        """
        session = await self._get_session()

        try:
            portfolio_uuid = uuid.UUID(portfolio_id)
            result = await session.execute(
                delete(PortfolioPosition)
                .where(PortfolioPosition.portfolio_id == portfolio_uuid)
            )
            await session.commit()

            deleted_count = result.rowcount
            logger.info(f"Cleared {deleted_count} positions from portfolio {portfolio_id}")
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"Error clearing portfolio {portfolio_id}: {e}")
            return False

    async def delete_portfolio(
        self,
        portfolio_id: str,
    ) -> bool:
        """
        Delete portfolio and all its positions.

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            True if deleted successfully
        """
        session = await self._get_session()

        try:
            portfolio_uuid = uuid.UUID(portfolio_id)

            # Delete portfolio (cascade will delete positions)
            result = await session.execute(
                delete(UserPortfolio).where(UserPortfolio.id == portfolio_uuid)
            )
            await session.commit()

            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted portfolio {portfolio_id}")
            return deleted
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting portfolio {portfolio_id}: {e}")
            return False

    async def get_or_create_portfolio(
        self,
        user_id: str,
        portfolio_name: str,
    ) -> dict[str, Any]:
        """
        Get existing portfolio or create new one.

        Args:
            user_id: User identifier
            portfolio_name: Portfolio name

        Returns:
            Portfolio data dictionary
        """
        existing = await self.get_portfolio(user_id, portfolio_name)
        if existing:
            return existing

        return await self.save_portfolio({
            "user_id": user_id,
            "name": portfolio_name,
        })

    def _portfolio_to_dict(self, portfolio: UserPortfolio) -> dict[str, Any]:
        """Convert portfolio model to dictionary."""
        return {
            "id": str(portfolio.id),
            "user_id": portfolio.user_id,
            "name": portfolio.name,
            "positions": [
                self._position_to_dict(p) for p in portfolio.positions
            ] if portfolio.positions else [],
            "created_at": portfolio.created_at.isoformat() if portfolio.created_at else None,
            "updated_at": portfolio.updated_at.isoformat() if portfolio.updated_at else None,
        }

    def _position_to_dict(self, position: PortfolioPosition) -> dict[str, Any]:
        """Convert position model to dictionary."""
        return {
            "id": str(position.id),
            "portfolio_id": str(position.portfolio_id),
            "ticker": position.ticker,
            "shares": float(position.shares),
            "average_cost_basis": float(position.average_cost_basis),
            "total_cost": float(position.total_cost),
            "purchase_date": position.purchase_date.isoformat() if position.purchase_date else None,
            "notes": position.notes,
            "created_at": position.created_at.isoformat() if position.created_at else None,
            "updated_at": position.updated_at.isoformat() if position.updated_at else None,
        }


__all__ = ["PortfolioRepository"]
