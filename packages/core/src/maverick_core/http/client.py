"""
Async HTTP Client Manager.

Provides a shared, reusable async HTTP client to prevent resource leaks
from creating new httpx.AsyncClient instances per request.

Features:
    - Singleton pattern with thread-safe initialization
    - Connection pooling for performance
    - Automatic cleanup on shutdown
    - Context manager for scoped usage
    - Configurable timeouts and limits

Usage:
    # Module-level singleton (recommended for long-running services)
    from maverick_core.http import get_http_client, close_http_client

    async def fetch_data(url: str):
        client = get_http_client()
        response = await client.get(url)
        return response.json()

    # At shutdown
    await close_http_client()

    # Context manager (for scripts or tests)
    async with http_client_context() as client:
        response = await client.get(url)
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import httpx

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_CONNECTIONS = 100
DEFAULT_MAX_KEEPALIVE_CONNECTIONS = 20
DEFAULT_KEEPALIVE_EXPIRY = 5.0


class AsyncHTTPClient:
    """
    Managed async HTTP client with connection pooling.

    Wraps httpx.AsyncClient with proper lifecycle management,
    connection pooling, and automatic cleanup.

    Features:
        - Connection pooling (reuses TCP connections)
        - Configurable timeouts
        - Automatic retry headers
        - Proper resource cleanup
    """

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
        max_keepalive_connections: int = DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
        keepalive_expiry: float = DEFAULT_KEEPALIVE_EXPIRY,
        base_url: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        """
        Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds
            max_connections: Maximum concurrent connections
            max_keepalive_connections: Max idle connections to keep
            keepalive_expiry: Time before closing idle connections
            base_url: Optional base URL for all requests
            headers: Optional default headers for all requests
        """
        self._timeout = timeout
        self._max_connections = max_connections
        self._max_keepalive_connections = max_keepalive_connections
        self._keepalive_expiry = keepalive_expiry
        self._base_url = base_url
        self._headers = headers or {}

        self._client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()
        self._closed = False

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Lazily create or return existing client."""
        if self._client is None or self._closed:
            async with self._lock:
                # Double-check after acquiring lock
                if self._client is None or self._closed:
                    self._client = httpx.AsyncClient(
                        timeout=httpx.Timeout(self._timeout),
                        limits=httpx.Limits(
                            max_connections=self._max_connections,
                            max_keepalive_connections=self._max_keepalive_connections,
                            keepalive_expiry=self._keepalive_expiry,
                        ),
                        base_url=self._base_url or "",
                        headers=self._headers,
                        follow_redirects=True,
                    )
                    self._closed = False
                    logger.debug("Created new AsyncHTTPClient")
        return self._client

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """
        Make GET request.

        Args:
            url: Request URL
            params: Query parameters
            headers: Additional headers
            timeout: Override default timeout

        Returns:
            HTTP response
        """
        client = await self._ensure_client()
        return await client.get(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    async def post(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """
        Make POST request.

        Args:
            url: Request URL
            json: JSON body
            data: Form data
            headers: Additional headers
            timeout: Override default timeout

        Returns:
            HTTP response
        """
        client = await self._ensure_client()
        return await client.post(
            url,
            json=json,
            data=data,
            headers=headers,
            timeout=timeout,
        )

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        async with self._lock:
            if self._client is not None and not self._closed:
                await self._client.aclose()
                self._client = None
                self._closed = True
                logger.debug("Closed AsyncHTTPClient")

    @property
    def is_closed(self) -> bool:
        """Check if client is closed."""
        return self._closed or self._client is None

    async def __aenter__(self) -> "AsyncHTTPClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


# Global singleton instance
_global_client: AsyncHTTPClient | None = None
_global_client_lock = asyncio.Lock()


async def get_http_client(
    timeout: float = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> AsyncHTTPClient:
    """
    Get or create global HTTP client singleton.

    Thread-safe lazy initialization with double-checked locking.

    Args:
        timeout: Request timeout (only used on first call)
        **kwargs: Additional client options (only used on first call)

    Returns:
        Shared AsyncHTTPClient instance
    """
    global _global_client

    # Fast path - already initialized
    if _global_client is not None and not _global_client.is_closed:
        return _global_client

    # Slow path - need to initialize
    async with _global_client_lock:
        # Double-check after acquiring lock
        if _global_client is None or _global_client.is_closed:
            _global_client = AsyncHTTPClient(timeout=timeout, **kwargs)
            logger.info("Initialized global HTTP client")

    return _global_client


async def close_http_client() -> None:
    """
    Close the global HTTP client.

    Should be called at application shutdown.
    """
    global _global_client

    async with _global_client_lock:
        if _global_client is not None:
            await _global_client.close()
            _global_client = None
            logger.info("Closed global HTTP client")


@asynccontextmanager
async def http_client_context(
    timeout: float = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> AsyncIterator[AsyncHTTPClient]:
    """
    Create a scoped HTTP client that auto-closes.

    Use for scripts or tests where you want automatic cleanup.
    For long-running services, use get_http_client() instead.

    Args:
        timeout: Request timeout
        **kwargs: Additional client options

    Yields:
        AsyncHTTPClient instance

    Example:
        async with http_client_context() as client:
            response = await client.get("https://api.example.com/data")
    """
    client = AsyncHTTPClient(timeout=timeout, **kwargs)
    try:
        yield client
    finally:
        await client.close()
