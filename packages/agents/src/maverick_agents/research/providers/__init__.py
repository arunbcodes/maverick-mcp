"""
Web search providers for research agents.

Provides multiple search provider implementations with health tracking,
circuit breaker integration, and financial optimization.
"""

from maverick_agents.research.providers.base import (
    DefaultPerformanceSettings,
    DefaultSettings,
    SettingsProtocol,
    WebSearchError,
    WebSearchProvider,
    get_cached_search_provider,
)
from maverick_agents.research.providers.exa import ExaSearchProvider
from maverick_agents.research.providers.tavily import TavilySearchProvider

__all__ = [
    # Base classes and protocols
    "WebSearchProvider",
    "WebSearchError",
    "SettingsProtocol",
    "DefaultSettings",
    "DefaultPerformanceSettings",
    # Provider implementations
    "ExaSearchProvider",
    "TavilySearchProvider",
    # Factory functions
    "get_cached_search_provider",
]
