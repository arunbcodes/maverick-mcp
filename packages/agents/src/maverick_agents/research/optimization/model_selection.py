"""
Adaptive model selection for research agents.

Provides intelligent model selection based on time budgets, task complexity,
and performance requirements.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from maverick_agents.llm import OpenRouterProvider

from maverick_agents.llm import TaskType

logger = logging.getLogger(__name__)


class ModelConfiguration(BaseModel):
    """Configuration for model selection with time optimization."""

    model_id: str = Field(description="OpenRouter model identifier")
    max_tokens: int = Field(description="Maximum output tokens")
    temperature: float = Field(description="Model temperature")
    timeout_seconds: float = Field(description="Request timeout")
    parallel_batch_size: int = Field(
        default=1, description="Sources per batch for this model"
    )


class AdaptiveModelSelector:
    """Intelligent model selection based on time budgets and task complexity."""

    def __init__(self, openrouter_provider: OpenRouterProvider):
        self.provider = openrouter_provider
        self.performance_cache: dict[str, float] = {}

    def select_model_for_time_budget(
        self,
        task_type: TaskType,
        time_remaining_seconds: float,
        complexity_score: float,
        content_size_tokens: int,
        confidence_threshold: float = 0.8,
        current_confidence: float = 0.0,
    ) -> ModelConfiguration:
        """Select optimal model based on available time and requirements."""

        if time_remaining_seconds < 10:
            return self._select_emergency_model(task_type, content_size_tokens)
        elif time_remaining_seconds < 25:
            return self._select_fast_quality_model(task_type, complexity_score)
        elif time_remaining_seconds < 45:
            return self._select_balanced_model(
                task_type, complexity_score, current_confidence
            )
        else:
            return self._select_optimal_model(
                task_type, complexity_score, confidence_threshold
            )

    def _select_emergency_model(
        self, task_type: TaskType, content_size: int
    ) -> ModelConfiguration:
        """Ultra-fast models for time-critical situations."""
        if content_size > 20000:
            return ModelConfiguration(
                model_id="google/gemini-2.5-flash",
                max_tokens=min(800, content_size // 25),
                temperature=0.05,
                timeout_seconds=5,
                parallel_batch_size=8,
            )
        else:
            return ModelConfiguration(
                model_id="openai/gpt-4o-mini",
                max_tokens=min(500, content_size // 20),
                temperature=0.03,
                timeout_seconds=4,
                parallel_batch_size=10,
            )

    def _select_fast_quality_model(
        self, task_type: TaskType, complexity_score: float
    ) -> ModelConfiguration:
        """Balance speed and quality for time-constrained situations."""
        if complexity_score > 0.7 or task_type == TaskType.COMPLEX_REASONING:
            return ModelConfiguration(
                model_id="openai/gpt-4o-mini",
                max_tokens=1200,
                temperature=0.1,
                timeout_seconds=10,
                parallel_batch_size=6,
            )
        else:
            return ModelConfiguration(
                model_id="google/gemini-2.5-flash",
                max_tokens=1000,
                temperature=0.1,
                timeout_seconds=8,
                parallel_batch_size=8,
            )

    def _select_balanced_model(
        self, task_type: TaskType, complexity_score: float, current_confidence: float
    ) -> ModelConfiguration:
        """Standard mode with cost-effectiveness focus."""
        if current_confidence > 0.7:
            return ModelConfiguration(
                model_id="google/gemini-2.5-flash",
                max_tokens=1500,
                temperature=0.25,
                timeout_seconds=20,
                parallel_batch_size=4,
            )

        if task_type in [TaskType.DEEP_RESEARCH, TaskType.RESULT_SYNTHESIS]:
            return ModelConfiguration(
                model_id="openai/gpt-4o-mini",
                max_tokens=2000,
                temperature=0.3,
                timeout_seconds=25,
                parallel_batch_size=3,
            )
        else:
            return ModelConfiguration(
                model_id="google/gemini-2.5-flash",
                max_tokens=1500,
                temperature=0.25,
                timeout_seconds=20,
                parallel_batch_size=4,
            )

    def _select_optimal_model(
        self, task_type: TaskType, complexity_score: float, confidence_threshold: float
    ) -> ModelConfiguration:
        """Comprehensive mode for complex analysis."""
        if complexity_score > 0.8 and task_type == TaskType.DEEP_RESEARCH:
            return ModelConfiguration(
                model_id="google/gemini-2.5-pro",
                max_tokens=3000,
                temperature=0.3,
                timeout_seconds=45,
                parallel_batch_size=1,
            )

        return ModelConfiguration(
            model_id="anthropic/claude-sonnet-4",
            max_tokens=2500,
            temperature=0.3,
            timeout_seconds=40,
            parallel_batch_size=2,
        )

    def calculate_task_complexity(
        self, content: str, task_type: TaskType, focus_areas: list[str] | None = None
    ) -> float:
        """Calculate complexity score based on content and task requirements."""
        if not content:
            return 0.3

        content_lower = content.lower()

        complexity_indicators = {
            "financial_jargon": len(
                re.findall(
                    r"\b(?:ebitda|dcf|roic?|wacc|beta|volatility|sharpe)\b",
                    content_lower,
                )
            ),
            "numerical_data": len(re.findall(r"\$?[\d,]+\.?\d*[%kmbKMB]?", content)),
            "comparative_analysis": len(
                re.findall(
                    r"\b(?:versus|compared|relative|outperform|underperform)\b",
                    content_lower,
                )
            ),
            "temporal_analysis": len(
                re.findall(r"\b(?:quarterly|q[1-4]|fy|yoy|qoq|annual)\b", content_lower)
            ),
            "market_terms": len(
                re.findall(
                    r"\b(?:bullish|bearish|catalyst|headwind|tailwind)\b", content_lower
                )
            ),
            "technical_terms": len(
                re.findall(
                    r"\b(?:support|resistance|breakout|rsi|macd|sma|ema)\b",
                    content_lower,
                )
            ),
        }

        total_indicators = sum(complexity_indicators.values())
        content_length = len(content.split())
        base_complexity = min(total_indicators / max(content_length / 100, 1), 1.0)

        task_multipliers = {
            TaskType.DEEP_RESEARCH: 1.4,
            TaskType.COMPLEX_REASONING: 1.6,
            TaskType.RESULT_SYNTHESIS: 1.2,
            TaskType.TECHNICAL_ANALYSIS: 1.3,
            TaskType.SENTIMENT_ANALYSIS: 0.8,
            TaskType.QUICK_ANSWER: 0.5,
        }

        focus_multiplier = 1.0
        if focus_areas:
            complex_focus_areas = [
                "competitive_analysis",
                "fundamental_analysis",
                "complex_reasoning",
            ]
            if any(area in focus_areas for area in complex_focus_areas):
                focus_multiplier = 1.2

        final_complexity = (
            base_complexity * task_multipliers.get(task_type, 1.0) * focus_multiplier
        )
        return min(final_complexity, 1.0)
