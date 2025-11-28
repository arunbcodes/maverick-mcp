"""
Stock Repository Implementation.

Implements IStockRepository interface for stock data persistence operations.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from maverick_data.models import Stock, PriceCache
from maverick_data.session import get_async_db

logger = logging.getLogger(__name__)


class StockRepository:
    """
    Repository for stock-related persistence operations.

    Implements IStockRepository interface to provide CRUD operations
    for stocks and price history with database persistence.

    Features:
    - Async operations for better performance
    - Bulk insert for price data
    - Market-aware queries
    - Intelligent caching
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
        # Create new session via generator
        async for session in get_async_db():
            return session
        raise RuntimeError("Failed to get database session")

    async def get_stock(self, symbol: str) -> dict[str, Any] | None:
        """
        Get stock by symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Stock data dictionary or None if not found
        """
        session = await self._get_session()
        symbol = symbol.upper()

        try:
            result = await session.execute(
                select(Stock).where(Stock.ticker_symbol == symbol)
            )
            stock = result.scalar_one_or_none()

            if stock:
                return stock.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting stock {symbol}: {e}")
            return None

    async def save_stock(self, stock: dict[str, Any]) -> dict[str, Any]:
        """
        Save stock information (create or update).

        Args:
            stock: Stock data dictionary with at least 'ticker_symbol'

        Returns:
            Saved stock data
        """
        session = await self._get_session()
        symbol = stock.get("ticker_symbol", "").upper()

        try:
            # Check if stock exists
            result = await session.execute(
                select(Stock).where(Stock.ticker_symbol == symbol)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing stock
                for key, value in stock.items():
                    if hasattr(existing, key) and key != "stock_id":
                        setattr(existing, key, value)
            else:
                # Create new stock
                existing = Stock(
                    ticker_symbol=symbol,
                    company_name=stock.get("company_name", symbol),
                    market=stock.get("market", "US"),
                    sector=stock.get("sector"),
                    industry=stock.get("industry"),
                    currency=stock.get("currency", "USD"),
                    is_active=stock.get("is_active", True),
                )
                session.add(existing)

            await session.commit()
            await session.refresh(existing)
            return existing.to_dict()

        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving stock {symbol}: {e}")
            raise

    async def get_price_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame | None:
        """
        Get cached price history from database.

        Args:
            symbol: Stock ticker
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data or None if not cached
        """
        session = await self._get_session()
        symbol = symbol.upper()

        try:
            # Get stock to get stock_id
            stock_result = await session.execute(
                select(Stock).where(Stock.ticker_symbol == symbol)
            )
            stock = stock_result.scalar_one_or_none()

            if not stock:
                logger.debug(f"Stock {symbol} not found in database")
                return None

            # Query price cache
            start_dt = pd.to_datetime(start_date).date()
            end_dt = pd.to_datetime(end_date).date()

            result = await session.execute(
                select(PriceCache)
                .where(PriceCache.stock_id == stock.stock_id)
                .where(PriceCache.date >= start_dt)
                .where(PriceCache.date <= end_dt)
                .order_by(PriceCache.date)
            )
            rows = result.scalars().all()

            if not rows:
                logger.debug(f"No cached data for {symbol} from {start_date} to {end_date}")
                return None

            # Convert to DataFrame
            data = []
            for row in rows:
                data.append({
                    "Date": pd.Timestamp(row.date),
                    "Open": float(row.open) if row.open else None,
                    "High": float(row.high) if row.high else None,
                    "Low": float(row.low) if row.low else None,
                    "Close": float(row.close) if row.close else None,
                    "Volume": int(row.volume) if row.volume else 0,
                })

            df = pd.DataFrame(data)
            df.set_index("Date", inplace=True)
            df.index = df.index.tz_localize(None)

            logger.debug(f"Retrieved {len(df)} cached records for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error getting price history for {symbol}: {e}")
            return None

    async def save_price_history(
        self,
        symbol: str,
        data: pd.DataFrame,
    ) -> bool:
        """
        Save price history to database.

        Args:
            symbol: Stock ticker
            data: DataFrame with OHLCV data

        Returns:
            True if saved successfully
        """
        if data.empty:
            logger.debug(f"Skipping empty DataFrame for {symbol}")
            return True

        session = await self._get_session()
        symbol = symbol.upper()

        try:
            # Ensure stock exists
            stock_result = await session.execute(
                select(Stock).where(Stock.ticker_symbol == symbol)
            )
            stock = stock_result.scalar_one_or_none()

            if not stock:
                # Create stock record
                stock = Stock(ticker_symbol=symbol)
                session.add(stock)
                await session.flush()

            # Prepare data for bulk insert
            records = []
            for idx, row in data.iterrows():
                date_val = pd.Timestamp(idx).date() if not isinstance(idx, datetime) else idx.date()
                records.append({
                    "stock_id": stock.stock_id,
                    "date": date_val,
                    "open": Decimal(str(row.get("Open", row.get("open", 0)))),
                    "high": Decimal(str(row.get("High", row.get("high", 0)))),
                    "low": Decimal(str(row.get("Low", row.get("low", 0)))),
                    "close": Decimal(str(row.get("Close", row.get("close", 0)))),
                    "volume": int(row.get("Volume", row.get("volume", 0))),
                })

            # Bulk insert with ON CONFLICT DO NOTHING
            if records:
                # Use SQLite syntax for now (works with both SQLite and PostgreSQL)
                stmt = sqlite_insert(PriceCache).values(records)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["stock_id", "date"]
                )
                await session.execute(stmt)
                await session.commit()

            logger.info(f"Saved {len(records)} price records for {symbol}")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving price history for {symbol}: {e}")
            return False

    async def get_stocks_by_sector(self, sector: str) -> list[dict[str, Any]]:
        """
        Get all stocks in a sector.

        Args:
            sector: Sector name

        Returns:
            List of stock data dictionaries
        """
        session = await self._get_session()

        try:
            result = await session.execute(
                select(Stock)
                .where(Stock.sector == sector)
                .where(Stock.is_active == True)  # noqa: E712
                .order_by(Stock.ticker_symbol)
            )
            stocks = result.scalars().all()
            return [s.to_dict() for s in stocks]
        except Exception as e:
            logger.error(f"Error getting stocks by sector {sector}: {e}")
            return []

    async def search_stocks(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search stocks by name or symbol.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching stocks
        """
        session = await self._get_session()
        search_pattern = f"%{query.upper()}%"

        try:
            result = await session.execute(
                select(Stock)
                .where(
                    (Stock.ticker_symbol.ilike(search_pattern))
                    | (Stock.company_name.ilike(search_pattern))
                )
                .where(Stock.is_active == True)  # noqa: E712
                .limit(limit)
            )
            stocks = result.scalars().all()
            return [s.to_dict() for s in stocks]
        except Exception as e:
            logger.error(f"Error searching stocks for '{query}': {e}")
            return []

    async def get_all_symbols(self) -> list[str]:
        """
        Get all tracked stock symbols.

        Returns:
            List of stock ticker symbols
        """
        session = await self._get_session()

        try:
            result = await session.execute(
                select(Stock.ticker_symbol)
                .where(Stock.is_active == True)  # noqa: E712
                .order_by(Stock.ticker_symbol)
            )
            return [row[0] for row in result.all()]
        except Exception as e:
            logger.error(f"Error getting all symbols: {e}")
            return []

    async def get_stocks_by_market(self, market: str) -> list[dict[str, Any]]:
        """
        Get all stocks in a market.

        Args:
            market: Market identifier (US, NSE, BSE)

        Returns:
            List of stock data dictionaries
        """
        session = await self._get_session()

        try:
            result = await session.execute(
                select(Stock)
                .where(Stock.market == market.upper())
                .where(Stock.is_active == True)  # noqa: E712
                .order_by(Stock.ticker_symbol)
            )
            stocks = result.scalars().all()
            return [s.to_dict() for s in stocks]
        except Exception as e:
            logger.error(f"Error getting stocks by market {market}: {e}")
            return []

    async def count_stocks(self, market: str | None = None) -> int:
        """
        Count total stocks, optionally by market.

        Args:
            market: Optional market filter

        Returns:
            Count of stocks
        """
        session = await self._get_session()

        try:
            query = select(func.count(Stock.stock_id)).where(
                Stock.is_active == True  # noqa: E712
            )
            if market:
                query = query.where(Stock.market == market.upper())

            result = await session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting stocks: {e}")
            return 0


__all__ = ["StockRepository"]
