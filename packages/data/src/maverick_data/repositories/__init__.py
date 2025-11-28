"""
Maverick Data Repositories.

Repository pattern implementations for data access.
These repositories implement the interfaces defined in maverick-core.
"""

from maverick_data.repositories.stock_repository import StockRepository
from maverick_data.repositories.portfolio_repository import PortfolioRepository
from maverick_data.repositories.screening_repository import ScreeningRepository

__all__ = [
    "StockRepository",
    "PortfolioRepository",
    "ScreeningRepository",
]
