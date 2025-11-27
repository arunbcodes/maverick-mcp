"""
Base web search provider for research agents.

Provides abstract base class with health tracking, timeout handling,
and circuit breaker integration.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from maverick_agents.circuit_breaker import CircuitBreakerManager

logger = logging.getLogger(__name__)


class WebSearchError(Exception):
    """Exception raised for web search failures."""

    def __init__(self, message: str, provider: str | None = None):
        self.message = message
        self.provider = provider
        super().__init__(message)


@runtime_checkable
class SettingsProtocol(Protocol):
    """Protocol for settings object."""

    @property
    def performance(self) -> Any:
        """Performance settings."""
        ...


class DefaultPerformanceSettings:
    """Default performance settings for search providers."""

    search_default_timeout: float = 30.0
    search_timeout_per_result: float = 2.0
    search_max_timeout: float = 60.0
    search_timeout_failure_threshold: int = 12
    search_circuit_breaker_failure_threshold: int = 8
    search_circuit_breaker_recovery_timeout: float = 30.0


class DefaultSettings:
    """Default settings container."""

    def __init__(self):
        self.performance = DefaultPerformanceSettings()


class WebSearchProvider(ABC):
    """
    Abstract base class for web search providers.

    Provides common functionality for health tracking, timeout calculation,
    and failure handling that all search providers should inherit.

    Attributes:
        api_key: API key for the search provider
        logger: Logger instance for this provider
        settings: Application settings (injected or default)
    """

    def __init__(
        self,
        api_key: str,
        settings: SettingsProtocol | None = None,
        circuit_manager: CircuitBreakerManager | None = None,
    ):
        """
        Initialize the web search provider.

        Args:
            api_key: API key for authentication
            settings: Optional settings protocol implementation
            circuit_manager: Optional circuit breaker manager
        """
        self.api_key = api_key
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.settings = settings or DefaultSettings()
        self.circuit_manager = circuit_manager

        # Health tracking
        self._is_healthy = True
        self._failure_count = 0
        self._max_failures = 5
        self._last_success: datetime | None = None
        self._last_failure: datetime | None = None

    def _calculate_timeout(
        self, query: str, timeout_budget: float | None = None
    ) -> float:
        """
        Calculate adaptive timeout based on query complexity and budget.

        Args:
            query: The search query
            timeout_budget: Optional timeout budget from parent operation

        Returns:
            Calculated timeout in seconds
        """
        perf = self.settings.performance

        # Base timeout from settings
        base_timeout = getattr(perf, "search_default_timeout", 30.0)
        timeout_per_result = getattr(perf, "search_timeout_per_result", 2.0)
        max_timeout = getattr(perf, "search_max_timeout", 60.0)

        # Adjust based on query complexity
        query_length = len(query)
        complexity_factor = 1.0 + (min(query_length, 200) / 200) * 0.5

        calculated_timeout = base_timeout * complexity_factor + timeout_per_result * 5

        # Apply budget constraint if provided
        if timeout_budget is not None and timeout_budget > 0:
            # Use minimum of calculated and budget, but ensure reasonable minimum
            final_timeout = max(min(calculated_timeout, timeout_budget), 10.0)
        else:
            final_timeout = min(calculated_timeout, max_timeout)

        return final_timeout

    def _record_failure(self, error_type: str = "unknown") -> None:
        """
        Record a search failure and check if provider should be disabled.

        Args:
            error_type: Type of failure (e.g., "timeout", "error")
        """
        self._failure_count += 1
        self._last_failure = datetime.now(UTC)

        # Use separate thresholds for timeout vs other failures
        timeout_threshold = getattr(
            self.settings.performance, "search_timeout_failure_threshold", 12
        )

        # Much more tolerant of timeout failures - may be due to network/complexity
        if error_type == "timeout" and self._failure_count >= timeout_threshold:
            self._is_healthy = False
            logger.warning(
                f"Search provider {self.__class__.__name__} disabled after "
                f"{self._failure_count} consecutive timeout failures (threshold: {timeout_threshold})"
            )
        elif error_type != "timeout" and self._failure_count >= self._max_failures * 2:
            # Be more lenient for non-timeout failures (2x threshold)
            self._is_healthy = False
            logger.warning(
                f"Search provider {self.__class__.__name__} disabled after "
                f"{self._failure_count} total non-timeout failures"
            )

        logger.debug(
            f"Provider {self.__class__.__name__} failure recorded: "
            f"type={error_type}, count={self._failure_count}, healthy={self._is_healthy}"
        )

    def _record_success(self) -> None:
        """Record a successful search and reset failure count."""
        if self._failure_count > 0:
            logger.info(
                f"Search provider {self.__class__.__name__} recovered after "
                f"{self._failure_count} failures"
            )
        self._failure_count = 0
        self._is_healthy = True
        self._last_success = datetime.now(UTC)

    def is_healthy(self) -> bool:
        """
        Check if provider is healthy and should be used.

        Returns:
            True if provider is healthy, False otherwise
        """
        return self._is_healthy

    def reset_health(self) -> None:
        """Reset provider health status to healthy."""
        self._is_healthy = True
        self._failure_count = 0
        logger.info(f"Search provider {self.__class__.__name__} health reset")

    @abstractmethod
    async def search(
        self, query: str, num_results: int = 10, timeout_budget: float | None = None
    ) -> list[dict[str, Any]]:
        """
        Perform web search and return results.

        Args:
            query: Search query string
            num_results: Number of results to return
            timeout_budget: Optional timeout budget in seconds

        Returns:
            List of search result dictionaries

        Raises:
            WebSearchError: If search fails
        """
        raise NotImplementedError

    @abstractmethod
    async def get_content(self, url: str) -> dict[str, Any]:
        """
        Extract content from a URL.

        Args:
            url: URL to extract content from

        Returns:
            Dictionary containing extracted content

        Raises:
            WebSearchError: If content extraction fails
        """
        raise NotImplementedError

    async def search_multiple_providers(
        self,
        queries: list[str],
        providers: list[str] | None = None,
        max_results_per_query: int = 5,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Search using multiple providers and return aggregated results.

        Args:
            queries: List of search queries
            providers: List of provider names to use
            max_results_per_query: Maximum results per query

        Returns:
            Dictionary mapping provider names to their results
        """
        providers = providers or ["exa"]  # Default to available providers
        results: dict[str, list[dict[str, Any]]] = {}

        for provider_name in providers:
            provider_results: list[dict[str, Any]] = []
            for query in queries:
                try:
                    query_results = await self.search(query, max_results_per_query)
                    provider_results.extend(query_results or [])
                except Exception as e:
                    self.logger.warning(
                        f"Search failed for provider {provider_name}, query '{query}': {e}"
                    )
                    continue

            results[provider_name] = provider_results

        return results

    def _timeframe_to_date(self, timeframe: str) -> str | None:
        """
        Convert timeframe string to date string.

        Args:
            timeframe: Timeframe string (e.g., "1d", "1w", "1m")

        Returns:
            Date string in YYYY-MM-DD format, or None if invalid
        """
        from datetime import timedelta

        now = datetime.now(UTC)

        if timeframe == "1d":
            date = now - timedelta(days=1)
        elif timeframe == "1w":
            date = now - timedelta(weeks=1)
        elif timeframe == "1m":
            date = now - timedelta(days=30)
        elif timeframe == "3m":
            date = now - timedelta(days=90)
        elif timeframe == "1y":
            date = now - timedelta(days=365)
        else:
            # Invalid or unsupported timeframe
            return None

        return date.strftime("%Y-%m-%d")


# Factory function for creating search providers
async def get_cached_search_provider(
    api_key: str | None, provider_type: str = "exa"
) -> WebSearchProvider | None:
    """
    Get or create a cached search provider instance.

    This is a placeholder for the actual implementation which should
    use a provider registry or dependency injection.

    Args:
        api_key: API key for the provider
        provider_type: Type of provider to create

    Returns:
        Search provider instance or None if not available
    """
    if not api_key:
        logger.warning(f"No API key provided for {provider_type} search provider")
        return None

    # This should be implemented by the actual provider modules
    # and use proper dependency injection
    logger.info(f"Search provider factory called for {provider_type}")
    return None
