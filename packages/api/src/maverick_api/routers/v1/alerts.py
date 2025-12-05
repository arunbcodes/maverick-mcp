"""
AI Alerts API Endpoints.

Provides endpoints for managing alert rules and receiving real-time notifications.
"""

import asyncio
import json
import logging
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import Field

from maverick_schemas.base import MaverickBaseModel
from maverick_schemas.responses import APIResponse, ResponseMeta
from maverick_schemas.auth import AuthenticatedUser
from maverick_services import (
    AlertService,
    AlertType,
    AlertPriority,
    AlertStatus,
    get_alert_service,
    PRESET_RULES,
)
from maverick_api.dependencies import get_current_user, get_request_id, get_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


# ============================================
# Request/Response Models
# ============================================


class CreateRuleRequest(MaverickBaseModel):
    """Request to create an alert rule."""
    
    name: str = Field(min_length=1, max_length=100, description="Rule name")
    alert_type: str = Field(description="Alert type")
    conditions: dict = Field(default_factory=dict, description="Alert conditions")
    priority: str = Field(default="medium", description="Alert priority")
    cooldown_minutes: int = Field(default=60, ge=5, le=1440, description="Cooldown in minutes")


class UpdateRuleRequest(MaverickBaseModel):
    """Request to update an alert rule."""
    
    name: str | None = Field(default=None, max_length=100)
    conditions: dict | None = None
    priority: str | None = None
    cooldown_minutes: int | None = Field(default=None, ge=5, le=1440)
    enabled: bool | None = None


class RuleResponse(MaverickBaseModel):
    """Alert rule response."""
    
    rule_id: str
    user_id: str
    name: str
    alert_type: str
    enabled: bool
    conditions: dict
    priority: str
    cooldown_minutes: int
    created_at: str
    updated_at: str | None = None


class AlertResponse(MaverickBaseModel):
    """Alert response."""
    
    alert_id: str
    user_id: str
    rule_id: str | None = None
    alert_type: str
    priority: str
    title: str
    message: str
    ticker: str | None = None
    data: dict = Field(default_factory=dict)
    ai_insight: str | None = None
    status: str
    created_at: str
    read_at: str | None = None


class AlertCountResponse(MaverickBaseModel):
    """Unread alert count."""
    
    unread_count: int


class PresetRuleResponse(MaverickBaseModel):
    """Preset rule template."""
    
    name: str
    alert_type: str
    conditions: dict
    description: str


# ============================================
# Dependencies
# ============================================


async def get_alert_service_dep(
    redis=Depends(get_redis),
) -> AlertService:
    """Get alert service instance."""
    return get_alert_service(redis_client=redis)


# ============================================
# Rule Management Endpoints
# ============================================


