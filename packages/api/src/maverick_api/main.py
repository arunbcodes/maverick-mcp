"""
FastAPI application factory.

Creates and configures the FastAPI application with all middleware,
routers, and exception handlers.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from maverick_api.config import Settings, get_settings
from maverick_api.middleware.logging import RequestLoggingMiddleware
from maverick_api.middleware.rate_limit import RateLimitMiddleware
from maverick_api.auth.middleware import AuthMiddleware
from maverick_api.auth.cookie import CookieAuthStrategy
from maverick_api.auth.jwt import JWTAuthStrategy
from maverick_api.auth.api_key import APIKeyAuthStrategy
from maverick_api.exceptions import register_exception_handlers

logger = logging.getLogger(__name__)

# Global Redis connection pool (singleton)
_redis_pool: Redis | None = None


async def get_redis_pool(settings: Settings) -> Redis:
    """Get or create Redis connection pool singleton."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False,
        )
    return _redis_pool


async def close_redis_pool() -> None:
    """Close Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")

    # Startup - Initialize Redis connection pool
    redis = await get_redis_pool(settings)
    app.state.redis = redis
    logger.info("Redis connection pool initialized")

    # Initialize capabilities system
    try:
        from maverick_server.capabilities_integration import initialize_capabilities
        initialize_capabilities()
        logger.info("Capabilities system initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize capabilities: {e}")

    # Initialize task queue for async operations
    try:
        from maverick_api.capabilities.async_endpoints import set_task_queue
        from maverick_capabilities.tasks import RedisTaskQueue

        task_queue = RedisTaskQueue(redis)
        await task_queue.start()
        set_task_queue(task_queue)
        app.state.task_queue = task_queue
        logger.info("Task queue initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize task queue: {e}")

    yield

    # Shutdown - Close connections
    logger.info("Shutting down...")

    # Stop task queue
    if hasattr(app.state, "task_queue"):
        try:
            await app.state.task_queue.stop()
            logger.info("Task queue stopped")
        except Exception as e:
            logger.warning(f"Error stopping task queue: {e}")

    # Shutdown capabilities
    try:
        from maverick_server.capabilities_integration import shutdown_capabilities
        shutdown_capabilities()
    except Exception:
        pass

    await close_redis_pool()
    logger.info("Redis connection pool closed")


def create_app(
    settings: Settings | None = None,
    testing: bool = False,
) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        settings: Optional settings override
        testing: Whether app is in testing mode

    Returns:
        Configured FastAPI application
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Stock analysis and portfolio management API",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else "/api/openapi.json",
        lifespan=lifespan,
    )

    # Store settings on app
    app.state.settings = settings
    app.state.testing = testing

    # Register capabilities BEFORE configuring routers
    # This ensures the capability registry is populated when routes are generated
    try:
        from maverick_capabilities.definitions import register_all_capabilities

        register_all_capabilities()
        logger.info("Capabilities registered for route generation")
    except Exception as e:
        logger.warning(f"Failed to register capabilities: {e}")

    # Add middleware (order matters - last added = first executed)
    _configure_middleware(app, settings)

    # Register exception handlers
    register_exception_handlers(app)

    # Include routers
    _configure_routers(app)

    return app


def _configure_middleware(app: FastAPI, settings: Settings) -> None:
    """
    Configure middleware stack.

    Note: Middleware is executed in REVERSE order of addition.
    Last added = First executed.

    Execution order will be:
    1. CORS (first - handles preflight)
    2. Request Logging (adds correlation ID)
    3. Auth (populates request.state.user)
    4. Rate Limiting (uses request.state.user for tier)
    """

    # CORS - must be first (added last)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "Sunset", "Deprecation"],
    )

    # Request logging with correlation ID
    app.add_middleware(RequestLoggingMiddleware)

    # Authentication middleware (tries each strategy in order)
    # Note: We create strategies without Redis here - they'll use app.state.redis
    auth_strategies = [
        CookieAuthStrategy(redis=None, secure=settings.is_production),
        JWTAuthStrategy(
            secret_key=settings.jwt_secret,
            redis=None,
            access_token_expire_minutes=settings.jwt_access_token_expire_minutes,
            refresh_token_expire_days=settings.jwt_refresh_token_expire_days,
        ),
        APIKeyAuthStrategy(redis=None, key_prefix=settings.api_key_prefix),
    ]
    app.add_middleware(AuthMiddleware, strategies=auth_strategies)

    # Rate limiting (if enabled) - runs after auth populates user
    if settings.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware, settings=settings)


def _configure_routers(app: FastAPI) -> None:
    """Configure API routers."""

    # Health endpoints (unversioned)
    from maverick_api.routers import health
    app.include_router(health.router, tags=["Health"])

    # Version 1 API (manual routes)
    from maverick_api.routers.v1 import router as v1_router
    app.include_router(v1_router, prefix="/api/v1")

    # Auto-generated capability routes
    try:
        from maverick_api.capabilities import (
            generate_capability_routes,
            create_async_endpoints,
        )

        # Generate REST endpoints from screening capabilities
        screening_router = generate_capability_routes(
            groups=["screening"],
            prefix="/screening",
            tags=["Screening (Auto)"],
            require_auth=True,
        )
        app.include_router(screening_router, prefix="/api/v1")

        # Generate REST endpoints from portfolio capabilities
        portfolio_router = generate_capability_routes(
            groups=["portfolio"],
            prefix="/portfolio",
            tags=["Portfolio (Auto)"],
            require_auth=True,
        )
        app.include_router(portfolio_router, prefix="/api/v1")

        # Generate REST endpoints from technical capabilities
        technical_router = generate_capability_routes(
            groups=["technical"],
            prefix="/technical",
            tags=["Technical (Auto)"],
            require_auth=True,
        )
        app.include_router(technical_router, prefix="/api/v1")

        # Async task endpoints for long-running operations
        async_router = create_async_endpoints(
            groups=["research", "risk"],
            prefix="/tasks",
            tags=["Async Tasks"],
        )
        app.include_router(async_router, prefix="/api/v1")

        logger.info("Registered capability-based routes")
    except Exception as e:
        logger.warning(f"Failed to register capability routes: {e}")


# Create default app instance
app = create_app()


__all__ = ["create_app", "app"]
