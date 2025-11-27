"""
Base classes for web search providers.

Provides a common interface for web search operations with
health tracking, rate limiting, and timeout management.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result."""

    url: str
    title: str
    snippet: str
    score: float = 0.0
    published_date: datetime | None = None
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "score": self.score,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "source": self.source,
            "metadata": self.metadata,
        }


@dataclass
class WebSearchConfig:
    """Configuration for web search providers."""

    # Timeout settings
    default_timeout: float = 30.0
    min_timeout: float = 15.0
    max_timeout: float = 120.0

    # Failure thresholds
    max_failures: int = 3
    timeout_failure_threshold: int = 12

    # Rate limiting
    requests_per_minute: int = 60
    rate_limit_window_seconds: int = 60

    # Content extraction
    max_content_length: int = 50000
    content_timeout: float = 30.0

    # Financial domains for priority
    financial_domains: list[str] = field(default_factory=lambda: [
        "sec.gov",
        "edgar.sec.gov",
        "investor.gov",
        "bloomberg.com",
        "reuters.com",
        "wsj.com",
        "ft.com",
        "marketwatch.com",
        "yahoo.com/finance",
        "finance.yahoo.com",
        "morningstar.com",
        "fool.com",
        "seekingalpha.com",
        "investopedia.com",
        "barrons.com",
        "cnbc.com",
        "nasdaq.com",
        "nyse.com",
    ])

    # Domains to exclude
    excluded_domains: list[str] = field(default_factory=lambda: [
        "facebook.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "tiktok.com",
        "reddit.com",
        "pinterest.com",
        "linkedin.com",
        "youtube.com",
        "wikipedia.org",
    ])


class WebSearchProvider(ABC):
    """
    Abstract base class for web search providers.

    Provides common functionality for health tracking, timeout calculation,
    and failure recording. Concrete implementations should override the
    search() and get_content() methods.
    """

    def __init__(
        self,
        api_key: str,
        config: WebSearchConfig | None = None,
    ):
        """
        Initialize the web search provider.

        Args:
            api_key: API key for the search provider
            config: Optional configuration overrides
        """
        self.api_key = api_key
        self.config = config or WebSearchConfig()
        self._failure_count = 0
        self._is_healthy = True
        self._last_request_time: datetime | None = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def calculate_timeout(
        self,
        query: str,
        timeout_budget: float | None = None,
    ) -> float:
        """
        Calculate timeout for a search operation.

        Args:
            query: The search query
            timeout_budget: Optional timeout budget constraint

        Returns:
            Calculated timeout in seconds
        """
        query_words = len(query.split())

        # Base timeout based on query complexity
        if query_words <= 3:
            base_timeout = 30.0
        elif query_words <= 8:
            base_timeout = 45.0
        else:
            base_timeout = 60.0

        # Apply budget constraints
        if timeout_budget and timeout_budget > 0:
            budget_timeout = max(timeout_budget * 0.6, self.config.min_timeout)
            calculated_timeout = min(base_timeout, budget_timeout)
        else:
            calculated_timeout = base_timeout

        # Ensure within bounds
        return max(
            self.config.min_timeout,
            min(calculated_timeout, self.config.max_timeout),
        )

    def record_failure(self, error_type: str = "unknown") -> None:
        """
        Record a search failure and check if provider should be disabled.

        Args:
            error_type: Type of error (timeout, api_error, etc.)
        """
        self._failure_count += 1

        # Different thresholds for different error types
        if error_type == "timeout":
            threshold = self.config.timeout_failure_threshold
        else:
            threshold = self.config.max_failures * 2

        if self._failure_count >= threshold:
            self._is_healthy = False
            self.logger.warning(
                f"Provider {self.__class__.__name__} disabled after "
                f"{self._failure_count} {error_type} failures"
            )

        self.logger.debug(
            f"Provider {self.__class__.__name__} failure recorded: "
            f"type={error_type}, count={self._failure_count}"
        )

    def record_success(self) -> None:
        """Record a successful search and reset failure count."""
        if self._failure_count > 0:
            self.logger.info(
                f"Provider {self.__class__.__name__} recovered after "
                f"{self._failure_count} failures"
            )
        self._failure_count = 0
        self._is_healthy = True

    def is_healthy(self) -> bool:
        """Check if provider is healthy and should be used."""
        return self._is_healthy

    def reset_health(self) -> None:
        """Reset provider health status."""
        self._failure_count = 0
        self._is_healthy = True

    def timeframe_to_date(self, timeframe: str) -> str | None:
        """
        Convert timeframe string to date string.

        Args:
            timeframe: Timeframe string (1d, 1w, 1m, 3m)

        Returns:
            Date string in YYYY-MM-DD format or None
        """
        now = datetime.now()

        timeframe_map = {
            "1d": timedelta(days=1),
            "7d": timedelta(days=7),
            "1w": timedelta(weeks=1),
            "1m": timedelta(days=30),
            "3m": timedelta(days=90),
            "6m": timedelta(days=180),
            "1y": timedelta(days=365),
        }

        delta = timeframe_map.get(timeframe)
        if delta is None:
            return None

        date = now - delta
        return date.strftime("%Y-%m-%d")

    @abstractmethod
    async def search(
        self,
        query: str,
        num_results: int = 10,
        timeout_budget: float | None = None,
    ) -> list[SearchResult]:
        """
        Perform web search and return results.

        Args:
            query: Search query
            num_results: Maximum number of results
            timeout_budget: Optional timeout budget

        Returns:
            List of SearchResult objects
        """
        raise NotImplementedError

    @abstractmethod
    async def get_content(self, url: str) -> dict[str, Any]:
        """
        Extract content from a URL.

        Args:
            url: URL to extract content from

        Returns:
            Dictionary with extracted content
        """
        raise NotImplementedError

    async def search_multiple(
        self,
        queries: list[str],
        max_results_per_query: int = 5,
    ) -> dict[str, list[SearchResult]]:
        """
        Search multiple queries and aggregate results.

        Args:
            queries: List of search queries
            max_results_per_query: Maximum results per query

        Returns:
            Dictionary mapping queries to results
        """
        results = {}

        for query in queries:
            try:
                query_results = await self.search(query, max_results_per_query)
                results[query] = query_results
            except Exception as e:
                self.logger.warning(f"Search failed for query '{query}': {e}")
                results[query] = []

        return results

    def get_status(self) -> dict[str, Any]:
        """Get provider status information."""
        return {
            "provider": self.__class__.__name__,
            "healthy": self._is_healthy,
            "failure_count": self._failure_count,
            "max_failures": self.config.max_failures,
            "has_api_key": bool(self.api_key),
        }
