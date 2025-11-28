"""
Conference Call Data Providers.

Provides the base provider interface and implementations for fetching
conference call transcripts from various sources.

Available Providers:
    - ConcallProvider: Abstract base interface
    - CompanyIRProvider: Fetch from company IR websites
    - NSEProvider: Fetch from NSE exchange filings

Note: Full implementations with database integration are available
in the main maverick_mcp.concall package.
"""

from abc import ABC, abstractmethod
from typing import Any


class ConcallProvider(ABC):
    """
    Abstract base class for conference call data providers.

    All providers (IR, NSE, Screener, YouTube) must implement this interface.
    This ensures consistency and allows easy swapping of providers.

    Design: Interface Segregation - minimal interface with only essential methods.
    """

    @abstractmethod
    async def fetch_transcript(
        self, ticker: str, quarter: str, fiscal_year: int
    ) -> dict[str, Any] | None:
        """
        Fetch conference call transcript for given company and quarter.

        Args:
            ticker: Stock symbol (e.g., "RELIANCE.NS", "AAPL")
            quarter: Quarter identifier (e.g., "Q1", "Q2", "Q3", "Q4")
            fiscal_year: Fiscal year (e.g., 2025)

        Returns:
            dict with keys:
                - transcript_text: Full transcript content
                - source_url: URL where transcript was found
                - transcript_format: Format (pdf, html, txt)
                - metadata: Additional info (call_date, etc.)
            None if transcript not found

        Raises:
            Exception: If fetching fails due to network/parsing errors
        """
        pass

    @abstractmethod
    def is_available(self, ticker: str) -> bool:
        """
        Check if this provider supports the given ticker.

        Args:
            ticker: Stock symbol to check

        Returns:
            bool: True if provider can fetch data for this ticker
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get provider name for logging/debugging."""
        pass


__all__ = ["ConcallProvider"]
