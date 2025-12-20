"""
Capabilities router - MCP tools for capability introspection.

Exposes tools to list capabilities, get audit stats, and
query execution history.
"""

import logging
from typing import Any

from fastmcp import FastMCP

from maverick_server.capabilities_integration import (
    list_capabilities,
    get_capability_info,
    get_audit_stats,
)
from maverick_capabilities import get_audit_logger

logger = logging.getLogger(__name__)


def register_capabilities_tools(mcp: FastMCP) -> None:
    """Register capability introspection tools with MCP server."""

    @mcp.tool()
    async def system_list_capabilities(
        group: str | None = None,
        mcp_only: bool = False,
    ) -> dict[str, Any]:
        """List all registered capabilities in the system.

        Returns information about available capabilities, their groups,
        and whether they are exposed as MCP tools or API endpoints.

        Args:
            group: Filter by capability group (screening, portfolio, technical, research, risk)
            mcp_only: If True, only return MCP-exposed capabilities

        Returns:
            Dictionary containing list of capabilities with their metadata
        """
        try:
            capabilities = list_capabilities(group=group, mcp_only=mcp_only)
            return {
                "count": len(capabilities),
                "filter": {"group": group, "mcp_only": mcp_only},
                "capabilities": capabilities,
            }
        except Exception as e:
            logger.error(f"Error listing capabilities: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def system_get_capability(capability_id: str) -> dict[str, Any]:
        """Get detailed information about a specific capability.

        Args:
            capability_id: The unique identifier of the capability

        Returns:
            Dictionary containing capability details including execution config,
            MCP config, and API config
        """
        try:
            info = get_capability_info(capability_id)
            if info is None:
                return {"error": f"Capability '{capability_id}' not found"}
            return {"capability": info}
        except Exception as e:
            logger.error(f"Error getting capability {capability_id}: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def system_get_audit_stats() -> dict[str, Any]:
        """Get audit statistics for tool executions.

        Returns statistics about recent tool executions including
        total events, events by type, and events by capability.

        Returns:
            Dictionary containing audit statistics
        """
        try:
            stats = get_audit_stats()
            return {"audit_stats": stats}
        except Exception as e:
            logger.error(f"Error getting audit stats: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def system_get_recent_executions(
        capability_id: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Get recent tool execution events from the audit log.

        Args:
            capability_id: Filter by specific capability (optional)
            limit: Maximum number of events to return (default: 10)

        Returns:
            Dictionary containing recent execution events
        """
        try:
            audit_logger = get_audit_logger()
            events = await audit_logger.query(
                capability_id=capability_id,
                limit=limit,
            )
            return {
                "count": len(events),
                "filter": {"capability_id": capability_id},
                "events": [e.to_dict() for e in events],
            }
        except Exception as e:
            logger.error(f"Error getting recent executions: {e}")
            return {"error": str(e)}

    logger.info("Registered capabilities introspection tools")
