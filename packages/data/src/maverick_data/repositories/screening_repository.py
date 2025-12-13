"""
Screening Repository Implementation.

Implements IScreeningRepository interface for screening results persistence.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from maverick_data.models import (
    Stock,
    MaverickStocks,
    MaverickBearStocks,
    SupplyDemandBreakoutStocks,
)
from maverick_data.session import get_async_db

logger = logging.getLogger(__name__)


# Mapping of strategy names to models
STRATEGY_MODELS = {
    "maverick": MaverickStocks,
    "maverick_bullish": MaverickStocks,
    "maverick_bear": MaverickBearStocks,
    "maverick_bearish": MaverickBearStocks,
    "supply_demand": SupplyDemandBreakoutStocks,
    "supply_demand_breakout": SupplyDemandBreakoutStocks,
}


class ScreeningRepository:
    """
    Repository for screening results persistence.

    Implements IScreeningRepository interface to provide storage
    and retrieval of stock screening results.

    Features:
    - Multiple screening strategy support
    - Pre-calculated recommendations storage
    - Batch save for performance
    - Timestamp tracking for freshness
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

    def _get_model_for_strategy(self, strategy: str):
        """Get the appropriate model class for a strategy."""
        normalized = strategy.lower().replace("-", "_")
        model = STRATEGY_MODELS.get(normalized)
        if not model:
            raise ValueError(f"Unknown screening strategy: {strategy}")
        return model

    async def save_screening_result(
        self,
        strategy: str,
        results: list[dict[str, Any]],
    ) -> bool:
        """
        Save screening results.

        Args:
            strategy: Screening strategy name
            results: List of screening results

        Returns:
            True if saved successfully
        """
        if not results:
            logger.debug(f"No results to save for strategy {strategy}")
            return True

        session = await self._get_session()

        try:
            model = self._get_model_for_strategy(strategy)

            # Clear existing results for this strategy
            await session.execute(delete(model))

            # Extract all symbols from results
            symbols = [
                result.get("symbol", result.get("ticker", "")).upper()
                for result in results
            ]
            symbols = [s for s in symbols if s]  # Filter empty

            # Batch fetch all existing stocks in ONE query (fixes N+1)
            existing_stocks_result = await session.execute(
                select(Stock).where(Stock.ticker_symbol.in_(symbols))
            )
            existing_stocks = {
                stock.ticker_symbol: stock
                for stock in existing_stocks_result.scalars().all()
            }

            # Create missing stocks in batch
            missing_symbols = set(symbols) - set(existing_stocks.keys())
            if missing_symbols:
                new_stocks = [Stock(ticker_symbol=s) for s in missing_symbols]
                session.add_all(new_stocks)
                await session.flush()
                # Refresh stock map with newly created stocks
                for stock in new_stocks:
                    existing_stocks[stock.ticker_symbol] = stock

            # Now create screening records using the pre-loaded stock map
            for result in results:
                symbol = result.get("symbol", result.get("ticker", "")).upper()
                if not symbol:
                    continue

                stock = existing_stocks.get(symbol)
                if not stock:
                    logger.warning(f"Stock not found for symbol {symbol}, skipping")
                    continue

                # Create screening record based on model type
                if model == MaverickStocks:
                    record = MaverickStocks(
                        stock_id=stock.stock_id,
                        momentum_score=Decimal(str(result.get("momentum_score", 0))),
                        combined_score=int(result.get("combined_score", result.get("score", 0))),
                        price=Decimal(str(result.get("price", 0))),
                        rsi_14=Decimal(str(result.get("rsi_14", result.get("rsi", 0)))),
                        change_52w=Decimal(str(result.get("change_52w", 0))),
                        change_26w=Decimal(str(result.get("change_26w", 0))),
                        change_13w=Decimal(str(result.get("change_13w", 0))),
                        change_4w=Decimal(str(result.get("change_4w", 0))),
                        volume=int(result.get("volume", 0)),
                        avg_volume=int(result.get("avg_volume", result.get("average_volume", 0))),
                        market_cap=int(result.get("market_cap", 0)),
                        pe_ratio=Decimal(str(result.get("pe_ratio", 0))) if result.get("pe_ratio") else None,
                        sector=result.get("sector"),
                        industry=result.get("industry"),
                        pattern=result.get("pattern"),
                        trend_strength=Decimal(str(result.get("trend_strength", 0))),
                    )
                elif model == MaverickBearStocks:
                    record = MaverickBearStocks(
                        stock_id=stock.stock_id,
                        bear_score=int(result.get("bear_score", result.get("score", 0))),
                        price=Decimal(str(result.get("price", 0))),
                        rsi_14=Decimal(str(result.get("rsi_14", result.get("rsi", 0)))),
                        change_52w=Decimal(str(result.get("change_52w", 0))),
                        change_26w=Decimal(str(result.get("change_26w", 0))),
                        change_13w=Decimal(str(result.get("change_13w", 0))),
                        change_4w=Decimal(str(result.get("change_4w", 0))),
                        volume=int(result.get("volume", 0)),
                        avg_volume=int(result.get("avg_volume", result.get("average_volume", 0))),
                        market_cap=int(result.get("market_cap", 0)),
                        pe_ratio=Decimal(str(result.get("pe_ratio", 0))) if result.get("pe_ratio") else None,
                        sector=result.get("sector"),
                        industry=result.get("industry"),
                        pattern=result.get("pattern"),
                    )
                elif model == SupplyDemandBreakoutStocks:
                    record = SupplyDemandBreakoutStocks(
                        stock_id=stock.stock_id,
                        momentum_score=Decimal(str(result.get("momentum_score", 0))),
                        price=Decimal(str(result.get("price", 0))),
                        sma_20=Decimal(str(result.get("sma_20", 0))),
                        sma_50=Decimal(str(result.get("sma_50", 0))),
                        sma_150=Decimal(str(result.get("sma_150", 0))),
                        sma_200=Decimal(str(result.get("sma_200", 0))),
                        above_sma_20=result.get("above_sma_20", False),
                        above_sma_50=result.get("above_sma_50", False),
                        above_sma_150=result.get("above_sma_150", False),
                        above_sma_200=result.get("above_sma_200", False),
                        ma_alignment=result.get("ma_alignment", False),
                        volume=int(result.get("volume", 0)),
                        avg_volume=int(result.get("avg_volume", result.get("average_volume", 0))),
                        volume_ratio=Decimal(str(result.get("volume_ratio", 0))),
                        breakout_signal=result.get("breakout_signal"),
                        consolidation_days=result.get("consolidation_days"),
                        sector=result.get("sector"),
                        industry=result.get("industry"),
                    )
                else:
                    continue

                session.add(record)

            await session.commit()
            logger.info(f"Saved {len(results)} screening results for strategy {strategy}")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving screening results for {strategy}: {e}")
            return False

    async def get_maverick_stocks(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get cached Maverick bullish picks."""
        return await self.get_screening_results("maverick", limit=limit)

    async def get_maverick_bear_stocks(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get cached Maverick bearish picks."""
        return await self.get_screening_results("maverick_bear", limit=limit)

    async def get_breakout_stocks(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get supply/demand breakout stocks."""
        return await self.get_screening_results("supply_demand", limit=limit)

    async def get_screening_results(
        self,
        strategy: str,
        limit: int = 20,
        min_score: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get screening results.

        Args:
            strategy: Screening strategy name
            limit: Maximum results
            min_score: Optional minimum score filter

        Returns:
            List of screening results
        """
        session = await self._get_session()

        try:
            model = self._get_model_for_strategy(strategy)

            # Build query with optional score filter
            query = select(model, Stock).join(Stock, model.stock_id == Stock.stock_id)

            # Apply score filter if provided
            if min_score is not None:
                if hasattr(model, "combined_score"):
                    query = query.where(model.combined_score >= int(min_score))
                elif hasattr(model, "bear_score"):
                    query = query.where(model.bear_score >= int(min_score))
                elif hasattr(model, "momentum_score"):
                    query = query.where(model.momentum_score >= Decimal(str(min_score)))

            # Add ordering by score
            if hasattr(model, "combined_score"):
                query = query.order_by(model.combined_score.desc())
            elif hasattr(model, "bear_score"):
                query = query.order_by(model.bear_score.desc())
            elif hasattr(model, "momentum_score"):
                query = query.order_by(model.momentum_score.desc())

            query = query.limit(limit)

            result = await session.execute(query)
            rows = result.all()

            # Convert to dictionaries
            results = []
            for screening, stock in rows:
                result_dict = self._screening_to_dict(screening, stock)
                results.append(result_dict)

            return results

        except Exception as e:
            logger.error(f"Error getting screening results for {strategy}: {e}")
            return []

    async def get_latest_screening_timestamp(
        self,
        strategy: str,
    ) -> str | None:
        """
        Get timestamp of latest screening run.

        Args:
            strategy: Screening strategy name

        Returns:
            ISO format timestamp or None
        """
        session = await self._get_session()

        try:
            model = self._get_model_for_strategy(strategy)

            result = await session.execute(
                select(func.max(model.updated_at))
            )
            timestamp = result.scalar()

            if timestamp:
                return timestamp.isoformat()
            return None

        except Exception as e:
            logger.error(f"Error getting screening timestamp for {strategy}: {e}")
            return None

    async def get_all_screening_results(
        self,
        limits: dict[str, int] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Get all screening results in one call.

        Args:
            limits: Optional dict of strategy name to limit

        Returns:
            Dictionary with all screening types and their recommendations
        """
        import asyncio

        default_limit = 20
        limits = limits or {}

        # Fetch all strategies concurrently using asyncio.gather
        maverick, maverick_bear, supply_demand = await asyncio.gather(
            self.get_screening_results(
                "maverick",
                limit=limits.get("maverick", default_limit)
            ),
            self.get_screening_results(
                "maverick_bear",
                limit=limits.get("maverick_bear", default_limit)
            ),
            self.get_screening_results(
                "supply_demand",
                limit=limits.get("supply_demand", default_limit)
            ),
        )

        return {
            "maverick": maverick,
            "maverick_bear": maverick_bear,
            "supply_demand": supply_demand,
        }

    async def count_screening_results(self, strategy: str) -> int:
        """
        Count total screening results for a strategy.

        Args:
            strategy: Screening strategy name

        Returns:
            Count of results
        """
        session = await self._get_session()

        try:
            model = self._get_model_for_strategy(strategy)
            result = await session.execute(select(func.count(model.id)))
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting screening results for {strategy}: {e}")
            return 0

    async def clear_screening_results(self, strategy: str | None = None) -> int:
        """
        Clear screening results.

        Args:
            strategy: Strategy to clear, or None to clear all

        Returns:
            Number of records deleted
        """
        session = await self._get_session()
        total_deleted = 0

        try:
            if strategy:
                model = self._get_model_for_strategy(strategy)
                result = await session.execute(delete(model))
                total_deleted = result.rowcount
            else:
                # Clear all strategies
                for model in [MaverickStocks, MaverickBearStocks, SupplyDemandBreakoutStocks]:
                    result = await session.execute(delete(model))
                    total_deleted += result.rowcount

            await session.commit()
            logger.info(f"Cleared {total_deleted} screening results")
            return total_deleted

        except Exception as e:
            await session.rollback()
            logger.error(f"Error clearing screening results: {e}")
            return 0

    def _screening_to_dict(self, screening, stock: Stock) -> dict[str, Any]:
        """Convert screening model to dictionary."""
        base_dict = {
            "symbol": stock.ticker_symbol,
            "company_name": stock.company_name,
            "sector": stock.sector,
            "industry": stock.industry,
            "market": stock.market,
        }

        if isinstance(screening, MaverickStocks):
            base_dict.update({
                "momentum_score": float(screening.momentum_score) if screening.momentum_score else 0,
                "combined_score": screening.combined_score or 0,
                "score": screening.combined_score or 0,
                "price": float(screening.price) if screening.price else 0,
                "rsi_14": float(screening.rsi_14) if screening.rsi_14 else 0,
                "change_52w": float(screening.change_52w) if screening.change_52w else 0,
                "change_26w": float(screening.change_26w) if screening.change_26w else 0,
                "change_13w": float(screening.change_13w) if screening.change_13w else 0,
                "change_4w": float(screening.change_4w) if screening.change_4w else 0,
                "volume": screening.volume or 0,
                "avg_volume": screening.avg_volume or 0,
                "market_cap": screening.market_cap or 0,
                "pe_ratio": float(screening.pe_ratio) if screening.pe_ratio else None,
                "pattern": screening.pattern,
                "trend_strength": float(screening.trend_strength) if screening.trend_strength else 0,
                "strategy": "maverick",
            })
        elif isinstance(screening, MaverickBearStocks):
            base_dict.update({
                "bear_score": screening.bear_score or 0,
                "score": screening.bear_score or 0,
                "price": float(screening.price) if screening.price else 0,
                "rsi_14": float(screening.rsi_14) if screening.rsi_14 else 0,
                "change_52w": float(screening.change_52w) if screening.change_52w else 0,
                "change_26w": float(screening.change_26w) if screening.change_26w else 0,
                "change_13w": float(screening.change_13w) if screening.change_13w else 0,
                "change_4w": float(screening.change_4w) if screening.change_4w else 0,
                "volume": screening.volume or 0,
                "avg_volume": screening.avg_volume or 0,
                "market_cap": screening.market_cap or 0,
                "pe_ratio": float(screening.pe_ratio) if screening.pe_ratio else None,
                "pattern": screening.pattern,
                "strategy": "maverick_bear",
            })
        elif isinstance(screening, SupplyDemandBreakoutStocks):
            base_dict.update({
                "momentum_score": float(screening.momentum_score) if screening.momentum_score else 0,
                "score": float(screening.momentum_score) if screening.momentum_score else 0,
                "price": float(screening.price) if screening.price else 0,
                "sma_20": float(screening.sma_20) if screening.sma_20 else 0,
                "sma_50": float(screening.sma_50) if screening.sma_50 else 0,
                "sma_150": float(screening.sma_150) if screening.sma_150 else 0,
                "sma_200": float(screening.sma_200) if screening.sma_200 else 0,
                "above_sma_20": screening.above_sma_20,
                "above_sma_50": screening.above_sma_50,
                "above_sma_150": screening.above_sma_150,
                "above_sma_200": screening.above_sma_200,
                "ma_alignment": screening.ma_alignment,
                "volume": screening.volume or 0,
                "avg_volume": screening.avg_volume or 0,
                "volume_ratio": float(screening.volume_ratio) if screening.volume_ratio else 0,
                "breakout_signal": screening.breakout_signal,
                "consolidation_days": screening.consolidation_days,
                "strategy": "supply_demand",
            })

        return base_dict


__all__ = ["ScreeningRepository"]
