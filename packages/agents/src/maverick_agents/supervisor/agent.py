"""
SupervisorAgent implementation using LangGraph patterns.

Orchestrates multiple specialized agents with intelligent routing,
result synthesis, and conflict resolution.
"""

import logging
from datetime import datetime
from typing import Any, Protocol

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool, tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from maverick_agents.base import PersonaAwareAgent
from maverick_agents.exceptions import AgentInitializationError
from maverick_agents.personas import INVESTOR_PERSONAS
from maverick_agents.state import SupervisorState
from maverick_agents.supervisor.classifier import QueryClassifier
from maverick_agents.supervisor.synthesizer import ResultSynthesizer

logger = logging.getLogger(__name__)


class ConversationStoreProtocol(Protocol):
    """Protocol for conversation storage."""

    def store(self, session_id: str, messages: list) -> None: ...
    def retrieve(self, session_id: str) -> list: ...


class SupervisorAgent(PersonaAwareAgent):
    """
    Multi-agent supervisor using LangGraph patterns.

    Orchestrates MarketAnalysisAgent, TechnicalAnalysisAgent, and DeepResearchAgent
    with intelligent routing, result synthesis, and conflict resolution.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        agents: dict[str, PersonaAwareAgent],
        persona: str = "moderate",
        checkpointer: MemorySaver | None = None,
        ttl_hours: int = 1,
        routing_strategy: str = "llm_powered",
        synthesis_mode: str = "weighted",
        conflict_resolution: str = "confidence_based",
        max_iterations: int = 5,
        conversation_store: ConversationStoreProtocol | None = None,
    ):
        """
        Initialize supervisor with agent instances.

        Args:
            llm: Language model for coordination
            agents: Dictionary of agent name to agent instance
            persona: Investor persona name
            checkpointer: Optional memory checkpointer
            ttl_hours: Time-to-live for memory
            routing_strategy: Strategy for routing queries
            synthesis_mode: Mode for synthesizing results
            conflict_resolution: Strategy for resolving conflicts
            max_iterations: Maximum workflow iterations
            conversation_store: Optional conversation storage
        """
        if not agents:
            raise AgentInitializationError(
                agent_type="SupervisorAgent",
                reason="No agents provided for supervision",
            )

        # Store agent references
        self.agents = agents
        self.market_agent = agents.get("market")
        self.technical_agent = agents.get("technical")
        self.research_agent = agents.get("research")

        # Configuration
        self.routing_strategy = routing_strategy
        self.synthesis_mode = synthesis_mode
        self.conflict_resolution = conflict_resolution
        self.max_iterations = max_iterations

        # Ensure all agents use the same persona
        persona_obj = INVESTOR_PERSONAS.get(persona, INVESTOR_PERSONAS["moderate"])
        for agent in agents.values():
            if hasattr(agent, "persona"):
                agent.persona = persona_obj

        # Get supervisor-specific tools
        supervisor_tools = self._get_supervisor_tools()

        # Initialize base class
        super().__init__(
            llm=llm,
            tools=supervisor_tools,
            persona=persona,
            checkpointer=checkpointer or MemorySaver(),
            ttl_hours=ttl_hours,
        )

        # Initialize components
        self.conversation_store = conversation_store
        self.query_classifier = QueryClassifier(llm)
        self.result_synthesizer = ResultSynthesizer(llm, self.persona)

        logger.info(
            f"SupervisorAgent initialized with {len(agents)} agents: {list(agents.keys())}"
        )

    def get_state_schema(self) -> type:
        """Return SupervisorState schema."""
        return SupervisorState

    def _get_supervisor_tools(self) -> list[BaseTool]:
        """Get tools specific to supervision and coordination."""
        tools = []

        if self.market_agent:

            @tool
            async def query_market_agent(
                query: str,
                session_id: str,
                screening_strategy: str = "momentum",
                max_results: int = 20,
            ) -> dict[str, Any]:
                """Query the market analysis agent for stock screening and market analysis."""
                try:
                    if hasattr(self.market_agent, "analyze_market"):
                        return await self.market_agent.analyze_market(
                            query=query,
                            session_id=session_id,
                            screening_strategy=screening_strategy,
                            max_results=max_results,
                        )
                    return await self.market_agent.ainvoke(query, session_id)
                except Exception as e:
                    return {"error": f"Market agent error: {str(e)}"}

            tools.append(query_market_agent)

        if self.technical_agent:

            @tool
            async def query_technical_agent(
                symbol: str, timeframe: str = "1d", indicators: list[str] | None = None
            ) -> dict[str, Any]:
                """Query the technical analysis agent for chart analysis and indicators."""
                try:
                    if indicators is None:
                        indicators = ["sma_20", "rsi", "macd"]

                    if hasattr(self.technical_agent, "analyze_stock"):
                        return await self.technical_agent.analyze_stock(
                            symbol=symbol, timeframe=timeframe, indicators=indicators
                        )
                    return {"status": "technical analysis not available"}
                except Exception as e:
                    return {"error": f"Technical agent error: {str(e)}"}

            tools.append(query_technical_agent)

        if self.research_agent:

            @tool
            async def query_research_agent(
                query: str,
                session_id: str,
                research_scope: str = "comprehensive",
                max_sources: int = 50,
                timeframe: str = "1m",
            ) -> dict[str, Any]:
                """Query the deep research agent for comprehensive research and analysis."""
                try:
                    if hasattr(self.research_agent, "research_topic"):
                        return await self.research_agent.research_topic(
                            query=query,
                            session_id=session_id,
                            research_scope=research_scope,
                            max_sources=max_sources,
                            timeframe=timeframe,
                        )
                    return await self.research_agent.ainvoke(query, session_id)
                except Exception as e:
                    return {"error": f"Research agent error: {str(e)}"}

            tools.append(query_research_agent)

        return tools

    def _build_graph(self):
        """Build supervisor graph with multi-agent coordination."""
        workflow = StateGraph(SupervisorState)

        # Core supervisor nodes
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("create_execution_plan", self._create_execution_plan)
        workflow.add_node("route_to_agents", self._route_to_agents)
        workflow.add_node("aggregate_results", self._aggregate_results)
        workflow.add_node("resolve_conflicts", self._resolve_conflicts)
        workflow.add_node("synthesize_response", self._synthesize_response)

        # Agent invocation nodes
        if self.market_agent:
            workflow.add_node("invoke_market_agent", self._invoke_market_agent)
        if self.technical_agent:
            workflow.add_node("invoke_technical_agent", self._invoke_technical_agent)
        if self.research_agent:
            workflow.add_node("invoke_research_agent", self._invoke_research_agent)

        # Coordination nodes
        workflow.add_node("parallel_coordinator", self._parallel_coordinator)

        # Tool node
        if self.tools:
            tool_node = ToolNode(self.tools)
            workflow.add_node("tools", tool_node)

        # Define workflow edges
        workflow.add_edge(START, "analyze_query")
        workflow.add_edge("analyze_query", "create_execution_plan")
        workflow.add_edge("create_execution_plan", "route_to_agents")

        # Conditional routing based on execution plan
        workflow.add_conditional_edges(
            "route_to_agents",
            self._route_decision,
            {
                "market_only": "invoke_market_agent"
                if self.market_agent
                else "synthesize_response",
                "technical_only": "invoke_technical_agent"
                if self.technical_agent
                else "synthesize_response",
                "research_only": "invoke_research_agent"
                if self.research_agent
                else "synthesize_response",
                "parallel_execution": "parallel_coordinator",
                "use_tools": "tools" if self.tools else "synthesize_response",
                "synthesize": "synthesize_response",
            },
        )

        # Agent result collection
        if self.market_agent:
            workflow.add_edge("invoke_market_agent", "aggregate_results")
        if self.technical_agent:
            workflow.add_edge("invoke_technical_agent", "aggregate_results")
        if self.research_agent:
            workflow.add_edge("invoke_research_agent", "aggregate_results")

        workflow.add_edge("parallel_coordinator", "aggregate_results")

        if self.tools:
            workflow.add_edge("tools", "aggregate_results")

        # Conflict detection and resolution
        workflow.add_conditional_edges(
            "aggregate_results",
            self._check_conflicts,
            {"resolve": "resolve_conflicts", "synthesize": "synthesize_response"},
        )

        workflow.add_edge("resolve_conflicts", "synthesize_response")
        workflow.add_edge("synthesize_response", END)

        return workflow.compile(checkpointer=self.checkpointer)

    async def coordinate_agents(
        self, query: str, session_id: str, **kwargs
    ) -> dict[str, Any]:
        """
        Main entry point for multi-agent coordination.

        Args:
            query: User query requiring multiple agents
            session_id: Session identifier
            **kwargs: Additional parameters

        Returns:
            Coordinated response from multiple agents
        """
        start_time = datetime.now()

        # Initialize supervisor state
        initial_state = self._create_initial_state(query, session_id, **kwargs)

        # Execute supervision workflow
        try:
            result = await self.graph.ainvoke(
                initial_state,
                config={
                    "configurable": {
                        "thread_id": session_id,
                        "checkpoint_ns": "supervisor",
                    }
                },
            )

            # Calculate total execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            result["total_execution_time_ms"] = execution_time

            return self._format_supervisor_response(result)

        except Exception as e:
            logger.error(f"Error in supervisor coordination: {e}")
            return {
                "status": "error",
                "error": str(e),
                "total_execution_time_ms": (datetime.now() - start_time).total_seconds()
                * 1000,
                "agent_type": "supervisor",
            }

    def _create_initial_state(
        self, query: str, session_id: str, **kwargs
    ) -> dict[str, Any]:
        """Create initial state for supervisor workflow."""
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "persona": self.persona.name,
            "session_id": session_id,
            "timestamp": datetime.now(),
            "token_count": 0,
            "error": None,
            "analyzed_stocks": {},
            "key_price_levels": {},
            "last_analysis_time": {},
            "conversation_context": {},
            "execution_time_ms": None,
            "api_calls_made": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "query_classification": {},
            "execution_plan": [],
            "current_subtask_index": 0,
            "routing_strategy": self.routing_strategy,
            "active_agents": [],
            "agent_results": {},
            "agent_confidence": {},
            "agent_execution_times": {},
            "agent_errors": {},
            "workflow_status": "planning",
            "parallel_execution": False,
            "dependency_graph": {},
            "max_iterations": self.max_iterations,
            "current_iteration": 0,
            "conflicts_detected": [],
            "conflict_resolution": {},
            "synthesis_weights": {},
            "final_recommendation_confidence": 0.0,
            "synthesis_mode": self.synthesis_mode,
            "total_execution_time_ms": 0.0,
            "agent_coordination_overhead_ms": 0.0,
            "synthesis_time_ms": 0.0,
            "cache_utilization": {},
            # Legacy fields
            "query_type": None,
            "subtasks": None,
            "current_subtask": None,
            "workflow_plan": None,
            "completed_steps": None,
            "pending_steps": None,
            "final_recommendations": None,
            "confidence_scores": None,
            "risk_warnings": None,
        }

        initial_state.update(kwargs)
        return initial_state

    def _format_supervisor_response(self, result: dict[str, Any]) -> dict[str, Any]:
        """Format supervisor response for consistent output."""
        messages = result.get("messages", [])
        synthesis = "No synthesis available"
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "content"):
                synthesis = last_msg.content

        return {
            "status": "success",
            "agent_type": "supervisor",
            "persona": result.get("persona"),
            "query_classification": result.get("query_classification", {}),
            "agents_used": result.get("active_agents", []),
            "synthesis": synthesis,
            "confidence_score": result.get("final_recommendation_confidence", 0.0),
            "execution_time_ms": result.get("total_execution_time_ms", 0.0),
            "conflicts_resolved": len(result.get("conflicts_detected", [])),
            "workflow_status": result.get("workflow_status", "completed"),
        }

    # Workflow node implementations

    async def _analyze_query(self, state: SupervisorState) -> Command:
        """Analyze query to determine routing strategy."""
        query = state["messages"][-1].content if state["messages"] else ""

        classification = await self.query_classifier.classify_query(
            query, state["persona"]
        )

        return Command(
            goto="create_execution_plan",
            update={
                "query_classification": classification,
                "workflow_status": "analyzing",
            },
        )

    async def _create_execution_plan(self, state: SupervisorState) -> Command:
        """Create execution plan based on query classification."""
        classification = state["query_classification"]

        execution_plan = [
            {
                "task_id": "main_analysis",
                "agents": classification.get("required_agents", ["market"]),
                "parallel": classification.get("parallel_capable", False),
                "priority": 1,
            }
        ]

        return Command(
            goto="route_to_agents",
            update={"execution_plan": execution_plan, "workflow_status": "planning"},
        )

    async def _route_to_agents(self, state: SupervisorState) -> Command:
        """Route query to appropriate agents."""
        return Command(
            goto="parallel_execution", update={"workflow_status": "executing"}
        )

    async def _route_decision(self, state: SupervisorState) -> str:
        """Decide routing strategy based on state."""
        classification = state.get("query_classification", {})
        required_agents = classification.get("required_agents", ["market"])
        parallel = classification.get("parallel_capable", False)

        if len(required_agents) == 1:
            agent = required_agents[0]
            if agent == "market" and self.market_agent:
                return "market_only"
            elif agent == "technical" and self.technical_agent:
                return "technical_only"
            elif agent == "research" and self.research_agent:
                return "research_only"
        elif len(required_agents) > 1 and parallel:
            return "parallel_execution"

        return "synthesize"

    async def _parallel_coordinator(self, state: SupervisorState) -> Command:
        """Coordinate parallel execution of multiple agents."""
        return Command(
            goto="aggregate_results", update={"workflow_status": "aggregating"}
        )

    async def _invoke_market_agent(self, state: SupervisorState) -> Command:
        """Invoke market analysis agent."""
        if not self.market_agent:
            return Command(
                goto="aggregate_results",
                update={"agent_errors": {"market": "Market agent not available"}},
            )

        try:
            query = state["messages"][-1].content if state["messages"] else ""
            if hasattr(self.market_agent, "analyze_market"):
                result = await self.market_agent.analyze_market(
                    query=query, session_id=state["session_id"]
                )
            else:
                result = await self.market_agent.ainvoke(query, state["session_id"])

            return Command(
                goto="aggregate_results",
                update={
                    "agent_results": {"market": result},
                    "active_agents": ["market"],
                },
            )

        except Exception as e:
            return Command(
                goto="aggregate_results",
                update={
                    "agent_errors": {"market": str(e)},
                    "active_agents": ["market"],
                },
            )

    async def _invoke_technical_agent(self, state: SupervisorState) -> Command:
        """Invoke technical analysis agent."""
        if not self.technical_agent:
            return Command(
                goto="aggregate_results",
                update={"agent_errors": {"technical": "Technical agent not available"}},
            )

        return Command(
            goto="aggregate_results", update={"active_agents": ["technical"]}
        )

    async def _invoke_research_agent(self, state: SupervisorState) -> Command:
        """Invoke deep research agent."""
        if not self.research_agent:
            return Command(
                goto="aggregate_results",
                update={"agent_errors": {"research": "Research agent not available"}},
            )

        return Command(goto="aggregate_results", update={"active_agents": ["research"]})

    async def _aggregate_results(self, state: SupervisorState) -> Command:
        """Aggregate results from all agents."""
        return Command(
            goto="synthesize_response", update={"workflow_status": "synthesizing"}
        )

    def _check_conflicts(self, state: SupervisorState) -> str:
        """Check if there are conflicts between agent results."""
        conflicts = state.get("conflicts_detected", [])
        return "resolve" if conflicts else "synthesize"

    async def _resolve_conflicts(self, state: SupervisorState) -> Command:
        """Resolve conflicts between agent recommendations."""
        return Command(
            goto="synthesize_response",
            update={"conflict_resolution": {"strategy": "confidence_based"}},
        )

    async def _synthesize_response(self, state: SupervisorState) -> Command:
        """Synthesize final response from agent results."""
        agent_results = state.get("agent_results", {})
        conflicts = state.get("conflicts_detected", [])
        classification = state.get("query_classification", {})

        if agent_results:
            synthesis = await self.result_synthesizer.synthesize_results(
                agent_results=agent_results,
                query_type=classification.get("category", "stock_investment_decision"),
                conflicts=conflicts,
            )

            return Command(
                goto="__end__",
                update={
                    "final_recommendation_confidence": synthesis["confidence_score"],
                    "synthesis_weights": synthesis["weights_applied"],
                    "workflow_status": "completed",
                    "messages": state["messages"]
                    + [HumanMessage(content=synthesis["synthesis"])],
                },
            )
        else:
            return Command(
                goto="__end__",
                update={
                    "workflow_status": "completed",
                    "messages": state["messages"]
                    + [
                        HumanMessage(content="No agent results available for synthesis")
                    ],
                },
            )
