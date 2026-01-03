"""
Dependency injection for FastAPI.

Provides singleton and per-request dependencies for services.
"""

from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from maverick_core.config import Settings, get_settings
#from maverick_api.config import Settings, get_settings
from maverick_api.main import logger
from maverick_schemas.auth import AuthenticatedUser


# --- Settings ---
#logger = logging.getLogger(__name__)

def get_current_settings() -> Settings:
    """Get settings dependency."""
    return get_settings()


# --- Redis ---

# Global Redis connection pool (singleton)
_redis_pool: Redis | None = None


async def get_redis_pool() -> Redis:
    """
    Get Redis connection pool singleton.
    
    Uses a global connection pool for better performance.
    The pool is created once and reused across all requests.
    """
    global _redis_pool
    if _redis_pool is None:
        settings = get_settings()
        _redis_pool = Redis.from_url(
            settings.redis.url,
            encoding="utf-8",
            decode_responses=False,
            # Connection pool settings
            max_connections=20,
            retry_on_timeout=True,
        )
    return _redis_pool


async def get_redis() -> Redis:
    """
    Get Redis connection from pool.
    
    This is a dependency that provides a Redis client from the connection pool.
    The pool manages connections efficiently.
    """
    return await get_redis_pool()


async def close_redis_pool() -> None:
    """Close Redis connection pool. Call on app shutdown."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None


# --- Database ---


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.

    Yields an async SQLAlchemy session for the request duration.
    """
    from maverick_data import get_async_db

    async for session in get_async_db():
        yield session


# --- Authentication ---


async def get_current_user(request: Request) -> AuthenticatedUser:
    """
    Get authenticated user from request state.

    Raises HTTPException 401 if not authenticated.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )
    return user


async def get_current_user_optional(request: Request) -> AuthenticatedUser | None:
    """
    Get authenticated user if present.

    Returns None if not authenticated (no error).
    """
    return getattr(request.state, "user", None)


# --- Request Context ---


def get_request_id(request: Request) -> str:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", "unknown")


# --- Services ---

# Note: Services are imported here to avoid circular imports
# They depend on providers from maverick-data


async def get_stock_service():
    """
    Get stock service instance.

    Uses maverick-data providers under the hood.
    """
    from maverick_services import StockService
    from maverick_data import YFinanceProvider, get_cache_manager
    provider = YFinanceProvider()
    cache_manager = get_cache_manager()
    # Get the actual cache provider, not the manager
    cache = cache_manager._ensure_initialized()
    service = StockService(provider=provider, cache=cache)
    return service
"""
    try:
        from maverick_services import StockService
        from maverick_data import YFinanceProvider, get_cache_manager
        provider = YFinanceProvider()

        # Try to get cache manager, but don't fail if Redis is not available
        try:
            cache_manager = get_cache_manager()
            # Get the actual cache provider, not the manager
            cache = cache_manager._ensure_initialized()
            #logger.info(f"StockService cache using Redis initialized")
        except Exception as cache_error:
            #logger.warning(f"StockService cache not available, proceeding without cache: {cache_error}")
            cache = None
        service = StockService(provider=provider, cache=cache)
        return service
    except Exception as e:
        logger.error(f"Failed to create stock service: {e}")
        raise
"""

async def get_technical_service():
    """Get technical analysis service."""
    from maverick_services.technical_service import TechnicalService
    from maverick_data import YFinanceProvider

    return TechnicalService(provider=YFinanceProvider())


async def get_portfolio_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Get portfolio service with database session."""
    from maverick_services import PortfolioService
    from maverick_data import PortfolioRepository

    # Create repository adapter
    repository = PortfolioRepository(db)

    return PortfolioService(repository=repository)


async def get_screening_service(
    db: AsyncSession = Depends(get_db),
):
    """Get screening service."""
    from maverick_services import ScreeningService
    from maverick_data import ScreeningRepository

    repository = ScreeningRepository(db)

    return ScreeningService(repository=repository)


# --- SSE Manager ---

# Global in-memory SSE manager (singleton, used when Redis unavailable)
_memory_sse_manager = None


async def get_sse_manager(request: Request):
    """
    Get SSE manager for real-time updates.

    Uses Redis-based manager when available, falls back to in-memory
    manager for single-instance deployments without Redis.
    """
    global _memory_sse_manager

    from maverick_api.sse.manager import SSEManager
    from maverick_api.sse.memory_manager import InMemorySSEManager

    # Try to get Redis from app state (set during lifespan)
    redis = getattr(request.app.state, "redis", None)

    if redis is not None:
        try:
            # Quick ping to verify Redis is connected
            await redis.ping()
            return SSEManager(redis=redis)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Redis unavailable for SSE, using in-memory fallback: {e}")

    # Fallback to in-memory manager
    if _memory_sse_manager is None:
        _memory_sse_manager = InMemorySSEManager()

    return _memory_sse_manager


__all__ = [
    # Settings
    "get_current_settings",
    # Redis
    "get_redis",
    # Database
    "get_db",
    # Auth
    "get_current_user",
    "get_current_user_optional",
    # Request
    "get_request_id",
    # Services
    "get_stock_service",
    "get_technical_service",
    "get_portfolio_service",
    "get_screening_service",
    # SSE
    "get_sse_manager",
]

