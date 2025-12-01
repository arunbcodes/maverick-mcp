"""
Maverick Data Utilities.

Common utility functions for stock data processing, helpers, and pagination.
"""

from maverick_data.utils.pagination import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    PaginatedResult,
    get_paginated_async,
    get_paginated_sync,
    paginate_query,
)
from maverick_data.utils.stock_helpers import (
    calculate_date_range,
    get_multiple_stock_dataframes_async,
    get_stock_dataframe,
    get_stock_dataframe_async,
    validate_ticker,
)

__all__ = [
    # Stock helpers
    "get_stock_dataframe",
    "get_stock_dataframe_async",
    "get_multiple_stock_dataframes_async",
    "validate_ticker",
    "calculate_date_range",
    # Pagination
    "PaginatedResult",
    "paginate_query",
    "get_paginated_async",
    "get_paginated_sync",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
]

