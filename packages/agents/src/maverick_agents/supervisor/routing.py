"""
Query routing configuration for multi-agent coordination.

Provides routing matrix and decision logic for directing queries
to appropriate specialized agents.
"""

from typing import Any


# Query routing matrix for intelligent agent selection
ROUTING_MATRIX: dict[str, dict[str, Any]] = {
    "market_screening": {
        "agents": ["market"],
        "primary": "market",
        "parallel": False,
        "confidence_threshold": 0.7,
        "synthesis_required": False,
    },
    "technical_analysis": {
        "agents": ["technical"],
        "primary": "technical",
        "parallel": False,
        "confidence_threshold": 0.8,
        "synthesis_required": False,
    },
    "stock_investment_decision": {
        "agents": ["market", "technical"],
        "primary": "technical",
        "parallel": True,
        "confidence_threshold": 0.85,
        "synthesis_required": True,
    },
    "portfolio_analysis": {
        "agents": ["market", "technical"],
        "primary": "market",
        "parallel": True,
        "confidence_threshold": 0.75,
        "synthesis_required": True,
    },
    "deep_research": {
        "agents": ["research"],
        "primary": "research",
        "parallel": False,
        "confidence_threshold": 0.9,
        "synthesis_required": False,
    },
    "company_research": {
        "agents": ["research"],
        "primary": "research",
        "parallel": False,
        "confidence_threshold": 0.85,
        "synthesis_required": False,
    },
    "sentiment_analysis": {
        "agents": ["research"],
        "primary": "research",
        "parallel": False,
        "confidence_threshold": 0.8,
        "synthesis_required": False,
    },
    "risk_assessment": {
        "agents": ["market", "technical"],
        "primary": "market",
        "parallel": True,
        "confidence_threshold": 0.8,
        "synthesis_required": True,
    },
}


# Agent weight configuration by query type
AGENT_WEIGHTS: dict[str, dict[str, float]] = {
    "market_screening": {"market": 0.9, "technical": 0.1},
    "technical_analysis": {"market": 0.2, "technical": 0.8},
    "stock_investment_decision": {"market": 0.4, "technical": 0.6},
    "portfolio_analysis": {"market": 0.6, "technical": 0.4},
    "deep_research": {"research": 1.0},
    "company_research": {"research": 1.0},
    "sentiment_analysis": {"research": 1.0},
    "risk_assessment": {"market": 0.3, "technical": 0.3, "risk": 0.4},
}


# Keywords for rule-based classification fallback
CLASSIFICATION_KEYWORDS: dict[str, list[str]] = {
    "market_screening": ["screen", "find stocks", "scan", "search", "filter"],
    "technical_analysis": ["chart", "technical", "rsi", "macd", "pattern", "indicator"],
    "portfolio_analysis": ["portfolio", "allocation", "diversif", "holdings", "balance"],
    "deep_research": ["research", "fundamental", "news", "earnings", "analyze"],
    "company_research": ["company", "business", "competitive", "industry", "sector"],
    "sentiment_analysis": ["sentiment", "opinion", "mood", "feeling", "outlook"],
    "risk_assessment": ["risk", "position size", "stop loss", "drawdown", "volatility"],
}


def get_routing_config(category: str) -> dict[str, Any]:
    """
    Get routing configuration for a query category.

    Args:
        category: Query category name

    Returns:
        Routing configuration dictionary
    """
    return ROUTING_MATRIX.get(category, ROUTING_MATRIX["stock_investment_decision"])


def get_agent_weights(query_type: str) -> dict[str, float]:
    """
    Get agent weights for a query type.

    Args:
        query_type: Query type/category

    Returns:
        Dictionary mapping agent names to weights
    """
    return AGENT_WEIGHTS.get(query_type, {"market": 0.5, "technical": 0.5})


def classify_query_by_keywords(query: str) -> str:
    """
    Classify query using keyword matching (rule-based fallback).

    Args:
        query: User query string

    Returns:
        Category name
    """
    query_lower = query.lower()

    for category, keywords in CLASSIFICATION_KEYWORDS.items():
        if any(keyword in query_lower for keyword in keywords):
            return category

    return "stock_investment_decision"
