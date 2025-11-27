"""
Query classification for intelligent agent routing.

Provides LLM-powered query classification with rule-based fallback.
"""

import json
import logging
from datetime import datetime
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from maverick_agents.supervisor.routing import (
    ROUTING_MATRIX,
    classify_query_by_keywords,
    get_routing_config,
)

logger = logging.getLogger(__name__)


class QueryClassifier:
    """LLM-powered query classification with rule-based fallback."""

    def __init__(self, llm: BaseChatModel):
        """
        Initialize the query classifier.

        Args:
            llm: Language model for classification
        """
        self.llm = llm

    async def classify_query(self, query: str, persona: str) -> dict[str, Any]:
        """
        Classify query using LLM with structured output.

        Args:
            query: User query to classify
            persona: Investor persona name

        Returns:
            Classification result with routing configuration
        """
        classification_prompt = self._build_classification_prompt(query, persona)

        try:
            response = await self.llm.ainvoke(
                [
                    SystemMessage(
                        content="You are a financial query classifier. Return only valid JSON."
                    ),
                    HumanMessage(content=classification_prompt),
                ]
            )

            # Parse LLM response
            classification = json.loads(response.content.strip())

            # Validate and enhance with routing matrix
            category = classification.get("category", "stock_investment_decision")
            routing_config = get_routing_config(category)

            return {
                **classification,
                "routing_config": routing_config,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            logger.warning(f"LLM classification failed: {e}, using rule-based fallback")
            return self._rule_based_fallback(query, persona)

    def _build_classification_prompt(self, query: str, persona: str) -> str:
        """Build the classification prompt for the LLM."""
        return f"""
        Analyze this financial query and classify it for multi-agent routing.

        Query: "{query}"
        Investor Persona: {persona}

        Classify into one of these categories:
        1. market_screening - Finding stocks, sector analysis, market breadth
        2. technical_analysis - Chart patterns, indicators, entry/exit points
        3. stock_investment_decision - Complete analysis of specific stock(s)
        4. portfolio_analysis - Portfolio optimization, risk assessment
        5. deep_research - Fundamental analysis, company research, news analysis
        6. risk_assessment - Position sizing, risk management, portfolio risk

        Consider the complexity and return classification with confidence.

        Return ONLY valid JSON in this exact format:
        {{
            "category": "category_name",
            "confidence": 0.85,
            "required_agents": ["agent1", "agent2"],
            "complexity": "simple",
            "estimated_execution_time_ms": 30000,
            "parallel_capable": true,
            "reasoning": "Brief explanation of classification"
        }}
        """

    def _rule_based_fallback(self, query: str, persona: str) -> dict[str, Any]:
        """
        Rule-based classification fallback when LLM fails.

        Args:
            query: User query to classify
            persona: Investor persona name

        Returns:
            Classification result
        """
        category = classify_query_by_keywords(query)
        routing_config = get_routing_config(category)

        return {
            "category": category,
            "confidence": 0.6,
            "required_agents": routing_config["agents"],
            "complexity": "moderate",
            "estimated_execution_time_ms": 60000,
            "parallel_capable": routing_config["parallel"],
            "reasoning": "Rule-based classification fallback",
            "routing_config": routing_config,
            "timestamp": datetime.now(),
        }

    def classify_sync(self, query: str, persona: str) -> dict[str, Any]:
        """
        Synchronous classification using rule-based approach.

        Useful when async is not available.

        Args:
            query: User query to classify
            persona: Investor persona name

        Returns:
            Classification result
        """
        return self._rule_based_fallback(query, persona)
