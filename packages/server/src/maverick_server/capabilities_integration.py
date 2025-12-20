"""
Capabilities integration for MCP server.

Integrates maverick-capabilities with the MCP server for:
- Audit logging of tool executions
- Capability registry initialization
- Future: capability-based tool generation
"""

import logging
import functools
from datetime import datetime, UTC
from typing import Any, Callable, TypeVar, ParamSpec
from uuid import uuid4

from maverick_capabilities import (
    get_registry,
    get_orchestrator,
    get_audit_logger,
    set_orchestrator,
    set_audit_logger,
    reset_registry,
    reset_orchestrator,
    reset_audit_logger,
)
from maverick_capabilities.definitions import register_all_capabilities
from maverick_capabilities.orchestration import (
    ServiceOrchestrator,
    OrchestratorType,
    create_orchestrator,
)
from maverick_capabilities.audit import (
    AuditEvent,
    AuditEventType,
    MemoryAuditLogger,
    create_database_audit_logger,
)

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")

# Global state for tracking initialization
_initialized = False


def initialize_capabilities(
    orchestrator_type: OrchestratorType = OrchestratorType.SERVICE,
    enable_audit: bool = True,
    audit_max_events: int = 10000,
    use_database_audit: bool = False,
    async_session_factory: Any | None = None,
) -> None:
    """
    Initialize the capabilities system.

    Should be called once during server startup.

    Args:
        orchestrator_type: Type of orchestrator to use
        enable_audit: Whether to enable audit logging
        audit_max_events: Maximum events to keep in memory audit log
        use_database_audit: Use DatabaseAuditLogger (requires async_session_factory)
        async_session_factory: Async session factory for database audit logging
    """
    global _initialized

    if _initialized:
        logger.debug("Capabilities already initialized")
        return

    # Reset any existing state
    reset_registry()
    reset_orchestrator()
    reset_audit_logger()

    # Register all capability definitions
    register_all_capabilities()
    registry = get_registry()
    logger.info(f"Registered {len(registry.list_all())} capabilities")

    # Initialize orchestrator
    orchestrator = create_orchestrator(orchestrator_type, registry=registry)
    set_orchestrator(orchestrator)
    logger.info(f"Initialized {orchestrator_type.value} orchestrator")

    # Initialize audit logger
    if enable_audit:
        if use_database_audit and async_session_factory:
            audit_logger = create_database_audit_logger(async_session_factory)
            logger.info("Initialized database audit logger (PostgreSQL)")
        else:
            audit_logger = MemoryAuditLogger(max_events=audit_max_events)
            if use_database_audit:
                logger.warning(
                    "Database audit requested but no session_factory provided. "
                    "Falling back to memory audit logger."
                )
            logger.info("Initialized memory audit logger")
        set_audit_logger(audit_logger)

    _initialized = True
    logger.info("Capabilities system initialized")


def shutdown_capabilities() -> None:
    """Shutdown the capabilities system."""
    global _initialized
    reset_registry()
    reset_orchestrator()
    reset_audit_logger()
    _initialized = False
    logger.info("Capabilities system shutdown")


