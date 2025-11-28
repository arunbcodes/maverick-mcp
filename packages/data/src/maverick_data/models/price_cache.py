"""
Price cache model for historical stock price data.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pandas as pd
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    ForeignKey,
    Index,
    Numeric,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, Session, relationship

from maverick_data.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from maverick_data.models.stock import Stock


class PriceCache(Base, TimestampMixin):
    """Cache for historical stock price data."""

    __tablename__ = "mcp_price_cache"
    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="mcp_price_cache_stock_date_unique"),
        Index("mcp_price_cache_stock_id_date_idx", "stock_id", "date"),
        Index("mcp_price_cache_ticker_date_idx", "stock_id", "date"),
    )

    price_cache_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    stock_id = Column(Uuid, ForeignKey("mcp_stocks.stock_id"), nullable=False)
    date = Column(Date, nullable=False)
    open_price = Column(Numeric(12, 4))
    high_price = Column(Numeric(12, 4))
    low_price = Column(Numeric(12, 4))
    close_price = Column(Numeric(12, 4))
    volume = Column(BigInteger)

    # Relationships
    stock: Mapped["Stock"] = relationship("Stock", back_populates="price_caches", lazy="joined")

    def __repr__(self):
        return f"<PriceCache(stock_id={self.stock_id}, date={self.date}, close={self.close_price})>"

    @classmethod
    def get_price_data(
        cls,
        session: Session,
        ticker_symbol: str,
        start_date: str,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        Return a pandas DataFrame of price data for the specified symbol and date range.

        Args:
            session: Database session
            ticker_symbol: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (default: today)

        Returns:
            DataFrame with OHLCV data indexed by date
        """
        from maverick_data.models.stock import Stock

        if not end_date:
            end_date = datetime.now(UTC).strftime("%Y-%m-%d")

        query = (
            session.query(
                cls.date,
                cls.open_price.label("open"),
                cls.high_price.label("high"),
                cls.low_price.label("low"),
                cls.close_price.label("close"),
                cls.volume,
            )
            .join(Stock)
            .filter(
                Stock.ticker_symbol == ticker_symbol.upper(),
                cls.date >= pd.to_datetime(start_date).date(),
                cls.date <= pd.to_datetime(end_date).date(),
            )
            .order_by(cls.date)
        )

        df = pd.DataFrame(query.all())

        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)

            for col in ["open", "high", "low", "close"]:
                df[col] = df[col].astype(float)

            df["volume"] = df["volume"].astype(int)
            df["symbol"] = ticker_symbol.upper()

        return df
