"""
Maverick API Package.

REST API layer for MaverickMCP. Provides HTTP endpoints for web and mobile clients
with multi-strategy authentication and real-time updates via SSE.
"""

from maverick_api.main import create_app, app
from maverick_api.config import Settings, get_settings

__all__ = [
    "create_app",
    "app",
    "Settings",
    "get_settings",
]

