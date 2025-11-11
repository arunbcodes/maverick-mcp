"""
Cache Key Generator.

Single Responsibility: Generate consistent, collision-free cache keys.
Open/Closed: Extensible via new namespaces without modifying core logic.
Interface Segregation: Simple, focused interface for key generation.

This module ensures cache key consistency across all services and supports
future multi-repo deployment by providing a centralized key generation strategy.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any


class CacheNamespace(str, Enum):
    """
    Cache key namespaces for different data types.

    Namespaces prevent key collisions and enable selective cache invalidation.
    Can be extended for new data types without breaking existing keys.

    Design Benefits:
        - Type-safe namespace management
        - Clear separation of cached data types
        - Easy to add new namespaces
        - Supports wildcard invalidation by namespace
    """

    TRANSCRIPT = "concall:transcript"
    SUMMARY = "concall:summary"
    SENTIMENT = "concall:sentiment"
    RAG_EMBEDDING = "concall:rag:embedding"
    RAG_QUERY = "concall:rag:query"
    METADATA = "concall:metadata"


class CacheKeyGenerator:
    """
    Generate consistent, versioned cache keys.

    Implements a deterministic key generation strategy that:
    - Prevents key collisions via namespacing
    - Supports versioning for cache invalidation
    - Handles complex data structures
    - Generates human-readable keys for debugging
    - Produces hash-based keys for arbitrary data

    Key Format:
        {namespace}:{version}:{identifier}
        or
        {namespace}:{version}:{hash}

    Example Keys:
        - concall:transcript:v1:RELIANCE.NS:Q1:2025
        - concall:summary:v1:AAPL:Q4:2024:standard
        - concall:sentiment:v1:8f3a9b2c

    Design Philosophy:
        - Deterministic: Same input always produces same key
        - Collision-resistant: Namespace + versioning prevents conflicts
        - Debuggable: Human-readable when possible
        - Efficient: Hashing for complex/large inputs
    """

    def __init__(self, version: str = "v1"):
        """
        Initialize key generator.

        Args:
            version: Cache version for invalidation (default: v1)
        """
        self.version = version

    def generate_transcript_key(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
    ) -> str:
        """
        Generate cache key for transcript data.

        Args:
            ticker: Stock symbol (e.g., "RELIANCE.NS")
            quarter: Quarter (e.g., "Q1", "Q2", "Q3", "Q4")
            fiscal_year: Fiscal year (e.g., 2025)

        Returns:
            Cache key in format: concall:transcript:v1:{ticker}:{quarter}:{year}

        Example:
            >>> gen = CacheKeyGenerator()
            >>> gen.generate_transcript_key("RELIANCE.NS", "Q1", 2025)
            'concall:transcript:v1:RELIANCE.NS:Q1:2025'
        """
        return self._generate_key(
            namespace=CacheNamespace.TRANSCRIPT,
            parts=[ticker.upper(), quarter.upper(), str(fiscal_year)],
        )

    def generate_summary_key(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        mode: str = "standard",
    ) -> str:
        """
        Generate cache key for summary data.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year
            mode: Summarization mode (concise, standard, detailed)

        Returns:
            Cache key including mode for different summary types

        Example:
            >>> gen = CacheKeyGenerator()
            >>> gen.generate_summary_key("AAPL", "Q4", 2024, "detailed")
            'concall:summary:v1:AAPL:Q4:2024:detailed'
        """
        return self._generate_key(
            namespace=CacheNamespace.SUMMARY,
            parts=[ticker.upper(), quarter.upper(), str(fiscal_year), mode.lower()],
        )

    def generate_sentiment_key(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
    ) -> str:
        """
        Generate cache key for sentiment analysis data.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year

        Returns:
            Cache key for sentiment analysis results

        Example:
            >>> gen = CacheKeyGenerator()
            >>> gen.generate_sentiment_key("TCS.NS", "Q2", 2025)
            'concall:sentiment:v1:TCS.NS:Q2:2025'
        """
        return self._generate_key(
            namespace=CacheNamespace.SENTIMENT,
            parts=[ticker.upper(), quarter.upper(), str(fiscal_year)],
        )

    def generate_rag_embedding_key(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
    ) -> str:
        """
        Generate cache key for RAG vector embeddings.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year

        Returns:
            Cache key for vector embeddings

        Example:
            >>> gen = CacheKeyGenerator()
            >>> gen.generate_rag_embedding_key("INFY.NS", "Q3", 2025)
            'concall:rag:embedding:v1:INFY.NS:Q3:2025'
        """
        return self._generate_key(
            namespace=CacheNamespace.RAG_EMBEDDING,
            parts=[ticker.upper(), quarter.upper(), str(fiscal_year)],
        )

    def generate_rag_query_key(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
        query: str,
    ) -> str:
        """
        Generate cache key for RAG query results.

        Uses hash for query to handle arbitrary length and characters.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year
            query: User query text

        Returns:
            Cache key with hashed query

        Example:
            >>> gen = CacheKeyGenerator()
            >>> key = gen.generate_rag_query_key("AAPL", "Q1", 2025, "What is revenue?")
            >>> key.startswith('concall:rag:query:v1:AAPL:Q1:2025:')
            True
        """
        query_hash = self._hash_string(query)
        return self._generate_key(
            namespace=CacheNamespace.RAG_QUERY,
            parts=[ticker.upper(), quarter.upper(), str(fiscal_year), query_hash],
        )

    def generate_metadata_key(
        self,
        ticker: str,
        quarter: str,
        fiscal_year: int,
    ) -> str:
        """
        Generate cache key for call metadata.

        Args:
            ticker: Stock symbol
            quarter: Quarter
            fiscal_year: Fiscal year

        Returns:
            Cache key for metadata

        Example:
            >>> gen = CacheKeyGenerator()
            >>> gen.generate_metadata_key("RELIANCE.NS", "Q1", 2025)
            'concall:metadata:v1:RELIANCE.NS:Q1:2025'
        """
        return self._generate_key(
            namespace=CacheNamespace.METADATA,
            parts=[ticker.upper(), quarter.upper(), str(fiscal_year)],
        )

    def generate_custom_key(
        self,
        namespace: CacheNamespace,
        **kwargs: Any,
    ) -> str:
        """
        Generate cache key for custom data structures.

        Uses JSON serialization + hashing for arbitrary data.

        Args:
            namespace: Cache namespace
            **kwargs: Arbitrary key-value pairs to include

        Returns:
            Cache key with hash of serialized data

        Example:
            >>> gen = CacheKeyGenerator()
            >>> key = gen.generate_custom_key(
            ...     CacheNamespace.METADATA,
            ...     ticker="AAPL",
            ...     data_type="price"
            ... )
            >>> key.startswith('concall:metadata:v1:')
            True
        """
        data_hash = self._hash_dict(kwargs)
        return self._generate_key(namespace=namespace, parts=[data_hash])

    def _generate_key(
        self,
        namespace: CacheNamespace,
        parts: list[str],
    ) -> str:
        """
        Internal: Generate key from namespace and parts.

        Args:
            namespace: Cache namespace enum
            parts: List of key components

        Returns:
            Formatted cache key
        """
        key_parts = [namespace.value, self.version] + parts
        return ":".join(key_parts)

    @staticmethod
    def _hash_string(value: str) -> str:
        """
        Generate short hash of string value.

        Args:
            value: String to hash

        Returns:
            First 8 characters of SHA-256 hash
        """
        return hashlib.sha256(value.encode()).hexdigest()[:8]

    @staticmethod
    def _hash_dict(data: dict[str, Any]) -> str:
        """
        Generate deterministic hash of dictionary.

        Args:
            data: Dictionary to hash

        Returns:
            First 8 characters of SHA-256 hash of sorted JSON
        """
        # Sort keys for deterministic serialization
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:8]

    def get_namespace_pattern(self, namespace: CacheNamespace) -> str:
        """
        Get pattern for namespace-based cache operations.

        Useful for bulk operations like invalidation or listing.

        Args:
            namespace: Cache namespace

        Returns:
            Pattern string for matching all keys in namespace

        Example:
            >>> gen = CacheKeyGenerator()
            >>> gen.get_namespace_pattern(CacheNamespace.TRANSCRIPT)
            'concall:transcript:v1:*'
        """
        return f"{namespace.value}:{self.version}:*"

    def bump_version(self, new_version: str) -> CacheKeyGenerator:
        """
        Create new generator with different version.

        Useful for cache invalidation strategies.

        Args:
            new_version: New version string

        Returns:
            New CacheKeyGenerator instance with updated version

        Example:
            >>> gen_v1 = CacheKeyGenerator("v1")
            >>> gen_v2 = gen_v1.bump_version("v2")
            >>> gen_v1.version
            'v1'
            >>> gen_v2.version
            'v2'
        """
        return CacheKeyGenerator(version=new_version)
