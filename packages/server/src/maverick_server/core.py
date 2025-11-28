"""
MaverickMCP Server Core Implementation.

Core server setup for FastMCP with stock analysis tools.
Provides a clean interface for creating and configuring the MCP server.
"""

import logging
import sys
import warnings
from typing import Any, Callable, Protocol

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def configure_warnings() -> None:
    """Configure warning filters for known deprecation warnings."""
    # pandas_ta warnings
    warnings.filterwarnings(
        "ignore",
        message="pkg_resources is deprecated as an API.*",
        category=UserWarning,
        module="pandas_ta.*",
    )

    # passlib warnings
    warnings.filterwarnings(
        "ignore",
        message="'crypt' is deprecated and slated for removal.*",
        category=DeprecationWarning,
        module="passlib.*",
    )

    # langchain pydantic warnings
    warnings.filterwarnings(
        "ignore",
        message=".*pydantic.* is deprecated.*",
        category=DeprecationWarning,
        module="langchain.*",
    )

    # starlette cookie warnings
    warnings.filterwarnings(
        "ignore",
        message=".*cookie.*deprecated.*",
        category=DeprecationWarning,
        module="starlette.*",
    )

    # Kaleido/plotly warnings
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        module=r".*kaleido.*",
    )

    # websockets warnings
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        module="websockets.*",
    )


class FastMCPProtocol(Protocol):
    """Protocol describing the FastMCP interface."""

    fastapi_app: Any
    dependencies: list[Any]

    def resource(
        self, uri: str
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        ...

    def tool(
        self, name: str | None = None, *, description: str | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        ...

    def prompt(
        self, name: str | None = None, *, description: str | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        ...

    def run(self, *args: Any, **kwargs: Any) -> None:
        ...


class MaverickServer:
    """
    MaverickMCP Server wrapper.

    Provides a clean interface for creating and configuring the FastMCP server
    with stock analysis tools.
    """

    def __init__(
        self,
        name: str = "MaverickMCP",
        configure_warnings_filter: bool = True,
    ):
        """
        Initialize the Maverick server.

        Args:
            name: Server name for identification
            configure_warnings_filter: Whether to configure warning filters
        """
        if configure_warnings_filter:
            configure_warnings()

        self._fastmcp = FastMCP(name=name)
        self._fastmcp.dependencies = []
        self._name = name
        self._tools_registered = False

        logger.info(f"MaverickServer '{name}' initialized")

    @property
    def mcp(self) -> FastMCP:
        """Get the underlying FastMCP instance."""
        return self._fastmcp

    @property
    def name(self) -> str:
        """Get the server name."""
        return self._name

    def register_tool(
        self,
        func: Callable,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """
        Register a tool function with the server.

        Args:
            func: The tool function to register
            name: Optional tool name (defaults to function name)
            description: Optional description
        """
        decorator = self._fastmcp.tool(name=name, description=description)
        decorator(func)

    def register_resource(self, uri: str, func: Callable) -> None:
        """
        Register a resource with the server.

        Args:
            uri: Resource URI
            func: The resource function
        """
        decorator = self._fastmcp.resource(uri)
        decorator(func)

    def register_prompt(
        self,
        func: Callable,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """
        Register a prompt with the server.

        Args:
            func: The prompt function
            name: Optional prompt name
            description: Optional description
        """
        decorator = self._fastmcp.prompt(name=name, description=description)
        decorator(func)

    def run(
        self,
        transport: str = "stdio",
        host: str = "0.0.0.0",
        port: int = 8003,
    ) -> None:
        """
        Run the server.

        Args:
            transport: Transport type (stdio, sse, streamable-http)
            host: Host to bind to (for HTTP transports)
            port: Port to bind to (for HTTP transports)
        """
        logger.info(f"Starting MaverickServer with transport={transport}")

        if transport == "stdio":
            self._fastmcp.run(transport="stdio")
        elif transport == "sse":
            self._fastmcp.run(transport="sse", host=host, port=port)
        elif transport == "streamable-http":
            self._fastmcp.run(transport="streamable-http", host=host, port=port)
        else:
            raise ValueError(f"Unknown transport: {transport}")


def create_server(
    name: str = "MaverickMCP",
    configure_warnings_filter: bool = True,
) -> MaverickServer:
    """
    Create a new Maverick server instance.

    Args:
        name: Server name
        configure_warnings_filter: Whether to configure warning filters

    Returns:
        Configured MaverickServer instance
    """
    return MaverickServer(
        name=name,
        configure_warnings_filter=configure_warnings_filter,
    )


__all__ = [
    "MaverickServer",
    "FastMCPProtocol",
    "create_server",
    "configure_warnings",
]
