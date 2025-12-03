"""
API Routers.

- health: Health check endpoints (liveness, readiness, startup)
- v1: Version 1 API endpoints
"""

from maverick_api.routers import health
from maverick_api.routers import v1

__all__ = ["health", "v1"]