def with_audit(
    capability_id: str | None = None,
    log_input: bool = True,
    log_output: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to add audit logging to a tool function.

    Usage:
        @mcp.tool()
        @with_audit("screening_get_maverick_stocks")
        async def screening_get_maverick_stocks(limit: int = 20):
            ...

    Args:
        capability_id: ID of the capability (defaults to function name)
        log_input: Whether to log input parameters
        log_output: Whether to log output data
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        cap_id = capability_id or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            execution_id = uuid4()
            audit_logger = get_audit_logger()
            start_time = datetime.now(UTC)

            # Log execution started
            await audit_logger.log(
                AuditEvent(
                    event_type=AuditEventType.EXECUTION_STARTED,
                    execution_id=execution_id,
                    capability_id=cap_id,
                    input_data=dict(kwargs) if log_input else None,
                )
            )

            try:
                result = await func(*args, **kwargs)

                # Calculate duration
                duration_ms = int(
                    (datetime.now(UTC) - start_time).total_seconds() * 1000
                )

                # Log success
                await audit_logger.log(
                    AuditEvent(
                        event_type=AuditEventType.EXECUTION_COMPLETED,
                        execution_id=execution_id,
                        capability_id=cap_id,
                        output_data=result if log_output else None,
                        duration_ms=duration_ms,
                    )
                )

                return result

            except Exception as e:
                # Calculate duration
                duration_ms = int(
                    (datetime.now(UTC) - start_time).total_seconds() * 1000
                )

                # Log failure
                await audit_logger.log(
                    AuditEvent(
                        event_type=AuditEventType.EXECUTION_FAILED,
                        execution_id=execution_id,
                        capability_id=cap_id,
                        error=str(e),
                        error_type=type(e).__name__,
                        duration_ms=duration_ms,
                    )
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # For sync functions, we can't use audit logging directly
            # (would need to run in event loop)
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def get_capability_info(capability_id: str) -> dict[str, Any] | None:
    """
    Get information about a capability.

    Args:
        capability_id: The capability ID

    Returns:
        Dictionary with capability info or None if not found
    """
    registry = get_registry()
    cap = registry.get(capability_id)
    if not cap:
        return None

    return {
        "id": cap.id,
        "title": cap.title,
        "description": cap.description,
        "group": cap.group.value,
        "execution": {
            "mode": cap.execution.mode.value,
            "timeout_seconds": cap.execution.timeout_seconds,
            "cache_enabled": cap.execution.cache_enabled,
        },
        "mcp": {
            "expose": cap.mcp.expose if cap.mcp else False,
            "tool_name": cap.mcp.tool_name if cap.mcp else None,
        } if cap.mcp else None,
        "api": {
            "expose": cap.api.expose if cap.api else False,
            "path": cap.api.path if cap.api else None,
        } if cap.api else None,
    }


def list_capabilities(
    group: str | None = None,
    mcp_only: bool = False,
    api_only: bool = False,
) -> list[dict[str, Any]]:
    """
    List all registered capabilities.

    Args:
        group: Filter by capability group
        mcp_only: Only return MCP-exposed capabilities
        api_only: Only return API-exposed capabilities

    Returns:
        List of capability info dictionaries
    """
    registry = get_registry()

    if mcp_only:
        caps = registry.list_mcp()
    elif api_only:
        caps = registry.list_api()
    else:
        caps = registry.list_all()

    if group:
        caps = [c for c in caps if c.group.value == group]

    return [
        {
            "id": c.id,
            "title": c.title,
            "group": c.group.value,
            "mcp_tool": c.mcp.tool_name if c.mcp and c.mcp.expose else None,
            "api_path": c.api.path if c.api and c.api.expose else None,
        }
        for c in caps
    ]


def get_audit_stats() -> dict[str, Any]:
    """Get audit statistics."""
    audit_logger = get_audit_logger()

    # MemoryAuditLogger has a synchronous interface for stats
    if hasattr(audit_logger, "_events"):
        events = audit_logger._events
        return {
            "total_events": len(events),
            "by_type": {},  # Would need to count
            "recent_events": len(events),
        }

    return {"total_events": 0}


async def execute_capability(
    capability_id: str,
    input_data: dict[str, Any] | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """
    Execute a capability through the orchestrator.

    This is the primary function for executing capabilities in a standardized way.
    It routes through the orchestrator which handles:
    - Timeout management
    - Error handling
    - Audit logging (if configured)
    - Future: caching, retry logic

    Args:
        capability_id: The capability to execute
        input_data: Input parameters for the capability
        user_id: Optional user ID for audit logging

    Returns:
        Dictionary with execution result

    Example:
        >>> result = await execute_capability(
        ...     "get_maverick_stocks",
        ...     {"limit": 10}
        ... )
        >>> if result["success"]:
        ...     stocks = result["data"]
    """
    from maverick_capabilities.orchestration.protocols import (
        ExecutionContext,
        ExecutionStatus,
    )

    orchestrator = get_orchestrator()
    input_data = input_data or {}

    # Create execution context
    context = ExecutionContext(
        capability_id=capability_id,
        user_id=user_id,
    )

    # Execute through orchestrator
    result = await orchestrator.execute(capability_id, input_data, context)

    # Convert to standard response format
    if result.status == ExecutionStatus.COMPLETED:
        return {
            "success": True,
            "data": result.result,
            "execution_id": str(result.execution_id),
            "duration_ms": result.duration_ms,
        }
    else:
        return {
            "success": False,
            "error": result.error,
            "error_type": result.error_type,
            "execution_id": str(result.execution_id),
            "status": result.status.value,
        }


def with_orchestrator(
    capability_id: str,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to route tool execution through the orchestrator.

    This decorator replaces direct service calls with orchestrator-based
    execution, enabling:
    - Centralized timeout handling
    - Consistent error handling
    - Execution tracing
    - Future: capability-based routing to different backends

    Usage:
        @mcp.tool()
        @with_orchestrator("get_maverick_stocks")
        async def screening_get_maverick_stocks(limit: int = 20):
            # The body is ignored when using orchestrator
            pass

    Note:
        When using @with_orchestrator, the function body is not executed.
        Instead, execution is delegated to the orchestrator which calls
        the configured service method for the capability.

    Args:
        capability_id: The capability ID to execute
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Execute through orchestrator
            result = await execute_capability(capability_id, dict(kwargs))

            if result["success"]:
                return result["data"]  # type: ignore
            else:
                # Return error in standard format for MCP tools
                return {  # type: ignore
                    "error": result.get("error", "Unknown error"),
                    "error_type": result.get("error_type", "ExecutionError"),
                    "execution_id": result.get("execution_id"),
                }

        return async_wrapper  # type: ignore

    return decorator


def register_service_instance(service_name: str, instance: Any) -> None:
    """
    Register a service instance with the orchestrator.

    This allows the orchestrator to use dependency-injected service instances
    rather than instantiating services directly.

    Args:
        service_name: Name of the service class (e.g., "ScreeningService")
        instance: The service instance to use

    Example:
        >>> from maverick_services import ScreeningService
        >>> service = ScreeningService(repository=my_repo)
        >>> register_service_instance("ScreeningService", service)
    """
    orchestrator = get_orchestrator()
    if hasattr(orchestrator, "register_service"):
        orchestrator.register_service(service_name, instance)
    else:
        logger.warning(
            f"Orchestrator does not support service registration: {type(orchestrator)}"
        )


__all__ = [
    "initialize_capabilities",
    "shutdown_capabilities",
    "with_audit",
    "with_orchestrator",
    "execute_capability",
    "register_service_instance",
    "get_capability_info",
    "list_capabilities",
    "get_audit_stats",
]
