"""
Portfolio models for tracking user investment holdings.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, relationship

from maverick_data.models.base import Base, TimestampMixin

# Forward reference for type hints
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from maverick_data.models.user import User


class UserPortfolio(TimestampMixin, Base):
    """
    User portfolio for tracking investment holdings.

    Supports both legacy mode (user_id as string) and new authenticated mode
    (owner_id as foreign key to User).

    Attributes:
        id: Unique portfolio identifier (UUID)
        user_id: Legacy user identifier (for backward compatibility)
        owner_id: Foreign key to User (for authenticated users)
        name: Portfolio display name
        positions: Relationship to PortfolioPosition records
        user: Relationship to User (when owner_id is set)
    """

    __tablename__ = "mcp_portfolios"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    # Legacy field for backward compatibility with MCP server
    user_id = Column(String(100), nullable=False, default="default", index=True)
    # New field for authenticated users (nullable for migration)
    owner_id = Column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = Column(String(200), nullable=False, default="My Portfolio")

    # Relationships
    positions: Mapped[list["PortfolioPosition"]] = relationship(
        "PortfolioPosition",
        back_populates="portfolio",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="portfolios",
        foreign_keys=[owner_id],
    )

    # Indexes for queries
    __table_args__ = (
        Index("idx_portfolio_user", "user_id"),
        Index("idx_portfolio_owner", "owner_id"),
        UniqueConstraint("user_id", "name", name="uq_user_portfolio_name"),
    )

    def __repr__(self):
        return f"<UserPortfolio(id={self.id}, name='{self.name}', positions={len(self.positions)})>"


class PortfolioPosition(TimestampMixin, Base):
    """
    Individual position within a portfolio with cost basis tracking.

    Stores position details with high-precision Decimal types for financial accuracy.
    Uses average cost basis method for educational simplicity.

    Attributes:
        id: Unique position identifier (UUID)
        portfolio_id: Foreign key to parent portfolio
        ticker: Stock ticker symbol (e.g., "AAPL")
        shares: Number of shares owned (supports fractional shares)
        average_cost_basis: Average cost per share
        total_cost: Total capital invested (shares × average_cost_basis)
        purchase_date: Earliest purchase date for this position
        notes: Optional user notes about the position
    """

    __tablename__ = "mcp_portfolio_positions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(
        Uuid, ForeignKey("mcp_portfolios.id", ondelete="CASCADE"), nullable=False
    )

    # Position details with financial precision
    ticker = Column(String(20), nullable=False, index=True)
    shares = Column(Numeric(20, 8), nullable=False)
    average_cost_basis = Column(Numeric(12, 4), nullable=False)
    total_cost = Column(Numeric(20, 4), nullable=False)
    purchase_date = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    portfolio: Mapped["UserPortfolio"] = relationship("UserPortfolio", back_populates="positions")

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_position_portfolio", "portfolio_id"),
        Index("idx_position_ticker", "ticker"),
        Index("idx_position_portfolio_ticker", "portfolio_id", "ticker"),
        UniqueConstraint("portfolio_id", "ticker", name="uq_portfolio_position_ticker"),
    )

    def __repr__(self):
        return f"<PortfolioPosition(ticker='{self.ticker}', shares={self.shares}, cost_basis={self.average_cost_basis})>"
