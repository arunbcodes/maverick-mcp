"""
Base models and common types for MaverickMCP schemas.

This module provides the foundation for all Pydantic models in the system.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MaverickBaseModel(BaseModel):
    """
    Base model with consistent configuration for all Maverick schemas.
    
    Features:
    - ORM mode for SQLAlchemy compatibility
    - Field alias support for API flexibility
    - Enum values serialization
    """
    
    model_config = ConfigDict(
        from_attributes=True,  # ORM mode - allows creating from SQLAlchemy models
        populate_by_name=True,  # Allow field aliases
        use_enum_values=True,  # Serialize enums to their values
        str_strip_whitespace=True,  # Strip whitespace from strings
        validate_default=True,  # Validate default values
    )


class TimestampMixin(BaseModel):
    """Mixin for models that track creation and update times."""
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None


class Market(str, Enum):
    """Supported markets."""
    
    US = "US"
    NSE = "NSE"  # National Stock Exchange of India
    BSE = "BSE"  # Bombay Stock Exchange
    CRYPTO = "CRYPTO"


class TimeInterval(str, Enum):
    """Time intervals for historical data."""
    
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1wk"
    MONTH_1 = "1mo"


class Tier(str, Enum):
    """User subscription tiers."""
    
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class AuthMethod(str, Enum):
    """Authentication methods."""
    
    COOKIE = "cookie"
    JWT = "jwt"
    API_KEY = "api_key"


class SentimentScore(str, Enum):
    """Sentiment classifications."""
    
    VERY_BULLISH = "very_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very_bearish"


class TrendDirection(str, Enum):
    """Trend direction classifications."""
    
    STRONG_UP = "strong_up"
    UP = "up"
    SIDEWAYS = "sideways"
    DOWN = "down"
    STRONG_DOWN = "strong_down"


class OrderSide(str, Enum):
    """Order side for trades."""
    
    BUY = "buy"
    SELL = "sell"


class PositionStatus(str, Enum):
    """Position status."""
    
    OPEN = "open"
    CLOSED = "closed"


# Type aliases for common patterns
JsonDict = dict[str, Any]


__all__ = [
    "MaverickBaseModel",
    "TimestampMixin",
    "Market",
    "TimeInterval",
    "Tier",
    "AuthMethod",
    "SentimentScore",
    "TrendDirection",
    "OrderSide",
    "PositionStatus",
    "JsonDict",
]

