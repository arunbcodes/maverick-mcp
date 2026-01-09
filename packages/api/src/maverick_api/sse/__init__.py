"""
Server-Sent Events (SSE) module.

Provides real-time updates via SSE with Redis pub/sub for scalability.
Falls back to in-memory pub/sub when Redis is unavailable.
"""

from maverick_api.sse.manager import SSEManager
from maverick_api.sse.memory_manager import InMemorySSEManager

__all__ = ["SSEManager", "InMemorySSEManager"]

