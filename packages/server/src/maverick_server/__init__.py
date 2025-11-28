"""
Maverick MCP Server Package.

FastMCP-based server providing stock analysis tools for Claude Desktop.
This is a thin orchestration layer that combines all other Maverick packages.
"""

# Core server components
from maverick_server.core import (
    FastMCPProtocol,
    MaverickServer,
    configure_warnings,
    create_server,
)

# Tool registry infrastructure
from maverick_server.tools import (
    ToolRegistrar,
    ToolRegistry,
    create_tool_wrapper,
    get_default_registry,
    register_tool_group,
    reset_default_registry,
)

__version__ = "0.1.0"

__all__ = [
    # Core server
    "MaverickServer",
    "FastMCPProtocol",
    "create_server",
    "configure_warnings",
    # Tool registry
    "ToolRegistry",
    "ToolRegistrar",
    "create_tool_wrapper",
    "register_tool_group",
    "get_default_registry",
    "reset_default_registry",
    # Version
    "__version__",
]
