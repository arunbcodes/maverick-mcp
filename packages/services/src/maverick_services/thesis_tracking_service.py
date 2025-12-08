"""
Investment Thesis Tracking Service.

Track investment theses, milestones, and validate decisions over time.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from uuid import uuid4

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


# ============================================
# Enums and Data Classes
# ============================================


class ThesisStatus(Enum):
    """Status of an investment thesis."""
    
    ACTIVE = "active"
    VALIDATED = "validated"
    INVALIDATED = "invalidated"
    CLOSED = "closed"


class MilestoneStatus(Enum):
    """Status of a milestone."""
    
    PENDING = "pending"
    HIT = "hit"
    MISSED = "missed"
    CANCELLED = "cancelled"


class MilestoneType(Enum):
    """Types of milestones to track."""
    
    PRICE_TARGET = "price_target"
    STOP_LOSS = "stop_loss"
    EARNINGS = "earnings"
    DIVIDEND = "dividend"
    PRODUCT_LAUNCH = "product_launch"
    REGULATORY = "regulatory"
    CUSTOM = "custom"


class DecisionType(Enum):
    """Types of investment decisions."""
    
    BUY = "buy"
    SELL = "sell"
    ADD = "add"  # Add to position
    TRIM = "trim"  # Reduce position
    HOLD = "hold"


@dataclass
class Milestone:
    """A milestone to track for a thesis."""
    
    milestone_id: str
    type: MilestoneType
    description: str
    target_date: datetime | None = None
    target_value: float | None = None  # For price targets
    status: MilestoneStatus = MilestoneStatus.PENDING
    actual_date: datetime | None = None
    actual_value: float | None = None
    notes: str | None = None
    
    def to_dict(self) -> dict:
        return {
            "milestone_id": self.milestone_id,
            "type": self.type.value,
            "description": self.description,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "target_value": self.target_value,
            "status": self.status.value,
            "actual_date": self.actual_date.isoformat() if self.actual_date else None,
            "actual_value": self.actual_value,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Milestone":
        return cls(
            milestone_id=data["milestone_id"],
            type=MilestoneType(data["type"]),
            description=data["description"],
            target_date=datetime.fromisoformat(data["target_date"]) if data.get("target_date") else None,
            target_value=data.get("target_value"),
            status=MilestoneStatus(data.get("status", "pending")),
            actual_date=datetime.fromisoformat(data["actual_date"]) if data.get("actual_date") else None,
            actual_value=data.get("actual_value"),
            notes=data.get("notes"),
        )


@dataclass
class Decision:
    """A trading decision with reasoning."""
    
    decision_id: str
    type: DecisionType
    date: datetime
    shares: float
    price: float
    reasoning: str
    thesis_reference: str | None = None  # Which thesis point drove this
    outcome: str | None = None  # Hindsight evaluation
    
    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "type": self.type.value,
            "date": self.date.isoformat(),
            "shares": self.shares,
            "price": self.price,
            "reasoning": self.reasoning,
            "thesis_reference": self.thesis_reference,
            "outcome": self.outcome,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Decision":
        return cls(
            decision_id=data["decision_id"],
            type=DecisionType(data["type"]),
            date=datetime.fromisoformat(data["date"]),
            shares=data["shares"],
            price=data["price"],
            reasoning=data["reasoning"],
            thesis_reference=data.get("thesis_reference"),
            outcome=data.get("outcome"),
        )


@dataclass
class InvestmentThesisEntry:
    """A tracked investment thesis."""
    
    thesis_id: str
    user_id: str
    ticker: str
    
    # Thesis content
    title: str
    summary: str
    bull_case: list[str] = field(default_factory=list)
    bear_case: list[str] = field(default_factory=list)
    key_metrics: dict = field(default_factory=dict)
    
    # Tracking
    entry_price: float | None = None
    entry_date: datetime | None = None
    target_price: float | None = None
    stop_price: float | None = None
    time_horizon: str | None = None  # e.g., "6 months", "1 year"
    
    # Milestones
    milestones: list[Milestone] = field(default_factory=list)
    
    # Decisions
    decisions: list[Decision] = field(default_factory=list)
    
    # Status
    status: ThesisStatus = ThesisStatus.ACTIVE
    
    # Validation
    validation_notes: str | None = None
    lessons_learned: str | None = None
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
    closed_at: datetime | None = None
    
    # Current state (populated at runtime)
    current_price: float | None = None
    unrealized_pl: float | None = None
    unrealized_pl_pct: float | None = None
    
    def to_dict(self) -> dict:
        return {
            "thesis_id": self.thesis_id,
            "user_id": self.user_id,
            "ticker": self.ticker,
            "title": self.title,
            "summary": self.summary,
            "bull_case": self.bull_case,
            "bear_case": self.bear_case,
            "key_metrics": self.key_metrics,
            "entry_price": self.entry_price,
            "entry_date": self.entry_date.isoformat() if self.entry_date else None,
            "target_price": self.target_price,
            "stop_price": self.stop_price,
            "time_horizon": self.time_horizon,
            "milestones": [m.to_dict() for m in self.milestones],
            "decisions": [d.to_dict() for d in self.decisions],
            "status": self.status.value,
            "validation_notes": self.validation_notes,
            "lessons_learned": self.lessons_learned,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "InvestmentThesisEntry":
        return cls(
            thesis_id=data["thesis_id"],
            user_id=data["user_id"],
            ticker=data["ticker"],
            title=data["title"],
            summary=data["summary"],
            bull_case=data.get("bull_case", []),
            bear_case=data.get("bear_case", []),
            key_metrics=data.get("key_metrics", {}),
            entry_price=data.get("entry_price"),
            entry_date=datetime.fromisoformat(data["entry_date"]) if data.get("entry_date") else None,
            target_price=data.get("target_price"),
            stop_price=data.get("stop_price"),
            time_horizon=data.get("time_horizon"),
            milestones=[Milestone.from_dict(m) for m in data.get("milestones", [])],
            decisions=[Decision.from_dict(d) for d in data.get("decisions", [])],
            status=ThesisStatus(data.get("status", "active")),
            validation_notes=data.get("validation_notes"),
            lessons_learned=data.get("lessons_learned"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(UTC),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            closed_at=datetime.fromisoformat(data["closed_at"]) if data.get("closed_at") else None,
        )


# ============================================
# Thesis Tracking Service
# ============================================


class ThesisTrackingService:
    """
    Service for tracking investment theses over time.
    
    Features:
    - Log investment thesis for each position
    - Set milestones (earnings, price targets, etc.)
    - Track decisions with reasoning
    - Validate/invalidate thesis over time
    - Learn from outcomes
    """
    
    # Redis keys
    THESES_KEY = "theses:{user_id}"
    THESIS_KEY = "thesis:{thesis_id}"
    TICKER_THESES_KEY = "ticker_theses:{user_id}:{ticker}"
    
    # Limits
    MAX_THESES_PER_USER = 100
    MAX_MILESTONES_PER_THESIS = 20
    MAX_DECISIONS_PER_THESIS = 50
    
    def __init__(self, redis_client: Redis | None = None):
        self.redis = redis_client
    
    # ================================
    # Thesis CRUD
    # ================================
    
    async def create_thesis(
        self,
        user_id: str,
        ticker: str,
        title: str,
        summary: str,
        bull_case: list[str] | None = None,
        bear_case: list[str] | None = None,
        entry_price: float | None = None,
        target_price: float | None = None,
        stop_price: float | None = None,
        time_horizon: str | None = None,
        key_metrics: dict | None = None,
    ) -> InvestmentThesisEntry:
        """Create a new investment thesis."""
        if not self.redis:
            raise RuntimeError("Redis not available")
        
        existing = await self.get_theses(user_id)
        if len(existing) >= self.MAX_THESES_PER_USER:
            raise ValueError(f"Maximum {self.MAX_THESES_PER_USER} theses allowed")
        
        thesis = InvestmentThesisEntry(
            thesis_id=str(uuid4()),
            user_id=user_id,
            ticker=ticker.upper(),
            title=title,
            summary=summary,
            bull_case=bull_case or [],
            bear_case=bear_case or [],
            entry_price=entry_price,
            entry_date=datetime.now(UTC) if entry_price else None,
            target_price=target_price,
            stop_price=stop_price,
            time_horizon=time_horizon,
            key_metrics=key_metrics or {},
        )
        
        await self._save_thesis(thesis)
        
        # Add to indices
        theses_key = self.THESES_KEY.format(user_id=user_id)
        await self.redis.sadd(theses_key, thesis.thesis_id)
        
        ticker_key = self.TICKER_THESES_KEY.format(user_id=user_id, ticker=thesis.ticker)
        await self.redis.sadd(ticker_key, thesis.thesis_id)
        
        logger.info(f"Created thesis {thesis.thesis_id} for {ticker}")
        return thesis
    
    async def get_theses(
        self,
        user_id: str,
        status: ThesisStatus | None = None,
    ) -> list[InvestmentThesisEntry]:
        """Get all theses for a user."""
        if not self.redis:
            return []
        
        theses_key = self.THESES_KEY.format(user_id=user_id)
        thesis_ids = await self.redis.smembers(theses_key)
        
        theses = []
        for tid in thesis_ids:
            thesis = await self.get_thesis(user_id, tid)
            if thesis:
                if status is None or thesis.status == status:
                    theses.append(thesis)
        
        # Sort by created date, newest first
        theses.sort(key=lambda t: t.created_at, reverse=True)
        return theses
    
    async def get_thesis(self, user_id: str, thesis_id: str) -> InvestmentThesisEntry | None:
        """Get a specific thesis."""
        if not self.redis:
            return None
        
        thesis_key = self.THESIS_KEY.format(thesis_id=thesis_id)
        data = await self.redis.get(thesis_key)
        
        if not data:
            return None
        
        thesis = InvestmentThesisEntry.from_dict(json.loads(data))
        
        if thesis.user_id != user_id:
            return None
        
        return thesis
    
    async def get_thesis_for_ticker(
        self,
        user_id: str,
        ticker: str,
    ) -> InvestmentThesisEntry | None:
        """Get the active thesis for a specific ticker."""
        if not self.redis:
            return None
        
        ticker_key = self.TICKER_THESES_KEY.format(user_id=user_id, ticker=ticker.upper())
        thesis_ids = await self.redis.smembers(ticker_key)
        
        for tid in thesis_ids:
            thesis = await self.get_thesis(user_id, tid)
            if thesis and thesis.status == ThesisStatus.ACTIVE:
                return thesis
        
        return None
    
    async def update_thesis(
        self,
        user_id: str,
        thesis_id: str,
        **updates,
    ) -> InvestmentThesisEntry | None:
        """Update thesis fields."""
        thesis = await self.get_thesis(user_id, thesis_id)
        if not thesis:
            return None
        
        for key, value in updates.items():
            if hasattr(thesis, key) and value is not None:
                setattr(thesis, key, value)
        
        thesis.updated_at = datetime.now(UTC)
        await self._save_thesis(thesis)
        return thesis
    
    async def close_thesis(
        self,
        user_id: str,
        thesis_id: str,
        status: ThesisStatus,
        validation_notes: str | None = None,
        lessons_learned: str | None = None,
    ) -> InvestmentThesisEntry | None:
        """Close a thesis with final status."""
        thesis = await self.get_thesis(user_id, thesis_id)
        if not thesis:
            return None
        
        thesis.status = status
        thesis.validation_notes = validation_notes
        thesis.lessons_learned = lessons_learned
        thesis.closed_at = datetime.now(UTC)
        thesis.updated_at = datetime.now(UTC)
        
        await self._save_thesis(thesis)
        return thesis
    
    async def delete_thesis(self, user_id: str, thesis_id: str) -> bool:
        """Delete a thesis."""
        if not self.redis:
            return False
        
        thesis = await self.get_thesis(user_id, thesis_id)
        if not thesis:
            return False
        
        # Remove from Redis
        thesis_key = self.THESIS_KEY.format(thesis_id=thesis_id)
        await self.redis.delete(thesis_key)
        
        # Remove from indices
        theses_key = self.THESES_KEY.format(user_id=user_id)
        await self.redis.srem(theses_key, thesis_id)
        
        ticker_key = self.TICKER_THESES_KEY.format(user_id=user_id, ticker=thesis.ticker)
        await self.redis.srem(ticker_key, thesis_id)
        
        return True
    
    # ================================
    # Milestone Management
    # ================================
    
    async def add_milestone(
        self,
        user_id: str,
        thesis_id: str,
        type: MilestoneType,
        description: str,
        target_date: datetime | None = None,
        target_value: float | None = None,
    ) -> Milestone:
        """Add a milestone to a thesis."""
        thesis = await self.get_thesis(user_id, thesis_id)
        if not thesis:
            raise ValueError("Thesis not found")
        
        if len(thesis.milestones) >= self.MAX_MILESTONES_PER_THESIS:
            raise ValueError(f"Maximum {self.MAX_MILESTONES_PER_THESIS} milestones")
        
        milestone = Milestone(
            milestone_id=str(uuid4()),
            type=type,
            description=description,
            target_date=target_date,
            target_value=target_value,
        )
        
        thesis.milestones.append(milestone)
        thesis.updated_at = datetime.now(UTC)
        await self._save_thesis(thesis)
        
        return milestone
    
    async def update_milestone(
        self,
        user_id: str,
        thesis_id: str,
        milestone_id: str,
        status: MilestoneStatus | None = None,
        actual_date: datetime | None = None,
        actual_value: float | None = None,
        notes: str | None = None,
    ) -> Milestone | None:
        """Update a milestone."""
        thesis = await self.get_thesis(user_id, thesis_id)
        if not thesis:
            return None
        
        milestone = next((m for m in thesis.milestones if m.milestone_id == milestone_id), None)
        if not milestone:
            return None
        
        if status is not None:
            milestone.status = status
        if actual_date is not None:
            milestone.actual_date = actual_date
        if actual_value is not None:
            milestone.actual_value = actual_value
        if notes is not None:
            milestone.notes = notes
        
        thesis.updated_at = datetime.now(UTC)
        await self._save_thesis(thesis)
        
        return milestone
    
    async def remove_milestone(
        self,
        user_id: str,
        thesis_id: str,
        milestone_id: str,
    ) -> bool:
        """Remove a milestone."""
        thesis = await self.get_thesis(user_id, thesis_id)
        if not thesis:
            return False
        
        original_len = len(thesis.milestones)
        thesis.milestones = [m for m in thesis.milestones if m.milestone_id != milestone_id]
        
        if len(thesis.milestones) == original_len:
            return False
        
        thesis.updated_at = datetime.now(UTC)
        await self._save_thesis(thesis)
        return True
    
    # ================================
    # Decision Journal
    # ================================
    
    async def add_decision(
        self,
        user_id: str,
        thesis_id: str,
        type: DecisionType,
        shares: float,
        price: float,
        reasoning: str,
        thesis_reference: str | None = None,
    ) -> Decision:
        """Add a trading decision to the thesis."""
        thesis = await self.get_thesis(user_id, thesis_id)
        if not thesis:
            raise ValueError("Thesis not found")
        
        if len(thesis.decisions) >= self.MAX_DECISIONS_PER_THESIS:
            raise ValueError(f"Maximum {self.MAX_DECISIONS_PER_THESIS} decisions")
        
        decision = Decision(
            decision_id=str(uuid4()),
            type=type,
            date=datetime.now(UTC),
            shares=shares,
            price=price,
            reasoning=reasoning,
            thesis_reference=thesis_reference,
        )
        
        thesis.decisions.append(decision)
        thesis.updated_at = datetime.now(UTC)
        await self._save_thesis(thesis)
        
        return decision
    
    async def update_decision_outcome(
        self,
        user_id: str,
        thesis_id: str,
        decision_id: str,
        outcome: str,
    ) -> Decision | None:
        """Update the outcome of a decision (hindsight evaluation)."""
        thesis = await self.get_thesis(user_id, thesis_id)
        if not thesis:
            return None
        
        decision = next((d for d in thesis.decisions if d.decision_id == decision_id), None)
        if not decision:
            return None
        
        decision.outcome = outcome
        thesis.updated_at = datetime.now(UTC)
        await self._save_thesis(thesis)
        
        return decision
    
    # ================================
    # Analytics
    # ================================
    
    async def get_win_loss_analysis(self, user_id: str) -> dict:
        """Analyze win/loss patterns across closed theses."""
        theses = await self.get_theses(user_id)
        closed_theses = [t for t in theses if t.status != ThesisStatus.ACTIVE]
        
        if not closed_theses:
            return {"message": "No closed theses to analyze"}
        
        validated = [t for t in closed_theses if t.status == ThesisStatus.VALIDATED]
        invalidated = [t for t in closed_theses if t.status == ThesisStatus.INVALIDATED]
        
        win_rate = len(validated) / len(closed_theses) * 100 if closed_theses else 0
        
        # Analyze common patterns
        bull_patterns = {}
        bear_patterns = {}
        
        for thesis in validated:
            for point in thesis.bull_case:
                bull_patterns[point] = bull_patterns.get(point, 0) + 1
        
        for thesis in invalidated:
            for point in thesis.bear_case:
                bear_patterns[point] = bear_patterns.get(point, 0) + 1
        
        return {
            "total_closed": len(closed_theses),
            "validated": len(validated),
            "invalidated": len(invalidated),
            "win_rate": round(win_rate, 1),
            "common_winning_factors": sorted(
                bull_patterns.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "common_losing_factors": sorted(
                bear_patterns.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }
    
    # ================================
    # Helpers
    # ================================
    
    async def _save_thesis(self, thesis: InvestmentThesisEntry) -> None:
        """Save thesis to Redis."""
        if not self.redis:
            raise RuntimeError("Redis not available")
        
        thesis_key = self.THESIS_KEY.format(thesis_id=thesis.thesis_id)
        await self.redis.set(thesis_key, json.dumps(thesis.to_dict()))


# ============================================
# Factory Function
# ============================================


def get_thesis_tracking_service(
    redis_client: Redis | None = None,
) -> ThesisTrackingService:
    """Get ThesisTrackingService instance."""
    return ThesisTrackingService(redis_client=redis_client)

