"""
Web search providers for deep research agents.

Provides abstraction over various web search APIs with circuit breaker
protection and caching.
"""

from maverick_agents.providers.base import (
    SearchResult,
    WebSearchConfig,
    WebSearchProvider,
)

__all__ = [
    "WebSearchProvider",
    "WebSearchConfig",
    "SearchResult",
]
