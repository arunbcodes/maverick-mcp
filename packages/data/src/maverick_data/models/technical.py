"""
Technical cache model for storing calculated technical indicators.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pandas as pd
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, Session, relationship

from maverick_data.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from maverick_data.models.stock import Stock


def _get_primary_key_type():
    """Get the appropriate primary key type based on database backend."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///maverick_mcp.db")
    if "sqlite" in database_url:
        return Integer
    else:
        return BigInteger


class TechnicalCache(Base, TimestampMixin):
    """Cache for calculated technical indicators."""

    __tablename__ = "mcp_technical_cache"
    __table_args__ = (
        UniqueConstraint(
            "stock_id",
            "date",
            "indicator_type",
            name="mcp_technical_cache_stock_date_indicator_unique",
        ),
        Index("mcp_technical_cache_stock_date_idx", "stock_id", "date"),
        Index("mcp_technical_cache_indicator_idx", "indicator_type"),
        Index("mcp_technical_cache_date_idx", "date"),
    )

    id = Column(_get_primary_key_type(), primary_key=True, autoincrement=True)
    stock_id = Column(Uuid, ForeignKey("mcp_stocks.stock_id"), nullable=False)
    date = Column(Date, nullable=False)
    indicator_type = Column(String(50), nullable=False)

    # Flexible indicator values
    value = Column(Numeric(20, 8))
    value_2 = Column(Numeric(20, 8))
    value_3 = Column(Numeric(20, 8))

    # Text values for complex indicators
    meta_data = Column(Text)

    # Calculation parameters
    period = Column(Integer)
    parameters = Column(Text)

    # Relationships
    stock: Mapped["Stock"] = relationship("Stock", back_populates="technical_cache")

    def __repr__(self):
        return (
            f"<TechnicalCache(stock_id={self.stock_id}, date={self.date}, "
            f"indicator={self.indicator_type}, value={self.value})>"
        )

    @classmethod
    def get_indicator(
        cls,
        session: Session,
        ticker_symbol: str,
        indicator_type: str,
        start_date: str,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        Get technical indicator data for a symbol and date range.

        Args:
            session: Database session
            ticker_symbol: Stock ticker symbol
            indicator_type: Type of indicator (e.g., 'SMA_20', 'RSI_14')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (default: today)

        Returns:
            DataFrame with indicator data indexed by date
        """
        from maverick_data.models.stock import Stock

        if not end_date:
            end_date = datetime.now(UTC).strftime("%Y-%m-%d")

        query = (
            session.query(
                cls.date,
                cls.value,
                cls.value_2,
                cls.value_3,
                cls.meta_data,
                cls.parameters,
            )
            .join(Stock)
            .filter(
                Stock.ticker_symbol == ticker_symbol.upper(),
                cls.indicator_type == indicator_type,
                cls.date >= pd.to_datetime(start_date).date(),
                cls.date <= pd.to_datetime(end_date).date(),
            )
            .order_by(cls.date)
        )

        df = pd.DataFrame(query.all())

        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)

            for col in ["value", "value_2", "value_3"]:
                if col in df.columns:
                    df[col] = df[col].astype(float)

            df["symbol"] = ticker_symbol.upper()
            df["indicator_type"] = indicator_type

        return df

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "stock_id": str(self.stock_id),
            "date": self.date.isoformat() if self.date else None,
            "indicator_type": self.indicator_type,
            "value": float(self.value) if self.value else None,
            "value_2": float(self.value_2) if self.value_2 else None,
            "value_3": float(self.value_3) if self.value_3 else None,
            "period": self.period,
            "meta_data": self.meta_data,
            "parameters": self.parameters,
        }
