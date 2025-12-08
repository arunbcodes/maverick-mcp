"""
Thesis Tracking API Endpoints.

Track investment theses, milestones, and decisions over time.
"""

import logging
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field

from maverick_schemas.base import MaverickBaseModel
from maverick_schemas.responses import APIResponse, ResponseMeta
from maverick_schemas.auth import AuthenticatedUser
from maverick_services import (
    ThesisTrackingService,
    ThesisStatus,
    MilestoneStatus,
    MilestoneType,
    DecisionType,
    get_thesis_tracking_service,
)
from maverick_api.dependencies import get_current_user, get_request_id, get_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/thesis-tracking", tags=["Thesis Tracking"])


# ============================================
# Request/Response Models
# ============================================


class CreateThesisRequest(MaverickBaseModel):
    """Request to create a thesis."""
    
    ticker: str = Field(min_length=1, max_length=10)
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=2000)
    bull_case: list[str] = Field(default_factory=list, max_length=10)
    bear_case: list[str] = Field(default_factory=list, max_length=10)
    entry_price: float | None = Field(default=None, gt=0)
    target_price: float | None = Field(default=None, gt=0)
    stop_price: float | None = Field(default=None, gt=0)
    time_horizon: str | None = Field(default=None, max_length=50)
    key_metrics: dict = Field(default_factory=dict)


class UpdateThesisRequest(MaverickBaseModel):
    """Request to update a thesis."""
    
    title: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=2000)
    bull_case: list[str] | None = None
    bear_case: list[str] | None = None
    target_price: float | None = None
    stop_price: float | None = None
    time_horizon: str | None = None
    key_metrics: dict | None = None


class CloseThesisRequest(MaverickBaseModel):
    """Request to close a thesis."""
    
    status: str = Field(description="validated, invalidated, or closed")
    validation_notes: str | None = Field(default=None, max_length=1000)
    lessons_learned: str | None = Field(default=None, max_length=1000)


class AddMilestoneRequest(MaverickBaseModel):
    """Request to add a milestone."""
    
    type: str = Field(description="Milestone type")
    description: str = Field(min_length=1, max_length=500)
    target_date: str | None = None
    target_value: float | None = None


class UpdateMilestoneRequest(MaverickBaseModel):
    """Request to update a milestone."""
    
    status: str | None = None
    actual_date: str | None = None
    actual_value: float | None = None
    notes: str | None = Field(default=None, max_length=500)


class AddDecisionRequest(MaverickBaseModel):
    """Request to add a decision."""
    
    type: str = Field(description="buy, sell, add, trim, hold")
    shares: float = Field(gt=0)
    price: float = Field(gt=0)
    reasoning: str = Field(min_length=1, max_length=1000)
    thesis_reference: str | None = None


class MilestoneResponse(MaverickBaseModel):
    """Milestone response."""
    
    milestone_id: str
    type: str
    description: str
    target_date: str | None = None
    target_value: float | None = None
    status: str
    actual_date: str | None = None
    actual_value: float | None = None
    notes: str | None = None


class DecisionResponse(MaverickBaseModel):
    """Decision response."""
    
    decision_id: str
    type: str
    date: str
    shares: float
    price: float
    reasoning: str
    thesis_reference: str | None = None
    outcome: str | None = None


class ThesisResponse(MaverickBaseModel):
    """Thesis response."""
    
    thesis_id: str
    user_id: str
    ticker: str
    title: str
    summary: str
    bull_case: list[str]
    bear_case: list[str]
    key_metrics: dict
    entry_price: float | None = None
    entry_date: str | None = None
    target_price: float | None = None
    stop_price: float | None = None
    time_horizon: str | None = None
    milestones: list[MilestoneResponse]
    decisions: list[DecisionResponse]
    status: str
    validation_notes: str | None = None
    lessons_learned: str | None = None
    created_at: str
    updated_at: str | None = None
    closed_at: str | None = None


class ThesisSummaryResponse(MaverickBaseModel):
    """Thesis summary."""
    
    thesis_id: str
    ticker: str
    title: str
    status: str
    entry_price: float | None = None
    target_price: float | None = None
    milestone_count: int
    decision_count: int
    created_at: str


# ============================================
# Dependencies
# ============================================


async def get_thesis_service_dep(
    redis=Depends(get_redis),
) -> ThesisTrackingService:
    """Get thesis tracking service instance."""
    return get_thesis_tracking_service(redis_client=redis)


# ============================================
# Thesis CRUD Endpoints
# ============================================


