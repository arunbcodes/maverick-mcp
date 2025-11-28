"""
LLM optimization utilities for research agents.

This module provides comprehensive optimization strategies including:
- Adaptive model selection based on time constraints
- Progressive token budgeting with confidence tracking
- Parallel LLM processing with intelligent load balancing
- Optimized prompt engineering for speed
- Early termination based on confidence thresholds
- Content filtering to reduce processing overhead
"""

from maverick_agents.research.optimization.model_selection import (
    AdaptiveModelSelector,
    ModelConfiguration,
)
from maverick_agents.research.optimization.token_budgeting import (
    ProgressiveTokenBudgeter,
    ResearchPhase,
    TokenAllocation,
)
from maverick_agents.research.optimization.confidence_tracker import ConfidenceTracker
from maverick_agents.research.optimization.content_filter import IntelligentContentFilter
from maverick_agents.research.optimization.prompt_engine import OptimizedPromptEngine
from maverick_agents.research.optimization.parallel_processor import ParallelLLMProcessor

__all__ = [
    # Model selection
    "AdaptiveModelSelector",
    "ModelConfiguration",
    # Token budgeting
    "ProgressiveTokenBudgeter",
    "ResearchPhase",
    "TokenAllocation",
    # Confidence tracking
    "ConfidenceTracker",
    # Content filtering
    "IntelligentContentFilter",
    # Prompt optimization
    "OptimizedPromptEngine",
    # Parallel processing
    "ParallelLLMProcessor",
]
