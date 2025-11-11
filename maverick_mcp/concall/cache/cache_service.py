"""
Conference Call Cache Service.

Single Responsibility: Manage conference call data caching.
Open/Closed: Extensible via backend injection.
Liskov Substitution: Works with any ICacheBackend implementation.
Interface Segregation: Domain-specific interface for conference calls.
Dependency Inversion: Depends on ICacheBackend abstraction.

This service provides high-level caching operations specifically for conference
call data, abstracting away cache key generation and backend details.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from .backends import ICacheBackend, InMemoryCacheBackend, RedisCacheBackend
from .key_generator import CacheKeyGenerator, CacheNamespace

logger = logging.getLogger(__name__)


class ConcallCacheService:
    """
    High-level caching service for conference call data.

    Provides domain-specific caching operations that:
        - Abstract cache key generation
        - Handle serialization/deserialization
        - Support multiple backend implementations
        - Provide namespace-based invalidation
        - Track cache performance

    Design Philosophy:
        - Domain-focused: Operations match business needs
        - Backend-agnostic: Works with Redis, in-memory, or future backends
        - Fail-safe: Cache failures don't break the application
        - Observable: Comprehensive stats for monitoring

    Example Usage:
        >>> cache = ConcallCacheService()
        >>>
        >>> # Cache transcript
        >>> await cache.cache_transcript(
        ...     ticker="RELIANCE.NS",
        ...     quarter="Q1",
        ...     fiscal_year=2025,
        ...     transcript_text="...",
        ...     metadata={"source": "IR website"}
        ... )
        >>>
        >>> # Retrieve transcript
        >>> result = await cache.get_transcript("RELIANCE.NS", "Q1", 2025)
        >>> if result:
        ...     print(result["transcript_text"][:100])
    """

    def __init__(
        self,
        backend: ICacheBackend | None = None,
        key_generator: CacheKeyGenerator | None = None,
        default_ttl_seconds: int | None = None,
    ):
        """
        Initialize cache service.

        Args:
            backend: Cache backend (default: auto-detect Redis or in-memory)
            key_generator: Key generator (default: new instance)
            default_ttl_seconds: Default TTL for cached items (default: 7 days)
        """
        # Default TTL: 7 days for conference call data (semi-static)
        self.default_ttl_seconds = default_ttl_seconds or 7 * 24 * 3600

        # Auto-detect backend if not provided
        if backend is None:
            backend = self._create_default_backend()
        self.backend = backend

        # Initialize key generator
        self.key_generator = key_generator or CacheKeyGenerator()

        logger.info(
            f"Initialized ConcallCacheService with {type(self.backend).__name__}"
        )

    @staticmethod
    def _create_default_backend() -> ICacheBackend:
        """
        Create default cache backend based on environment.

        Returns:
            RedisCacheBackend if Redis is available, else InMemoryCacheBackend

        Note:
            Tries to connect to Redis, falls back to in-memory on failure.
        """
        redis_host = os.getenv("REDIS_HOST")
        if redis_host:
            logger.info(f"Attempting to use Redis backend at {redis_host}")
            return RedisCacheBackend(host=redis_host)
        else:
            logger.info("Redis not configured, using in-memory cache")
            return InMemoryCacheBackend(max_size=1000)

    # ===== Transcript Operations =====

    async def cache_transcript(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        transcript_text: str,
        metadata: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
    ) -> bool:
        """
        Cache conference call transcript.

        Args:
            ticker: Stock symbol (e.g., "RELIANCE.NS")
            quarter: Quarter (e.g., "Q1", "Q2", "Q3", "Q4")
            fiscal_year: Fiscal year (e.g., 2025)
            transcript_text: Full transcript content
            metadata: Additional metadata (source, format, etc.)
            ttl_seconds: TTL override (default: 7 days)

        Returns:
            True if cached successfully, False otherwise

        Example:
            >>> cache = ConcallCacheService()
            >>> success = await cache.cache_transcript(
            ...     ticker="AAPL",
            ...     quarter="Q1",
            ...     fiscal_year=2025,
            ...     transcript_text="Full transcript...",
            ...     metadata={"source": "IR website", "format": "pdf"}
            ... )
        """
        key = self.key_generator.generate_transcript_key(ticker, quarter, fiscal_year)

        value = {
            "ticker": ticker,
            "quarter": quarter,
            "fiscal_year": fiscal_year,
            "transcript_text": transcript_text,
            "metadata": metadata or {},
        }

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        return await self.backend.set(key, value, ttl_seconds=ttl)

    async def get_transcript(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
    ) -> dict[str, Any] | None:
        """
        Retrieve cached transcript.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year

        Returns:
            Dictionary with transcript data or None if not cached

        Example:
            >>> cache = ConcallCacheService()
            >>> result = await cache.get_transcript("AAPL", "Q1", 2025)
            >>> if result:
            ...     print(result["transcript_text"][:100])
        """
        key = self.key_generator.generate_transcript_key(ticker, quarter, fiscal_year)
        return await self.backend.get(key)

    async def has_transcript(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
    ) -> bool:
        """
        Check if transcript is cached.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year

        Returns:
            True if transcript exists in cache

        Example:
            >>> cache = ConcallCacheService()
            >>> if await cache.has_transcript("AAPL", "Q1", 2025):
            ...     print("Transcript is cached")
        """
        key = self.key_generator.generate_transcript_key(ticker, quarter, fiscal_year)
        return await self.backend.exists(key)

    # ===== Summary Operations =====

    async def cache_summary(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        summary_data: dict[str, Any],
        mode: str = "standard",
        ttl_seconds: int | None = None,
    ) -> bool:
        """
        Cache conference call summary.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year
            summary_data: Summary content (executive_summary, key_metrics, etc.)
            mode: Summarization mode (concise, standard, detailed)
            ttl_seconds: TTL override (default: 7 days)

        Returns:
            True if cached successfully

        Example:
            >>> cache = ConcallCacheService()
            >>> await cache.cache_summary(
            ...     ticker="AAPL",
            ...     quarter="Q1",
            ...     fiscal_year=2025,
            ...     summary_data={
            ...         "executive_summary": "Strong quarter...",
            ...         "key_metrics": {...}
            ...     },
            ...     mode="detailed"
            ... )
        """
        key = self.key_generator.generate_summary_key(
            ticker, quarter, fiscal_year, mode
        )

        value = {
            "ticker": ticker,
            "quarter": quarter,
            "fiscal_year": fiscal_year,
            "mode": mode,
            "summary": summary_data,
        }

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        return await self.backend.set(key, value, ttl_seconds=ttl)

    async def get_summary(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        mode: str = "standard",
    ) -> dict[str, Any] | None:
        """
        Retrieve cached summary.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year
            mode: Summarization mode

        Returns:
            Dictionary with summary data or None if not cached

        Example:
            >>> cache = ConcallCacheService()
            >>> result = await cache.get_summary("AAPL", "Q1", 2025, "detailed")
            >>> if result:
            ...     print(result["summary"]["executive_summary"])
        """
        key = self.key_generator.generate_summary_key(
            ticker, quarter, fiscal_year, mode
        )
        return await self.backend.get(key)

    # ===== Sentiment Operations =====

    async def cache_sentiment(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        sentiment_data: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> bool:
        """
        Cache sentiment analysis results.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year
            sentiment_data: Sentiment analysis results
            ttl_seconds: TTL override (default: 7 days)

        Returns:
            True if cached successfully

        Example:
            >>> cache = ConcallCacheService()
            >>> await cache.cache_sentiment(
            ...     ticker="AAPL",
            ...     quarter="Q1",
            ...     fiscal_year=2025,
            ...     sentiment_data={
            ...         "overall_sentiment": "positive",
            ...         "confidence": 0.85,
            ...         "dimensions": {...}
            ...     }
            ... )
        """
        key = self.key_generator.generate_sentiment_key(ticker, quarter, fiscal_year)

        value = {
            "ticker": ticker,
            "quarter": quarter,
            "fiscal_year": fiscal_year,
            "sentiment": sentiment_data,
        }

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        return await self.backend.set(key, value, ttl_seconds=ttl)

    async def get_sentiment(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
    ) -> dict[str, Any] | None:
        """
        Retrieve cached sentiment analysis.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year

        Returns:
            Dictionary with sentiment data or None if not cached

        Example:
            >>> cache = ConcallCacheService()
            >>> result = await cache.get_sentiment("AAPL", "Q1", 2025)
            >>> if result:
            ...     print(result["sentiment"]["overall_sentiment"])
        """
        key = self.key_generator.generate_sentiment_key(ticker, quarter, fiscal_year)
        return await self.backend.get(key)

    # ===== RAG Operations =====

    async def cache_rag_embeddings(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        embeddings_data: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> bool:
        """
        Cache RAG vector embeddings.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year
            embeddings_data: Vector embeddings and chunks
            ttl_seconds: TTL override (default: 7 days)

        Returns:
            True if cached successfully

        Note:
            Embeddings are expensive to compute, caching is highly recommended.
        """
        key = self.key_generator.generate_rag_embedding_key(
            ticker, quarter, fiscal_year
        )

        value = {
            "ticker": ticker,
            "quarter": quarter,
            "fiscal_year": fiscal_year,
            "embeddings": embeddings_data,
        }

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        return await self.backend.set(key, value, ttl_seconds=ttl)

    async def get_rag_embeddings(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
    ) -> dict[str, Any] | None:
        """
        Retrieve cached RAG embeddings.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year

        Returns:
            Dictionary with embeddings data or None if not cached
        """
        key = self.key_generator.generate_rag_embedding_key(
            ticker, quarter, fiscal_year
        )
        return await self.backend.get(key)

    async def cache_rag_query(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        query: str,
        answer_data: dict[str, Any],
        ttl_seconds: int = 3600,  # 1 hour default for queries
    ) -> bool:
        """
        Cache RAG query result.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year
            query: User query text
            answer_data: Query answer and sources
            ttl_seconds: TTL override (default: 1 hour for queries)

        Returns:
            True if cached successfully

        Note:
            Query results have shorter TTL as they're less expensive to recompute.
        """
        key = self.key_generator.generate_rag_query_key(
            ticker, quarter, fiscal_year, query
        )

        value = {
            "ticker": ticker,
            "quarter": quarter,
            "fiscal_year": fiscal_year,
            "query": query,
            "answer": answer_data,
        }

        return await self.backend.set(key, value, ttl_seconds=ttl_seconds)

    async def get_rag_query(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        query: str,
    ) -> dict[str, Any] | None:
        """
        Retrieve cached RAG query result.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year
            query: User query text

        Returns:
            Dictionary with answer data or None if not cached
        """
        key = self.key_generator.generate_rag_query_key(
            ticker, quarter, fiscal_year, query
        )
        return await self.backend.get(key)

    # ===== Metadata Operations =====

    async def cache_metadata(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        metadata: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> bool:
        """
        Cache call metadata.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year
            metadata: Metadata (call date, participants, etc.)
            ttl_seconds: TTL override

        Returns:
            True if cached successfully
        """
        key = self.key_generator.generate_metadata_key(ticker, quarter, fiscal_year)

        value = {
            "ticker": ticker,
            "quarter": quarter,
            "fiscal_year": fiscal_year,
            "metadata": metadata,
        }

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        return await self.backend.set(key, value, ttl_seconds=ttl)

    async def get_metadata(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
    ) -> dict[str, Any] | None:
        """
        Retrieve cached metadata.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year

        Returns:
            Dictionary with metadata or None if not cached
        """
        key = self.key_generator.generate_metadata_key(ticker, quarter, fiscal_year)
        return await self.backend.get(key)

    # ===== Bulk Operations =====

    async def invalidate_call(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
    ) -> int:
        """
        Invalidate all cached data for a specific call.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year

        Returns:
            Number of cache entries invalidated

        Example:
            >>> cache = ConcallCacheService()
            >>> count = await cache.invalidate_call("AAPL", "Q1", 2025)
            >>> print(f"Invalidated {count} cache entries")
        """
        patterns = [
            self.key_generator.generate_transcript_key(ticker, quarter, fiscal_year),
            self.key_generator.generate_sentiment_key(ticker, quarter, fiscal_year),
            self.key_generator.generate_metadata_key(ticker, quarter, fiscal_year),
            # Summary patterns for all modes
            self.key_generator.generate_summary_key(
                ticker, quarter, fiscal_year, "concise"
            ),
            self.key_generator.generate_summary_key(
                ticker, quarter, fiscal_year, "standard"
            ),
            self.key_generator.generate_summary_key(
                ticker, quarter, fiscal_year, "detailed"
            ),
            # RAG embeddings
            self.key_generator.generate_rag_embedding_key(ticker, quarter, fiscal_year),
        ]

        count = 0
        for pattern in patterns:
            deleted = await self.backend.delete(pattern)
            if deleted:
                count += 1

        logger.info(
            f"Invalidated {count} cache entries for {ticker} {quarter} {fiscal_year}"
        )
        return count

    async def invalidate_namespace(self, namespace: CacheNamespace) -> int:
        """
        Invalidate all cached data in a namespace.

        Args:
            namespace: Cache namespace to invalidate

        Returns:
            Number of cache entries invalidated

        Example:
            >>> cache = ConcallCacheService()
            >>> count = await cache.invalidate_namespace(CacheNamespace.TRANSCRIPT)
            >>> print(f"Invalidated {count} transcripts")
        """
        pattern = self.key_generator.get_namespace_pattern(namespace)
        count = await self.backend.clear_namespace(pattern)
        logger.info(f"Invalidated {count} entries in namespace {namespace.value}")
        return count

    # ===== Monitoring =====

    async def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats

        Example:
            >>> cache = ConcallCacheService()
            >>> stats = await cache.get_stats()
            >>> print(f"Cache hit rate: {stats['hits'] / (stats['hits'] + stats['misses']):.2%}")
        """
        return await self.backend.get_stats()

    async def health_check(self) -> dict[str, Any]:
        """
        Check cache service health.

        Returns:
            Dictionary with health status

        Example:
            >>> cache = ConcallCacheService()
            >>> health = await cache.health_check()
            >>> if health["healthy"]:
            ...     print("Cache is operational")
        """
        is_healthy = await self.backend.health_check()
        stats = await self.backend.get_stats()

        return {
            "healthy": is_healthy,
            "backend": type(self.backend).__name__,
            "stats": stats,
        }

    async def close(self) -> None:
        """
        Close cache service and cleanup resources.

        Example:
            >>> cache = ConcallCacheService()
            >>> # ... use cache ...
            >>> await cache.close()
        """
        if hasattr(self.backend, "close"):
            await self.backend.close()
        logger.info("Cache service closed")