@router.get("", response_model=APIResponse[list[ThesisSummaryResponse]])
async def get_theses(
    status: str | None = Query(default=None, description="Filter by status"),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisTrackingService = Depends(get_thesis_service_dep),
):
    """Get all investment theses."""
    status_filter = None
    if status:
        try:
            status_filter = ThesisStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    theses = await thesis_service.get_theses(user.user_id, status_filter)
    
    return APIResponse(
        data=[
            ThesisSummaryResponse(
                thesis_id=t.thesis_id,
                ticker=t.ticker,
                title=t.title,
                status=t.status.value,
                entry_price=t.entry_price,
                target_price=t.target_price,
                milestone_count=len(t.milestones),
                decision_count=len(t.decisions),
                created_at=t.created_at.isoformat(),
            )
            for t in theses
        ],
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("", response_model=APIResponse[ThesisResponse])
async def create_thesis(
    data: CreateThesisRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisTrackingService = Depends(get_thesis_service_dep),
):
    """Create a new investment thesis."""
    try:
        thesis = await thesis_service.create_thesis(
            user_id=user.user_id,
            ticker=data.ticker,
            title=data.title,
            summary=data.summary,
            bull_case=data.bull_case,
            bear_case=data.bear_case,
            entry_price=data.entry_price,
            target_price=data.target_price,
            stop_price=data.stop_price,
            time_horizon=data.time_horizon,
            key_metrics=data.key_metrics,
        )
        
        return APIResponse(
            data=_thesis_to_response(thesis),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ticker/{ticker}", response_model=APIResponse[ThesisResponse | None])
async def get_thesis_for_ticker(
    ticker: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisTrackingService = Depends(get_thesis_service_dep),
):
    """Get the active thesis for a specific ticker."""
    thesis = await thesis_service.get_thesis_for_ticker(user.user_id, ticker)
    
    return APIResponse(
        data=_thesis_to_response(thesis) if thesis else None,
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.get("/{thesis_id}", response_model=APIResponse[ThesisResponse])
async def get_thesis(
    thesis_id: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisTrackingService = Depends(get_thesis_service_dep),
):
    """Get a specific thesis."""
    thesis = await thesis_service.get_thesis(user.user_id, thesis_id)
    
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")
    
    return APIResponse(
        data=_thesis_to_response(thesis),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.patch("/{thesis_id}", response_model=APIResponse[ThesisResponse])
async def update_thesis(
    thesis_id: str,
    data: UpdateThesisRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisTrackingService = Depends(get_thesis_service_dep),
):
    """Update a thesis."""
    thesis = await thesis_service.update_thesis(
        user_id=user.user_id,
        thesis_id=thesis_id,
        **data.model_dump(exclude_unset=True),
    )
    
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")
    
    return APIResponse(
        data=_thesis_to_response(thesis),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.post("/{thesis_id}/close", response_model=APIResponse[ThesisResponse])
async def close_thesis(
    thesis_id: str,
    data: CloseThesisRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisTrackingService = Depends(get_thesis_service_dep),
):
    """Close a thesis with final status."""
    try:
        status = ThesisStatus(data.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    thesis = await thesis_service.close_thesis(
        user_id=user.user_id,
        thesis_id=thesis_id,
        status=status,
        validation_notes=data.validation_notes,
        lessons_learned=data.lessons_learned,
    )
    
    if not thesis:
        raise HTTPException(status_code=404, detail="Thesis not found")
    
    return APIResponse(
        data=_thesis_to_response(thesis),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.delete("/{thesis_id}")
async def delete_thesis(
    thesis_id: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisTrackingService = Depends(get_thesis_service_dep),
):
    """Delete a thesis."""
    deleted = await thesis_service.delete_thesis(user.user_id, thesis_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Thesis not found")
    
    return APIResponse(
        data={"deleted": True, "thesis_id": thesis_id},
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


# ============================================
# Milestone Endpoints
# ============================================


@router.post("/{thesis_id}/milestones", response_model=APIResponse[MilestoneResponse])
async def add_milestone(
    thesis_id: str,
    data: AddMilestoneRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisTrackingService = Depends(get_thesis_service_dep),
):
    """Add a milestone to a thesis."""
    try:
        milestone_type = MilestoneType(data.type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid milestone type")
    
    target_date = None
    if data.target_date:
        try:
            target_date = datetime.fromisoformat(data.target_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid target_date format")
    
    try:
        milestone = await thesis_service.add_milestone(
            user_id=user.user_id,
            thesis_id=thesis_id,
            type=milestone_type,
            description=data.description,
            target_date=target_date,
            target_value=data.target_value,
        )
        
        return APIResponse(
            data=_milestone_to_response(milestone),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{thesis_id}/milestones/{milestone_id}", response_model=APIResponse[MilestoneResponse])
async def update_milestone(
    thesis_id: str,
    milestone_id: str,
    data: UpdateMilestoneRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisTrackingService = Depends(get_thesis_service_dep),
):
    """Update a milestone."""
    status = None
    if data.status:
        try:
            status = MilestoneStatus(data.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    actual_date = None
    if data.actual_date:
        try:
            actual_date = datetime.fromisoformat(data.actual_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid actual_date format")
    
    milestone = await thesis_service.update_milestone(
        user_id=user.user_id,
        thesis_id=thesis_id,
        milestone_id=milestone_id,
        status=status,
        actual_date=actual_date,
        actual_value=data.actual_value,
        notes=data.notes,
    )
    
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    return APIResponse(
        data=_milestone_to_response(milestone),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


@router.delete("/{thesis_id}/milestones/{milestone_id}")
async def remove_milestone(
    thesis_id: str,
    milestone_id: str,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisTrackingService = Depends(get_thesis_service_dep),
):
    """Remove a milestone."""
    removed = await thesis_service.remove_milestone(
        user_id=user.user_id,
        thesis_id=thesis_id,
        milestone_id=milestone_id,
    )
    
    if not removed:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    return APIResponse(
        data={"removed": True, "milestone_id": milestone_id},
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


# ============================================
# Decision Endpoints
# ============================================


@router.post("/{thesis_id}/decisions", response_model=APIResponse[DecisionResponse])
async def add_decision(
    thesis_id: str,
    data: AddDecisionRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisTrackingService = Depends(get_thesis_service_dep),
):
    """Add a trading decision to a thesis."""
    try:
        decision_type = DecisionType(data.type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision type")
    
    try:
        decision = await thesis_service.add_decision(
            user_id=user.user_id,
            thesis_id=thesis_id,
            type=decision_type,
            shares=data.shares,
            price=data.price,
            reasoning=data.reasoning,
            thesis_reference=data.thesis_reference,
        )
        
        return APIResponse(
            data=_decision_to_response(decision),
            meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{thesis_id}/decisions/{decision_id}/outcome")
async def update_decision_outcome(
    thesis_id: str,
    decision_id: str,
    outcome: str = Query(description="Hindsight evaluation of the decision"),
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisTrackingService = Depends(get_thesis_service_dep),
):
    """Update the outcome of a decision."""
    decision = await thesis_service.update_decision_outcome(
        user_id=user.user_id,
        thesis_id=thesis_id,
        decision_id=decision_id,
        outcome=outcome,
    )
    
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    return APIResponse(
        data=_decision_to_response(decision),
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


# ============================================
# Analytics Endpoints
# ============================================


@router.get("/analytics/win-loss")
async def get_win_loss_analysis(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    thesis_service: ThesisTrackingService = Depends(get_thesis_service_dep),
):
    """Get win/loss analysis across closed theses."""
    analysis = await thesis_service.get_win_loss_analysis(user.user_id)
    
    return APIResponse(
        data=analysis,
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )


# ============================================
# Helpers
# ============================================


def _thesis_to_response(thesis) -> ThesisResponse:
    return ThesisResponse(
        thesis_id=thesis.thesis_id,
        user_id=thesis.user_id,
        ticker=thesis.ticker,
        title=thesis.title,
        summary=thesis.summary,
        bull_case=thesis.bull_case,
        bear_case=thesis.bear_case,
        key_metrics=thesis.key_metrics,
        entry_price=thesis.entry_price,
        entry_date=thesis.entry_date.isoformat() if thesis.entry_date else None,
        target_price=thesis.target_price,
        stop_price=thesis.stop_price,
        time_horizon=thesis.time_horizon,
        milestones=[_milestone_to_response(m) for m in thesis.milestones],
        decisions=[_decision_to_response(d) for d in thesis.decisions],
        status=thesis.status.value,
        validation_notes=thesis.validation_notes,
        lessons_learned=thesis.lessons_learned,
        created_at=thesis.created_at.isoformat(),
        updated_at=thesis.updated_at.isoformat() if thesis.updated_at else None,
        closed_at=thesis.closed_at.isoformat() if thesis.closed_at else None,
    )


def _milestone_to_response(milestone) -> MilestoneResponse:
    return MilestoneResponse(
        milestone_id=milestone.milestone_id,
        type=milestone.type.value,
        description=milestone.description,
        target_date=milestone.target_date.isoformat() if milestone.target_date else None,
        target_value=milestone.target_value,
        status=milestone.status.value,
        actual_date=milestone.actual_date.isoformat() if milestone.actual_date else None,
        actual_value=milestone.actual_value,
        notes=milestone.notes,
    )


def _decision_to_response(decision) -> DecisionResponse:
    return DecisionResponse(
        decision_id=decision.decision_id,
        type=decision.type.value,
        date=decision.date.isoformat(),
        shares=decision.shares,
        price=decision.price,
        reasoning=decision.reasoning,
        thesis_reference=decision.thesis_reference,
        outcome=decision.outcome,
    )

