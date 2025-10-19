"""
Provider interfaces (protocols) for MaverickMCP.

This package defines interfaces for all major providers to enable:
- Dependency inversion (depend on abstractions, not implementations)
- Easy mocking and testing
- Multiple implementations (e.g., different data sources)
- Clear contracts
"""

from maverick_mcp.interfaces.stock_data import (
    IStockDataProvider,
    IMarketCalendar,
    ICacheManager,
    IDataFetcher,
    IScreeningProvider,
)

__all__ = [
    "IStockDataProvider",
    "IMarketCalendar",
    "ICacheManager",
    "IDataFetcher",
    "IScreeningProvider",
]

