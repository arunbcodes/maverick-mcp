"""
Capabilities router - MCP tools for capability introspection.

Exposes tools to list capabilities, get audit stats, and
query execution history. Also provides orchestrator-based
capability execution with rate limiting.
"""

import logging
import time
from collections import defaultdict
from typing import Any

from fastmcp import FastMCP

from maverick_server.capabilities_integration import (
    list_capabilities,
    get_capability_info,
    get_audit_stats,
    execute_capability,
    with_audit,
)
from maverick_capabilities import get_audit_logger

logger = logging.getLogger(__name__)


# Rate limiter for system_execute_capability
class RateLimiter:
    """Simple in-memory rate limiter with sliding window."""

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        per_capability_limit: int = 20,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.per_capability_limit = per_capability_limit
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._capability_requests: dict[str, dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def _cleanup_old(self, timestamps: list[float], now: float) -> list[float]:
        """Remove timestamps outside the window."""
        cutoff = now - self.window_seconds
        return [t for t in timestamps if t > cutoff]

    def check(
        self,
        user_id: str,
        capability_id: str | None = None,
    ) -> tuple[bool, str | None]:
        """
        Check if request is allowed under rate limits.

        Returns:
            Tuple of (allowed, error_message)
        """
        now = time.time()

        # Clean up old requests
        self._requests[user_id] = self._cleanup_old(self._requests[user_id], now)

        # Check global limit for user
        if len(self._requests[user_id]) >= self.max_requests:
            return False, f"Rate limit exceeded: max {self.max_requests} requests per {self.window_seconds}s"

        # Check per-capability limit if specified
        if capability_id:
            cap_requests = self._capability_requests[user_id]
            cap_requests[capability_id] = self._cleanup_old(
                cap_requests[capability_id], now
            )

            if len(cap_requests[capability_id]) >= self.per_capability_limit:
                return False, (
                    f"Rate limit exceeded for {capability_id}: "
                    f"max {self.per_capability_limit} requests per {self.window_seconds}s"
                )

        return True, None

    def record(self, user_id: str, capability_id: str | None = None) -> None:
        """Record a request."""
        now = time.time()
        self._requests[user_id].append(now)
        if capability_id:
            self._capability_requests[user_id][capability_id].append(now)


# Allowlist of capabilities that can be executed via system_execute_capability
# Empty list means all capabilities are allowed
ALLOWED_CAPABILITIES: set[str] = set()

# Denylist of sensitive capabilities that should never be executed via generic endpoint
DENIED_CAPABILITIES: set[str] = {
    "admin_clear_cache",
    "admin_reset_database",
    "admin_delete_user",
    "system_shutdown",
}

# Global rate limiter instance
_rate_limiter = RateLimiter(
    max_requests=100,  # 100 requests per minute per user
    window_seconds=60,
    per_capability_limit=20,  # 20 requests per minute per capability per user
)


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

    @mcp.tool()
    @with_audit("system_execute_capability")
    async def system_execute_capability(
        capability_id: str,
        parameters: dict[str, Any] | None = None,
        user_id: str = "mcp_anonymous",
    ) -> dict[str, Any]:
        """Execute a capability through the orchestrator.

        This is the universal execution endpoint that routes any capability
        through the orchestrator, enabling:
        - Centralized timeout handling
        - Consistent error handling
        - Execution tracing
        - Rate limiting (100 req/min global, 20 req/min per capability)
        - Access control (allowlist/denylist)

        Security:
        - Rate limited to prevent abuse
        - Certain admin capabilities are blocked
        - All executions are audit logged

        Args:
            capability_id: The capability to execute (e.g., "get_maverick_stocks")
            parameters: Input parameters for the capability (optional)
            user_id: User identifier for rate limiting (default: "mcp_anonymous")

        Returns:
            Dictionary containing execution result or error

        Examples:
            >>> system_execute_capability("get_maverick_stocks", {"limit": 10})
            >>> system_execute_capability("get_rsi_analysis", {"ticker": "AAPL"})
        """
        # Access control: check denylist
        if capability_id in DENIED_CAPABILITIES:
            logger.warning(
                f"Blocked access to denied capability: {capability_id} by {user_id}"
            )
            return {
                "success": False,
                "error": f"Capability '{capability_id}' cannot be executed through this endpoint",
                "error_type": "AccessDenied",
            }

        # Access control: check allowlist (if configured)
        if ALLOWED_CAPABILITIES and capability_id not in ALLOWED_CAPABILITIES:
            logger.warning(
                f"Capability not in allowlist: {capability_id} by {user_id}"
            )
            return {
                "success": False,
                "error": f"Capability '{capability_id}' is not available through this endpoint",
                "error_type": "NotAllowed",
            }

        # Rate limiting
        allowed, error_msg = _rate_limiter.check(user_id, capability_id)
        if not allowed:
            logger.warning(f"Rate limit hit: {user_id} for {capability_id}")
            return {
                "success": False,
                "error": error_msg,
                "error_type": "RateLimitExceeded",
            }

        # Record the request
        _rate_limiter.record(user_id, capability_id)

        try:
            result = await execute_capability(
                capability_id=capability_id,
                input_data=parameters or {},
                user_id=user_id,
            )
            return result
        except Exception as e:
            logger.error(f"Error executing capability {capability_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    logger.info("Registered capabilities introspection tools")
