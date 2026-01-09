"""
Generate FastAPI routes from capability definitions.

Provides automatic REST API endpoint generation from the capability registry,
ensuring consistency between MCP tools and REST endpoints.
"""

from __future__ import annotations

import logging
from datetime import datetime, UTC
from functools import partial
from typing import Any, Callable, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, create_model

from maverick_api.dependencies import get_current_user, get_request_id
from maverick_schemas.auth import AuthenticatedUser
from maverick_schemas.responses import APIResponse, ResponseMeta

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CapabilityRouter:
    """
    Router that generates endpoints from capability definitions.

    Usage:
        >>> from maverick_capabilities import get_registry
        >>> router = CapabilityRouter(prefix="/api/v1")
        >>> router.register_capabilities(["get_maverick_stocks", "get_breakout_stocks"])
        >>> app.include_router(router.to_fastapi_router())
    """

    def __init__(
        self,
        prefix: str = "",
        tags: list[str] | None = None,
        require_auth: bool = True,
    ):
        """
        Initialize capability router.

        Args:
            prefix: URL prefix for all routes
            tags: OpenAPI tags for documentation
            require_auth: Whether to require authentication
        """
        self.prefix = prefix
        self.tags = tags or []
        self.require_auth = require_auth
        self._router = APIRouter(prefix=prefix, tags=tags)
        self._registered: set[str] = set()

    def register_capability(
        self,
        capability_id: str,
        path_override: str | None = None,
        method_override: str | None = None,
        response_model: type | None = None,
    ) -> None:
        """
        Register a single capability as a REST endpoint.

        Args:
            capability_id: The capability ID to register
            path_override: Override the path from capability config
            method_override: Override the HTTP method
            response_model: Override the response model
        """
        from maverick_capabilities import get_registry
        from maverick_server.capabilities_integration import execute_capability

        registry = get_registry()
        cap = registry.get(capability_id)

        if not cap:
            logger.warning(f"Capability not found: {capability_id}")
            return

        if not cap.api or not cap.api.expose:
            logger.debug(f"Capability {capability_id} not exposed as API")
            return

        if capability_id in self._registered:
            logger.debug(f"Capability {capability_id} already registered")
            return

        # Determine path and method
        path = path_override or cap.api.path or f"/{cap.group.value}/{cap.id}"
        # Remove prefix if path already starts with it
        if path.startswith("/api/v1"):
            path = path[7:]
        method = (method_override or cap.api.method).upper()

        # Create endpoint handler
        handler = create_capability_endpoint(
            capability_id=capability_id,
            capability=cap,
            require_auth=self.require_auth,
        )

        # Register with FastAPI router
        if method == "GET":
            self._router.get(
                path,
                response_model=response_model or APIResponse[Any],
                summary=cap.title,
                description=cap.description,
            )(handler)
        elif method == "POST":
            self._router.post(
                path,
                response_model=response_model or APIResponse[Any],
                summary=cap.title,
                description=cap.description,
            )(handler)
        elif method == "PUT":
            self._router.put(
                path,
                response_model=response_model or APIResponse[Any],
                summary=cap.title,
                description=cap.description,
            )(handler)
        elif method == "DELETE":
            self._router.delete(
                path,
                response_model=response_model or APIResponse[Any],
                summary=cap.title,
                description=cap.description,
            )(handler)

        self._registered.add(capability_id)
        logger.debug(f"Registered capability endpoint: {method} {path}")

    def register_capabilities(self, capability_ids: list[str]) -> None:
        """Register multiple capabilities."""
        for cap_id in capability_ids:
            self.register_capability(cap_id)

    def register_all_for_group(self, group: str) -> None:
        """Register all API-exposed capabilities in a group."""
        from maverick_capabilities import get_registry

        registry = get_registry()
        caps = registry.list_api()

        for cap in caps:
            if cap.group.value == group:
                self.register_capability(cap.id)

    def to_fastapi_router(self) -> APIRouter:
        """Get the underlying FastAPI router."""
        return self._router


