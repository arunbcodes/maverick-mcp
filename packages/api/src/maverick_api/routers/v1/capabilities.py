"""
Capabilities API router.

Exposes capability registry, audit stats, and system information
via REST API endpoints.
"""

import logging
from typing import Any

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from maverick_capabilities import (
    get_registry,
    get_audit_logger,
    CapabilityGroup,
)
from maverick_capabilities.audit import AuditEventType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/capabilities")


class CapabilitySummary(BaseModel):
    """Summary of a capability."""

    id: str
    title: str
    description: str
    group: str
    mcp_tool: str | None = None
    api_path: str | None = None
    is_async: bool = False


class CapabilityDetail(BaseModel):
    """Detailed capability information."""

    id: str
    title: str
    description: str
    group: str
    execution: dict
    mcp: dict | None = None
    api: dict | None = None
    deprecated: bool = False
    tags: list[str] = []


class CapabilityListResponse(BaseModel):
    """Response for listing capabilities."""

    total: int
    capabilities: list[CapabilitySummary]
    filters: dict


class AuditStatsResponse(BaseModel):
    """Response for audit statistics."""

    total_events: int
    by_event_type: dict[str, int]
    by_capability: dict[str, int]


class RecentExecutionResponse(BaseModel):
    """Response for recent executions."""

    count: int
    events: list[dict]


@router.get("", response_model=CapabilityListResponse)
async def list_capabilities(
    group: str | None = Query(None, description="Filter by capability group"),
    mcp_only: bool = Query(False, description="Only return MCP-exposed capabilities"),
    api_only: bool = Query(False, description="Only return API-exposed capabilities"),
    search: str | None = Query(None, description="Search by title or description"),
) -> CapabilityListResponse:
    """
    List all registered capabilities.

    Returns information about available capabilities, their groups,
    and whether they are exposed as MCP tools or API endpoints.
    """
    registry = get_registry()

    # Get capabilities based on filters
    if mcp_only:
        caps = registry.list_mcp()
    elif api_only:
        caps = registry.list_api()
    elif group:
        try:
            group_enum = CapabilityGroup(group)
            caps = registry.list_by_group(group_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid group: {group}. Valid groups: {[g.value for g in CapabilityGroup]}",
            )
    else:
        caps = registry.list_all()

    # Apply search filter
    if search:
        caps = [
            c
            for c in caps
            if search.lower() in c.title.lower()
            or search.lower() in c.description.lower()
        ]

    # Convert to summaries
    summaries = [
        CapabilitySummary(
            id=c.id,
            title=c.title,
            description=c.description,
            group=c.group.value,
            mcp_tool=c.mcp.tool_name if c.mcp and c.mcp.expose else None,
            api_path=c.api.path if c.api and c.api.expose else None,
            is_async=c.is_async,
        )
        for c in caps
        if not c.deprecated
    ]

    return CapabilityListResponse(
        total=len(summaries),
        capabilities=summaries,
        filters={
            "group": group,
            "mcp_only": mcp_only,
            "api_only": api_only,
            "search": search,
        },
    )


@router.get("/groups")
async def list_groups() -> dict[str, list[str]]:
    """
    List all capability groups with their capabilities.
    """
    registry = get_registry()
    groups = {}

    for group in CapabilityGroup:
        caps = registry.list_by_group(group)
        if caps:
            groups[group.value] = [c.id for c in caps if not c.deprecated]

    return {"groups": groups}


@router.get("/stats")
async def get_capability_stats() -> dict[str, Any]:
    """
    Get statistics about registered capabilities.
    """
    registry = get_registry()
    stats = registry.stats()
    return {"stats": stats}


@router.get("/{capability_id}", response_model=CapabilityDetail)
async def get_capability(capability_id: str) -> CapabilityDetail:
    """
    Get detailed information about a specific capability.
    """
    registry = get_registry()
    cap = registry.get(capability_id)

    if cap is None:
        raise HTTPException(
            status_code=404,
            detail=f"Capability not found: {capability_id}",
        )

    return CapabilityDetail(
        id=cap.id,
        title=cap.title,
        description=cap.description,
        group=cap.group.value,
        execution={
            "mode": cap.execution.mode.value,
            "timeout_seconds": cap.execution.timeout_seconds,
            "cache_enabled": cap.execution.cache_enabled,
            "cache_ttl_seconds": cap.execution.cache_ttl_seconds,
        },
        mcp={
            "expose": cap.mcp.expose,
            "tool_name": cap.mcp.tool_name,
            "category": cap.mcp.category,
        }
        if cap.mcp
        else None,
        api={
            "expose": cap.api.expose,
            "path": cap.api.path,
            "method": cap.api.method,
        }
        if cap.api
        else None,
        ui={
            "expose": cap.ui.expose,
            "component": cap.ui.expose,
            "route": cap.ui.route,
            "menu_group": cap.ui.menu_group,
            "manu_label": cap.ui.menu_label,
            "menu_order": cap.ui.menu_order,
        },
        deprecated=cap.deprecated,
        tags=cap.tags,
    )


@router.get("/audit/stats", response_model=AuditStatsResponse)
async def get_audit_stats() -> AuditStatsResponse:
    """
    Get audit statistics for tool executions.
    """
    audit_logger = get_audit_logger()

    # Get counts by event type
    by_event_type = {}
    for event_type in AuditEventType:
        count = await audit_logger.count(event_type=event_type)
        if count > 0:
            by_event_type[event_type.value] = count

    # Get counts by capability
    by_capability = {}
    registry = get_registry()
    for cap in registry.list_all():
        count = await audit_logger.count(capability_id=cap.id)
        if count > 0:
            by_capability[cap.id] = count

    total = await audit_logger.count()

    return AuditStatsResponse(
        total_events=total,
        by_event_type=by_event_type,
        by_capability=by_capability,
    )


@router.get("/audit/recent", response_model=RecentExecutionResponse)
async def get_recent_executions(
    capability_id: str | None = Query(None, description="Filter by capability"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
) -> RecentExecutionResponse:
    """
    Get recent tool execution events from the audit log.
    """
    audit_logger = get_audit_logger()

    events = await audit_logger.query(
        capability_id=capability_id,
        limit=limit,
    )

    return RecentExecutionResponse(
        count=len(events),
        events=[e.to_dict() for e in events],
    )