@router.get("/rules", response_model=APIResponse[list[RuleResponse]])
async def get_alert_rules(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service_dep),
):
    """
    Get all alert rules for the current user.
    
    Returns all configured alert rules with their conditions and settings.
    """
    rules = await alert_service.get_rules(user.user_id)
    
    return APIResponse(
        data=[
            RuleResponse(
                rule_id=r.rule_id,
                user_id=r.user_id,
                name=r.name,
                alert_type=r.alert_type.value,
                enabled=r.enabled,
                conditions=r.conditions,
                priority=r.priority.value,
                cooldown_minutes=r.cooldown_minutes,
                created_at=r.created_at.isoformat(),
                updated_at=r.updated_at.isoformat() if r.updated_at else None,
            )
            for r in rules
        ],
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("/rules", response_model=APIResponse[RuleResponse])
async def create_alert_rule(
    data: CreateRuleRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service_dep),
):
    """
    Create a new alert rule.
    
    Alert types:
    - new_maverick_stock: When new stocks appear on Maverick screen
    - new_bear_stock: When new bearish opportunities appear
    - new_breakout: When new breakout patterns detected
    - rsi_oversold: When RSI drops below threshold
    - rsi_overbought: When RSI rises above threshold
    - price_target_hit: When price reaches target
    
    Example conditions:
    - {"min_score": 80} for screening alerts
    - {"threshold": 30} for RSI alerts
    - {"ticker": "AAPL", "target_price": 200, "direction": "above"} for price alerts
    """
    try:
        alert_type = AlertType(data.alert_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid alert_type. Must be one of: {[t.value for t in AlertType]}"
        )
    
    try:
        priority = AlertPriority(data.priority)
    except ValueError:
        priority = AlertPriority.MEDIUM
    
    try:
        rule = await alert_service.create_rule(
            user_id=user.user_id,
            name=data.name,
            alert_type=alert_type,
            conditions=data.conditions,
            priority=priority,
            cooldown_minutes=data.cooldown_minutes,
        )
        
        return APIResponse(
            data=RuleResponse(
                rule_id=rule.rule_id,
                user_id=rule.user_id,
                name=rule.name,
                alert_type=rule.alert_type.value,
                enabled=rule.enabled,
                conditions=rule.conditions,
                priority=rule.priority.value,
                cooldown_minutes=rule.cooldown_minutes,
                created_at=rule.created_at.isoformat(),
                updated_at=rule.updated_at.isoformat() if rule.updated_at else None,
            ),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.patch("/rules/{rule_id}", response_model=APIResponse[RuleResponse])
async def update_alert_rule(
    rule_id: str,
    data: UpdateRuleRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service_dep),
):
    """Update an existing alert rule."""
    updates = {}
    
    if data.name is not None:
        updates["name"] = data.name
    if data.conditions is not None:
        updates["conditions"] = data.conditions
    if data.priority is not None:
        try:
            updates["priority"] = AlertPriority(data.priority)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid priority")
    if data.cooldown_minutes is not None:
        updates["cooldown_minutes"] = data.cooldown_minutes
    if data.enabled is not None:
        updates["enabled"] = data.enabled
    
    rule = await alert_service.update_rule(user.user_id, rule_id, updates)
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return APIResponse(
        data=RuleResponse(
            rule_id=rule.rule_id,
            user_id=rule.user_id,
            name=rule.name,
            alert_type=rule.alert_type.value,
            enabled=rule.enabled,
            conditions=rule.conditions,
            priority=rule.priority.value,
            cooldown_minutes=rule.cooldown_minutes,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat() if rule.updated_at else None,
        ),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service_dep),
):
    """Delete an alert rule."""
    deleted = await alert_service.delete_rule(user.user_id, rule_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return APIResponse(
        data={"deleted": True, "rule_id": rule_id},
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("/rules/{rule_id}/toggle", response_model=APIResponse[RuleResponse])
async def toggle_alert_rule(
    rule_id: str,
    enabled: bool = Query(description="Enable or disable the rule"),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service_dep),
):
    """Enable or disable an alert rule."""
    success = await alert_service.toggle_rule(user.user_id, rule_id, enabled)
    
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule = await alert_service.get_rule(user.user_id, rule_id)
    
    return APIResponse(
        data=RuleResponse(
            rule_id=rule.rule_id,
            user_id=rule.user_id,
            name=rule.name,
            alert_type=rule.alert_type.value,
            enabled=rule.enabled,
            conditions=rule.conditions,
            priority=rule.priority.value,
            cooldown_minutes=rule.cooldown_minutes,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat() if rule.updated_at else None,
        ),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


# ============================================
# Alert History Endpoints
# ============================================


@router.get("", response_model=APIResponse[list[AlertResponse]])
async def get_alerts(
    limit: int = Query(default=50, ge=1, le=100),
    status: str | None = Query(default=None, description="Filter by status"),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service_dep),
):
    """
    Get alert history.
    
    Returns recent alerts with optional status filter.
    """
    status_filter = None
    if status:
        try:
            status_filter = AlertStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {[s.value for s in AlertStatus]}"
            )
    
    alerts = await alert_service.get_alerts(user.user_id, limit, status_filter)
    
    return APIResponse(
        data=[
            AlertResponse(
                alert_id=a.alert_id,
                user_id=a.user_id,
                rule_id=a.rule_id,
                alert_type=a.alert_type.value,
                priority=a.priority.value,
                title=a.title,
                message=a.message,
                ticker=a.ticker,
                data=a.data,
                ai_insight=a.ai_insight,
                status=a.status.value,
                created_at=a.created_at.isoformat(),
                read_at=a.read_at.isoformat() if a.read_at else None,
            )
            for a in alerts
        ],
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.get("/unread-count", response_model=APIResponse[AlertCountResponse])
async def get_unread_count(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service_dep),
):
    """Get count of unread alerts."""
    count = await alert_service.get_unread_count(user.user_id)
    
    return APIResponse(
        data=AlertCountResponse(unread_count=count),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service_dep),
):
    """Mark an alert as read."""
    success = await alert_service.mark_as_read(user.user_id, alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return APIResponse(
        data={"marked_read": True, "alert_id": alert_id},
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("/read-all")
async def mark_all_alerts_read(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service_dep),
):
    """Mark all alerts as read."""
    count = await alert_service.mark_all_as_read(user.user_id)
    
    return APIResponse(
        data={"marked_read": count},
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service_dep),
):
    """Dismiss an alert."""
    success = await alert_service.dismiss_alert(user.user_id, alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return APIResponse(
        data={"dismissed": True, "alert_id": alert_id},
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


# ============================================
# SSE Streaming Endpoint
# ============================================


@router.get("/stream")
async def stream_alerts(
    user: AuthenticatedUser = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service_dep),
):
    """
    Real-time alert stream via Server-Sent Events (SSE).
    
    Connects to a Redis pub/sub channel to receive alerts in real-time.
    The client should reconnect if the connection drops.
    
    Events:
    - alert: New alert triggered
    - ping: Keepalive (every 30 seconds)
    """
    async def event_generator():
        # Send initial connection event
        yield f"event: connected\ndata: {json.dumps({'user_id': user.user_id})}\n\n"
        
        try:
            # Create ping task for keepalive
            async def send_pings():
                while True:
                    await asyncio.sleep(30)
                    yield f"event: ping\ndata: {json.dumps({'timestamp': datetime.now(UTC).isoformat()})}\n\n"
            
            # Subscribe to alerts
            async for alert in alert_service.subscribe_to_alerts(user.user_id):
                yield f"event: alert\ndata: {json.dumps(alert.to_dict())}\n\n"
                
        except asyncio.CancelledError:
            logger.info(f"Alert stream cancelled for user {user.user_id}")
        except Exception as e:
            logger.error(f"Alert stream error for user {user.user_id}: {e}")
            yield f"event: error\ndata: {json.dumps({'error': 'Stream error'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# ============================================
# Preset Rules
# ============================================


@router.get("/presets", response_model=APIResponse[list[PresetRuleResponse]])
async def get_preset_rules(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get preset alert rule templates.
    
    These are pre-configured rules that users can quickly enable.
    """
    return APIResponse(
        data=[
            PresetRuleResponse(
                name=p["name"],
                alert_type=p["alert_type"].value,
                conditions=p["conditions"],
                description=p["description"],
            )
            for p in PRESET_RULES
        ],
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("/presets/{preset_name}/enable", response_model=APIResponse[RuleResponse])
async def enable_preset_rule(
    preset_name: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service_dep),
):
    """Enable a preset alert rule."""
    # Find preset
    preset = next((p for p in PRESET_RULES if p["name"] == preset_name), None)
    
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    try:
        rule = await alert_service.create_rule(
            user_id=user.user_id,
            name=preset["name"],
            alert_type=preset["alert_type"],
            conditions=preset["conditions"],
            priority=AlertPriority.MEDIUM,
        )
        
        return APIResponse(
            data=RuleResponse(
                rule_id=rule.rule_id,
                user_id=rule.user_id,
                name=rule.name,
                alert_type=rule.alert_type.value,
                enabled=rule.enabled,
                conditions=rule.conditions,
                priority=rule.priority.value,
                cooldown_minutes=rule.cooldown_minutes,
                created_at=rule.created_at.isoformat(),
                updated_at=rule.updated_at.isoformat() if rule.updated_at else None,
            ),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

