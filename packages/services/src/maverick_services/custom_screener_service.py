"""
Custom Screener Service.

Allows users to define, save, and run custom stock screening criteria.
"""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from uuid import uuid4

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


# ============================================
# Enums and Data Classes
# ============================================


class FilterOperator(Enum):
    """Filter comparison operators."""
    
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_THAN = "less_than"
    LESS_OR_EQUAL = "less_or_equal"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"


class FilterField(Enum):
    """Available filter fields."""
    
    # Price
    PRICE = "price"
    PRICE_CHANGE = "price_change"
    PRICE_CHANGE_PCT = "price_change_pct"
    
    # Technical Indicators
    RSI = "rsi"
    RSI_14 = "rsi_14"
    MACD = "macd"
    MACD_SIGNAL = "macd_signal"
    MACD_HISTOGRAM = "macd_histogram"
    SMA_20 = "sma_20"
    SMA_50 = "sma_50"
    SMA_200 = "sma_200"
    EMA_20 = "ema_20"
    EMA_50 = "ema_50"
    
    # Volume
    VOLUME = "volume"
    AVERAGE_VOLUME = "average_volume"
    VOLUME_RATIO = "volume_ratio"  # volume / avg_volume
    
    # Fundamentals
    MARKET_CAP = "market_cap"
    PE_RATIO = "pe_ratio"
    PEG_RATIO = "peg_ratio"
    PRICE_TO_BOOK = "price_to_book"
    PRICE_TO_SALES = "price_to_sales"
    DIVIDEND_YIELD = "dividend_yield"
    EPS = "eps"
    REVENUE_GROWTH = "revenue_growth"
    PROFIT_MARGIN = "profit_margin"
    
    # Classification
    SECTOR = "sector"
    INDUSTRY = "industry"
    EXCHANGE = "exchange"
    
    # Momentum
    MOMENTUM_SCORE = "momentum_score"
    TREND_STRENGTH = "trend_strength"
    
    # Custom / Screening
    MAVERICK_SCORE = "maverick_score"
    BEAR_SCORE = "bear_score"


@dataclass
class FilterCondition:
    """A single filter condition."""
    
    field: FilterField
    operator: FilterOperator
    value: float | str | list | None = None
    value2: float | None = None  # For BETWEEN operator
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "field": self.field.value,
            "operator": self.operator.value,
            "value": self.value,
            "value2": self.value2,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FilterCondition":
        """Create from dictionary."""
        return cls(
            field=FilterField(data["field"]),
            operator=FilterOperator(data["operator"]),
            value=data.get("value"),
            value2=data.get("value2"),
        )


