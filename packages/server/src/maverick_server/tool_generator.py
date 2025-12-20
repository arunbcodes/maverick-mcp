"""
Auto-generate MCP tools from capability definitions.

This module enables DRY tool development by automatically creating
MCP tool handlers from the capability registry. Each capability
with mcp.expose=True gets a corresponding tool.

Benefits:
- Single source of truth: capabilities define behavior once
- Consistent audit logging via with_audit
- Automatic orchestrator routing
- Parameter extraction from service method signatures
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, get_type_hints

from fastmcp import FastMCP

from maverick_capabilities import get_registry
from maverick_capabilities.models import Capability, ExecutionMode
from maverick_server.capabilities_integration import (
    with_audit,
    execute_capability,
)

logger = logging.getLogger(__name__)


def generate_mcp_tools(
    mcp: FastMCP,
    capability_ids: list[str] | None = None,
    groups: list[str] | None = None,
    exclude: list[str] | None = None,
) -> int:
    """
    Generate MCP tools from capability definitions.

    For each capability with mcp.expose=True, creates an MCP tool
    that routes execution through the orchestrator with audit logging.

    Args:
        mcp: FastMCP instance to register tools with
        capability_ids: Specific capabilities to register (None = all MCP-exposed)
        groups: Filter by capability groups
        exclude: Capability IDs to skip

    Returns:
        Number of tools generated

    Example:
        >>> from fastmcp import FastMCP
        >>> mcp = FastMCP("maverick")
        >>> count = generate_mcp_tools(mcp, groups=["screening"])
        >>> print(f"Generated {count} tools")
    """
    registry = get_registry()
    exclude = set(exclude or [])
    generated = 0

    # Get capabilities to process
    if capability_ids:
        caps = [registry.get(cap_id) for cap_id in capability_ids]
        caps = [c for c in caps if c is not None]
    else:
        caps = registry.list_mcp()

    # Filter by groups if specified
    if groups:
        caps = [c for c in caps if c.group.value in groups]

    # Generate tools
    for cap in caps:
        if cap.id in exclude:
            continue

        if not cap.mcp or not cap.mcp.expose:
            continue

        try:
            _create_tool_for_capability(mcp, cap)
            generated += 1
        except Exception as e:
            logger.error(f"Failed to generate tool for {cap.id}: {e}")

    logger.info(f"Generated {generated} MCP tools from capability definitions")
    return generated


def _create_tool_for_capability(mcp: FastMCP, cap: Capability) -> None:
    """
    Create a single MCP tool for a capability.

    The generated tool:
    1. Extracts parameters from the capability's service method
    2. Routes execution through the orchestrator
    3. Applies audit logging
    4. Handles sync/async/streaming modes
    """
    tool_name = cap.mcp.tool_name if cap.mcp else f"{cap.group.value}_{cap.id}"
    description = (
        cap.mcp.description_override if cap.mcp and cap.mcp.description_override else cap.description
    )

    # Get parameter info from service method
    params = _extract_parameters(cap)

    if cap.execution.mode == ExecutionMode.ASYNC:
        # Async capability - submit to task queue
        handler = _create_async_tool_handler(cap, tool_name)
    elif cap.execution.mode == ExecutionMode.STREAMING:
        # Streaming capability - return generator
        handler = _create_streaming_tool_handler(cap, tool_name)
    else:
        # Sync capability - execute directly
        handler = _create_sync_tool_handler(cap, tool_name)

    # Apply audit decorator
    if cap.audit and cap.audit.log:
        handler = with_audit(
            cap.id,
            log_input=cap.audit.log_input,
            log_output=cap.audit.log_output,
        )(handler)

    # Set function metadata
    handler.__name__ = tool_name
    handler.__doc__ = description

    # Register with MCP
    mcp.tool()(handler)

    logger.debug(f"Generated tool: {tool_name} for capability: {cap.id}")


def _extract_parameters(cap: Capability) -> dict[str, dict[str, Any]]:
    """
    Extract parameter definitions from a capability's service method.

    Returns a dict of parameter name -> {type, default, description}
    """
    params = {}

    try:
        # Get the method
        if cap.handler:
            method = cap.handler
        else:
            method = getattr(cap.service_class, cap.method_name)

        # Get signature
        sig = inspect.signature(method)

        # Get type hints
        try:
            hints = get_type_hints(method)
        except Exception:
            hints = {}

        # Extract parameters
        for name, param in sig.parameters.items():
            if name == "self":
                continue

            param_info = {
                "name": name,
                "type": hints.get(name, Any),
                "required": param.default == inspect.Parameter.empty,
            }

            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default

            params[name] = param_info

    except Exception as e:
        logger.warning(f"Could not extract parameters for {cap.id}: {e}")

    return params


def _get_simple_type_name(type_hint: Any) -> str:
    """Get a simple type name suitable for function signatures.

    Maps complex types to simple ones that work in exec() context.
    """
    if type_hint is None:
        return "str"

    type_name = getattr(type_hint, "__name__", None)
    if type_name:
        # Map to basic types that are always available
        if type_name in ("int", "str", "float", "bool", "list", "dict"):
            return type_name
        # Any other type becomes str (will be parsed by service)
        return "str"

    # Handle typing module types
    origin = getattr(type_hint, "__origin__", None)
    if origin is list:
        return "list"
    if origin is dict:
        return "dict"

    return "str"


def _create_sync_tool_handler(cap: Capability, tool_name: str) -> Callable:
    """Create a synchronous tool handler with explicit parameters.

    FastMCP requires explicit parameters (not **kwargs), so we dynamically
    create a function with the correct signature based on the capability's
    service method.
    """
    cap_id = cap.id
    params = _extract_parameters(cap)

    # Build parameter list for function signature
    param_parts = []
    param_names = []
    for name, info in params.items():
        param_names.append(name)
        type_name = _get_simple_type_name(info.get("type"))

        if info.get("required", True):
            param_parts.append(f"{name}: {type_name}")
        else:
            default = info.get("default")
            if isinstance(default, str):
                param_parts.append(f'{name}: {type_name} = "{default}"')
            elif default is None:
                param_parts.append(f"{name}: {type_name} = None")
            else:
                param_parts.append(f"{name}: {type_name} = {default!r}")

    param_str = ", ".join(param_parts) if param_parts else ""
    kwargs_collect = ", ".join(f'"{n}": {n}' for n in param_names)

    # Generate function code
    func_code = f'''
async def {tool_name}({param_str}) -> dict:
    """Auto-generated tool for {cap.title}."""
    kwargs = {{{kwargs_collect}}}
    result = await _execute('{cap_id}', kwargs)
    if result.get("success"):
        return result.get("data", {{}})
    return {{"error": result.get("error"), "error_type": result.get("error_type")}}
'''

    # Execute to create function
    local_ns: dict[str, Any] = {"_execute": execute_capability}
    try:
        exec(func_code, local_ns)
        return local_ns[tool_name]
    except Exception as e:
        logger.warning(f"Failed to create typed handler for {cap_id}: {e}")
        # Fallback to simple handler (may not work with all MCP clients)
        async def fallback_handler() -> dict[str, Any]:
            result = await execute_capability(cap_id, {})
            if result.get("success"):
                return result.get("data", {})
            return {"error": result.get("error")}
        fallback_handler.__name__ = tool_name
        return fallback_handler


def _create_async_tool_handler(cap: Capability, tool_name: str) -> Callable:
    """Create an async tool handler that uses task queue with explicit parameters."""
    cap_id = cap.id
    params = _extract_parameters(cap)

    # Build parameter list
    param_parts = []
    param_names = []
    for name, info in params.items():
        param_names.append(name)
        type_name = _get_simple_type_name(info.get("type"))

        if info.get("required", True):
            param_parts.append(f"{name}: {type_name}")
        else:
            default = info.get("default")
            if isinstance(default, str):
                param_parts.append(f'{name}: {type_name} = "{default}"')
            elif default is None:
                param_parts.append(f"{name}: {type_name} = None")
            else:
                param_parts.append(f"{name}: {type_name} = {default!r}")

    param_str = ", ".join(param_parts) if param_parts else ""
    kwargs_collect = ", ".join(f'"{n}": {n}' for n in param_names)

    # Store capability info for the handler
    cap_title = cap.title
    cap_execution = cap.execution

    async def _async_impl(kwargs: dict) -> dict[str, Any]:
        """Implementation for async handler."""
        try:
            from maverick_api.capabilities.async_endpoints import get_task_queue
            from maverick_capabilities.tasks.protocols import TaskConfig

            queue = get_task_queue()
            config = TaskConfig(
                queue=cap_execution.queue,
                timeout_seconds=cap_execution.timeout_seconds,
                max_retries=cap_execution.max_retries,
            )

            result = await queue.enqueue(cap_id, kwargs, config)

            return {
                "task_id": str(result.task_id),
                "status": result.status.value,
                "message": f"Task submitted for {cap_title}. Use system_get_task_status to check progress.",
            }
        except RuntimeError:
            logger.warning(f"Task queue not available, executing {cap_id} synchronously")
            result = await execute_capability(cap_id, kwargs)
            if result.get("success"):
                return result.get("data", {})
            return {"error": result.get("error")}

    # Generate function code
    func_code = f'''
async def {tool_name}({param_str}) -> dict:
    """Auto-generated async tool for {cap_title}. Returns task ID for polling."""
    kwargs = {{{kwargs_collect}}}
    return await _impl(kwargs)
'''

    local_ns: dict[str, Any] = {"_impl": _async_impl}
    try:
        exec(func_code, local_ns)
        return local_ns[tool_name]
    except Exception as e:
        logger.warning(f"Failed to create async handler for {cap_id}: {e}")
        async def fallback() -> dict[str, Any]:
            return await _async_impl({})
        fallback.__name__ = tool_name
        return fallback


def _create_streaming_tool_handler(cap: Capability, tool_name: str) -> Callable:
    """Create a streaming tool handler with explicit parameters."""
    cap_id = cap.id
    params = _extract_parameters(cap)

    # Build parameter list
    param_parts = []
    param_names = []
    for name, info in params.items():
        param_names.append(name)
        type_name = _get_simple_type_name(info.get("type"))

        if info.get("required", True):
            param_parts.append(f"{name}: {type_name}")
        else:
            default = info.get("default")
            if isinstance(default, str):
                param_parts.append(f'{name}: {type_name} = "{default}"')
            elif default is None:
                param_parts.append(f"{name}: {type_name} = None")
            else:
                param_parts.append(f"{name}: {type_name} = {default!r}")

    param_str = ", ".join(param_parts) if param_parts else ""
    kwargs_collect = ", ".join(f'"{n}": {n}' for n in param_names)

    # Generate function code
    func_code = f'''
async def {tool_name}({param_str}) -> dict:
    """Auto-generated streaming tool for {cap.title}."""
    kwargs = {{{kwargs_collect}}}
    result = await _execute('{cap_id}', kwargs)
    if result.get("success"):
        return result.get("data", {{}})
    return {{"error": result.get("error")}}
'''

    local_ns: dict[str, Any] = {"_execute": execute_capability}
    try:
        exec(func_code, local_ns)
        return local_ns[tool_name]
    except Exception as e:
        logger.warning(f"Failed to create streaming handler for {cap_id}: {e}")
        async def fallback() -> dict[str, Any]:
            result = await execute_capability(cap_id, {})
            if result.get("success"):
                return result.get("data", {})
            return {"error": result.get("error")}
        fallback.__name__ = tool_name
        return fallback


def get_generated_tool_manifest() -> dict[str, Any]:
    """
    Get a manifest of all auto-generated tools.

    Useful for debugging and documentation.
    """
    registry = get_registry()
    caps = registry.list_mcp()

    manifest = {
        "total_capabilities": len(caps),
        "tools": [],
    }

    for cap in caps:
        if not cap.mcp or not cap.mcp.expose:
            continue

        tool_info = {
            "id": cap.id,
            "tool_name": cap.mcp.tool_name,
            "title": cap.title,
            "description": cap.description[:100] + "..." if len(cap.description) > 100 else cap.description,
            "group": cap.group.value,
            "mode": cap.execution.mode.value,
            "audit": cap.audit.log if cap.audit else False,
            "parameters": list(_extract_parameters(cap).keys()),
        }
        manifest["tools"].append(tool_info)

    return manifest


__all__ = [
    "generate_mcp_tools",
    "get_generated_tool_manifest",
]
