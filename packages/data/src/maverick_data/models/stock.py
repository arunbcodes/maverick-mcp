"""
Stock model for storing basic stock information.

Supports multi-market functionality for US, Indian NSE, and Indian BSE stocks.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Column, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, Session, relationship

from maverick_data.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from maverick_data.models.price_cache import PriceCache
    from maverick_data.models.screening import (
        MaverickBearStocks,
        MaverickStocks,
        SupplyDemandBreakoutStocks,
    )
    from maverick_data.models.technical import TechnicalCache


class Stock(Base, TimestampMixin):
    """
    Stock model for storing basic stock information.

    Supports multi-market functionality for US, Indian NSE, and Indian BSE stocks.
    Market is automatically determined from ticker symbol suffix (e.g., .NS for NSE, .BO for BSE).
    """

    __tablename__ = "mcp_stocks"
    __table_args__ = (
        Index("idx_stock_market_country", "market", "country"),
        Index("idx_stock_market_sector", "market", "sector"),
        Index("idx_stock_country_active", "country", "is_active"),
    )

    stock_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    ticker_symbol = Column(String(20), unique=True, nullable=False, index=True)
    company_name = Column(String(255))
    description = Column(Text)

    # Multi-market support fields
    market = Column(String(10), nullable=False, default="US", index=True)
    exchange = Column(String(50))
    country = Column(String(2), default="US")
    currency = Column(String(3), default="USD")

    # Stock classification
    sector = Column(String(100))
    industry = Column(String(100))
    isin = Column(String(12))

    # Additional stock metadata
    market_cap = Column(BigInteger)
    shares_outstanding = Column(BigInteger)
    is_etf = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    price_caches: Mapped[list["PriceCache"]] = relationship(
        "PriceCache",
        back_populates="stock",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    maverick_stocks: Mapped[list["MaverickStocks"]] = relationship(
        "MaverickStocks", back_populates="stock", cascade="all, delete-orphan"
    )
    maverick_bear_stocks: Mapped[list["MaverickBearStocks"]] = relationship(
        "MaverickBearStocks", back_populates="stock", cascade="all, delete-orphan"
    )
    supply_demand_stocks: Mapped[list["SupplyDemandBreakoutStocks"]] = relationship(
        "SupplyDemandBreakoutStocks",
        back_populates="stock",
        cascade="all, delete-orphan",
    )
    technical_cache: Mapped[list["TechnicalCache"]] = relationship(
        "TechnicalCache", back_populates="stock", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Stock(ticker={self.ticker_symbol}, name={self.company_name}, market={self.market})>"

    def to_dict(self) -> dict:
        """Convert stock model to dictionary for JSON serialization."""
        return {
            "stock_id": str(self.stock_id) if self.stock_id else None,
            "ticker_symbol": self.ticker_symbol,
            "company_name": self.company_name,
            "description": self.description,
            "market": self.market,
            "exchange": self.exchange,
            "country": self.country,
            "currency": self.currency,
            "sector": self.sector,
            "industry": self.industry,
            "isin": self.isin,
            "market_cap": self.market_cap,
            "shares_outstanding": self.shares_outstanding,
            "is_etf": self.is_etf,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_or_create(
        cls,
        session: Session,
        ticker_symbol: str,
        **kwargs,
    ) -> Stock:
        """
        Get existing stock or create new one with automatic market detection.

        Market is automatically determined from ticker symbol suffix:
        - No suffix or US tickers: US market
        - .NS suffix: Indian NSE market
        - .BO suffix: Indian BSE market

        Args:
            session: Database session
            ticker_symbol: Stock ticker symbol (e.g., "AAPL", "RELIANCE.NS", "SENSEX.BO")
            **kwargs: Additional stock attributes

        Returns:
            Stock instance
        """
        ticker_upper = ticker_symbol.upper()
        stock = session.query(cls).filter_by(ticker_symbol=ticker_upper).first()

        if not stock:
            # Auto-detect market if not provided
            if "market" not in kwargs:
                market = _detect_market_from_symbol(ticker_upper)
                kwargs["market"] = market

            # Auto-set country and currency if not provided
            if "country" not in kwargs:
                if kwargs.get("market") in ["NSE", "BSE"]:
                    kwargs["country"] = "IN"
                else:
                    kwargs["country"] = "US"

            if "currency" not in kwargs:
                if kwargs.get("market") in ["NSE", "BSE"]:
                    kwargs["currency"] = "INR"
                else:
                    kwargs["currency"] = "USD"

            stock = cls(ticker_symbol=ticker_upper, **kwargs)
            session.add(stock)
            session.commit()
        return stock


def _detect_market_from_symbol(ticker: str) -> str:
    """Detect market from ticker symbol suffix."""
    ticker_upper = ticker.upper()
    if ticker_upper.endswith(".NS"):
        return "NSE"
    elif ticker_upper.endswith(".BO"):
        return "BSE"
    return "US"
