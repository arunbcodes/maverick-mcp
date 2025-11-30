"""
Cryptocurrency model for storing basic crypto information.

Mirrors the Stock model structure for consistency but handles
crypto-specific attributes like market cap rank, circulating supply, etc.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Column, Float, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, relationship

from maverick_crypto.models.base import CryptoBase, TimestampMixin

if TYPE_CHECKING:
    from maverick_crypto.models.price_cache import CryptoPriceCache


class Crypto(CryptoBase, TimestampMixin):
    """
    Cryptocurrency model for storing basic crypto information.
    
    Supports multiple data sources (yfinance, CoinGecko, etc.)
    and maintains consistency with the Stock model interface.
    
    Attributes:
        crypto_id: Unique identifier (UUID)
        symbol: Trading symbol (e.g., "BTC", "ETH")
        name: Full name (e.g., "Bitcoin", "Ethereum")
        coingecko_id: CoinGecko API identifier (e.g., "bitcoin")
        yfinance_symbol: Yahoo Finance symbol (e.g., "BTC-USD")
        
    Market Data:
        market_cap_rank: Rank by market capitalization
        market_cap: Total market capitalization in USD
        current_price: Latest price in USD
        circulating_supply: Coins currently in circulation
        total_supply: Maximum possible supply
        
    Metadata:
        category: Asset category (e.g., "cryptocurrency", "stablecoin", "defi")
        platform: Blockchain platform (e.g., "ethereum", "solana")
        is_active: Whether actively tracked
    """
    
    __tablename__ = "mcp_cryptos"
    __table_args__ = (
        Index("idx_crypto_symbol", "symbol"),
        Index("idx_crypto_market_cap_rank", "market_cap_rank"),
        Index("idx_crypto_category", "category"),
        Index("idx_crypto_active", "is_active"),
    )
    
    # Primary key
    crypto_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    
    # Identifiers
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    coingecko_id = Column(String(100), unique=True, index=True)
    yfinance_symbol = Column(String(20), index=True)  # e.g., "BTC-USD"
    
    # Description
    description = Column(Text)
    
    # Market data
    market_cap_rank = Column(BigInteger)
    market_cap = Column(BigInteger)
    current_price = Column(Float)
    price_change_24h = Column(Float)
    price_change_percentage_24h = Column(Float)
    
    # Supply data
    circulating_supply = Column(BigInteger)
    total_supply = Column(BigInteger)
    max_supply = Column(BigInteger)
    
    # Volume
    total_volume = Column(BigInteger)
    
    # ATH/ATL data
    ath = Column(Float)  # All-time high
    ath_date = Column(String(50))
    atl = Column(Float)  # All-time low
    atl_date = Column(String(50))
    
    # Metadata
    category = Column(String(50), default="cryptocurrency")
    platform = Column(String(50))  # Blockchain platform
    contract_address = Column(String(100))  # For tokens
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_stablecoin = Column(Boolean, default=False)
    
    # Relationships
    price_caches: Mapped[list["CryptoPriceCache"]] = relationship(
        "CryptoPriceCache",
        back_populates="crypto",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Crypto(symbol='{self.symbol}', name='{self.name}', rank={self.market_cap_rank})>"
    
    @property
    def trading_symbol(self) -> str:
        """Get the yfinance trading symbol."""
        return self.yfinance_symbol or f"{self.symbol}-USD"
    
    @classmethod
    def from_coingecko(cls, data: dict) -> "Crypto":
        """
        Create Crypto instance from CoinGecko API response.
        
        Args:
            data: CoinGecko coin market data
            
        Returns:
            Crypto instance
        """
        return cls(
            symbol=data.get("symbol", "").upper(),
            name=data.get("name", ""),
            coingecko_id=data.get("id"),
            yfinance_symbol=f"{data.get('symbol', '').upper()}-USD",
            market_cap_rank=data.get("market_cap_rank"),
            market_cap=data.get("market_cap"),
            current_price=data.get("current_price"),
            price_change_24h=data.get("price_change_24h"),
            price_change_percentage_24h=data.get("price_change_percentage_24h"),
            circulating_supply=data.get("circulating_supply"),
            total_supply=data.get("total_supply"),
            max_supply=data.get("max_supply"),
            total_volume=data.get("total_volume"),
            ath=data.get("ath"),
            ath_date=data.get("ath_date"),
            atl=data.get("atl"),
            atl_date=data.get("atl_date"),
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "crypto_id": str(self.crypto_id),
            "symbol": self.symbol,
            "name": self.name,
            "coingecko_id": self.coingecko_id,
            "yfinance_symbol": self.yfinance_symbol,
            "market_cap_rank": self.market_cap_rank,
            "market_cap": self.market_cap,
            "current_price": self.current_price,
            "price_change_24h": self.price_change_24h,
            "price_change_percentage_24h": self.price_change_percentage_24h,
            "circulating_supply": self.circulating_supply,
            "total_supply": self.total_supply,
            "max_supply": self.max_supply,
            "total_volume": self.total_volume,
            "category": self.category,
            "is_active": self.is_active,
            "is_stablecoin": self.is_stablecoin,
        }

