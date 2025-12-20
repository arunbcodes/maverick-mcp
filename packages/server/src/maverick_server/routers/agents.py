"""
Agent router for LangGraph-based financial analysis agents.

This router exposes the LangGraph agents as MCP tools while maintaining
compatibility with the existing infrastructure.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Any

from fastmcp import FastMCP

from maverick_server.capabilities_integration import with_audit

logger = logging.getLogger(__name__)

# Cache for agent instances to avoid recreation
_agent_cache: dict[str, Any] = {}


def _get_maverick_agents():
    """Lazy import maverick_agents to handle optional dependency."""
    try:
        from maverick_agents.analyzers.market import MarketAnalyzer
        from maverick_agents.llm.factory import get_llm
        from maverick_agents.llm.openrouter import TaskType
        from maverick_agents.research.optimized.research import OptimizedResearchAgent
        from maverick_agents.supervisor.agent import SupervisorAgent

        return {
            "MarketAnalyzer": MarketAnalyzer,
            "SupervisorAgent": SupervisorAgent,
            "OptimizedResearchAgent": OptimizedResearchAgent,
            "get_llm": get_llm,
            "TaskType": TaskType,
        }
    except ImportError as e:
        logger.warning(f"maverick_agents not fully available: {e}")
        return None


def get_or_create_agent(agent_type: str, persona: str = "moderate") -> Any:
    """Get or create an agent instance with caching."""
    cache_key = f"{agent_type}:{persona}"

    if cache_key not in _agent_cache:
        agents = _get_maverick_agents()
        if agents is None:
            raise ImportError("maverick_agents package not available")

        get_llm = agents["get_llm"]
        TaskType = agents["TaskType"]

        # Map agent types to task types for optimal model selection
        task_mapping = {
            "market": TaskType.MARKET_ANALYSIS,
            "technical": TaskType.TECHNICAL_ANALYSIS,
            "supervisor": TaskType.MULTI_AGENT_ORCHESTRATION,
            "deep_research": TaskType.DEEP_RESEARCH,
        }

        task_type = task_mapping.get(agent_type, TaskType.GENERAL)

        # Get optimized LLM for this task
        llm = get_llm(task_type=task_type)

        # Create agent based on type
        if agent_type == "market":
            MarketAnalyzer = agents["MarketAnalyzer"]
            _agent_cache[cache_key] = MarketAnalyzer(
                llm=llm, persona=persona, ttl_hours=1
            )
        elif agent_type == "supervisor":
            SupervisorAgent = agents["SupervisorAgent"]
            # Create with available agents
            sub_agents = {
                "market": get_or_create_agent("market", persona),
            }
            _agent_cache[cache_key] = SupervisorAgent(
                llm=llm, agents=sub_agents, persona=persona, ttl_hours=1
            )
        elif agent_type == "deep_research":
            OptimizedResearchAgent = agents["OptimizedResearchAgent"]
            exa_api_key = os.getenv("EXA_API_KEY")
            agent = OptimizedResearchAgent(
                llm=llm,
                persona=persona,
                ttl_hours=1,
                exa_api_key=exa_api_key,
            )
            _agent_cache[cache_key] = agent
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    return _agent_cache[cache_key]


def register_agents_tools(mcp: FastMCP) -> None:
    """Register agent tools with the MCP server."""

    @mcp.tool(description="Analyze market using LangGraph agent with persona-aware recommendations.")
    @with_audit("agents_analyze_market")
    async def analyze_market_with_agent(
        query: str,
        persona: str = "moderate",
        screening_strategy: str = "momentum",
        max_results: int = 20,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Analyze market using LangGraph agent with persona-aware recommendations.

        Args:
            query: Market analysis query (e.g., "Find top momentum stocks")
            persona: Investor persona (conservative, moderate, aggressive)
            screening_strategy: Strategy to use (momentum, maverick, supply_demand_breakout)
            max_results: Maximum number of results
            session_id: Optional session ID for conversation continuity

        Returns:
            Persona-adjusted market analysis with recommendations
        """
        try:
            if not session_id:
                session_id = str(uuid.uuid4())

            agent = get_or_create_agent("market", persona)

            result = await agent.analyze_market(
                query=query,
                session_id=session_id,
                screening_strategy=screening_strategy,
                max_results=max_results,
            )

            return {
                "status": "success",
                "agent_type": "market_analysis",
                "persona": persona,
                "session_id": session_id,
                **result,
            }

        except Exception as e:
            logger.error(f"Error in market agent analysis: {str(e)}")
            return {"status": "error", "error": str(e), "agent_type": "market_analysis"}

    @mcp.tool(description="Get streaming market analysis with real-time updates.")
    @with_audit("agents_streaming_analysis")
    async def get_agent_streaming_analysis(
        query: str,
        persona: str = "moderate",
        stream_mode: str = "updates",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Get streaming market analysis with real-time updates.

        Args:
            query: Analysis query
            persona: Investor persona
            stream_mode: Streaming mode (updates, values, messages)
            session_id: Optional session ID

        Returns:
            Streaming configuration and initial results
        """
        try:
            if not session_id:
                session_id = str(uuid.uuid4())

            agent = get_or_create_agent("market", persona)

            updates = []
            async for chunk in agent.stream_analysis(
                query=query, session_id=session_id, stream_mode=stream_mode
            ):
                updates.append(chunk)
                if len(updates) >= 5:
                    break

            return {
                "status": "success",
                "stream_mode": stream_mode,
                "persona": persona,
                "session_id": session_id,
                "updates_collected": len(updates),
                "sample_updates": updates[:3],
                "note": "Full streaming requires WebSocket or SSE endpoint",
            }

        except Exception as e:
            logger.error(f"Error in streaming analysis: {str(e)}")
            return {"status": "error", "error": str(e)}

    @mcp.tool(description="Run orchestrated multi-agent analysis using the SupervisorAgent.")
    @with_audit("agents_orchestrated_analysis")
    async def orchestrated_analysis(
        query: str,
        persona: str = "moderate",
        routing_strategy: str = "llm_powered",
        max_agents: int = 3,
        parallel_execution: bool = True,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Run orchestrated multi-agent analysis using the SupervisorAgent.

        Args:
            query: Financial analysis query
            persona: Investor persona (conservative, moderate, aggressive, day_trader)
            routing_strategy: How to route tasks (llm_powered, rule_based, hybrid)
            max_agents: Maximum number of agents to use
            parallel_execution: Whether to run agents in parallel
            session_id: Optional session ID for conversation continuity

        Returns:
            Orchestrated analysis with synthesized recommendations
        """
        try:
            if not session_id:
                session_id = str(uuid.uuid4())

            supervisor = get_or_create_agent("supervisor", persona)

            result = await supervisor.coordinate_agents(
                query=query,
                session_id=session_id,
                routing_strategy=routing_strategy,
                max_agents=max_agents,
                parallel_execution=parallel_execution,
            )

            return {
                "status": "success",
                "agent_type": "supervisor_orchestrated",
                "persona": persona,
                "session_id": session_id,
                "routing_strategy": routing_strategy,
                "agents_used": result.get("agents_used", []),
                "execution_time_ms": result.get("execution_time_ms"),
                "synthesis_confidence": result.get("synthesis_confidence"),
                **result,
            }

        except Exception as e:
            logger.error(f"Error in orchestrated analysis: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "agent_type": "supervisor_orchestrated",
            }

    @mcp.tool(description="Conduct comprehensive financial research using web search and AI analysis.")
    @with_audit("agents_deep_research")
    async def deep_research_financial(
        research_topic: str,
        persona: str = "moderate",
        research_depth: str = "comprehensive",
        focus_areas: list[str] | None = None,
        timeframe: str = "30d",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Conduct comprehensive financial research using web search and AI analysis.

        Args:
            research_topic: Main research topic (company, symbol, or market theme)
            persona: Investor persona affecting research focus
            research_depth: Depth level (basic, standard, comprehensive, exhaustive)
            focus_areas: Specific areas to focus on
            timeframe: Time range for research (7d, 30d, 90d, 1y)
            session_id: Optional session ID for conversation continuity

        Returns:
            Comprehensive research report with validated sources and analysis
        """
        try:
            if not session_id:
                session_id = str(uuid.uuid4())

            if focus_areas is None:
                focus_areas = ["fundamentals", "market_sentiment", "competitive_landscape"]

            researcher = get_or_create_agent("deep_research", persona)

            result = await researcher.research_comprehensive(
                topic=research_topic,
                session_id=session_id,
                depth=research_depth,
                focus_areas=focus_areas,
                timeframe=timeframe,
            )

            return {
                "status": "success",
                "agent_type": "deep_research",
                "persona": persona,
                "session_id": session_id,
                "research_topic": research_topic,
                "research_depth": research_depth,
                "focus_areas": focus_areas,
                "sources_analyzed": result.get("total_sources_processed", 0),
                "research_confidence": result.get("research_confidence"),
                "validation_checks_passed": result.get("validation_checks_passed"),
                **result,
            }

        except Exception as e:
            logger.error(f"Error in deep research: {str(e)}")
            return {"status": "error", "error": str(e), "agent_type": "deep_research"}

    @mcp.tool(description="Compare analysis results across multiple agent types.")
    @with_audit("agents_compare_multi")
    async def compare_multi_agent_analysis(
        query: str,
        agent_types: list[str] | None = None,
        persona: str = "moderate",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Compare analysis results across multiple agent types.

        Args:
            query: Analysis query to run across multiple agents
            agent_types: List of agent types to compare
            persona: Investor persona for all agents
            session_id: Optional session ID prefix

        Returns:
            Comparative analysis showing different agent perspectives
        """
        try:
            if not session_id:
                session_id = str(uuid.uuid4())

            if agent_types is None:
                agent_types = ["market", "supervisor"]

            results = {}
            execution_times = {}

            async def run_agent(agent_type: str) -> tuple[str, dict]:
                """Run single agent and return result tuple."""
                try:
                    agent = get_or_create_agent(agent_type, persona)

                    if agent_type == "market":
                        result = await agent.analyze_market(
                            query=query,
                            session_id=f"{session_id}_{agent_type}",
                            max_results=10,
                        )
                    elif agent_type == "supervisor":
                        result = await agent.coordinate_agents(
                            query=query,
                            session_id=f"{session_id}_{agent_type}",
                            max_agents=2,
                        )
                    else:
                        return agent_type, {"error": "unknown agent type", "status": "skipped"}

                    return agent_type, {
                        "result": {
                            "summary": result.get("summary", ""),
                            "key_findings": result.get("key_findings", []),
                            "confidence": result.get("confidence", 0.0),
                            "methodology": result.get("methodology", f"{agent_type} analysis"),
                        },
                        "execution_time_ms": result.get("execution_time_ms", 0),
                    }
                except Exception as e:
                    logger.warning(f"Error with {agent_type} agent: {str(e)}")
                    return agent_type, {"error": str(e), "status": "failed"}

            # Run all agents in parallel
            agent_results = await asyncio.gather(
                *[run_agent(agent_type) for agent_type in agent_types]
            )

            # Collect results
            for agent_type, result in agent_results:
                if "error" in result:
                    results[agent_type] = result
                else:
                    results[agent_type] = result["result"]
                    execution_times[agent_type] = result.get("execution_time_ms", 0)

            return {
                "status": "success",
                "query": query,
                "persona": persona,
                "agents_compared": list(results.keys()),
                "comparison": results,
                "execution_times_ms": execution_times,
                "insights": "Each agent brings unique analytical perspectives",
            }

        except Exception as e:
            logger.error(f"Error in multi-agent comparison: {str(e)}")
            return {"status": "error", "error": str(e)}

    @mcp.tool(description="List all available LangGraph agents and their capabilities.")
    @with_audit("agents_list_available")
    async def list_available_agents() -> dict[str, Any]:
        """List all available LangGraph agents and their capabilities."""
        return {
            "status": "success",
            "agents": {
                "market_analysis": {
                    "description": "Market screening and sector analysis",
                    "personas": ["conservative", "moderate", "aggressive"],
                    "capabilities": [
                        "Momentum screening",
                        "Sector rotation analysis",
                        "Market breadth indicators",
                        "Risk-adjusted recommendations",
                    ],
                    "streaming_modes": ["updates", "values", "messages", "debug"],
                    "status": "active",
                },
                "supervisor_orchestrated": {
                    "description": "Multi-agent orchestration and coordination",
                    "personas": ["conservative", "moderate", "aggressive", "day_trader"],
                    "capabilities": [
                        "Intelligent query routing",
                        "Multi-agent coordination",
                        "Result synthesis and conflict resolution",
                        "Parallel and sequential execution",
                    ],
                    "routing_strategies": ["llm_powered", "rule_based", "hybrid"],
                    "status": "active",
                },
                "deep_research": {
                    "description": "Comprehensive financial research with web search",
                    "personas": ["conservative", "moderate", "aggressive", "day_trader"],
                    "capabilities": [
                        "Multi-provider web search",
                        "AI-powered content analysis",
                        "Source validation and credibility scoring",
                        "Comprehensive research reports",
                    ],
                    "research_depths": ["basic", "standard", "comprehensive", "exhaustive"],
                    "status": "active",
                },
            },
            "personas": ["conservative", "moderate", "aggressive", "day_trader"],
            "routing_strategies": ["llm_powered", "rule_based", "hybrid"],
            "research_depths": ["basic", "standard", "comprehensive", "exhaustive"],
        }

    @mcp.tool(description="Compare analysis across different investor personas.")
    @with_audit("agents_compare_personas")
    async def compare_personas_analysis(
        query: str,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Compare analysis across different investor personas.

        Args:
            query: Analysis query to run
            session_id: Optional session ID prefix

        Returns:
            Comparative analysis across all personas
        """
        try:
            if not session_id:
                session_id = str(uuid.uuid4())

            async def analyze_with_persona(persona: str) -> tuple[str, dict]:
                """Analyze with specific persona."""
                agent = get_or_create_agent("market", persona)

                result = await agent.analyze_market(
                    query=query, session_id=f"{session_id}_{persona}", max_results=10
                )

                return persona, {
                    "summary": result.get("results", {}).get("summary", ""),
                    "top_picks": result.get("results", {}).get("screened_symbols", [])[:5],
                    "risk_parameters": {
                        "risk_tolerance": getattr(agent, "persona", {}).get("risk_tolerance", "N/A"),
                    },
                }

            # Run all persona analyses in parallel
            persona_results = await asyncio.gather(
                *[analyze_with_persona(p) for p in ["conservative", "moderate", "aggressive"]]
            )

            results = {persona: result for persona, result in persona_results}

            return {
                "status": "success",
                "query": query,
                "comparison": results,
                "insights": "Notice how recommendations vary by risk profile",
            }

        except Exception as e:
            logger.error(f"Error in persona comparison: {str(e)}")
            return {"status": "error", "error": str(e)}

    logger.info("Registered agents tools")


__all__ = ["register_agents_tools"]
