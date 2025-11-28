"""
Tool Registry - Central tool registration infrastructure for MaverickMCP.

This module provides the patterns and utilities for registering MCP tools
with the FastMCP server. It serves as the orchestration layer that connects
all Maverick packages to the MCP server.
"""

import logging
from typing import Any, Callable, Protocol

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


class ToolRegistrar(Protocol):
    """Protocol for tool registration functions."""

    def __call__(self, mcp: FastMCP) -> None:
        """Register tools with the MCP server."""
        ...


class ToolRegistry:
    """
    Central registry for MCP tools.

    Manages tool registration and provides utilities for organizing tools
    into logical groups.
    """

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._registrars: list[tuple[str, ToolRegistrar]] = []
        self._registered: set[str] = set()

    def add_registrar(self, name: str, registrar: ToolRegistrar) -> None:
        """
        Add a tool registrar to the registry.

        Args:
            name: Name of the tool group
            registrar: Function that registers tools with FastMCP
        """
        self._registrars.append((name, registrar))

    def register_all(self, mcp: FastMCP) -> dict[str, bool]:
        """
        Register all tools with the MCP server.

        Args:
            mcp: FastMCP server instance

        Returns:
            Dictionary mapping tool group names to registration success
        """
        results: dict[str, bool] = {}

        logger.info("Starting tool registration process...")

        for name, registrar in self._registrars:
            try:
                registrar(mcp)
                results[name] = True
                self._registered.add(name)
                logger.info(f"✓ {name} tools registered successfully")
            except Exception as e:
                results[name] = False
                logger.error(f"✗ Failed to register {name} tools: {e}")

        logger.info("Tool registration process completed")
        return results

    @property
    def registered_groups(self) -> set[str]:
        """Get set of successfully registered tool groups."""
        return self._registered.copy()


def create_tool_wrapper(
    name: str,
    func: Callable[..., Any],
    description: str | None = None,
) -> tuple[str, Callable[..., Any], str | None]:
    """
    Create a tool wrapper with consistent naming.

    Args:
        name: Tool name (will be prefixed with group)
        func: Tool function
        description: Optional description override

    Returns:
        Tuple of (name, function, description)
    """
    return (name, func, description)


def register_tool_group(
    mcp: FastMCP,
    prefix: str,
    tools: list[tuple[str, Callable[..., Any], str | None]],
) -> int:
    """
    Register a group of tools with a common prefix.

    Args:
        mcp: FastMCP server instance
        prefix: Prefix for tool names (e.g., "technical", "screening")
        tools: List of (name, function, description) tuples

    Returns:
        Number of tools successfully registered
    """
    count = 0
    for name, func, description in tools:
        full_name = f"{prefix}_{name}"
        try:
            if description:
                mcp.tool(name=full_name, description=description)(func)
            else:
                mcp.tool(name=full_name)(func)
            count += 1
        except Exception as e:
            logger.error(f"Failed to register tool {full_name}: {e}")

    return count


# Default registry instance
_default_registry: ToolRegistry | None = None


def get_default_registry() -> ToolRegistry:
    """Get the default tool registry instance."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry


def reset_default_registry() -> None:
    """Reset the default tool registry (useful for testing)."""
    global _default_registry
    _default_registry = None


__all__ = [
    "ToolRegistry",
    "ToolRegistrar",
    "create_tool_wrapper",
    "register_tool_group",
    "get_default_registry",
    "reset_default_registry",
]
