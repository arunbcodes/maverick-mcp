"""
Capability definitions.

This module contains the actual capability definitions for all
services in the system. Import and register these with the registry.
"""

from maverick_capabilities.definitions.screening import SCREENING_CAPABILITIES
from maverick_capabilities.definitions.portfolio import PORTFOLIO_CAPABILITIES
from maverick_capabilities.definitions.technical import TECHNICAL_CAPABILITIES
from maverick_capabilities.definitions.research import RESEARCH_CAPABILITIES
from maverick_capabilities.definitions.risk import RISK_CAPABILITIES

# All capabilities
ALL_CAPABILITIES = [
    *SCREENING_CAPABILITIES,
    *PORTFOLIO_CAPABILITIES,
    *TECHNICAL_CAPABILITIES,
    *RESEARCH_CAPABILITIES,
    *RISK_CAPABILITIES,
]


def register_all_capabilities() -> None:
    """Register all capability definitions with the global registry."""
    from maverick_capabilities.registry import get_registry

    registry = get_registry()
    registry.register_many(ALL_CAPABILITIES)


__all__ = [
    "SCREENING_CAPABILITIES",
    "PORTFOLIO_CAPABILITIES",
    "TECHNICAL_CAPABILITIES",
    "RESEARCH_CAPABILITIES",
    "RISK_CAPABILITIES",
    "ALL_CAPABILITIES",
    "register_all_capabilities",
]
