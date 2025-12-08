"""
Custom Screener API Endpoints.

Provides endpoints for creating, managing, and running custom stock screeners.
"""

import logging
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field

from maverick_schemas.base import MaverickBaseModel
from maverick_schemas.responses import APIResponse, ResponseMeta
from maverick_schemas.auth import AuthenticatedUser
from maverick_services import (
    CustomScreenerService,
    get_custom_screener_service,
    PRESET_SCREENERS,
    FILTER_FIELD_METADATA,
)
from maverick_api.dependencies import get_current_user, get_request_id, get_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-screeners", tags=["Custom Screeners"])


# ============================================
# Request/Response Models
# ============================================


class FilterConditionRequest(MaverickBaseModel):
    """A filter condition."""
    
    field: str
    operator: str
    value: float | str | list | None = None
    value2: float | None = None


class CreateScreenerRequest(MaverickBaseModel):
    """Request to create a screener."""
    
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    conditions: list[FilterConditionRequest] = Field(default_factory=list, max_length=15)
    sort_by: str | None = None
    sort_descending: bool = True
    max_results: int = Field(default=50, ge=1, le=100)


class UpdateScreenerRequest(MaverickBaseModel):
    """Request to update a screener."""
    
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    conditions: list[FilterConditionRequest] | None = None
    sort_by: str | None = None
    sort_descending: bool | None = None
    max_results: int | None = Field(default=None, ge=1, le=100)
    is_public: bool | None = None


class ConditionResponse(MaverickBaseModel):
    """Filter condition response."""
    
    field: str
    operator: str
    value: float | str | list | None = None
    value2: float | None = None


class ScreenerResponse(MaverickBaseModel):
    """Screener response."""
    
    screener_id: str
    user_id: str
    name: str
    description: str | None = None
    conditions: list[ConditionResponse]
    sort_by: str | None = None
    sort_descending: bool
    max_results: int
    is_public: bool
    run_count: int
    last_run: str | None = None
    created_at: str
    updated_at: str | None = None


class ScreenerSummaryResponse(MaverickBaseModel):
    """Screener summary."""
    
    screener_id: str
    name: str
    description: str | None = None
    condition_count: int
    run_count: int
    last_run: str | None = None
    is_public: bool


class ScreenerResultResponse(MaverickBaseModel):
    """Screener run result."""
    
    screener_id: str
    run_at: str
    stocks: list[dict]
    total_matches: int
    execution_time_ms: int


class PresetResponse(MaverickBaseModel):
    """Preset screener template."""
    
    name: str
    description: str | None = None
    conditions: list[dict]
    sort_by: str | None = None


class FieldMetadataResponse(MaverickBaseModel):
    """Filter field metadata."""
    
    field: str
    label: str
    type: str
    category: str
    min: float | None = None
    max: float | None = None


# ============================================
# Dependencies
# ============================================


async def get_screener_service_dep(
    redis=Depends(get_redis),
) -> CustomScreenerService:
    """Get custom screener service instance."""
    return get_custom_screener_service(redis_client=redis)


# ============================================
# Screener CRUD Endpoints
# ============================================


