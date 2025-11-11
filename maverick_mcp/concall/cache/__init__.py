"""
Conference Call Caching Layer.

This package provides a modular, SOLID-compliant caching layer for conference call
data. Designed for easy extraction into a separate microservice if needed.

Architecture:
    - ICacheBackend: Abstract interface for all cache implementations
    - RedisCacheBackend: Production Redis implementation
    - InMemoryCacheBackend: Development/testing fallback
    - ConcallCacheService: High-level service for conference call caching
    - CacheKeyGenerator: Consistent key generation across services

Key Design Principles:
    - Single Responsibility: Each class has one reason to change
    - Open/Closed: Extensible via new backends without modifying core
    - Liskov Substitution: All backends are interchangeable
    - Interface Segregation: Minimal, focused interfaces
    - Dependency Inversion: Services depend on abstractions

Example Usage:
    >>> from maverick_mcp.concall.cache import ConcallCacheService
    >>>
    >>> cache = ConcallCacheService()
    >>>
    >>> # Cache transcript
    >>> await cache.cache_transcript(
    ...     ticker="RELIANCE.NS",
    ...     quarter="Q1",
    ...     fiscal_year=2025,
    ...     transcript_text="...",
    ...     metadata={}
    ... )
    >>>
    >>> # Retrieve transcript
    >>> result = await cache.get_transcript("RELIANCE.NS", "Q1", 2025)
"""

from .backends import ICacheBackend, InMemoryCacheBackend, RedisCacheBackend
from .cache_service import ConcallCacheService
from .key_generator import CacheKeyGenerator, CacheNamespace

__all__ = [
    # Interfaces
    "ICacheBackend",
    # Implementations
    "RedisCacheBackend",
    "InMemoryCacheBackend",
    # Services
    "ConcallCacheService",
    # Utilities
    "CacheKeyGenerator",
    "CacheNamespace",
]
