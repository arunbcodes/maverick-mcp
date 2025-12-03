"""
API response envelope models.

Provides consistent response structure for all API endpoints.
"""

from datetime import datetime, UTC
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseMeta(BaseModel):
    """Metadata included in all API responses."""
    
    request_id: str = Field(description="Unique request identifier for tracing")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Response timestamp in UTC"
    )
    version: str = Field(default="1.0.0", description="API version")


class PaginationMeta(BaseModel):
    """Pagination metadata for list endpoints."""
    
    page: int = Field(ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(ge=1, le=100, description="Items per page")
    total: int = Field(ge=0, description="Total number of items")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there are more pages")
    has_prev: bool = Field(description="Whether there are previous pages")
    # Cursor-based pagination for mobile infinite scroll
    next_cursor: str | None = Field(default=None, description="Cursor for next page")
    prev_cursor: str | None = Field(default=None, description="Cursor for previous page")
    
    @classmethod
    def create(
        cls,
        page: int,
        page_size: int,
        total: int,
        next_cursor: str | None = None,
        prev_cursor: str | None = None,
    ) -> "PaginationMeta":
        """Factory method to create pagination metadata."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
        )


class ErrorDetail(BaseModel):
    """Error detail structure."""
    
    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional error details"
    )
    field: str | None = Field(
        default=None,
        description="Field that caused the error (for validation errors)"
    )


class APIResponse(BaseModel, Generic[T]):
    """
    Standard API response envelope.
    
    All successful API responses follow this structure:
    
    ```json
    {
        "success": true,
        "data": { ... },
        "meta": {
            "request_id": "uuid",
            "timestamp": "ISO8601",
            "version": "1.0.0"
        }
    }
    ```
    """
    
    success: bool = Field(default=True, description="Whether the request succeeded")
    data: T = Field(description="Response payload")
    meta: ResponseMeta = Field(description="Response metadata")
    
    @classmethod
    def create(cls, data: T, request_id: str) -> "APIResponse[T]":
        """Factory method to create a successful response."""
        return cls(
            success=True,
            data=data,
            meta=ResponseMeta(request_id=request_id),
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated API response envelope.
    
    For list endpoints with pagination:
    
    ```json
    {
        "success": true,
        "data": [ ... ],
        "meta": { ... },
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 100,
            "has_next": true
        }
    }
    ```
    """
    
    success: bool = Field(default=True, description="Whether the request succeeded")
    data: list[T] = Field(description="List of items")
    meta: ResponseMeta = Field(description="Response metadata")
    pagination: PaginationMeta = Field(description="Pagination metadata")
    
    @classmethod
    def create(
        cls,
        data: list[T],
        request_id: str,
        page: int,
        page_size: int,
        total: int,
        next_cursor: str | None = None,
    ) -> "PaginatedResponse[T]":
        """Factory method to create a paginated response."""
        return cls(
            success=True,
            data=data,
            meta=ResponseMeta(request_id=request_id),
            pagination=PaginationMeta.create(
                page=page,
                page_size=page_size,
                total=total,
                next_cursor=next_cursor,
            ),
        )


class ErrorResponse(BaseModel):
    """
    Error response envelope.
    
    All error responses follow this structure:
    
    ```json
    {
        "success": false,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Human readable message",
            "details": { ... },
            "field": "ticker"
        },
        "meta": { ... }
    }
    ```
    """
    
    success: bool = Field(default=False, description="Always false for errors")
    error: ErrorDetail = Field(description="Error details")
    meta: ResponseMeta = Field(description="Response metadata")
    
    @classmethod
    def create(
        cls,
        code: str,
        message: str,
        request_id: str,
        details: dict[str, Any] | None = None,
        field: str | None = None,
    ) -> "ErrorResponse":
        """Factory method to create an error response."""
        return cls(
            success=False,
            error=ErrorDetail(
                code=code,
                message=message,
                details=details,
                field=field,
            ),
            meta=ResponseMeta(request_id=request_id),
        )


__all__ = [
    "ResponseMeta",
    "PaginationMeta",
    "ErrorDetail",
    "APIResponse",
    "PaginatedResponse",
    "ErrorResponse",
]

