"""
Optimized research agents with LLM-side optimizations.

This module provides enhanced research agents with comprehensive optimization
strategies to prevent timeouts and improve performance.
"""

from maverick_agents.research.optimized.research import (
    OptimizedContentAnalyzer,
    OptimizedDeepResearchAgent,
    create_optimized_research_agent,
)

__all__ = [
    "OptimizedContentAnalyzer",
    "OptimizedDeepResearchAgent",
    "create_optimized_research_agent",
]
