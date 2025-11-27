"""
Tavily search provider for web search.

Provides web search capabilities with sensible filtering for financial research.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Iterable

from maverick_agents.research.providers.base import WebSearchError, WebSearchProvider

if TYPE_CHECKING:
    from maverick_agents.circuit_breaker import CircuitBreakerManager

logger = logging.getLogger(__name__)

# Try to import TavilyClient
try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None  # type: ignore


class TavilySearchProvider(WebSearchProvider):
    """
    Tavily search provider with sensible filtering for financial research.

    Features:
    - Domain filtering for better financial results
    - Circuit breaker integration
    - Adaptive timeout handling
    """

    # Domains to exclude for financial searches
    EXCLUDED_DOMAINS = {
        "facebook.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "reddit.com",
    }

    def __init__(
        self,
        api_key: str,
        settings: Any | None = None,
        circuit_manager: CircuitBreakerManager | None = None,
    ):
        """
        Initialize TavilySearchProvider.

        Args:
            api_key: Tavily API key
            settings: Optional settings protocol implementation
            circuit_manager: Optional circuit breaker manager
        """
        super().__init__(api_key, settings, circuit_manager)
        self.excluded_domains = set(self.EXCLUDED_DOMAINS)

        if TavilyClient is None:
            logger.warning("tavily package not installed - provider will not function")

        logger.info("Initialized TavilySearchProvider")

    async def search(
        self, query: str, num_results: int = 10, timeout_budget: float | None = None
    ) -> list[dict[str, Any]]:
        """
        Search using Tavily API.

        Args:
            query: Search query string
            num_results: Number of results to return
            timeout_budget: Optional timeout budget in seconds

        Returns:
            List of search result dictionaries

        Raises:
            WebSearchError: If search fails
        """
        if not self.is_healthy():
            raise WebSearchError(
                "Tavily provider disabled due to repeated failures", "tavily"
            )

        if TavilyClient is None:
            raise WebSearchError(
                "tavily package is required for TavilySearchProvider", "tavily"
            )

        timeout = self._calculate_timeout(query, timeout_budget)

        # Get or create circuit breaker if manager is available
        circuit_breaker = None
        if self.circuit_manager:
            circuit_breaker = await self.circuit_manager.get_or_create(
                "tavily_search",
                failure_threshold=8,
                recovery_timeout=30,
            )

        async def _search() -> list[dict[str, Any]]:
            client = TavilyClient(api_key=self.api_key)
            # Run synchronous Tavily client in executor
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.search(query=query, max_results=num_results),
            )
            return self._process_results(response.get("results", []))

        try:
            if circuit_breaker:
                return await circuit_breaker.call(_search, timeout=timeout)
            else:
                return await asyncio.wait_for(_search(), timeout=timeout)

        except TimeoutError:
            self._record_failure("timeout")
            raise WebSearchError(
                f"Tavily search timed out after {timeout:.1f} seconds", "tavily"
            )
        except Exception as e:
            self._record_failure("error")
            raise WebSearchError(f"Tavily search failed: {str(e)}", "tavily")

    def _process_results(
        self, results: Iterable[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Process and filter Tavily search results.

        Args:
            results: Raw search results from Tavily

        Returns:
            Processed list of search result dictionaries
        """
        processed: list[dict[str, Any]] = []
        for item in results:
            url = item.get("url", "")
            # Filter out excluded domains
            if any(domain in url for domain in self.excluded_domains):
                continue

            processed.append(
                {
                    "url": url,
                    "title": item.get("title"),
                    "content": item.get("content") or item.get("raw_content", ""),
                    "raw_content": item.get("raw_content"),
                    "published_date": item.get("published_date"),
                    "score": item.get("score", 0.0),
                    "provider": "tavily",
                }
            )
        return processed

    async def get_content(self, url: str) -> dict[str, Any]:
        """
        Extract content from a URL.

        Note: Tavily doesn't have a dedicated content extraction API,
        so we return a placeholder indicating this limitation.

        Args:
            url: URL to extract content from

        Returns:
            Dictionary with content or error
        """
        return {
            "url": url,
            "content": "",
            "error": "Tavily does not support direct content extraction",
        }
