"""
Multi-strategy authentication module.

Supports:
- Cookie authentication (web apps)
- JWT authentication (mobile apps)
- API Key authentication (programmatic access)
"""

from maverick_api.auth.base import AuthStrategy, AuthenticatedUser
from maverick_api.auth.cookie import CookieAuthStrategy
from maverick_api.auth.jwt import JWTAuthStrategy
from maverick_api.auth.api_key import APIKeyAuthStrategy
from maverick_api.auth.middleware import AuthMiddleware

__all__ = [
    "AuthStrategy",
    "AuthenticatedUser",
    "CookieAuthStrategy",
    "JWTAuthStrategy",
    "APIKeyAuthStrategy",
    "AuthMiddleware",
]

