"""
Confidence tracking for research agents.

Tracks research confidence and triggers early termination when appropriate
based on evidence accumulation and sentiment consensus.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


class ConfidenceTracker:
    """Tracks research confidence and triggers early termination when appropriate."""

    def __init__(
        self,
        target_confidence: float = 0.75,
        min_sources: int = 3,
        max_sources: int = 15,
    ):
        self.target_confidence = target_confidence
        self.min_sources = min_sources
        self.max_sources = max_sources
        self.confidence_history: list[float] = []
        self.evidence_history: list[dict[str, Any]] = []
        self.source_count = 0
        self.sources_analyzed = 0
        self.last_significant_improvement = 0
        self.sentiment_votes: dict[str, float] = {
            "bullish": 0,
            "bearish": 0,
            "neutral": 0,
        }

    def update_confidence(
        self,
        new_evidence: dict[str, Any],
        source_credibility: float | None = None,
        credibility_score: float | None = None,
    ) -> dict[str, Any]:
        """Update confidence based on new evidence and return continuation decision."""

        if source_credibility is None and credibility_score is not None:
            source_credibility = credibility_score
        elif source_credibility is None and credibility_score is None:
            source_credibility = 0.5

        self.source_count += 1
        self.sources_analyzed += 1

        self.evidence_history.append(
            {
                "evidence": new_evidence,
                "credibility": source_credibility,
                "timestamp": datetime.now(),
            }
        )

        # Update sentiment voting
        sentiment = new_evidence.get("sentiment", {})
        direction = sentiment.get("direction", "neutral")
        confidence = sentiment.get("confidence", 0.5)

        vote_weight = source_credibility * confidence
        self.sentiment_votes[direction] += vote_weight

        evidence_strength = self._calculate_evidence_strength(
            new_evidence, source_credibility
        )

        current_confidence = self._update_bayesian_confidence(evidence_strength)
        self.confidence_history.append(current_confidence)

        if len(self.confidence_history) >= 2:
            improvement = current_confidence - self.confidence_history[-2]
            if improvement > 0.1:
                self.last_significant_improvement = self.source_count

        should_continue = self._should_continue_research(current_confidence)

        return {
            "current_confidence": current_confidence,
            "should_continue": should_continue,
            "sources_processed": self.source_count,
            "sources_analyzed": self.source_count,
            "confidence_trend": self._calculate_confidence_trend(),
            "early_termination_reason": None
            if should_continue
            else self._get_termination_reason(current_confidence),
            "sentiment_consensus": self._calculate_sentiment_consensus(),
        }

    def _calculate_evidence_strength(
        self, evidence: dict[str, Any], credibility: float
    ) -> float:
        """Calculate the strength of new evidence."""

        sentiment = evidence.get("sentiment", {})
        sentiment_confidence = sentiment.get("confidence", 0.5)

        credibility_adjusted = sentiment_confidence * credibility

        insights_count = len(evidence.get("insights", []))
        risk_factors_count = len(evidence.get("risk_factors", []))
        opportunities_count = len(evidence.get("opportunities", []))

        evidence_richness = min(
            (insights_count + risk_factors_count + opportunities_count) / 12, 1.0
        )

        relevance_score = evidence.get("relevance_score", 0.5)

        final_strength = credibility_adjusted * (
            0.5 + 0.3 * evidence_richness + 0.2 * relevance_score
        )

        return min(final_strength, 1.0)

    def _update_bayesian_confidence(self, evidence_strength: float) -> float:
        """Update confidence using Bayesian approach."""

        if not self.confidence_history:
            return evidence_strength

        prior = self.confidence_history[-1]

        decay_factor = 0.9 ** (self.source_count - 1)

        updated = prior * decay_factor + evidence_strength * (1 - decay_factor)

        return max(0.1, min(updated, 0.95))

    def _should_continue_research(self, current_confidence: float) -> bool:
        """Determine if research should continue based on multiple factors."""

        if self.source_count < self.min_sources:
            return True

        if self.source_count >= self.max_sources:
            return False

        if current_confidence >= self.target_confidence:
            return False

        if self.source_count - self.last_significant_improvement > 4:
            return False

        consensus_score = self._calculate_sentiment_consensus()
        if consensus_score > 0.8 and self.source_count >= 5:
            return False

        if len(self.confidence_history) >= 3:
            recent_change = abs(current_confidence - self.confidence_history[-3])
            if recent_change < 0.03:
                return False

        return True

    def _calculate_confidence_trend(self) -> str:
        """Calculate the trend in confidence over recent sources."""

        if len(self.confidence_history) < 3:
            return "insufficient_data"

        recent = self.confidence_history[-3:]

        if recent[-1] > recent[0] + 0.05:
            return "increasing"
        elif recent[-1] < recent[0] - 0.05:
            return "decreasing"
        else:
            return "stable"

    def _calculate_sentiment_consensus(self) -> float:
        """Calculate how much sources agree on sentiment."""

        total_votes = sum(self.sentiment_votes.values())
        if total_votes == 0:
            return 0.0

        max_votes = max(self.sentiment_votes.values())
        consensus = max_votes / total_votes

        return consensus

    def _get_termination_reason(self, current_confidence: float) -> str:
        """Get reason for early termination."""

        if current_confidence >= self.target_confidence:
            return "target_confidence_reached"
        elif self.source_count >= self.max_sources:
            return "max_sources_reached"
        elif self._calculate_sentiment_consensus() > 0.8:
            return "strong_consensus"
        elif self.source_count - self.last_significant_improvement > 4:
            return "diminishing_returns"
        else:
            return "confidence_plateau"
