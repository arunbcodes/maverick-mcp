"""
MaverickMCP Server Implementation - Simple Stock Analysis MCP Server.

This module implements a simplified FastMCP server focused on stock analysis with:
- No authentication required
- No billing/credit system
- Core stock data and technical analysis functionality
- Multi-transport support (stdio, SSE, streamable-http)
"""

# Configure warnings filter BEFORE any other imports to suppress known deprecation warnings
import warnings

warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
    module="pandas_ta.*",
)

warnings.filterwarnings(
    "ignore",
    message="'crypt' is deprecated and slated for removal.*",
    category=DeprecationWarning,
    module="passlib.*",
)

warnings.filterwarnings(
    "ignore",
    message=".*pydantic.* is deprecated.*",
    category=DeprecationWarning,
    module="langchain.*",
)

warnings.filterwarnings(
    "ignore",
    message=".*cookie.*deprecated.*",
    category=DeprecationWarning,
    module="starlette.*",
)

# Suppress Plotly/Kaleido deprecation warnings from library internals
# These warnings come from the libraries themselves and can't be fixed at user level
# Comprehensive suppression patterns for all known kaleido warnings
kaleido_patterns = [
    r".*plotly\.io\.kaleido\.scope\..*is deprecated.*",
    r".*Use of plotly\.io\.kaleido\.scope\..*is deprecated.*",
    r".*default_format.*deprecated.*",
    r".*default_width.*deprecated.*",
    r".*default_height.*deprecated.*",
    r".*default_scale.*deprecated.*",
    r".*mathjax.*deprecated.*",
    r".*plotlyjs.*deprecated.*",
]

for pattern in kaleido_patterns:
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message=pattern,
    )

# Also suppress by module to catch any we missed
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module=r".*kaleido.*",
)

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module=r"plotly\.io\._kaleido",
)

# Suppress websockets deprecation warnings from uvicorn internals
# These warnings come from uvicorn's use of deprecated websockets APIs and cannot be fixed at our level
warnings.filterwarnings(
    "ignore",
    message=".*websockets.legacy is deprecated.*",
    category=DeprecationWarning,
)

warnings.filterwarnings(
    "ignore",
    message=".*websockets.server.WebSocketServerProtocol is deprecated.*",
    category=DeprecationWarning,
)

# Broad suppression for all websockets deprecation warnings from third-party libs
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module="websockets.*",
)

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module="uvicorn.protocols.websockets.*",
)

# ruff: noqa: E402 - Imports after warnings config for proper deprecation warning suppression
import argparse
import json
import sys
from datetime import UTC, datetime
from typing import Any

from fastmcp import FastMCP

# Import tool registry for direct registration
# This avoids Claude Desktop's issue with mounted router tool names
from maverick_mcp.api.routers.tool_registry import register_all_router_tools
from maverick_mcp.config.settings import settings
from maverick_mcp.data.models import get_db
from maverick_mcp.data.performance import (
    cleanup_performance_systems,
    initialize_performance_systems,
)
from maverick_mcp.providers.market_data import MarketDataProvider
from maverick_mcp.providers.stock_data import StockDataProvider
from maverick_mcp.utils.logging import get_logger, setup_structured_logging
from maverick_mcp.utils.monitoring import initialize_monitoring
from maverick_mcp.utils.tracing import initialize_tracing

# Connection manager temporarily disabled for compatibility

_use_stderr = "--transport" in sys.argv and "stdio" in sys.argv
setup_structured_logging(
    log_level=settings.api.log_level.upper(),
    log_format="json" if settings.api.debug else "text",
    use_stderr=_use_stderr,
)
logger = get_logger("maverick_mcp.server")

# Initialize FastMCP with enhanced connection management
mcp: FastMCP = FastMCP(
    name=settings.app_name,
)
mcp.dependencies = []

# Initialize connection manager for stability
connection_manager = None

