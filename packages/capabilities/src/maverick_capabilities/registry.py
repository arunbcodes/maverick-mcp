"""
Capability Registry.

Central registry for all capabilities in the system.
Provides lookup, filtering, and export functionality.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from maverick_capabilities.models import (
    Capability,
    CapabilityGroup,
    ExecutionMode,
)

if TYPE_CHECKING:
    pass


class CapabilityRegistry:
    """
    Central registry for all capabilities.

    The registry is the single source of truth for what capabilities
    exist in the system and how they should be exposed.

    Usage:
        >>> registry = CapabilityRegistry()
        >>> registry.register(my_capability)
        >>> cap = registry.get("run_screener")
        >>> mcp_caps = registry.list_mcp()
    """

    _instance: "CapabilityRegistry | None" = None

    def __init__(self):
        self._capabilities: dict[str, Capability] = {}
        self._by_group: dict[CapabilityGroup, list[Capability]] = {
            group: [] for group in CapabilityGroup
        }
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "CapabilityRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None

    def register(self, capability: Capability) -> None:
        """
        Register a capability.

        Args:
            capability: The capability to register

        Raises:
            ValueError: If a capability with the same ID already exists
        """
        if capability.id in self._capabilities:
            raise ValueError(f"Capability already registered: {capability.id}")

        self._capabilities[capability.id] = capability
        self._by_group[capability.group].append(capability)

    def register_many(self, capabilities: list[Capability]) -> None:
        """Register multiple capabilities."""
        for cap in capabilities:
            self.register(cap)

    def get(self, capability_id: str) -> Capability | None:
        """Get a capability by ID."""
        return self._capabilities.get(capability_id)

    def get_or_raise(self, capability_id: str) -> Capability:
        """Get a capability by ID, raising if not found."""
        cap = self.get(capability_id)
        if cap is None:
            raise KeyError(f"Unknown capability: {capability_id}")
        return cap

    def list_all(self) -> list[Capability]:
        """List all registered capabilities."""
        return list(self._capabilities.values())

    def list_by_group(self, group: CapabilityGroup) -> list[Capability]:
        """List capabilities in a specific group."""
        return self._by_group.get(group, [])

    def list_mcp(self) -> list[Capability]:
        """List capabilities exposed via MCP."""
        return [
            cap
            for cap in self._capabilities.values()
            if cap.mcp and cap.mcp.expose and not cap.deprecated
        ]

    def list_api(self) -> list[Capability]:
        """List capabilities exposed via REST API."""
        return [
            cap
            for cap in self._capabilities.values()
            if cap.api and cap.api.expose and not cap.deprecated
        ]

    def list_ui(self) -> list[Capability]:
        """List capabilities exposed in UI."""
        return [
            cap
            for cap in self._capabilities.values()
            if cap.ui and cap.ui.expose and not cap.deprecated
        ]

    def list_async(self) -> list[Capability]:
        """List async capabilities."""
        return [
            cap
            for cap in self._capabilities.values()
            if cap.execution.mode == ExecutionMode.ASYNC and not cap.deprecated
        ]

    def list_by_tag(self, tag: str) -> list[Capability]:
        """List capabilities with a specific tag."""
        return [cap for cap in self._capabilities.values() if tag in cap.tags]

    def search(
        self,
        query: str,
        group: CapabilityGroup | None = None,
        include_deprecated: bool = False,
    ) -> list[Capability]:
        """
        Search capabilities by title or description.

        Args:
            query: Search string (case-insensitive)
            group: Optional group filter
            include_deprecated: Include deprecated capabilities

        Returns:
            List of matching capabilities
        """
        query_lower = query.lower()
        results = []

        for cap in self._capabilities.values():
            if not include_deprecated and cap.deprecated:
                continue

            if group and cap.group != group:
                continue

            if (
                query_lower in cap.title.lower()
                or query_lower in cap.description.lower()
                or query_lower in cap.id.lower()
            ):
                results.append(cap)

        return results

    # Export methods

    def export_json(self, indent: int = 2) -> str:
        """Export all capabilities as JSON."""
        return json.dumps(
            {"capabilities": [cap.to_dict() for cap in self._capabilities.values()]},
            indent=indent,
        )

    def export_mcp_manifest(self) -> dict:
        """Export manifest for MCP tool registration."""
        return {
            "tools": [
                {
                    "name": cap.mcp.tool_name,
                    "description": cap.mcp.description_override or cap.description,
                    "category": cap.mcp.category or cap.group.value,
                    "is_async": cap.is_async,
                    "status_tool": cap.mcp.status_tool,
                }
                for cap in self.list_mcp()
                if cap.mcp
            ]
        }

    def export_api_manifest(self) -> dict:
        """Export manifest for REST API."""
        return {
            "endpoints": [
                {
                    "path": cap.api.path,
                    "method": cap.api.method,
                    "service": cap.service_class.__name__,
                    "service_method": cap.method_name,
                    "is_async": cap.is_async,
                    "status_path": cap.api.status_path,
                }
                for cap in self.list_api()
                if cap.api
            ]
        }

    def export_ui_manifest(self) -> dict:
        """Export manifest for UI."""
        menus: dict[str, list] = {}
        routes: list[dict] = []

        for cap in self.list_ui():
            if not cap.ui:
                continue

            if cap.ui.menu_group:
                group = cap.ui.menu_group
                if group not in menus:
                    menus[group] = []
                menus[group].append(
                    {
                        "label": cap.ui.menu_label or cap.title,
                        "route": cap.ui.route,
                        "order": cap.ui.menu_order,
                        "capability_id": cap.id,
                    }
                )

            if cap.ui.route:
                routes.append(
                    {
                        "path": cap.ui.route,
                        "component": cap.ui.component,
                        "capability_id": cap.id,
                        "permissions": cap.ui.permissions,
                    }
                )

        # Sort menu items by order
        for group in menus:
            menus[group].sort(key=lambda x: x["order"])

        return {"menus": menus, "routes": routes}

    # Statistics

    def stats(self) -> dict:
        """Get registry statistics."""
        all_caps = self.list_all()
        return {
            "total": len(all_caps),
            "by_group": {
                group.value: len(caps) for group, caps in self._by_group.items()
            },
            "mcp_exposed": len(self.list_mcp()),
            "api_exposed": len(self.list_api()),
            "ui_exposed": len(self.list_ui()),
            "async_capabilities": len(self.list_async()),
            "deprecated": len([c for c in all_caps if c.deprecated]),
        }


# Singleton accessor
_registry: CapabilityRegistry | None = None


def get_registry() -> CapabilityRegistry:
    """Get the global capability registry."""
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
    return _registry


def reset_registry() -> None:
    """Reset the global registry (for testing)."""
    global _registry
    _registry = None
    CapabilityRegistry.reset_instance()
