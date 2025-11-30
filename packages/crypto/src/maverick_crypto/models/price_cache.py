"""
Cryptocurrency price cache model for storing historical OHLCV data.

Mirrors the PriceCache model structure for consistency with stock data.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    Float,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, relationship

from maverick_crypto.models.base import CryptoBase, TimestampMixin

if TYPE_CHECKING:
    from maverick_crypto.models.crypto import Crypto


class CryptoPriceCache(CryptoBase, TimestampMixin):
    """
    Cryptocurrency price cache for storing historical OHLCV data.
    
    Stores daily price data fetched from various providers.
    Uses composite unique constraint on (crypto_id, price_date) to
    prevent duplicate entries.
    
    Attributes:
        cache_id: Unique identifier (UUID)
        crypto_id: Foreign key to Crypto
        symbol: Trading symbol for quick lookups
        price_date: Date of the price data
        
    OHLCV Data:
        open_price: Opening price
        high_price: Highest price
        low_price: Lowest price
        close_price: Closing price
        volume: Trading volume
        
    Metadata:
        source: Data provider (e.g., "yfinance", "coingecko")
    """
    
    __tablename__ = "mcp_crypto_price_cache"
    __table_args__ = (
        UniqueConstraint("crypto_id", "price_date", name="uq_crypto_price_date"),
        Index("idx_crypto_price_symbol_date", "symbol", "price_date"),
        Index("idx_crypto_price_date", "price_date"),
    )
    
    # Primary key
    cache_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    crypto_id = Column(
        Uuid,
        ForeignKey("mcp_cryptos.crypto_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Symbol for quick lookups without joins
    symbol = Column(String(20), nullable=False, index=True)
    
    # Date
    price_date = Column(Date, nullable=False, index=True)
    
    # OHLCV data
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    
    # Additional metrics
    market_cap = Column(BigInteger)
    
    # Data source
    source = Column(String(50), default="yfinance")
    
    # Relationships
    crypto: Mapped["Crypto"] = relationship(
        "Crypto",
        back_populates="price_caches",
    )
    
    def __repr__(self) -> str:
        return f"<CryptoPriceCache(symbol='{self.symbol}', date={self.price_date}, close={self.close_price})>"
    
    @classmethod
    def from_dataframe_row(
        cls,
        crypto_id: uuid.UUID,
        symbol: str,
        row_date: date,
        row: dict,
        source: str = "yfinance",
    ) -> "CryptoPriceCache":
        """
        Create CryptoPriceCache from a DataFrame row.
        
        Args:
            crypto_id: UUID of the parent Crypto
            symbol: Trading symbol
            row_date: Date of the price data
            row: Dictionary with OHLCV data
            source: Data provider name
            
        Returns:
            CryptoPriceCache instance
        """
        return cls(
            crypto_id=crypto_id,
            symbol=symbol,
            price_date=row_date,
            open_price=row.get("Open", row.get("open", 0)),
            high_price=row.get("High", row.get("high", 0)),
            low_price=row.get("Low", row.get("low", 0)),
            close_price=row.get("Close", row.get("close", 0)),
            volume=int(row.get("Volume", row.get("volume", 0))),
            market_cap=row.get("market_cap"),
            source=source,
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "cache_id": str(self.cache_id),
            "crypto_id": str(self.crypto_id),
            "symbol": self.symbol,
            "date": self.price_date.isoformat(),
            "open": self.open_price,
            "high": self.high_price,
            "low": self.low_price,
            "close": self.close_price,
            "volume": self.volume,
            "market_cap": self.market_cap,
            "source": self.source,
        }