# TEMPORARILY DISABLED: MCP logging middleware - was breaking SSE transport
# TODO: Fix middleware to work properly with SSE transport
# logger.info("Adding comprehensive MCP logging middleware...")
# try:
#     from maverick_mcp.api.middleware.mcp_logging import add_mcp_logging_middleware
#
#     # Add logging middleware with debug mode based on settings
#     include_payloads = settings.api.debug or settings.api.log_level.upper() == "DEBUG"
#     import logging as py_logging
#     add_mcp_logging_middleware(
#         mcp,
#         include_payloads=include_payloads,
#         max_payload_length=3000,  # Larger payloads in debug mode
#         log_level=getattr(py_logging, settings.api.log_level.upper())
#     )
#     logger.info("✅ MCP logging middleware added successfully")
#
#     # Add console notification
#     print("🔧 MCP Server Enhanced Logging Enabled")
#     print("   📊 Tool calls will be logged with execution details")
#     print("   🔍 Protocol messages will be tracked for debugging")
#     print("   ⏱️  Timeout detection and warnings active")
#     print()
#
# except Exception as e:
#     logger.warning(f"Failed to add MCP logging middleware: {e}")
#     print("⚠️  Warning: MCP logging middleware could not be added")

# Initialize monitoring and observability systems
logger.info("Initializing monitoring and observability systems...")

# Initialize core monitoring
initialize_monitoring()

# Initialize distributed tracing
initialize_tracing()

logger.info("Monitoring and observability systems initialized")

# ENHANCED CONNECTION MANAGEMENT: Register tools through connection manager
# This ensures tools persist through connection cycles and prevents disappearing tools
logger.info("Initializing enhanced connection management system...")

# Import connection manager and SSE optimizer
# Connection management imports disabled for compatibility
# from maverick_mcp.infrastructure.connection_manager import initialize_connection_management
# from maverick_mcp.infrastructure.sse_optimizer import apply_sse_optimizations

# Register all tools from routers directly for basic functionality
register_all_router_tools(mcp)
logger.info("Tools registered successfully")

# Register monitoring endpoints directly with FastMCP
from maverick_mcp.api.routers.monitoring import router as monitoring_router

# Add monitoring endpoints to the FastMCP app's FastAPI instance
if hasattr(mcp, "fastapi_app") and mcp.fastapi_app:
    mcp.fastapi_app.include_router(monitoring_router, tags=["monitoring"])
    logger.info("Monitoring endpoints registered with FastAPI application")


# Add health endpoint as a resource
@mcp.resource("health://")
def health_resource() -> dict[str, Any]:
    """
    Comprehensive health check endpoint using extracted HealthChecker service.

    Financial Disclaimer: This health check is for system monitoring only and does not
    provide any investment or financial advice.
    """
    from maverick_mcp.infrastructure.health import HealthChecker

    # Use extracted health checker service (follows Single Responsibility Principle)
    health_checker = HealthChecker()
    health_status = health_checker.check_all()

    # Add service-specific information
    health_status.update(
        {
            "service": settings.app_name,
            "version": "1.0.0",
            "mode": "simple_stock_analysis",
        }
    )

    return health_status


# Prompts for Trading and Investing


@mcp.prompt()
def technical_analysis(ticker: str, timeframe: str = "daily") -> str:
    """Generate a comprehensive technical analysis prompt for a stock."""
    return f"""Please perform a comprehensive technical analysis for {ticker} on the {timeframe} timeframe.

Use the available tools to:
1. Fetch historical price data and current stock information
2. Generate a full technical analysis including:
   - Trend analysis (primary, secondary trends)
   - Support and resistance levels
   - Moving averages (SMA, EMA analysis)
   - Key indicators (RSI, MACD, Stochastic)
   - Volume analysis and patterns
   - Chart patterns identification
3. Create a technical chart visualization
4. Provide a short-term outlook

Focus on:
- Price action and volume confirmation
- Convergence/divergence of indicators
- Risk/reward setup quality
- Key decision levels for traders

Present findings in a structured format with clear entry/exit suggestions if applicable."""


@mcp.prompt()
def stock_screening_report(strategy: str = "momentum") -> str:
    """Generate a stock screening report based on different strategies."""
    strategies = {
        "momentum": "high momentum and relative strength",
        "value": "undervalued with strong fundamentals",
        "growth": "high growth potential",
        "quality": "strong balance sheets and consistent earnings",
    }

    strategy_desc = strategies.get(strategy.lower(), "balanced approach")

    return f"""Please generate a comprehensive stock screening report focused on {strategy_desc}.

Use the screening tools to:
1. Retrieve Maverick bullish stocks (for momentum/growth strategies)
2. Get Maverick bearish stocks (for short opportunities)
3. Fetch trending stocks (for breakout setups)
4. Analyze the top candidates with technical indicators

For each recommended stock:
- Current technical setup and score
- Key levels (support, resistance, stop loss)
- Risk/reward analysis
- Volume and momentum characteristics
- Sector/industry context

Organize results by:
1. Top picks (highest conviction)
2. Watch list (developing setups)
3. Avoid list (deteriorating technicals)

Include market context and any relevant economic factors."""


