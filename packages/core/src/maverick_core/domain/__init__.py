"""
Maverick Core Domain Layer.

This module contains pure domain logic following Domain-Driven Design principles:
- Entities: Objects with identity and lifecycle
- Value Objects: Immutable objects defined by their attributes
- Domain Services: Operations that don't belong to a single entity

All domain objects are framework-independent and contain only business logic.
"""

from maverick_core.domain.portfolio import Portfolio, Position

__all__ = [
    "Portfolio",
    "Position",
]
