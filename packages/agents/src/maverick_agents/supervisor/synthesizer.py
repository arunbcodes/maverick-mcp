"""
Result synthesis for multi-agent coordination.

Provides synthesis of results from multiple agents with conflict resolution.
"""

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from maverick_agents.personas import InvestorPersona
from maverick_agents.supervisor.routing import get_agent_weights

logger = logging.getLogger(__name__)


class ResultSynthesizer:
    """Synthesize results from multiple agents with conflict resolution."""

    def __init__(self, llm: BaseChatModel, persona: InvestorPersona):
        """
        Initialize the result synthesizer.

        Args:
            llm: Language model for synthesis
            persona: Investor persona for tailored responses
        """
        self.llm = llm
        self.persona = persona

    async def synthesize_results(
        self,
        agent_results: dict[str, Any],
        query_type: str,
        conflicts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Synthesize final recommendation from agent results.

        Args:
            agent_results: Results from each agent
            query_type: Type of query being answered
            conflicts: List of detected conflicts between agents

        Returns:
            Synthesized result with confidence scoring
        """
        # Calculate agent weights based on query type and persona
        weights = self._calculate_agent_weights(query_type, agent_results)

        # Create synthesis prompt
        synthesis_prompt = self._build_synthesis_prompt(
            agent_results, weights, query_type, conflicts
        )

        # Use LLM to synthesize coherent response
        synthesis_response = await self.llm.ainvoke(
            [
                SystemMessage(content="You are a financial analysis synthesizer."),
                HumanMessage(content=synthesis_prompt),
            ]
        )

        return {
            "synthesis": synthesis_response.content,
            "weights_applied": weights,
            "conflicts_resolved": len(conflicts),
            "confidence_score": self._calculate_overall_confidence(
                agent_results, weights
            ),
            "contributing_agents": list(agent_results.keys()),
            "persona_alignment": self._assess_persona_alignment(
                synthesis_response.content
            ),
        }

    def _calculate_agent_weights(
        self, query_type: str, agent_results: dict
    ) -> dict[str, float]:
        """
        Calculate weights for agent results based on context.

        Args:
            query_type: Type of query
            agent_results: Results from agents

        Returns:
            Dictionary mapping agent names to weights
        """
        weights = get_agent_weights(query_type)

        # Adjust weights based on agent confidence scores
        for agent, base_weight in list(weights.items()):
            if agent in agent_results:
                confidence = agent_results[agent].get("confidence_score", 0.5)
                weights[agent] = base_weight * (0.5 + confidence * 0.5)

        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        return weights

    def _build_synthesis_prompt(
        self,
        agent_results: dict[str, Any],
        weights: dict[str, float],
        query_type: str,
        conflicts: list[dict[str, Any]],
    ) -> str:
        """Build synthesis prompt for LLM."""
        prompt = f"""
        Synthesize a comprehensive financial analysis response from multiple specialized agents.

        Query Type: {query_type}
        Investor Persona: {self.persona.name} - {", ".join(self.persona.characteristics)}

        Agent Results:
        """

        for agent, result in agent_results.items():
            weight = weights.get(agent, 0.0)
            prompt += f"\n{agent.upper()} Agent (Weight: {weight:.2f}):\n"
            prompt += f"  - Confidence: {result.get('confidence_score', 0.5)}\n"
            prompt += (
                f"  - Analysis: {result.get('analysis', 'No analysis provided')}\n"
            )
            if "recommendations" in result:
                prompt += f"  - Recommendations: {result['recommendations']}\n"

        if conflicts:
            prompt += f"\nConflicts Detected ({len(conflicts)}):\n"
            for i, conflict in enumerate(conflicts, 1):
                prompt += f"{i}. {conflict}\n"

        prompt += f"""

        Please synthesize these results into a coherent, actionable response that:
        1. Weighs agent inputs according to their weights and confidence scores
        2. Resolves any conflicts using the {self.persona.name} investor perspective
        3. Provides clear, actionable recommendations aligned with {self.persona.name} characteristics
        4. Includes appropriate risk disclaimers
        5. Maintains professional, confident tone

        Focus on actionable insights for the {self.persona.name} investor profile.
        """

        return prompt

    def _calculate_overall_confidence(
        self, agent_results: dict, weights: dict[str, float]
    ) -> float:
        """
        Calculate weighted overall confidence score.

        Args:
            agent_results: Results from agents
            weights: Agent weights

        Returns:
            Overall confidence score (0-1)
        """
        total_confidence = 0.0
        total_weight = 0.0

        for agent, weight in weights.items():
            if agent in agent_results:
                confidence = agent_results[agent].get("confidence_score", 0.5)
                total_confidence += confidence * weight
                total_weight += weight

        return total_confidence / total_weight if total_weight > 0 else 0.5

    def _assess_persona_alignment(self, synthesis_content: str) -> float:
        """
        Assess how well synthesis aligns with investor persona.

        Args:
            synthesis_content: Synthesized content

        Returns:
            Alignment score (0-1)
        """
        # Keyword-based alignment scoring
        persona_keywords = {
            "conservative": ["stable", "dividend", "low-risk", "preservation", "income"],
            "moderate": ["balanced", "diversified", "moderate", "growth", "value"],
            "aggressive": ["growth", "momentum", "high-return", "opportunity", "upside"],
            "day_trader": ["momentum", "volatility", "catalyst", "breakout", "volume"],
        }

        keywords = persona_keywords.get(self.persona.name.lower(), [])
        content_lower = synthesis_content.lower()

        if not keywords:
            return 0.5

        alignment_score = sum(1 for keyword in keywords if keyword in content_lower)
        return min(alignment_score / len(keywords), 1.0)

    def synthesize_sync(
        self,
        agent_results: dict[str, Any],
        query_type: str,
        conflicts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Synchronous synthesis without LLM (basic aggregation).

        Args:
            agent_results: Results from agents
            query_type: Query type
            conflicts: Detected conflicts

        Returns:
            Basic synthesized result
        """
        weights = self._calculate_agent_weights(query_type, agent_results)

        # Basic text aggregation
        synthesis_parts = []
        for agent, result in agent_results.items():
            analysis = result.get("analysis", result.get("content", ""))
            if analysis:
                synthesis_parts.append(f"[{agent.upper()}]: {analysis}")

        return {
            "synthesis": "\n\n".join(synthesis_parts) or "No results to synthesize",
            "weights_applied": weights,
            "conflicts_resolved": len(conflicts),
            "confidence_score": self._calculate_overall_confidence(
                agent_results, weights
            ),
            "contributing_agents": list(agent_results.keys()),
            "persona_alignment": 0.5,
        }
