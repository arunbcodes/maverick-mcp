"""
Server-Sent Events (SSE) module.

Provides real-time updates via SSE with Redis pub/sub for scalability.
"""

from maverick_api.sse.manager import SSEManager

__all__ = ["SSEManager"]