def create_capability_endpoint(
    capability_id: str,
    capability: Any,
    require_auth: bool = True,
) -> Callable:
    """
    Create a FastAPI endpoint handler for a capability.

    This creates an async endpoint that:
    - Validates input parameters using the capability's input_schema
    - Falls back to introspecting the service method if no schema defined
    - Executes the capability via the orchestrator
    - Returns a standardized APIResponse

    Args:
        capability_id: The capability ID
        capability: The Capability object
        require_auth: Whether to require authentication

    Returns:
        FastAPI-compatible async function
    """
    from maverick_server.capabilities_integration import execute_capability
    from maverick_capabilities.schema_generator import generate_schema_for_capability

    # Get input schema - either explicitly defined or generated via introspection
    input_schema = generate_schema_for_capability(capability)

    # Determine HTTP method to choose query params vs body parsing
    method = (capability.api.method if capability.api else "POST").upper()

    if input_schema is not None:
        if method in ("GET", "DELETE"):
            # GET/DELETE requests use query parameters via Depends()
            async def endpoint_with_query_params(
                request_id: str = Depends(get_request_id),
                user: AuthenticatedUser = Depends(get_current_user) if require_auth else None,
                params: input_schema = Depends(),
            ) -> APIResponse[Any]:
                """Auto-generated endpoint for {capability_id}."""
                try:
                    result = await execute_capability(
                        capability_id=capability_id,
                        input_data=params.model_dump(),
                        user_id=user.id if user else None,
                    )

                    if result.get("success"):
                        return APIResponse(
                            data=result.get("data"),
                            meta=ResponseMeta(
                                request_id=request_id,
                                timestamp=datetime.now(UTC),
                            ),
                        )
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail={
                                "error": result.get("error"),
                                "error_type": result.get("error_type"),
                            },
                        )
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Error executing capability {capability_id}: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail={"error": str(e), "error_type": type(e).__name__},
                    )

            endpoint_with_query_params.__name__ = f"capability_{capability_id}"
            endpoint_with_query_params.__doc__ = capability.description
            return endpoint_with_query_params

        else:
            # POST/PUT/PATCH requests parse from request body (no Depends())
            async def endpoint_with_body(
                request_id: str = Depends(get_request_id),
                user: AuthenticatedUser = Depends(get_current_user) if require_auth else None,
                params: input_schema = ...,
            ) -> APIResponse[Any]:
                """Auto-generated endpoint for {capability_id}."""
                try:
                    result = await execute_capability(
                        capability_id=capability_id,
                        input_data=params.model_dump(),
                        user_id=user.id if user else None,
                    )

                    if result.get("success"):
                        return APIResponse(
                            data=result.get("data"),
                            meta=ResponseMeta(
                                request_id=request_id,
                                timestamp=datetime.now(UTC),
                            ),
                        )
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail={
                                "error": result.get("error"),
                                "error_type": result.get("error_type"),
                            },
                        )
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Error executing capability {capability_id}: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail={"error": str(e), "error_type": type(e).__name__},
                    )

            endpoint_with_body.__name__ = f"capability_{capability_id}"
            endpoint_with_body.__doc__ = capability.description
            return endpoint_with_body

    else:
        # Fallback to **kwargs for capabilities without schema
        async def endpoint_handler(
            request_id: str = Depends(get_request_id),
            user: AuthenticatedUser = Depends(get_current_user) if require_auth else None,
            **kwargs: Any,
        ) -> APIResponse[Any]:
            """Auto-generated endpoint for {capability_id}."""
            try:
                result = await execute_capability(
                    capability_id=capability_id,
                    input_data=kwargs,
                    user_id=user.id if user else None,
                )

                if result.get("success"):
                    return APIResponse(
                        data=result.get("data"),
                        meta=ResponseMeta(
                            request_id=request_id,
                            timestamp=datetime.now(UTC),
                        ),
                    )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "error": result.get("error"),
                            "error_type": result.get("error_type"),
                        },
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error executing capability {capability_id}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail={"error": str(e), "error_type": type(e).__name__},
                )

        endpoint_handler.__name__ = f"capability_{capability_id}"
        endpoint_handler.__doc__ = capability.description
        return endpoint_handler


def generate_capability_routes(
    capability_ids: list[str] | None = None,
    groups: list[str] | None = None,
    prefix: str = "",
    tags: list[str] | None = None,
    require_auth: bool = True,
) -> APIRouter:
    """
    Generate a FastAPI router from capability definitions.

    This is a convenience function that creates a CapabilityRouter,
    registers the specified capabilities, and returns the FastAPI router.

    Args:
        capability_ids: Specific capability IDs to register
        groups: Capability groups to register (all API-exposed in group)
        prefix: URL prefix for all routes
        tags: OpenAPI tags for documentation
        require_auth: Whether to require authentication

    Returns:
        FastAPI APIRouter with generated endpoints

    Example:
        >>> # Register specific capabilities
        >>> router = generate_capability_routes(
        ...     capability_ids=["get_maverick_stocks", "get_breakout_stocks"],
        ...     prefix="/screening",
        ...     tags=["Screening"],
        ... )
        >>> app.include_router(router)

        >>> # Register all capabilities in a group
        >>> router = generate_capability_routes(
        ...     groups=["screening"],
        ...     tags=["Screening"],
        ... )
    """
    from maverick_capabilities import get_registry

    cap_router = CapabilityRouter(
        prefix=prefix,
        tags=tags,
        require_auth=require_auth,
    )

    if capability_ids:
        cap_router.register_capabilities(capability_ids)

    if groups:
        for group in groups:
            cap_router.register_all_for_group(group)

    return cap_router.to_fastapi_router()
