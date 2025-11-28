"""
Stock screening models for Maverick strategies.

Contains MaverickStocks, MaverickBearStocks, and SupplyDemandBreakoutStocks.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
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


class MaverickStocks(Base, TimestampMixin):
    """Maverick stocks screening results - self-contained model."""

    __tablename__ = "mcp_maverick_stocks"
    __table_args__ = (
        Index("mcp_maverick_stocks_combined_score_idx", "combined_score"),
        Index("mcp_maverick_stocks_momentum_score_idx", "momentum_score"),
        Index("mcp_maverick_stocks_date_analyzed_idx", "date_analyzed"),
        Index("mcp_maverick_stocks_stock_date_idx", "stock_id", "date_analyzed"),
    )

    id = Column(_get_primary_key_type(), primary_key=True, autoincrement=True)
    stock_id = Column(
        Uuid,
        ForeignKey("mcp_stocks.stock_id"),
        nullable=False,
        index=True,
    )
    date_analyzed = Column(
        Date, nullable=False, default=lambda: datetime.now(UTC).date()
    )

    # OHLCV Data
    open_price = Column(Numeric(12, 4), default=0)
    high_price = Column(Numeric(12, 4), default=0)
    low_price = Column(Numeric(12, 4), default=0)
    close_price = Column(Numeric(12, 4), default=0)
    volume = Column(BigInteger, default=0)

    # Technical Indicators
    ema_21 = Column(Numeric(12, 4), default=0)
    sma_50 = Column(Numeric(12, 4), default=0)
    sma_150 = Column(Numeric(12, 4), default=0)
    sma_200 = Column(Numeric(12, 4), default=0)
    momentum_score = Column(Numeric(5, 2), default=0)
    avg_vol_30d = Column(Numeric(15, 2), default=0)
    adr_pct = Column(Numeric(5, 2), default=0)
    atr = Column(Numeric(12, 4), default=0)

    # Pattern Analysis
    pattern_type = Column(String(50))
    squeeze_status = Column(String(50))
    consolidation_status = Column(String(50))
    entry_signal = Column(String(50))

    # Scoring
    compression_score = Column(Integer, default=0)
    pattern_detected = Column(Integer, default=0)
    combined_score = Column(Integer, default=0)

    # Relationships
    stock: Mapped["Stock"] = relationship("Stock", back_populates="maverick_stocks")

    def __repr__(self):
        return f"<MaverickStock(stock_id={self.stock_id}, close={self.close_price}, score={self.combined_score})>"

    @classmethod
    def get_top_stocks(
        cls, session: Session, limit: int = 20
    ) -> Sequence[MaverickStocks]:
        """Get top maverick stocks by combined score."""
        from maverick_data.models.stock import Stock

        return (
            session.query(cls)
            .join(Stock)
            .order_by(cls.combined_score.desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def get_latest_analysis(
        cls, session: Session, days_back: int = 1
    ) -> Sequence[MaverickStocks]:
        """Get latest maverick analysis within specified days."""
        from maverick_data.models.stock import Stock

        cutoff_date = datetime.now(UTC).date() - timedelta(days=days_back)
        return (
            session.query(cls)
            .join(Stock)
            .filter(cls.date_analyzed >= cutoff_date)
            .order_by(cls.combined_score.desc())
            .all()
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "stock_id": str(self.stock_id),
            "ticker": self.stock.ticker_symbol if self.stock else None,
            "date_analyzed": (
                self.date_analyzed.isoformat() if self.date_analyzed else None
            ),
            "close": float(self.close_price) if self.close_price else 0,
            "volume": self.volume,
            "momentum_score": float(self.momentum_score) if self.momentum_score else 0,
            "adr_pct": float(self.adr_pct) if self.adr_pct else 0,
            "pattern": self.pattern_type,
            "squeeze": self.squeeze_status,
            "consolidation": self.consolidation_status,
            "entry": self.entry_signal,
            "combined_score": self.combined_score,
            "compression_score": self.compression_score,
            "pattern_detected": self.pattern_detected,
            "ema_21": float(self.ema_21) if self.ema_21 else 0,
            "sma_50": float(self.sma_50) if self.sma_50 else 0,
            "sma_150": float(self.sma_150) if self.sma_150 else 0,
            "sma_200": float(self.sma_200) if self.sma_200 else 0,
            "atr": float(self.atr) if self.atr else 0,
            "avg_vol_30d": float(self.avg_vol_30d) if self.avg_vol_30d else 0,
        }


class MaverickBearStocks(Base, TimestampMixin):
    """Maverick bear stocks screening results - self-contained model."""

    __tablename__ = "mcp_maverick_bear_stocks"
    __table_args__ = (
        Index("mcp_maverick_bear_stocks_score_idx", "score"),
        Index("mcp_maverick_bear_stocks_momentum_score_idx", "momentum_score"),
        Index("mcp_maverick_bear_stocks_date_analyzed_idx", "date_analyzed"),
        Index("mcp_maverick_bear_stocks_stock_date_idx", "stock_id", "date_analyzed"),
    )

    id = Column(_get_primary_key_type(), primary_key=True, autoincrement=True)
    stock_id = Column(
        Uuid,
        ForeignKey("mcp_stocks.stock_id"),
        nullable=False,
        index=True,
    )
    date_analyzed = Column(
        Date, nullable=False, default=lambda: datetime.now(UTC).date()
    )

    # OHLCV Data
    open_price = Column(Numeric(12, 4), default=0)
    high_price = Column(Numeric(12, 4), default=0)
    low_price = Column(Numeric(12, 4), default=0)
    close_price = Column(Numeric(12, 4), default=0)
    volume = Column(BigInteger, default=0)

    # Technical Indicators
    momentum_score = Column(Numeric(5, 2), default=0)
    ema_21 = Column(Numeric(12, 4), default=0)
    sma_50 = Column(Numeric(12, 4), default=0)
    sma_200 = Column(Numeric(12, 4), default=0)
    rsi_14 = Column(Numeric(5, 2), default=0)

    # MACD Indicators
    macd = Column(Numeric(12, 6), default=0)
    macd_signal = Column(Numeric(12, 6), default=0)
    macd_histogram = Column(Numeric(12, 6), default=0)

    # Additional Bear Market Indicators
    dist_days_20 = Column(Integer, default=0)
    adr_pct = Column(Numeric(5, 2), default=0)
    atr_contraction = Column(Boolean, default=False)
    atr = Column(Numeric(12, 4), default=0)
    avg_vol_30d = Column(Numeric(15, 2), default=0)
    big_down_vol = Column(Boolean, default=False)

    # Pattern Analysis
    squeeze_status = Column(String(50))
    consolidation_status = Column(String(50))

    # Scoring
    score = Column(Integer, default=0)

    # Relationships
    stock: Mapped["Stock"] = relationship("Stock", back_populates="maverick_bear_stocks")

    def __repr__(self):
        return f"<MaverickBearStock(stock_id={self.stock_id}, close={self.close_price}, score={self.score})>"

    @classmethod
    def get_top_stocks(
        cls, session: Session, limit: int = 20
    ) -> Sequence[MaverickBearStocks]:
        """Get top maverick bear stocks by score."""
        from maverick_data.models.stock import Stock

        return (
            session.query(cls)
            .join(Stock)
            .order_by(cls.score.desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def get_latest_analysis(
        cls, session: Session, days_back: int = 1
    ) -> Sequence[MaverickBearStocks]:
        """Get latest bear analysis within specified days."""
        from maverick_data.models.stock import Stock

        cutoff_date = datetime.now(UTC).date() - timedelta(days=days_back)
        return (
            session.query(cls)
            .join(Stock)
            .filter(cls.date_analyzed >= cutoff_date)
            .order_by(cls.score.desc())
            .all()
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "stock_id": str(self.stock_id),
            "ticker": self.stock.ticker_symbol if self.stock else None,
            "date_analyzed": (
                self.date_analyzed.isoformat() if self.date_analyzed else None
            ),
            "close": float(self.close_price) if self.close_price else 0,
            "volume": self.volume,
            "momentum_score": float(self.momentum_score) if self.momentum_score else 0,
            "rsi_14": float(self.rsi_14) if self.rsi_14 else 0,
            "macd": float(self.macd) if self.macd else 0,
            "macd_signal": float(self.macd_signal) if self.macd_signal else 0,
            "macd_histogram": float(self.macd_histogram) if self.macd_histogram else 0,
            "adr_pct": float(self.adr_pct) if self.adr_pct else 0,
            "atr": float(self.atr) if self.atr else 0,
            "atr_contraction": self.atr_contraction,
            "avg_vol_30d": float(self.avg_vol_30d) if self.avg_vol_30d else 0,
            "big_down_vol": self.big_down_vol,
            "score": self.score,
            "squeeze": self.squeeze_status,
            "consolidation": self.consolidation_status,
            "ema_21": float(self.ema_21) if self.ema_21 else 0,
            "sma_50": float(self.sma_50) if self.sma_50 else 0,
            "sma_200": float(self.sma_200) if self.sma_200 else 0,
            "dist_days_20": self.dist_days_20,
        }


class SupplyDemandBreakoutStocks(Base, TimestampMixin):
    """Supply/demand breakout stocks screening results."""

    __tablename__ = "mcp_supply_demand_breakouts"
    __table_args__ = (
        Index("mcp_supply_demand_breakouts_momentum_score_idx", "momentum_score"),
        Index("mcp_supply_demand_breakouts_date_analyzed_idx", "date_analyzed"),
        Index(
            "mcp_supply_demand_breakouts_stock_date_idx", "stock_id", "date_analyzed"
        ),
        Index(
            "mcp_supply_demand_breakouts_ma_filter_idx",
            "close_price",
            "sma_50",
            "sma_150",
            "sma_200",
        ),
    )

    id = Column(_get_primary_key_type(), primary_key=True, autoincrement=True)
    stock_id = Column(
        Uuid,
        ForeignKey("mcp_stocks.stock_id"),
        nullable=False,
        index=True,
    )
    date_analyzed = Column(
        Date, nullable=False, default=lambda: datetime.now(UTC).date()
    )

    # OHLCV Data
    open_price = Column(Numeric(12, 4), default=0)
    high_price = Column(Numeric(12, 4), default=0)
    low_price = Column(Numeric(12, 4), default=0)
    close_price = Column(Numeric(12, 4), default=0)
    volume = Column(BigInteger, default=0)

    # Technical Indicators
    ema_21 = Column(Numeric(12, 4), default=0)
    sma_50 = Column(Numeric(12, 4), default=0)
    sma_150 = Column(Numeric(12, 4), default=0)
    sma_200 = Column(Numeric(12, 4), default=0)
    momentum_score = Column(Numeric(5, 2), default=0)
    avg_volume_30d = Column(Numeric(15, 2), default=0)
    adr_pct = Column(Numeric(5, 2), default=0)
    atr = Column(Numeric(12, 4), default=0)

    # Pattern Analysis
    pattern_type = Column(String(50))
    squeeze_status = Column(String(50))
    consolidation_status = Column(String(50))
    entry_signal = Column(String(50))

    # Supply/Demand Analysis
    accumulation_rating = Column(Numeric(5, 2), default=0)
    distribution_rating = Column(Numeric(5, 2), default=0)
    breakout_strength = Column(Numeric(5, 2), default=0)

    # Relationships
    stock: Mapped["Stock"] = relationship("Stock", back_populates="supply_demand_stocks")

    def __repr__(self):
        return f"<SupplyDemandBreakoutStock(stock_id={self.stock_id}, close={self.close_price}, momentum={self.momentum_score})>"

    @classmethod
    def get_top_stocks(
        cls, session: Session, limit: int = 20
    ) -> Sequence[SupplyDemandBreakoutStocks]:
        """Get top supply/demand breakout stocks by momentum score."""
        from maverick_data.models.stock import Stock

        return (
            session.query(cls)
            .join(Stock)
            .order_by(cls.momentum_score.desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def get_stocks_above_moving_averages(
        cls, session: Session
    ) -> Sequence[SupplyDemandBreakoutStocks]:
        """Get stocks in demand expansion phase - trading above all major moving averages."""
        from maverick_data.models.stock import Stock

        return (
            session.query(cls)
            .join(Stock)
            .filter(
                cls.close_price > cls.sma_50,
                cls.close_price > cls.sma_150,
                cls.close_price > cls.sma_200,
                cls.sma_50 > cls.sma_150,
                cls.sma_150 > cls.sma_200,
            )
            .order_by(cls.momentum_score.desc())
            .all()
        )

    @classmethod
    def get_latest_analysis(
        cls, session: Session, days_back: int = 1
    ) -> Sequence[SupplyDemandBreakoutStocks]:
        """Get latest supply/demand analysis within specified days."""
        from maverick_data.models.stock import Stock

        cutoff_date = datetime.now(UTC).date() - timedelta(days=days_back)
        return (
            session.query(cls)
            .join(Stock)
            .filter(cls.date_analyzed >= cutoff_date)
            .order_by(cls.momentum_score.desc())
            .all()
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "stock_id": str(self.stock_id),
            "ticker": self.stock.ticker_symbol if self.stock else None,
            "date_analyzed": (
                self.date_analyzed.isoformat() if self.date_analyzed else None
            ),
            "close": float(self.close_price) if self.close_price else 0,
            "volume": self.volume,
            "momentum_score": float(self.momentum_score) if self.momentum_score else 0,
            "adr_pct": float(self.adr_pct) if self.adr_pct else 0,
            "pattern": self.pattern_type,
            "squeeze": self.squeeze_status,
            "consolidation": self.consolidation_status,
            "entry": self.entry_signal,
            "ema_21": float(self.ema_21) if self.ema_21 else 0,
            "sma_50": float(self.sma_50) if self.sma_50 else 0,
            "sma_150": float(self.sma_150) if self.sma_150 else 0,
            "sma_200": float(self.sma_200) if self.sma_200 else 0,
            "atr": float(self.atr) if self.atr else 0,
            "avg_volume_30d": float(self.avg_volume_30d) if self.avg_volume_30d else 0,
            "accumulation_rating": (
                float(self.accumulation_rating) if self.accumulation_rating else 0
            ),
            "distribution_rating": (
                float(self.distribution_rating) if self.distribution_rating else 0
            ),
            "breakout_strength": (
                float(self.breakout_strength) if self.breakout_strength else 0
            ),
        }
