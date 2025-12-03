"""
Centralized exception handling.

Converts exceptions to consistent API error responses.
"""

import logging
from datetime import datetime, UTC

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from maverick_core.exceptions import MaverickError
from maverick_schemas.responses import ErrorResponse, ErrorDetail, ResponseMeta
from maverick_api.middleware.logging import get_request_id

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the app."""

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_handler)
    app.add_exception_handler(MaverickError, maverick_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    request_id = get_request_id()

    error_response = ErrorResponse(
        error=ErrorDetail(
            code=_status_to_code(exc.status_code),
            message=str(exc.detail) if isinstance(exc.detail, str) else "Error",
            details=exc.detail if isinstance(exc.detail, dict) else None,
        ),
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle FastAPI request validation errors."""
    request_id = get_request_id()

    # Extract first error for message
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    message = first_error.get("msg", "Validation error")

    error_response = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message=f"Validation error: {message}",
            field=field if field else None,
            details={"errors": errors},
        ),
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(mode="json"),
    )


async def pydantic_validation_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    request_id = get_request_id()

    errors = exc.errors()
    first_error = errors[0] if errors else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    message = first_error.get("msg", "Validation error")

    error_response = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message=f"Validation error: {message}",
            field=field if field else None,
            details={"errors": errors},
        ),
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(mode="json"),
    )


async def maverick_error_handler(
    request: Request,
    exc: MaverickError,
) -> JSONResponse:
    """Handle Maverick domain exceptions."""
    request_id = get_request_id()

    logger.warning(
        f"Maverick error: {exc.error_code} - {exc.message}",
        extra={"request_id": request_id, "context": exc.context},
    )

    error_response = ErrorResponse(
        error=ErrorDetail(
            code=exc.error_code,
            message=exc.message,
            field=exc.field,
            details=exc.context if exc.context else None,
        ),
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions."""
    request_id = get_request_id()

    # Log the full exception
    logger.exception(
        f"Unexpected error: {type(exc).__name__}: {exc}",
        extra={"request_id": request_id},
    )

    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            # Don't expose exception details in production
            details={"type": type(exc).__name__} if __debug__ else None,
        ),
        meta=ResponseMeta(
            request_id=request_id,
            timestamp=datetime.now(UTC),
        ),
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json"),
    )


def _status_to_code(status: int) -> str:
    """Convert HTTP status code to error code."""
    return {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }.get(status, "UNKNOWN_ERROR")


__all__ = ["register_exception_handlers"]

