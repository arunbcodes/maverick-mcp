"""
Pagination Utilities for Database Queries.

Provides standardized pagination for SQLAlchemy queries
with consistent response format and metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    """
    Container for paginated query results.

    Attributes:
        items: List of items for current page
        total: Total count of all items
        page: Current page number (1-indexed)
        page_size: Number of items per page
        total_pages: Total number of pages
        has_next: Whether there's a next page
        has_prev: Whether there's a previous page
    """

    items: Sequence[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        """Calculate total pages."""
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "items": list(self.items),
            "pagination": {
                "total": self.total,
                "page": self.page,
                "page_size": self.page_size,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_prev": self.has_prev,
            },
        }


def paginate_query(
    query: Select,
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100,
) -> Select:
    """
    Apply pagination to a SQLAlchemy select query.

    Args:
        query: SQLAlchemy Select query
        page: Page number (1-indexed)
        page_size: Number of items per page
        max_page_size: Maximum allowed page size

    Returns:
        Query with offset and limit applied

    Example:
        >>> query = select(Stock).where(Stock.is_active == True)
        >>> paginated = paginate_query(query, page=2, page_size=10)
    """
    # Validate inputs
    page = max(1, page)
    page_size = min(max(1, page_size), max_page_size)

    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)


async def get_paginated_async(
    session: AsyncSession,
    query: Select,
    count_query: Select | None = None,
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100,
) -> PaginatedResult:
    """
    Execute paginated query asynchronously.

    Args:
        session: Async database session
        query: SQLAlchemy Select query for items
        count_query: Optional separate count query (derived from query if not provided)
        page: Page number (1-indexed)
        page_size: Number of items per page
        max_page_size: Maximum allowed page size

    Returns:
        PaginatedResult with items and metadata

    Example:
        >>> query = select(Stock).where(Stock.is_active == True)
        >>> result = await get_paginated_async(session, query, page=2)
        >>> print(result.total_pages)
    """
    # Validate inputs
    page = max(1, page)
    page_size = min(max(1, page_size), max_page_size)

    # Get total count
    if count_query is None:
        # Build count query from the main query
        count_query = select(func.count()).select_from(query.subquery())

    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0

    # Apply pagination and fetch items
    paginated_query = paginate_query(query, page, page_size, max_page_size)
    result = await session.execute(paginated_query)
    items = result.scalars().all()

    return PaginatedResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


def get_paginated_sync(
    session: Session,
    query: Select,
    count_query: Select | None = None,
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100,
) -> PaginatedResult:
    """
    Execute paginated query synchronously.

    Args:
        session: Sync database session
        query: SQLAlchemy Select query for items
        count_query: Optional separate count query
        page: Page number (1-indexed)
        page_size: Number of items per page
        max_page_size: Maximum allowed page size

    Returns:
        PaginatedResult with items and metadata
    """
    # Validate inputs
    page = max(1, page)
    page_size = min(max(1, page_size), max_page_size)

    # Get total count
    if count_query is None:
        count_query = select(func.count()).select_from(query.subquery())

    total = session.execute(count_query).scalar() or 0

    # Apply pagination and fetch items
    paginated_query = paginate_query(query, page, page_size, max_page_size)
    items = session.execute(paginated_query).scalars().all()

    return PaginatedResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# Default pagination constants
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


__all__ = [
    "PaginatedResult",
    "paginate_query",
    "get_paginated_async",
    "get_paginated_sync",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
]