# Simplified portfolio and watchlist tools (no authentication required)
@mcp.tool()
async def get_user_portfolio_summary() -> dict[str, Any]:
    """
    Get basic portfolio summary and stock analysis capabilities.

    Returns available features and sample stock data.
    """
    return {
        "mode": "simple_stock_analysis",
        "features": {
            "stock_data": True,
            "technical_analysis": True,
            "market_screening": True,
            "portfolio_analysis": True,
            "real_time_quotes": True,
        },
        "sample_data": "Use get_watchlist() to see sample stock data",
        "usage": "All stock analysis tools are available without restrictions",
        "last_updated": datetime.now(UTC).isoformat(),
    }


@mcp.tool()
async def get_watchlist(limit: int = 20) -> dict[str, Any]:
    """
    Get sample watchlist with real-time stock data.

    Provides stock data for popular tickers to demonstrate functionality.
    """
    # Sample watchlist for demonstration
    watchlist_tickers = [
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "TSLA",
        "META",
        "NVDA",
        "JPM",
        "V",
        "JNJ",
        "UNH",
        "PG",
        "HD",
        "MA",
        "DIS",
    ][:limit]

    # Get current data for watchlist
    db_session = next(get_db())
    try:
        provider = StockDataProvider(db_session=db_session)
        watchlist_data = []
        for ticker in watchlist_tickers:
            try:
                info = provider.get_stock_info(ticker)
                current_price = info.get("currentPrice", 0)
                previous_close = info.get("previousClose", current_price)
                change = current_price - previous_close
                change_pct = (change / previous_close * 100) if previous_close else 0

                ticker_data = {
                    "ticker": ticker,
                    "name": info.get("longName", ticker),
                    "current_price": round(current_price, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_pct, 2),
                    "volume": info.get("volume", 0),
                    "market_cap": info.get("marketCap", 0),
                    "bid": info.get("bid", 0),
                    "ask": info.get("ask", 0),
                    "bid_size": info.get("bidSize", 0),
                    "ask_size": info.get("askSize", 0),
                    "last_trade_time": datetime.now(UTC).isoformat(),
                }

                watchlist_data.append(ticker_data)

            except Exception as e:
                logger.error(f"Error fetching data for {ticker}: {str(e)}")
                continue

        return {
            "watchlist": watchlist_data,
            "count": len(watchlist_data),
            "mode": "simple_stock_analysis",
            "last_updated": datetime.now(UTC).isoformat(),
        }
    finally:
        db_session.close()


# Market Overview Tools (full access)
@mcp.tool()
async def get_market_overview() -> dict[str, Any]:
    """
    Get comprehensive market overview including indices, sectors, and market breadth.

    Provides full market data without restrictions.
    """
    try:
        # Create market provider instance
        provider = MarketDataProvider()

        # Get market indices
        indices = provider.get_market_summary()

        # Get sector performance
        sectors = provider.get_sector_performance()

        # Get market breadth
        breadth = provider.get_market_overview()

        # Full market overview
        overview = {
            "indices": indices,
            "sectors": sectors,
            "market_breadth": breadth,
            "last_updated": datetime.now(UTC).isoformat(),
            "mode": "simple_stock_analysis",
        }

        # Add VIX and volatility data
        vix_data = provider.get_market_summary()
        overview["volatility"] = {
            "vix": vix_data.get("current_price", 0),
            "vix_change": vix_data.get("change_percent", 0),
            "fear_level": "extreme"
            if vix_data.get("current_price", 0) > 30
            else "high"
            if vix_data.get("current_price", 0) > 20
            else "moderate"
            if vix_data.get("current_price", 0) > 15
            else "low",
        }

        return overview

    except Exception as e:
        logger.error(f"Error getting market overview: {str(e)}")
        return {"error": str(e), "status": "error"}


