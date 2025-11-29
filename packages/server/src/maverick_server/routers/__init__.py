"""
MCP Server Routers.

Domain-specific routers that organize MCP tools into logical groups.
Each router is a thin wrapper around the corresponding maverick package.
"""

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

__all__ = [
    # Core routers (always available)
    "register_technical_tools",
    "register_screening_tools",
    "register_portfolio_tools",
    "register_data_tools",
    "register_health_tools",
    # Optional routers (require optional dependencies)
    "register_research_tools",
    "register_backtesting_tools",
    "register_india_tools",
    "register_concall_tools",
    "register_agents_tools",
]


def register_all_tools(mcp) -> dict[str, bool]:
    """Register all available tools with the MCP server.

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
        # Optional routers
        ("research", register_research_tools),
        ("backtesting", register_backtesting_tools),
        ("india", register_india_tools),
        ("concall", register_concall_tools),
        ("agents", register_agents_tools),
    ]

    for name, register_fn in routers:
        try:
            register_fn(mcp)
            results[name] = True
        except Exception as e:
            results[name] = False
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to register {name} tools: {e}"
            )

    return results
