"""
Base authentication strategy interface.
"""

from abc import ABC, abstractmethod

from fastapi import Request

from maverick_schemas.auth import AuthenticatedUser


class AuthStrategy(ABC):
    """
    Base authentication strategy.

    Implement this interface to add new authentication methods.
    """

    @abstractmethod
    async def authenticate(self, request: Request) -> AuthenticatedUser | None:
        """
        Attempt to authenticate the request.

        Args:
            request: FastAPI request object

        Returns:
            AuthenticatedUser if successful, None if this strategy doesn't apply
        """
        pass

    @abstractmethod
    def get_header_name(self) -> str | None:
        """
        Get the header name this strategy looks for.

        Returns:
            Header name or None if strategy uses cookies
        """
        pass


__all__ = ["AuthStrategy", "AuthenticatedUser"]

