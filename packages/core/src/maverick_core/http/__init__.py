"""
HTTP Client Management.

Provides shared async HTTP client management to prevent
resource leaks from creating new clients per request.
"""

from maverick_core.http.client import (
    AsyncHTTPClient,
    get_http_client,
    close_http_client,
    http_client_context,
)

__all__ = [
    "AsyncHTTPClient",
    "get_http_client",
    "close_http_client",
    "http_client_context",
]