@dataclass
class CustomScreener:
    """A user's custom screener."""
    
    screener_id: str
    user_id: str
    name: str
    description: str | None = None
    
    # Filter conditions (AND logic)
    conditions: list[FilterCondition] = field(default_factory=list)
    
    # Sorting
    sort_by: FilterField | None = None
    sort_descending: bool = True
    
    # Result limit
    max_results: int = 50
    
    # Scheduling
    schedule_enabled: bool = False
    schedule_cron: str | None = None  # e.g., "0 9 * * 1-5" for weekdays at 9am
    last_run: datetime | None = None
    
    # Sharing
    is_public: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
    run_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "screener_id": self.screener_id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "conditions": [c.to_dict() for c in self.conditions],
            "sort_by": self.sort_by.value if self.sort_by else None,
            "sort_descending": self.sort_descending,
            "max_results": self.max_results,
            "schedule_enabled": self.schedule_enabled,
            "schedule_cron": self.schedule_cron,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "run_count": self.run_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CustomScreener":
        """Create from dictionary."""
        return cls(
            screener_id=data["screener_id"],
            user_id=data["user_id"],
            name=data["name"],
            description=data.get("description"),
            conditions=[FilterCondition.from_dict(c) for c in data.get("conditions", [])],
            sort_by=FilterField(data["sort_by"]) if data.get("sort_by") else None,
            sort_descending=data.get("sort_descending", True),
            max_results=data.get("max_results", 50),
            schedule_enabled=data.get("schedule_enabled", False),
            schedule_cron=data.get("schedule_cron"),
            last_run=datetime.fromisoformat(data["last_run"]) if data.get("last_run") else None,
            is_public=data.get("is_public", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(UTC),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            run_count=data.get("run_count", 0),
        )


@dataclass
class ScreenerResult:
    """Result from running a screener."""
    
    screener_id: str
    run_at: datetime
    stocks: list[dict]  # List of stock data matching criteria
    total_matches: int
    execution_time_ms: int


# ============================================
# Preset Screeners
# ============================================


PRESET_SCREENERS = [
    {
        "name": "Momentum Leaders",
        "description": "High momentum stocks with strong technical setups",
        "conditions": [
            {"field": "rsi_14", "operator": "between", "value": 50, "value2": 70},
            {"field": "price", "operator": "greater_than", "value": 10},
            {"field": "volume_ratio", "operator": "greater_than", "value": 1.5},
            {"field": "price_change_pct", "operator": "greater_than", "value": 0},
        ],
        "sort_by": "momentum_score",
    },
    {
        "name": "Value Stocks",
        "description": "Undervalued stocks with solid fundamentals",
        "conditions": [
            {"field": "pe_ratio", "operator": "between", "value": 5, "value2": 20},
            {"field": "dividend_yield", "operator": "greater_than", "value": 2},
            {"field": "market_cap", "operator": "greater_than", "value": 1_000_000_000},
        ],
        "sort_by": "pe_ratio",
        "sort_descending": False,
    },
    {
        "name": "RSI Oversold",
        "description": "Stocks with RSI below 30 (potential bounce)",
        "conditions": [
            {"field": "rsi_14", "operator": "less_than", "value": 30},
            {"field": "price", "operator": "greater_than", "value": 5},
            {"field": "average_volume", "operator": "greater_than", "value": 500_000},
        ],
        "sort_by": "rsi_14",
        "sort_descending": False,
    },
    {
        "name": "RSI Overbought",
        "description": "Stocks with RSI above 70 (potential pullback)",
        "conditions": [
            {"field": "rsi_14", "operator": "greater_than", "value": 70},
            {"field": "price", "operator": "greater_than", "value": 5},
            {"field": "average_volume", "operator": "greater_than", "value": 500_000},
        ],
        "sort_by": "rsi_14",
    },
    {
        "name": "Volume Breakouts",
        "description": "Stocks with unusual volume activity",
        "conditions": [
            {"field": "volume_ratio", "operator": "greater_than", "value": 3},
            {"field": "price_change_pct", "operator": "greater_than", "value": 2},
            {"field": "price", "operator": "greater_than", "value": 10},
        ],
        "sort_by": "volume_ratio",
    },
    {
        "name": "Golden Cross",
        "description": "Stocks where 50-day SMA crossed above 200-day SMA",
        "conditions": [
            {"field": "sma_50", "operator": "greater_than", "value": 0},  # Placeholder - actual implementation needs cross detection
            {"field": "price", "operator": "greater_than", "value": 10},
        ],
        "sort_by": "momentum_score",
    },
    {
        "name": "Small Cap Growth",
        "description": "Small cap stocks with high growth potential",
        "conditions": [
            {"field": "market_cap", "operator": "between", "value": 300_000_000, "value2": 2_000_000_000},
            {"field": "revenue_growth", "operator": "greater_than", "value": 20},
            {"field": "price", "operator": "greater_than", "value": 5},
        ],
        "sort_by": "revenue_growth",
    },
    {
        "name": "Dividend Champions",
        "description": "High-yield dividend stocks",
        "conditions": [
            {"field": "dividend_yield", "operator": "greater_than", "value": 4},
            {"field": "market_cap", "operator": "greater_than", "value": 5_000_000_000},
            {"field": "pe_ratio", "operator": "less_than", "value": 25},
        ],
        "sort_by": "dividend_yield",
    },
]


# ============================================
# Custom Screener Service
# ============================================


class CustomScreenerService:
    """
    Service for managing custom stock screeners.
    
    Features:
    - Create/edit/delete custom screeners
    - Visual filter builder support
    - Run screener against stock universe
    - Save and load screener configurations
    - Preset screener templates
    - Schedule screeners for auto-run
    """
    
    # Redis keys
    SCREENERS_KEY = "screeners:{user_id}"
    SCREENER_KEY = "screener:{screener_id}"
    RESULTS_KEY = "screener_results:{screener_id}"
    
    # Limits
    MAX_SCREENERS_PER_USER = 20
    MAX_CONDITIONS_PER_SCREENER = 15
    
    def __init__(
        self,
        redis_client: Redis | None = None,
    ):
        self.redis = redis_client
    
    # ================================
    # Screener CRUD
    # ================================
    
    async def create_screener(
        self,
        user_id: str,
        name: str,
        conditions: list[dict],
        description: str | None = None,
        sort_by: str | None = None,
        sort_descending: bool = True,
        max_results: int = 50,
    ) -> CustomScreener:
        """Create a new custom screener."""
        if not self.redis:
            raise RuntimeError("Redis not available")
        
        # Check limit
        existing = await self.get_screeners(user_id)
        if len(existing) >= self.MAX_SCREENERS_PER_USER:
            raise ValueError(f"Maximum {self.MAX_SCREENERS_PER_USER} screeners allowed")
        
        # Parse conditions
        parsed_conditions = []
        for cond in conditions[:self.MAX_CONDITIONS_PER_SCREENER]:
            try:
                parsed_conditions.append(FilterCondition.from_dict(cond))
            except (KeyError, ValueError) as e:
                logger.warning(f"Invalid condition skipped: {e}")
        
        screener = CustomScreener(
            screener_id=str(uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            conditions=parsed_conditions,
            sort_by=FilterField(sort_by) if sort_by else None,
            sort_descending=sort_descending,
            max_results=min(max_results, 100),
        )
        
        await self._save_screener(screener)
        
        # Add to user's screener index
        screeners_key = self.SCREENERS_KEY.format(user_id=user_id)
        await self.redis.sadd(screeners_key, screener.screener_id)
        
        logger.info(f"Created screener {screener.screener_id} for user {user_id}")
        return screener
    
    async def get_screeners(self, user_id: str) -> list[CustomScreener]:
        """Get all screeners for a user."""
        if not self.redis:
            return []
        
        screeners_key = self.SCREENERS_KEY.format(user_id=user_id)
        screener_ids = await self.redis.smembers(screeners_key)
        
        screeners = []
        for scr_id in screener_ids:
            screener = await self.get_screener(user_id, scr_id)
            if screener:
                screeners.append(screener)
        
        # Sort by name
        screeners.sort(key=lambda s: s.name.lower())
        return screeners
    
    async def get_screener(self, user_id: str, screener_id: str) -> CustomScreener | None:
        """Get a specific screener."""
        if not self.redis:
            return None
        
        screener_key = self.SCREENER_KEY.format(screener_id=screener_id)
        data = await self.redis.get(screener_key)
        
        if not data:
            return None
        
        screener = CustomScreener.from_dict(json.loads(data))
        
        # Verify ownership (unless public)
        if screener.user_id != user_id and not screener.is_public:
            return None
        
        return screener
    
    async def update_screener(
        self,
        user_id: str,
        screener_id: str,
        name: str | None = None,
        description: str | None = None,
        conditions: list[dict] | None = None,
        sort_by: str | None = None,
        sort_descending: bool | None = None,
        max_results: int | None = None,
        is_public: bool | None = None,
    ) -> CustomScreener | None:
        """Update screener details."""
        screener = await self.get_screener(user_id, screener_id)
        if not screener or screener.user_id != user_id:
            return None
        
        if name is not None:
            screener.name = name
        if description is not None:
            screener.description = description
        if conditions is not None:
            screener.conditions = [
                FilterCondition.from_dict(c)
                for c in conditions[:self.MAX_CONDITIONS_PER_SCREENER]
            ]
        if sort_by is not None:
            screener.sort_by = FilterField(sort_by) if sort_by else None
        if sort_descending is not None:
            screener.sort_descending = sort_descending
        if max_results is not None:
            screener.max_results = min(max_results, 100)
        if is_public is not None:
            screener.is_public = is_public
        
        screener.updated_at = datetime.now(UTC)
        await self._save_screener(screener)
        return screener
    
    async def delete_screener(self, user_id: str, screener_id: str) -> bool:
        """Delete a screener."""
        if not self.redis:
            return False
        
        screener = await self.get_screener(user_id, screener_id)
        if not screener or screener.user_id != user_id:
            return False
        
        # Delete from Redis
        screener_key = self.SCREENER_KEY.format(screener_id=screener_id)
        await self.redis.delete(screener_key)
        
        # Remove from user's index
        screeners_key = self.SCREENERS_KEY.format(user_id=user_id)
        await self.redis.srem(screeners_key, screener_id)
        
        # Delete cached results
        results_key = self.RESULTS_KEY.format(screener_id=screener_id)
        await self.redis.delete(results_key)
        
        logger.info(f"Deleted screener {screener_id}")
        return True
    
    async def duplicate_screener(
        self,
        user_id: str,
        screener_id: str,
        new_name: str | None = None,
    ) -> CustomScreener:
        """Duplicate an existing screener."""
        original = await self.get_screener(user_id, screener_id)
        if not original:
            raise ValueError("Screener not found")
        
        return await self.create_screener(
            user_id=user_id,
            name=new_name or f"{original.name} (Copy)",
            description=original.description,
            conditions=[c.to_dict() for c in original.conditions],
            sort_by=original.sort_by.value if original.sort_by else None,
            sort_descending=original.sort_descending,
            max_results=original.max_results,
        )
    
    # ================================
    # Run Screener
    # ================================
    
    async def run_screener(
        self,
        user_id: str,
        screener_id: str,
        stock_data_fetcher: Callable | None = None,
    ) -> ScreenerResult:
        """
        Run a screener against the stock universe.
        
        stock_data_fetcher should be an async function that returns
        a list of stock data dicts with all filterable fields.
        """
        import time
        start_time = time.time()
        
        screener = await self.get_screener(user_id, screener_id)
        if not screener:
            raise ValueError("Screener not found")
        
        # Fetch stock data
        if stock_data_fetcher:
            stocks = await stock_data_fetcher()
        else:
            # Placeholder - would integrate with actual data service
            stocks = []
        
        # Apply filters
        filtered = self._apply_filters(stocks, screener.conditions)
        
        # Sort results
        if screener.sort_by:
            sort_field = screener.sort_by.value
            filtered.sort(
                key=lambda s: s.get(sort_field, 0) or 0,
                reverse=screener.sort_descending,
            )
        
        # Limit results
        filtered = filtered[:screener.max_results]
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # Update run count
        screener.run_count += 1
        screener.last_run = datetime.now(UTC)
        await self._save_screener(screener)
        
        result = ScreenerResult(
            screener_id=screener_id,
            run_at=datetime.now(UTC),
            stocks=filtered,
            total_matches=len(filtered),
            execution_time_ms=execution_time,
        )
        
        # Cache results
        if self.redis:
            results_key = self.RESULTS_KEY.format(screener_id=screener_id)
            await self.redis.setex(
                results_key,
                3600,  # 1 hour TTL
                json.dumps({
                    "run_at": result.run_at.isoformat(),
                    "stocks": result.stocks,
                    "total_matches": result.total_matches,
                }),
            )
        
        return result
    
    async def get_cached_results(
        self,
        user_id: str,
        screener_id: str,
    ) -> ScreenerResult | None:
        """Get cached screener results."""
        if not self.redis:
            return None
        
        # Verify access
        screener = await self.get_screener(user_id, screener_id)
        if not screener:
            return None
        
        results_key = self.RESULTS_KEY.format(screener_id=screener_id)
        data = await self.redis.get(results_key)
        
        if not data:
            return None
        
        cached = json.loads(data)
        return ScreenerResult(
            screener_id=screener_id,
            run_at=datetime.fromisoformat(cached["run_at"]),
            stocks=cached["stocks"],
            total_matches=cached["total_matches"],
            execution_time_ms=0,
        )
    
    # ================================
    # Presets
    # ================================
    
    def get_presets(self) -> list[dict]:
        """Get preset screener templates."""
        return PRESET_SCREENERS
    
    async def create_from_preset(
        self,
        user_id: str,
        preset_name: str,
    ) -> CustomScreener:
        """Create a screener from a preset template."""
        preset = next((p for p in PRESET_SCREENERS if p["name"] == preset_name), None)
        if not preset:
            raise ValueError(f"Preset '{preset_name}' not found")
        
        return await self.create_screener(
            user_id=user_id,
            name=preset["name"],
            description=preset.get("description"),
            conditions=preset["conditions"],
            sort_by=preset.get("sort_by"),
            sort_descending=preset.get("sort_descending", True),
        )
    
    # ================================
    # Filter Application
    # ================================
    
    def _apply_filters(
        self,
        stocks: list[dict],
        conditions: list[FilterCondition],
    ) -> list[dict]:
        """Apply filter conditions to stock list."""
        if not conditions:
            return stocks
        
        filtered = []
        for stock in stocks:
            if self._matches_conditions(stock, conditions):
                filtered.append(stock)
        
        return filtered
    
    def _matches_conditions(
        self,
        stock: dict,
        conditions: list[FilterCondition],
    ) -> bool:
        """Check if stock matches all conditions (AND logic)."""
        for condition in conditions:
            value = stock.get(condition.field.value)
            if value is None:
                return False
            
            if not self._evaluate_condition(value, condition):
                return False
        
        return True
    
    def _evaluate_condition(
        self,
        value: float | str,
        condition: FilterCondition,
    ) -> bool:
        """Evaluate a single condition."""
        op = condition.operator
        cond_value = condition.value
        
        try:
            if op == FilterOperator.EQUALS:
                return value == cond_value
            elif op == FilterOperator.NOT_EQUALS:
                return value != cond_value
            elif op == FilterOperator.GREATER_THAN:
                return float(value) > float(cond_value)
            elif op == FilterOperator.GREATER_OR_EQUAL:
                return float(value) >= float(cond_value)
            elif op == FilterOperator.LESS_THAN:
                return float(value) < float(cond_value)
            elif op == FilterOperator.LESS_OR_EQUAL:
                return float(value) <= float(cond_value)
            elif op == FilterOperator.BETWEEN:
                return float(condition.value) <= float(value) <= float(condition.value2)
            elif op == FilterOperator.IN:
                return value in cond_value
            elif op == FilterOperator.NOT_IN:
                return value not in cond_value
            elif op == FilterOperator.CONTAINS:
                return str(cond_value).lower() in str(value).lower()
        except (TypeError, ValueError):
            return False
        
        return False
    
    # ================================
    # Helpers
    # ================================
    
    async def _save_screener(self, screener: CustomScreener) -> None:
        """Save screener to Redis."""
        if not self.redis:
            raise RuntimeError("Redis not available")
        
        screener_key = self.SCREENER_KEY.format(screener_id=screener.screener_id)
        await self.redis.set(screener_key, json.dumps(screener.to_dict()))


# ============================================
# Factory Function
# ============================================


def get_custom_screener_service(
    redis_client: Redis | None = None,
) -> CustomScreenerService:
    """Get CustomScreenerService instance."""
    return CustomScreenerService(redis_client=redis_client)


# ============================================
# Field Metadata (for UI)
# ============================================


FILTER_FIELD_METADATA = {
    "price": {"label": "Price", "type": "number", "category": "Price"},
    "price_change": {"label": "Price Change ($)", "type": "number", "category": "Price"},
    "price_change_pct": {"label": "Price Change (%)", "type": "number", "category": "Price"},
    "rsi": {"label": "RSI", "type": "number", "category": "Technical", "min": 0, "max": 100},
    "rsi_14": {"label": "RSI (14)", "type": "number", "category": "Technical", "min": 0, "max": 100},
    "macd": {"label": "MACD", "type": "number", "category": "Technical"},
    "macd_signal": {"label": "MACD Signal", "type": "number", "category": "Technical"},
    "sma_20": {"label": "SMA (20)", "type": "number", "category": "Technical"},
    "sma_50": {"label": "SMA (50)", "type": "number", "category": "Technical"},
    "sma_200": {"label": "SMA (200)", "type": "number", "category": "Technical"},
    "volume": {"label": "Volume", "type": "number", "category": "Volume"},
    "average_volume": {"label": "Avg Volume", "type": "number", "category": "Volume"},
    "volume_ratio": {"label": "Volume Ratio", "type": "number", "category": "Volume"},
    "market_cap": {"label": "Market Cap", "type": "number", "category": "Fundamental"},
    "pe_ratio": {"label": "P/E Ratio", "type": "number", "category": "Fundamental"},
    "peg_ratio": {"label": "PEG Ratio", "type": "number", "category": "Fundamental"},
    "dividend_yield": {"label": "Dividend Yield (%)", "type": "number", "category": "Fundamental"},
    "revenue_growth": {"label": "Revenue Growth (%)", "type": "number", "category": "Fundamental"},
    "profit_margin": {"label": "Profit Margin (%)", "type": "number", "category": "Fundamental"},
    "sector": {"label": "Sector", "type": "select", "category": "Classification"},
    "industry": {"label": "Industry", "type": "select", "category": "Classification"},
    "momentum_score": {"label": "Momentum Score", "type": "number", "category": "Screening"},
    "maverick_score": {"label": "Maverick Score", "type": "number", "category": "Screening"},
}

