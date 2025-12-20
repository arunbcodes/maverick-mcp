"""
MCP Server Routers.

Domain-specific routers that organize MCP tools into logical groups.
Each router is a thin wrapper around the corresponding maverick package.

Supports two modes:
1. Manual registration: Traditional approach with explicit tool definitions
2. Auto-generation: Generate tools from capability definitions (DRY)
"""

import logging

from maverick_server.routers.technical import register_technical_tools
from maverick_server.routers.screening import register_screening_tools
from maverick_server.routers.portfolio import register_portfolio_tools
from maverick_server.routers.data import register_data_tools
from maverick_server.routers.research import register_research_tools
from maverick_server.routers.backtesting import register_backtesting_tools
from maverick_server.routers.india import register_india_tools
from maverick_server.routers.health import register_health_tools
from maverick_server.routers.concall import register_concall_tools
from maverick_server.routers.agents import register_agents_tools
from maverick_server.routers.capabilities import register_capabilities_tools

logger = logging.getLogger(__name__)

# Optional crypto router (standalone package)
try:
    from maverick_crypto.routers import register_crypto_tools
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False
    register_crypto_tools = None

__all__ = [
    # Core routers (always available)
    "register_technical_tools",
    "register_screening_tools",
    "register_portfolio_tools",
    "register_data_tools",
    "register_health_tools",
    "register_capabilities_tools",
    # Optional routers (require optional dependencies)
    "register_research_tools",
    "register_backtesting_tools",
    "register_india_tools",
    "register_concall_tools",
    "register_agents_tools",
    "register_crypto_tools",
    # Registration functions
    "register_all_tools",
    "register_auto_generated_tools",
]


def register_all_tools(mcp) -> dict[str, bool]:
    """Register all available tools with the MCP server (manual mode).

    This is the traditional approach where each router explicitly defines
    its tools. Use register_auto_generated_tools() for capability-based
    generation.

    Args:
        mcp: FastMCP server instance

    Returns:
        Dictionary mapping router name to success status
    """
    results = {}

    # Core routers (always available with core + data)
    routers = [
        ("technical", register_technical_tools),
        ("screening", register_screening_tools),
        ("portfolio", register_portfolio_tools),
        ("data", register_data_tools),
        ("health", register_health_tools),
        ("capabilities", register_capabilities_tools),
        # Optional routers
        ("research", register_research_tools),
        ("backtesting", register_backtesting_tools),
        ("india", register_india_tools),
        ("concall", register_concall_tools),
        ("agents", register_agents_tools),
    ]

    # Add crypto router if available (standalone package)
    if _HAS_CRYPTO and register_crypto_tools is not None:
        routers.append(("crypto", register_crypto_tools))

    for name, register_fn in routers:
        try:
            register_fn(mcp)
            results[name] = True
        except Exception as e:
            results[name] = False
            logger.warning(f"Failed to register {name} tools: {e}")

    return results


def register_auto_generated_tools(
    mcp,
    groups: list[str] | None = None,
    include_manual: list[str] | None = None,
) -> dict[str, int | bool]:
    """Register tools using auto-generation from capability definitions.

    This is the DRY approach where tools are automatically created from
    capability definitions in the registry. Each capability with
    mcp.expose=True gets a corresponding MCP tool.

    Args:
        mcp: FastMCP server instance
        groups: Capability groups to auto-generate (None = all)
                Options: screening, portfolio, technical, research, risk
        include_manual: Manual routers to include alongside auto-generated
                       Options: health, capabilities, data, crypto

    Returns:
        Dictionary with:
        - "auto_generated": Number of auto-generated tools
        - Router names: True/False for manual routers

    Example:
        >>> # Auto-generate all capability-based tools + health/capabilities
        >>> results = register_auto_generated_tools(
        ...     mcp,
        ...     groups=["screening", "portfolio", "technical", "research", "risk"],
        ...     include_manual=["health", "capabilities"],
        ... )
        >>> print(f"Auto-generated {results['auto_generated']} tools")
    """
    from maverick_server.tool_generator import generate_mcp_tools

    results = {}

    # Auto-generate tools from capability definitions
    try:
        count = generate_mcp_tools(mcp, groups=groups)
        results["auto_generated"] = count
        logger.info(f"Auto-generated {count} MCP tools from capabilities")
    except Exception as e:
        results["auto_generated"] = 0
        logger.error(f"Failed to auto-generate tools: {e}")

    # Include specified manual routers (for tools not in capability registry)
    manual_routers = {
        "health": register_health_tools,
        "capabilities": register_capabilities_tools,
        "data": register_data_tools,
        "crypto": register_crypto_tools if _HAS_CRYPTO else None,
    }

    include_manual = include_manual or ["health", "capabilities"]

    for name in include_manual:
        register_fn = manual_routers.get(name)
        if register_fn is None:
            continue
        try:
            register_fn(mcp)
            results[name] = True
        except Exception as e:
            results[name] = False
            logger.warning(f"Failed to register {name} tools: {e}")

    return results