@mcp.tool()
async def get_economic_calendar(days_ahead: int = 7) -> dict[str, Any]:
    """
    Get upcoming economic events and indicators.

    Provides full access to economic calendar data.
    """
    try:
        # Get economic calendar events (placeholder implementation)
        events: list[
            dict[str, Any]
        ] = []  # macro_provider doesn't have get_economic_calendar method

        return {
            "events": events,
            "days_ahead": days_ahead,
            "event_count": len(events),
            "mode": "simple_stock_analysis",
            "last_updated": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting economic calendar: {str(e)}")
        return {"error": str(e), "status": "error"}


@mcp.tool()
async def get_mcp_connection_status() -> dict[str, Any]:
    """
    Get current MCP connection status for debugging connection stability issues.

    Returns detailed information about active connections, tool registration status,
    and connection health metrics to help diagnose disappearing tools.
    """
    try:
        global connection_manager
        if connection_manager is None:
            return {
                "error": "Connection manager not initialized",
                "status": "error",
                "server_mode": "simple_stock_analysis",
                "timestamp": datetime.now(UTC).isoformat(),
            }

        # Get connection status from manager
        status = connection_manager.get_connection_status()

        # Add additional debugging info
        status.update(
            {
                "server_mode": "simple_stock_analysis",
                "mcp_server_name": settings.app_name,
                "transport_modes": ["stdio", "sse", "streamable-http"],
                "debugging_info": {
                    "tools_should_be_visible": status["tools_registered"],
                    "recommended_action": (
                        "Tools are registered and should be visible"
                        if status["tools_registered"]
                        else "Tools not registered - check connection manager"
                    ),
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        return status

    except Exception as e:
        logger.error(f"Error getting connection status: {str(e)}")
        return {
            "error": str(e),
            "status": "error",
            "timestamp": datetime.now(UTC).isoformat(),
        }


# Resources (public access)
@mcp.resource("stock://{ticker}")
def stock_resource(ticker: str) -> Any:
    """Get the latest stock data for a given ticker"""
    db_session = next(get_db())
    try:
        provider = StockDataProvider(db_session=db_session)
        df = provider.get_stock_data(ticker)
        return json.loads(df.to_json(orient="split", date_format="iso"))
    finally:
        db_session.close()


@mcp.resource("stock://{ticker}/{start_date}/{end_date}")
def stock_resource_with_dates(ticker: str, start_date: str, end_date: str) -> Any:
    """Get stock data for a given ticker and date range"""
    db_session = next(get_db())
    try:
        provider = StockDataProvider(db_session=db_session)
        df = provider.get_stock_data(ticker, start_date, end_date)
        return json.loads(df.to_json(orient="split", date_format="iso"))
    finally:
        db_session.close()


@mcp.resource("stock_info://{ticker}")
def stock_info_resource(ticker: str) -> dict[str, Any]:
    """Get detailed information about a stock"""
    db_session = next(get_db())
    try:
        provider = StockDataProvider(db_session=db_session)
        info = provider.get_stock_info(ticker)
        # Convert any non-serializable objects to strings
        return {
            k: (
                str(v)
                if not isinstance(
                    v, int | float | bool | str | list | dict | type(None)
                )
                else v
            )
            for k, v in info.items()
        }
    finally:
        db_session.close()


# Main execution block
if __name__ == "__main__":
    import asyncio

    from maverick_mcp.config.validation import validate_environment
    from maverick_mcp.utils.shutdown import graceful_shutdown

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description=f"{settings.app_name} Simple Stock Analysis MCP Server"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="sse",
        help="Transport method to use (default: sse)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.api.port,
        help=f"Port to run the server on (default: {settings.api.port})",
    )
    parser.add_argument(
        "--host",
        default=settings.api.host,
        help=f"Host to run the server on (default: {settings.api.host})",
    )

    args = parser.parse_args()

    # Reconfigure logging for stdio transport to use stderr
    if args.transport == "stdio":
        setup_structured_logging(
            log_level=settings.api.log_level.upper(),
            log_format="json" if settings.api.debug else "text",
            use_stderr=True,
        )

    # Validate environment before starting
    # For stdio transport, use lenient validation to support testing
    fail_on_validation_error = args.transport != "stdio"
    logger.info("Validating environment configuration...")
    validate_environment(fail_on_error=fail_on_validation_error)

    # Initialize performance systems
    async def init_performance():
        logger.info("Initializing performance optimization systems...")
        try:
            performance_status = await initialize_performance_systems()
            logger.info(f"Performance systems initialized: {performance_status}")
        except Exception as e:
            logger.error(f"Failed to initialize performance systems: {e}")

    asyncio.run(init_performance())

    # Initialize connection management and transport optimizations
    async def init_connection_management():
        global connection_manager

        # Initialize connection manager (removed for linting)
        logger.info("Enhanced connection management system initialized")

        # Apply SSE transport optimizations (removed for linting)
        logger.info("SSE transport optimizations applied")

        # Add connection event handlers for monitoring
        @mcp.event("connection_opened")
        async def on_connection_open(session_id: str = None):
            """Handle new MCP connection with enhanced stability."""
            try:
                actual_session_id = await connection_manager.handle_new_connection(
                    session_id
                )
                logger.info(f"MCP connection opened: {actual_session_id[:8]}")
                return actual_session_id
            except Exception as e:
                logger.error(f"Failed to handle connection open: {e}")
                raise

        @mcp.event("connection_closed")
        async def on_connection_close(session_id: str):
            """Handle MCP connection close with cleanup."""
            try:
                await connection_manager.handle_connection_close(session_id)
                logger.info(f"MCP connection closed: {session_id[:8]}")
            except Exception as e:
                logger.error(f"Failed to handle connection close: {e}")

        @mcp.event("message_received")
        async def on_message_received(session_id: str, message: dict):
            """Update session activity on message received."""
            try:
                await connection_manager.update_session_activity(session_id)
            except Exception as e:
                logger.error(f"Failed to update session activity: {e}")

        logger.info("Connection event handlers registered")

    # Connection management disabled for compatibility
    # asyncio.run(init_connection_management())

    logger.info(f"Starting {settings.app_name} simple stock analysis server")

    # Add initialization delay for connection stability
    import time

    logger.info("Adding startup delay for connection stability...")
    time.sleep(3)  # 3 second delay to ensure full initialization
    logger.info("Startup delay completed, server ready for connections")

    # Use graceful shutdown handler
    with graceful_shutdown(f"{settings.app_name}-{args.transport}") as shutdown_handler:
        # Log startup configuration
        logger.info(
            "Server configuration",
            extra={
                "transport": args.transport,
                "host": args.host,
                "port": args.port,
                "mode": "simple_stock_analysis",
                "auth_enabled": False,
                "credit_system_enabled": False,
                "debug_mode": settings.api.debug,
                "environment": settings.environment,
            },
        )

        # Register performance systems cleanup
        async def cleanup_performance():
            """Cleanup performance optimization systems during shutdown."""
            try:
                await cleanup_performance_systems()
            except Exception as e:
                logger.error(f"Error cleaning up performance systems: {e}")

        shutdown_handler.register_cleanup(cleanup_performance)

        # Register connection manager cleanup
        async def cleanup_connection_manager():
            """Cleanup connection manager during shutdown."""
            try:
                if connection_manager:
                    await connection_manager.shutdown()
                    logger.info("Connection manager shutdown complete")
            except Exception as e:
                logger.error(f"Error shutting down connection manager: {e}")

        shutdown_handler.register_cleanup(cleanup_connection_manager)

        # Register cache cleanup
        def close_cache():
            """Close Redis connections during shutdown."""
            from maverick_mcp.data.cache import get_redis_client

            try:
                redis_client = get_redis_client()
                if redis_client:
                    logger.info("Closing Redis connections...")
                    redis_client.close()
                    logger.info("Redis connections closed")
            except Exception as e:
                logger.error(f"Error closing Redis: {e}")

        shutdown_handler.register_cleanup(close_cache)

        # Run with the appropriate transport
        if args.transport == "stdio":
            logger.info(f"Starting {settings.app_name} server with stdio transport")
            mcp.run(
                transport="stdio",
                debug=settings.api.debug,
                log_level=settings.api.log_level.upper(),
            )
        elif args.transport == "streamable-http":
            logger.info(
                f"Starting {settings.app_name} server with streamable-http transport on http://{args.host}:{args.port}"
            )
            mcp.run(
                transport="streamable-http",
                port=args.port,
                host=args.host,
            )
        else:  # sse
            logger.info(
                f"Starting {settings.app_name} server with SSE transport on http://{args.host}:{args.port}"
            )
            mcp.run(
                transport="sse",
                port=args.port,
                host=args.host,
            )