@router.get("", response_model=APIResponse[list[ScreenerSummaryResponse]])
async def get_screeners(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    screener_service: CustomScreenerService = Depends(get_screener_service_dep),
):
    """Get all custom screeners for the current user."""
    screeners = await screener_service.get_screeners(user.user_id)
    
    return APIResponse(
        data=[
            ScreenerSummaryResponse(
                screener_id=s.screener_id,
                name=s.name,
                description=s.description,
                condition_count=len(s.conditions),
                run_count=s.run_count,
                last_run=s.last_run.isoformat() if s.last_run else None,
                is_public=s.is_public,
            )
            for s in screeners
        ],
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("", response_model=APIResponse[ScreenerResponse])
async def create_screener(
    data: CreateScreenerRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    screener_service: CustomScreenerService = Depends(get_screener_service_dep),
):
    """Create a new custom screener."""
    try:
        screener = await screener_service.create_screener(
            user_id=user.user_id,
            name=data.name,
            description=data.description,
            conditions=[c.model_dump() for c in data.conditions],
            sort_by=data.sort_by,
            sort_descending=data.sort_descending,
            max_results=data.max_results,
        )
        
        return APIResponse(
            data=_screener_to_response(screener),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/{screener_id}", response_model=APIResponse[ScreenerResponse])
async def get_screener(
    screener_id: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    screener_service: CustomScreenerService = Depends(get_screener_service_dep),
):
    """Get a specific screener."""
    screener = await screener_service.get_screener(user.user_id, screener_id)
    
    if not screener:
        raise HTTPException(status_code=404, detail="Screener not found")
    
    return APIResponse(
        data=_screener_to_response(screener),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.patch("/{screener_id}", response_model=APIResponse[ScreenerResponse])
async def update_screener(
    screener_id: str,
    data: UpdateScreenerRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    screener_service: CustomScreenerService = Depends(get_screener_service_dep),
):
    """Update a screener."""
    conditions = None
    if data.conditions is not None:
        conditions = [c.model_dump() for c in data.conditions]
    
    screener = await screener_service.update_screener(
        user_id=user.user_id,
        screener_id=screener_id,
        name=data.name,
        description=data.description,
        conditions=conditions,
        sort_by=data.sort_by,
        sort_descending=data.sort_descending,
        max_results=data.max_results,
        is_public=data.is_public,
    )
    
    if not screener:
        raise HTTPException(status_code=404, detail="Screener not found")
    
    return APIResponse(
        data=_screener_to_response(screener),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.delete("/{screener_id}")
async def delete_screener(
    screener_id: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    screener_service: CustomScreenerService = Depends(get_screener_service_dep),
):
    """Delete a screener."""
    deleted = await screener_service.delete_screener(user.user_id, screener_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Screener not found")
    
    return APIResponse(
        data={"deleted": True, "screener_id": screener_id},
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("/{screener_id}/duplicate", response_model=APIResponse[ScreenerResponse])
async def duplicate_screener(
    screener_id: str,
    new_name: str | None = Query(default=None),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    screener_service: CustomScreenerService = Depends(get_screener_service_dep),
):
    """Duplicate a screener."""
    try:
        screener = await screener_service.duplicate_screener(
            user_id=user.user_id,
            screener_id=screener_id,
            new_name=new_name,
        )
        
        return APIResponse(
            data=_screener_to_response(screener),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# Run Screener Endpoints
# ============================================


@router.post("/{screener_id}/run", response_model=APIResponse[ScreenerResultResponse])
async def run_screener(
    screener_id: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    screener_service: CustomScreenerService = Depends(get_screener_service_dep),
):
    """
    Run a screener and get results.
    
    Note: This is a placeholder implementation. In production, this would
    integrate with the actual stock data service to screen stocks.
    """
    try:
        # TODO: Integrate with actual stock data fetcher
        result = await screener_service.run_screener(
            user_id=user.user_id,
            screener_id=screener_id,
            stock_data_fetcher=None,
        )
        
        return APIResponse(
            data=ScreenerResultResponse(
                screener_id=result.screener_id,
                run_at=result.run_at.isoformat(),
                stocks=result.stocks,
                total_matches=result.total_matches,
                execution_time_ms=result.execution_time_ms,
            ),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{screener_id}/results", response_model=APIResponse[ScreenerResultResponse | None])
async def get_cached_results(
    screener_id: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    screener_service: CustomScreenerService = Depends(get_screener_service_dep),
):
    """Get cached results from a previous run."""
    result = await screener_service.get_cached_results(user.user_id, screener_id)
    
    if not result:
        return APIResponse(
            data=None,
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    
    return APIResponse(
        data=ScreenerResultResponse(
            screener_id=result.screener_id,
            run_at=result.run_at.isoformat(),
            stocks=result.stocks,
            total_matches=result.total_matches,
            execution_time_ms=result.execution_time_ms,
        ),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


# ============================================
# Presets & Metadata Endpoints
# ============================================


@router.get("/meta/presets", response_model=APIResponse[list[PresetResponse]])
async def get_presets(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    screener_service: CustomScreenerService = Depends(get_screener_service_dep),
):
    """Get preset screener templates."""
    presets = screener_service.get_presets()
    
    return APIResponse(
        data=[
            PresetResponse(
                name=p["name"],
                description=p.get("description"),
                conditions=p["conditions"],
                sort_by=p.get("sort_by"),
            )
            for p in presets
        ],
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("/meta/presets/{preset_name}/create", response_model=APIResponse[ScreenerResponse])
async def create_from_preset(
    preset_name: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    screener_service: CustomScreenerService = Depends(get_screener_service_dep),
):
    """Create a screener from a preset template."""
    try:
        screener = await screener_service.create_from_preset(
            user_id=user.user_id,
            preset_name=preset_name,
        )
        
        return APIResponse(
            data=_screener_to_response(screener),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/meta/fields", response_model=APIResponse[list[FieldMetadataResponse]])
async def get_filter_fields(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get available filter fields with metadata for the UI."""
    fields = [
        FieldMetadataResponse(
            field=field,
            label=meta["label"],
            type=meta["type"],
            category=meta["category"],
            min=meta.get("min"),
            max=meta.get("max"),
        )
        for field, meta in FILTER_FIELD_METADATA.items()
    ]
    
    return APIResponse(
        data=fields,
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


# ============================================
# Helpers
# ============================================


def _screener_to_response(screener) -> ScreenerResponse:
    """Convert CustomScreener to response model."""
    return ScreenerResponse(
        screener_id=screener.screener_id,
        user_id=screener.user_id,
        name=screener.name,
        description=screener.description,
        conditions=[
            ConditionResponse(
                field=c.field.value,
                operator=c.operator.value,
                value=c.value,
                value2=c.value2,
            )
            for c in screener.conditions
        ],
        sort_by=screener.sort_by.value if screener.sort_by else None,
        sort_descending=screener.sort_descending,
        max_results=screener.max_results,
        is_public=screener.is_public,
        run_count=screener.run_count,
        last_run=screener.last_run.isoformat() if screener.last_run else None,
        created_at=screener.created_at.isoformat(),
        updated_at=screener.updated_at.isoformat() if screener.updated_at else None,
    )

