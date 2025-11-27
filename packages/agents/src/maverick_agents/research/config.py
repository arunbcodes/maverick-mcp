"""
Configuration constants for research agents.

Provides research depth levels and persona-specific research focus areas.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ResearchDepth(str, Enum):
    """Research depth levels."""

    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    EXHAUSTIVE = "exhaustive"


@dataclass
class ResearchDepthConfig:
    """Configuration for a research depth level."""

    max_sources: int
    max_searches: int
    analysis_depth: str
    validation_required: bool
    timeout_seconds: int


# Research depth levels optimized for thorough yet efficient searches
RESEARCH_DEPTH_LEVELS: dict[str, dict[str, Any]] = {
    "basic": {
        "max_sources": 3,
        "max_searches": 1,
        "analysis_depth": "summary",
        "validation_required": False,
        "timeout_seconds": 120,
    },
    "standard": {
        "max_sources": 5,
        "max_searches": 2,
        "analysis_depth": "detailed",
        "validation_required": False,
        "timeout_seconds": 240,
    },
    "comprehensive": {
        "max_sources": 10,
        "max_searches": 3,
        "analysis_depth": "comprehensive",
        "validation_required": False,
        "timeout_seconds": 360,
    },
    "exhaustive": {
        "max_sources": 15,
        "max_searches": 5,
        "analysis_depth": "exhaustive",
        "validation_required": True,
        "timeout_seconds": 600,
    },
}


def get_depth_config(depth: str | ResearchDepth) -> dict[str, Any]:
    """
    Get configuration for a research depth level.

    Args:
        depth: Research depth level name or enum

    Returns:
        Configuration dictionary for the depth level

    Raises:
        ValueError: If depth level is not found
    """
    if isinstance(depth, ResearchDepth):
        depth = depth.value

    if depth not in RESEARCH_DEPTH_LEVELS:
        raise ValueError(
            f"Unknown research depth: {depth}. "
            f"Available: {list(RESEARCH_DEPTH_LEVELS.keys())}"
        )

    return RESEARCH_DEPTH_LEVELS[depth]


# Persona-specific research focus areas
PERSONA_RESEARCH_FOCUS: dict[str, dict[str, Any]] = {
    "conservative": {
        "keywords": [
            "dividend",
            "stability",
            "risk",
            "debt",
            "cash flow",
            "established",
            "blue chip",
            "defensive",
        ],
        "sources": [
            "sec filings",
            "annual reports",
            "rating agencies",
            "dividend history",
            "credit ratings",
        ],
        "risk_focus": "downside protection",
        "time_horizon": "long-term",
        "analysis_priorities": [
            "financial_stability",
            "dividend_sustainability",
            "debt_levels",
            "cash_reserves",
        ],
    },
    "moderate": {
        "keywords": [
            "growth",
            "value",
            "balance",
            "diversification",
            "fundamentals",
            "earnings",
            "revenue",
        ],
        "sources": [
            "financial statements",
            "analyst reports",
            "industry analysis",
            "earnings calls",
        ],
        "risk_focus": "risk-adjusted returns",
        "time_horizon": "medium-term",
        "analysis_priorities": [
            "growth_trajectory",
            "valuation_metrics",
            "competitive_position",
            "market_trends",
        ],
    },
    "aggressive": {
        "keywords": [
            "growth",
            "momentum",
            "opportunity",
            "innovation",
            "expansion",
            "disruptive",
            "market share",
        ],
        "sources": [
            "news",
            "earnings calls",
            "industry trends",
            "competitive analysis",
            "product launches",
        ],
        "risk_focus": "upside potential",
        "time_horizon": "short to medium-term",
        "analysis_priorities": [
            "growth_catalysts",
            "market_opportunity",
            "competitive_moats",
            "innovation_pipeline",
        ],
    },
    "day_trader": {
        "keywords": [
            "catalysts",
            "earnings",
            "news",
            "volume",
            "volatility",
            "momentum",
            "breakout",
            "technical",
        ],
        "sources": [
            "breaking news",
            "social sentiment",
            "earnings announcements",
            "technical patterns",
            "options flow",
        ],
        "risk_focus": "short-term risks",
        "time_horizon": "intraday to weekly",
        "analysis_priorities": [
            "near_term_catalysts",
            "volume_patterns",
            "price_momentum",
            "sentiment_shifts",
        ],
    },
}


def get_persona_focus(persona: str) -> dict[str, Any]:
    """
    Get research focus configuration for a persona.

    Args:
        persona: Persona name

    Returns:
        Research focus configuration dictionary

    Raises:
        ValueError: If persona is not found
    """
    if persona not in PERSONA_RESEARCH_FOCUS:
        raise ValueError(
            f"Unknown persona: {persona}. "
            f"Available: {list(PERSONA_RESEARCH_FOCUS.keys())}"
        )

    return PERSONA_RESEARCH_FOCUS[persona]


def get_persona_keywords(persona: str) -> list[str]:
    """Get search keywords for a persona."""
    focus = get_persona_focus(persona)
    return focus.get("keywords", [])


def get_persona_sources(persona: str) -> list[str]:
    """Get preferred sources for a persona."""
    focus = get_persona_focus(persona)
    return focus.get("sources", [])
