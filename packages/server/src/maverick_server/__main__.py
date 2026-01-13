"""
Entry point for running maverick-server as a module.

Usage:
    python -m maverick_server [--transport TYPE] [--port PORT] [--host HOST]

Transports:
    stdio         - Standard I/O (default for Claude Desktop STDIO mode)
    sse           - Server-Sent Events (default, recommended for Claude Desktop)
    streamable-http - HTTP with streaming support

Tool Registration:
    --auto-gen    - Use capability-based auto-generation (DRY mode)
    (default)     - Use manual tool registration
"""

from __future__ import annotations

import argparse
import logging
import sys

from maverick_server import MaverickServer, configure_warnings
#from maverick_server.config import get_settings
from maverick_core.config.settings import get_settings
from maverick_server.routers import register_all_tools, register_auto_generated_tools
from maverick_server.capabilities_integration import (
    initialize_capabilities,
    shutdown_capabilities,
)


def main() -> int:
    """Run the MaverickMCP server."""
    settings = get_settings()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="MaverickMCP - Stock Analysis MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=settings.server.server_transport,
        help=f"Transport type (default: {settings.server.server_transport})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.server.server_port,
        help=f"Server port (default: {settings.server.server_port})",
    )
    parser.add_argument(
        "--host",
        default=settings.server.server_host,
        help=f"Server host (default: {settings.server.server_host})",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=settings.log_level,
        help=f"Logging level (default: {settings.log_level})",
    )
    parser.add_argument(
        "--name",
        default=settings.server.server_name,
        help=f"Server name (default: {settings.server.server_name})",
    )
    parser.add_argument(
        "--auto-gen",
        action="store_true",
        default=False,
        help="Use capability-based tool auto-generation (DRY mode)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Configure warnings to filter noisy deprecations
    configure_warnings()

    # Validate configuration
    warnings = settings.validate()
    for warning in warnings:
        logger.warning(warning)

    # Initialize capabilities system (registry, orchestrator, audit)
    try:
        initialize_capabilities()
        logger.info("Capabilities system initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize capabilities: {e}")

    # Create server
    server = MaverickServer(name=args.name)
    logger.info(f"Created MaverickMCP server: {args.name}")

    # Register tools (auto-gen or manual mode)
    if args.auto_gen:
        logger.info("Using capability-based auto-generation (DRY mode)")
        results = register_auto_generated_tools(
            server.mcp,
            groups=["screening", "portfolio", "technical", "research", "risk"],
            include_manual=["health", "capabilities", "data"],
        )
        auto_count = results.get("auto_generated", 0)
        manual_count = sum(1 for k, v in results.items() if k != "auto_generated" and v)
        logger.info(f"Registered {auto_count} auto-generated tools + {manual_count} manual routers")
    else:
        logger.info("Using manual tool registration")
        results = register_all_tools(server.mcp)
        successful = sum(1 for v in results.values() if v)
        total = len(results)
        logger.info(f"Registered {successful}/{total} tool groups")

    for name, success in results.items():
        if name == "auto_generated":
            continue
        if success:
            logger.debug(f"  ✓ {name}")
        else:
            logger.warning(f"  ✗ {name} (failed)")

    logger.info("Tools registered successfully")

    # Run server
    logger.info(f"Starting server on {args.host}:{args.port} ({args.transport})")

    try:
        server.run(
            transport=args.transport,
            host=args.host,
            port=args.port,
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Server error: {e}")
        return 1
    finally:
        # Cleanup capabilities system
        try:
            shutdown_capabilities()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
