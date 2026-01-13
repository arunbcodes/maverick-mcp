"""
Health check router for system monitoring.

Provides system health, performance metrics, and diagnostics.
"""

import logging
import platform
import sys
from datetime import datetime
from typing import Any, Dict

from fastmcp import FastMCP

#from maverick_server.config import get_settings
from maverick_core.config.settings import get_settings

logger = logging.getLogger(__name__)


async def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system health status.

    This is the core logic that can be called directly from HTTP routes
    or via MCP tools.

    Returns:
        Dictionary containing system health information
    """
    settings = get_settings()

    # Check component availability
    components = {
        "database": _check_database(),
        "cache": _check_cache(settings),
        "tiingo_api": settings.has_tiingo,
        "openrouter_api": settings.has_openrouter,
        "exa_api": settings.has_exa,
    }

    # Check optional packages
    optional_packages = {
        "maverick_agents": _check_package("maverick_agents"),
        "maverick_backtest": _check_package("maverick_backtest"),
        "maverick_india": _check_package("maverick_india"),
    }

    all_required_healthy = all([
        components["database"],
        components["tiingo_api"],
    ])

    return {
        "status": "healthy" if all_required_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.machine(),
        },
        "server": {
            "name": settings.server.server_name,
            "host": settings.server.server_host,
            "port": settings.server.server_port,
            "transport": settings.server.server_transport,
        },
        "components": components,
        "optional_packages": optional_packages,
        "feature_flags": {
            "research_enabled": settings.enable_research,
            "backtesting_enabled": settings.enable_backtesting,
            "india_enabled": settings.enable_india,
        },
    }


def register_health_tools(mcp: FastMCP) -> None:
    """Register health check tools with MCP server."""

    @mcp.tool()
    async def health_get_system_status() -> Dict[str, Any]:
        """Get comprehensive system health status.

        Returns system information, component status, and configuration.

        Returns:
            Dictionary containing system health information
        """
        return await get_system_status()

    @mcp.tool()
    async def health_get_configuration() -> Dict[str, Any]:
        """Get current server configuration (non-sensitive).

        Returns:
            Dictionary containing configuration information
        """
        settings = get_settings()

        return {
            "server": {
                "name": settings.server.server_name,
                "host": settings.server.server_host,
                "port": settings.server.server_port,
                "transport": settings.server.server_transport,
                "log_level": settings.log_level,
            },
            "database": {
                "type": "sqlite" if "sqlite" in settings.database.url else "postgresql",
                "configured": bool(settings.database.url),
            },
            "cache": {
                "type": "redis" if settings.redis.host else "memory",
                "redis_configured": bool(settings.redis.host),
            },
            "apis": {
                "tiingo": settings.has_tiingo,
                "openrouter": settings.has_openrouter,
                "exa": settings.has_exa,
                "fred": bool(settings.fred_api_key),
            },
            "features": {
                "research": settings.enable_research,
                "backtesting": settings.enable_backtesting,
                "india": settings.enable_india,
            },
        }

    @mcp.tool()
    async def health_validate_configuration() -> Dict[str, Any]:
        """Validate configuration and return warnings.

        Returns:
            Dictionary containing validation results and warnings
        """
        settings = get_settings()
        warnings = settings.validate()

        return {
            "valid": len(warnings) == 0,
            "warning_count": len(warnings),
            "warnings": warnings,
            "recommendations": _get_recommendations(settings),
        }

    @mcp.tool()
    async def health_get_version_info() -> Dict[str, Any]:
        """Get version information for all components.

        Returns:
            Dictionary containing version information
        """
        versions = {
            "maverick_server": _get_version("maverick_server"),
            "maverick_core": _get_version("maverick_core"),
            "maverick_data": _get_version("maverick_data"),
        }

        # Add optional packages if available
        if _check_package("maverick_agents"):
            versions["maverick_agents"] = _get_version("maverick_agents")
        if _check_package("maverick_backtest"):
            versions["maverick_backtest"] = _get_version("maverick_backtest")
        if _check_package("maverick_india"):
            versions["maverick_india"] = _get_version("maverick_india")

        return {
            "versions": versions,
            "python": sys.version.split()[0],
            "platform": platform.system(),
        }

    logger.info("Registered health tools")


def _check_database() -> bool:
    """Check if database is accessible."""
    try:
        from maverick_data import get_db
        from sqlalchemy import text
        with next(get_db()) as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False


def _check_cache(settings) -> bool:
    """Check if cache is accessible."""
    if settings.redis.host:
        try:
            import redis
            client_params: dict[str, Any] = {
                "host": settings.redis.host,
                "port": settings.redis.port,
                "db": settings.redis.db,

            }
            if settings.redis.password and settings.redis.username:
                client_params["password"] = settings.redis.password
                client_params["username"] = settings.redis.username

            if settings.redis.ssl:
                client_params["ssl"] = True
                client_params["ssl_check_hostname"] = False

            #r = redis.Redis(host=settings.redis_host, port=settings.redis_port)
            r = redis.Redis(**client_params)
            r.ping()
            return True
        except Exception as e:
            logger.error(f"Cache check failed: {e}")
            return False
    return True  # Memory cache always available


def _check_package(package_name: str) -> bool:
    """Check if a package is importable."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def _get_version(package_name: str) -> str:
    """Get package version."""
    try:
        module = __import__(package_name)
        return getattr(module, "__version__", "unknown")
    except Exception:
        return "not installed"


def _get_recommendations(settings) -> list[str]:
    """Get configuration recommendations."""
    recommendations = []

    if not settings.redis.host:
        recommendations.append(
            "Consider enabling Redis for better caching performance"
        )

    if not settings.has_openrouter and settings.enable_research:
        recommendations.append(
            "Set OPENROUTER_API_KEY to enable AI-powered research features"
        )

    if "sqlite" in settings.database.url:
        recommendations.append(
            "Consider PostgreSQL for production workloads"
        )

    return recommendations
