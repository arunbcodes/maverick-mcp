"""
Capability-based API generation.

Provides utilities to generate FastAPI routes from capability definitions,
enabling DRY API development and consistent behavior across MCP/REST.
"""

from maverick_api.capabilities.route_generator import (
    generate_capability_routes,
    create_capability_endpoint,
    CapabilityRouter,
)
from maverick_api.capabilities.async_endpoints import (
    create_async_endpoints,
)

__all__ = [
    "generate_capability_routes",
    "create_capability_endpoint",
    "CapabilityRouter",
    "create_async_endpoints",
]
