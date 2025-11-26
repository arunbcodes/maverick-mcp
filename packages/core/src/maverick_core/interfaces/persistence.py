"""
Persistence interfaces.

This module defines abstract interfaces for data persistence operations.
These interfaces follow the Repository pattern from Domain-Driven Design.
"""

from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

import pandas as pd

T = TypeVar("T")
ID = TypeVar("ID")


@runtime_checkable
class IRepository(Protocol[T, ID]):
    """
    Generic repository interface.

    This interface defines basic CRUD operations for any entity type.

    Type Parameters:
        T: Entity type
        ID: Identifier type (usually str or int)
    """

    async def get_by_id(self, id: ID) -> T | None:
        """
        Get entity by ID.

        Args:
            id: Entity identifier

        Returns:
            Entity if found, None otherwise
        """
        ...

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[T]:
        """
        Get all entities with pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entities
        """
        ...

    async def save(self, entity: T) -> T:
        """
        Save entity (create or update).

        Args:
            entity: Entity to save

        Returns:
            Saved entity (with ID if newly created)
        """
        ...

    async def delete(self, id: ID) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity identifier

        Returns:
            True if entity was deleted, False if not found
        """
        ...

    async def exists(self, id: ID) -> bool:
        """
        Check if entity exists.

        Args:
            id: Entity identifier

        Returns:
            True if entity exists
        """
        ...


@runtime_checkable
class IStockRepository(Protocol):
    """
    Repository for stock-related persistence.

    This interface defines operations specific to stock data storage,
    including price history and stock information.

    Implemented by: maverick-data (StockRepository)
    """

    async def get_stock(self, symbol: str) -> dict[str, Any] | None:
        """
        Get stock by symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Stock data dictionary or None if not found
        """
        ...

    async def save_stock(self, stock: dict[str, Any]) -> dict[str, Any]:
        """
        Save stock information.

        Args:
            stock: Stock data dictionary

        Returns:
            Saved stock data
        """
        ...

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
        ...

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
        ...

    async def get_stocks_by_sector(self, sector: str) -> list[dict[str, Any]]:
        """
        Get all stocks in a sector.

        Args:
            sector: Sector name

        Returns:
            List of stock data dictionaries
        """
        ...

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
        ...

    async def get_all_symbols(self) -> list[str]:
        """
        Get all tracked stock symbols.

        Returns:
            List of stock ticker symbols
        """
        ...


@runtime_checkable
class IPortfolioRepository(Protocol):
    """
    Repository for portfolio persistence.

    This interface defines operations for managing user portfolios
    and their positions.

    Implemented by: maverick-data (PortfolioRepository)
    """

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
        ...

    async def save_portfolio(self, portfolio: dict[str, Any]) -> dict[str, Any]:
        """
        Save portfolio.

        Args:
            portfolio: Portfolio data dictionary

        Returns:
            Saved portfolio data
        """
        ...

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
        ...

    async def save_position(self, position: dict[str, Any]) -> dict[str, Any]:
        """
        Save position.

        Args:
            position: Position data dictionary

        Returns:
            Saved position data
        """
        ...

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
        ...

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
        ...

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
        ...


@runtime_checkable
class IScreeningRepository(Protocol):
    """
    Repository for screening results persistence.

    This interface defines operations for storing and retrieving
    stock screening results.

    Implemented by: maverick-data (ScreeningRepository)
    """

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
        ...

    async def get_screening_results(
        self,
        strategy: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Get screening results.

        Args:
            strategy: Screening strategy name
            limit: Maximum results

        Returns:
            List of screening results
        """
        ...

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
        ...
