"""
Redis cache provider.

Implements ICacheProvider interface with Redis backend.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import redis.asyncio as redis

from maverick_core import ICacheProvider
from maverick_data.cache.serialization import deserialize_data, serialize_data

logger = logging.getLogger("maverick_data.cache.redis")


class RedisCache(ICacheProvider):
    """Redis-based cache provider implementing ICacheProvider interface."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int = 0,
        password: str | None = None,
        ssl: bool = False,
        max_connections: int = 10,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        retry_on_timeout: bool = True,
    ):
        """
        Initialize Redis cache provider.

        Args:
            host: Redis host (defaults to REDIS_HOST env var or localhost)
            port: Redis port (defaults to REDIS_PORT env var or 6379)
            db: Redis database number
            password: Redis password (defaults to REDIS_PASSWORD env var)
            ssl: Enable SSL connection
            max_connections: Maximum connections in pool
            socket_timeout: Socket operation timeout
            socket_connect_timeout: Socket connect timeout
            retry_on_timeout: Retry on timeout errors
        """
        self._host = host or os.getenv("REDIS_HOST", "localhost")
        self._port = port or int(os.getenv("REDIS_PORT", "6379"))
        self._db = db
        self._password = password or os.getenv("REDIS_PASSWORD", "")
        self._ssl = ssl or os.getenv("REDIS_SSL", "false").lower() == "true"
        self._max_connections = max_connections
        self._socket_timeout = socket_timeout
        self._socket_connect_timeout = socket_connect_timeout
        self._retry_on_timeout = retry_on_timeout

        self._client: redis.Redis | None = None
        self._connected = False

    async def _get_client(self) -> redis.Redis | None:
        """Get Redis client with connection."""
        if self._client is not None and self._connected:
            try:
                await self._client.ping()
                return self._client
            except Exception:
                self._connected = False
                self._client = None

        try:
            client_params: dict[str, Any] = {
                "host": self._host,
                "port": self._port,
                "db": self._db,
                "max_connections": self._max_connections,
                "retry_on_timeout": self._retry_on_timeout,
                "socket_timeout": self._socket_timeout,
                "socket_connect_timeout": self._socket_connect_timeout,
                "health_check_interval": 30,
                "decode_responses": False,
            }

            if self._password:
                client_params["password"] = self._password

            if self._ssl:
                client_params["ssl"] = True
                client_params["ssl_check_hostname"] = False

            self._client = redis.Redis(**client_params)
            await self._client.ping()
            self._connected = True
            logger.debug(
                f"Created Redis async client with {self._max_connections} max connections"
            )
            return self._client
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}")
            self._connected = False
            self._client = None
            return None
        except redis.TimeoutError as e:
            logger.warning(f"Redis connection timeout: {e}")
            self._connected = False
            self._client = None
            return None
        except Exception as e:
            logger.warning(f"Redis client error: {e}")
            self._connected = False
            self._client = None
            return None

    async def get(self, key: str) -> Any:
        """Get value from cache."""
        client = await self._get_client()
        if not client:
            return None

        try:
            data = await client.get(key)
            if data:
                return deserialize_data(data, key)  # type: ignore[arg-type]
            return None
        except Exception as e:
            logger.warning(f"Error reading from Redis cache: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache with optional TTL."""
        client = await self._get_client()
        if not client:
            return False

        try:
            serialized = serialize_data(value, key)
            if ttl:
                await client.setex(key, ttl, serialized)
            else:
                await client.set(key, serialized)
            return True
        except Exception as e:
            logger.warning(f"Error saving to Redis cache: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        client = await self._get_client()
        if not client:
            return False

        try:
            return bool(await client.delete(key))
        except Exception as e:
            logger.warning(f"Error deleting from Redis cache: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        client = await self._get_client()
        if not client:
            return False

        try:
            return bool(await client.exists(key))
        except Exception as e:
            logger.warning(f"Error checking key existence: {e}")
            return False

    async def clear(self, pattern: str | None = None) -> int:
        """Clear cache entries matching pattern."""
        client = await self._get_client()
        if not client:
            return 0

        try:
            if pattern:
                keys = await client.keys(pattern)
                if keys:
                    return int(await client.delete(*keys))  # type: ignore[arg-type]
                return 0
            else:
                return int(await client.flushdb())  # type: ignore[return-value]
        except Exception as e:
            logger.warning(f"Error clearing Redis cache: {e}")
            return 0

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        client = await self._get_client()
        stats: dict[str, Any] = {
            "connected": self._connected,
            "backend": "redis",
            "host": self._host,
            "port": self._port,
        }

        if client:
            try:
                info = await client.info()
                stats.update(
                    {
                        "used_memory": info.get("used_memory", 0),
                        "used_memory_human": info.get("used_memory_human", "0B"),
                        "connected_clients": info.get("connected_clients", 0),
                        "keyspace_hits": info.get("keyspace_hits", 0),
                        "keyspace_misses": info.get("keyspace_misses", 0),
                        "total_connections_received": info.get(
                            "total_connections_received", 0
                        ),
                    }
                )
            except Exception as e:
                logger.warning(f"Error getting Redis stats: {e}")

        return stats

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            try:
                await self._client.aclose()
                logger.debug("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self._client = None
                self._connected = False
