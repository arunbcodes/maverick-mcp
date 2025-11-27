"""
Base classes for persona-aware agents using LangGraph best practices.

Provides foundational agent patterns that adapt behavior based on investor personas.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from maverick_agents.personas import INVESTOR_PERSONAS, InvestorPersona
from maverick_agents.tools import PersonaAwareTool

logger = logging.getLogger(__name__)


class BaseAgentState(TypedDict):
    """Base state for all persona-aware agents."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    persona: str
    session_id: str


class PersonaAwareAgent(ABC):
    """
    Base class for agents that adapt behavior based on investor personas.

    This follows LangGraph best practices:
    - Uses StateGraph for workflow definition
    - Implements proper node/edge patterns
    - Supports native streaming modes
    - Uses TypedDict for state management
    """

    def __init__(
        self,
        llm,
        tools: list[BaseTool],
        persona: str = "moderate",
        checkpointer: MemorySaver | None = None,
        ttl_hours: int = 1,
    ):
        """
        Initialize a persona-aware agent.

        Args:
            llm: Language model to use
            tools: List of tools available to the agent
            persona: Investor persona name
            checkpointer: Optional checkpointer (defaults to MemorySaver)
            ttl_hours: Time-to-live for memory in hours
        """
        self.llm = llm
        self.tools = tools
        self.persona = INVESTOR_PERSONAS.get(persona, INVESTOR_PERSONAS["moderate"])
        self.ttl_hours = ttl_hours

        # Set up checkpointing
        if checkpointer is None:
            self.checkpointer = MemorySaver()
        else:
            self.checkpointer = checkpointer

        # Configure tools with persona
        for tool in self.tools:
            if isinstance(tool, PersonaAwareTool):
                tool.set_persona(self.persona)

        # Build the graph
        self.graph = self._build_graph()

        # Track usage
        self.total_tokens = 0
        self.conversation_start = datetime.now()

    def _build_graph(self):
        """Build the LangGraph workflow."""
        # Create the graph builder
        workflow = StateGraph(self.get_state_schema())

        # Add the agent node
        workflow.add_node("agent", self._agent_node)

        # Create tool node if tools are available
        if self.tools:
            tool_node = ToolNode(self.tools)
            workflow.add_node("tools", tool_node)

            # Add conditional edge from agent
            workflow.add_conditional_edges(
                "agent",
                self._should_continue,
                {
                    # If agent returns tool calls, route to tools
                    "continue": "tools",
                    # Otherwise end
                    "end": END,
                },
            )

            # Add edge from tools back to agent
            workflow.add_edge("tools", "agent")
        else:
            # No tools, just end after agent
            workflow.add_edge("agent", END)

        # Set entry point
        workflow.add_edge(START, "agent")

        # Compile with checkpointer
        return workflow.compile(checkpointer=self.checkpointer)

    def _agent_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """The main agent node that processes messages."""
        messages = state["messages"]

        # Add system message if it's the first message
        if len(messages) == 1 and isinstance(messages[0], HumanMessage):
            system_prompt = self._build_system_prompt()
            messages = [SystemMessage(content=system_prompt)] + messages

        # Call the LLM
        if self.tools:
            response = self.llm.bind_tools(self.tools).invoke(messages)
        else:
            response = self.llm.invoke(messages)

        # Track tokens (simplified)
        if hasattr(response, "content"):
            self.total_tokens += len(response.content) // 4

        # Return the response
        return {"messages": [response]}

    def _should_continue(self, state: dict[str, Any]) -> str:
        """Determine whether to continue to tools or end."""
        last_message = state["messages"][-1]

        # If the LLM makes a tool call, continue to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"

        # Otherwise we're done
        return "end"

    def _build_system_prompt(self) -> str:
        """Build system prompt based on persona."""
        base_prompt = f"""You are a financial advisor configured for a {self.persona.name} investor profile.

Risk Parameters:
- Risk Tolerance: {self.persona.risk_tolerance[0]}-{self.persona.risk_tolerance[1]}/100
- Max Position Size: {self.persona.position_size_max * 100:.1f}% of portfolio
- Stop Loss Multiplier: {self.persona.stop_loss_multiplier}x
- Preferred Timeframe: {self.persona.preferred_timeframe}

Key Characteristics:
{chr(10).join(f"- {char}" for char in self.persona.characteristics)}

Always adjust your recommendations to match this risk profile. Be explicit about risk management."""

        return base_prompt

    @abstractmethod
    def get_state_schema(self) -> type:
        """
        Get the state schema for this agent.

        Subclasses should return their specific state schema.
        """
        return BaseAgentState

    async def ainvoke(self, query: str, session_id: str, **kwargs) -> dict[str, Any]:
        """
        Invoke the agent asynchronously.

        Args:
            query: User query
            session_id: Session identifier
            **kwargs: Additional parameters

        Returns:
            Agent response
        """
        config = {
            "configurable": {"thread_id": session_id, "persona": self.persona.name}
        }

        # Merge additional config
        if "config" in kwargs:
            config.update(kwargs["config"])

        # Run the graph
        result = await self.graph.ainvoke(
            {
                "messages": [HumanMessage(content=query)],
                "persona": self.persona.name,
                "session_id": session_id,
            },
            config=config,
        )

        return self._extract_response(result)

    def invoke(self, query: str, session_id: str, **kwargs) -> dict[str, Any]:
        """
        Invoke the agent synchronously.

        Args:
            query: User query
            session_id: Session identifier
            **kwargs: Additional parameters

        Returns:
            Agent response
        """
        config = {
            "configurable": {"thread_id": session_id, "persona": self.persona.name}
        }

        # Merge additional config
        if "config" in kwargs:
            config.update(kwargs["config"])

        # Run the graph
        result = self.graph.invoke(
            {
                "messages": [HumanMessage(content=query)],
                "persona": self.persona.name,
                "session_id": session_id,
            },
            config=config,
        )

        return self._extract_response(result)

    async def astream(
        self, query: str, session_id: str, stream_mode: str = "values", **kwargs
    ):
        """
        Stream agent responses asynchronously.

        Args:
            query: User query
            session_id: Session identifier
            stream_mode: Streaming mode (values, updates, messages, custom, debug)
            **kwargs: Additional parameters

        Yields:
            Streamed chunks based on mode
        """
        config = {
            "configurable": {"thread_id": session_id, "persona": self.persona.name}
        }

        # Merge additional config
        if "config" in kwargs:
            config.update(kwargs["config"])

        # Stream the graph
        async for chunk in self.graph.astream(
            {
                "messages": [HumanMessage(content=query)],
                "persona": self.persona.name,
                "session_id": session_id,
            },
            config=config,
            stream_mode=stream_mode,
        ):
            yield chunk

    def stream(
        self, query: str, session_id: str, stream_mode: str = "values", **kwargs
    ):
        """
        Stream agent responses synchronously.

        Args:
            query: User query
            session_id: Session identifier
            stream_mode: Streaming mode (values, updates, messages, custom, debug)
            **kwargs: Additional parameters

        Yields:
            Streamed chunks based on mode
        """
        config = {
            "configurable": {"thread_id": session_id, "persona": self.persona.name}
        }

        # Merge additional config
        if "config" in kwargs:
            config.update(kwargs["config"])

        # Stream the graph
        yield from self.graph.stream(
            {
                "messages": [HumanMessage(content=query)],
                "persona": self.persona.name,
                "session_id": session_id,
            },
            config=config,
            stream_mode=stream_mode,
        )

    def _extract_response(self, result: dict[str, Any]) -> dict[str, Any]:
        """Extract the final response from graph execution."""
        messages = result.get("messages", [])

        if not messages:
            return {"content": "No response generated", "status": "error"}

        # Get the last AI message
        last_message = messages[-1]

        return {
            "content": last_message.content
            if hasattr(last_message, "content")
            else str(last_message),
            "status": "success",
            "persona": self.persona.name,
            "message_count": len(messages),
            "session_id": result.get("session_id", ""),
        }

    def get_risk_adjusted_params(
        self, base_params: dict[str, float]
    ) -> dict[str, float]:
        """Adjust parameters based on persona risk profile."""
        adjusted = {}

        for key, value in base_params.items():
            if "size" in key.lower() or "position" in key.lower():
                adjusted[key] = self.adjust_for_risk(value, "position_size")
            elif "stop" in key.lower():
                adjusted[key] = self.adjust_for_risk(value, "stop_loss")
            elif "target" in key.lower() or "profit" in key.lower():
                adjusted[key] = self.adjust_for_risk(value, "profit_target")
            else:
                adjusted[key] = value

        return adjusted

    def adjust_for_risk(self, value: float, parameter_type: str) -> float:
        """Adjust a value based on the persona's risk profile."""
        # Get average risk tolerance
        risk_avg = sum(self.persona.risk_tolerance) / 2
        risk_factor = risk_avg / 50  # Normalize to 1.0 at moderate risk

        # Adjust based on parameter type
        if parameter_type == "position_size":
            return min(value * risk_factor, self.persona.position_size_max)
        elif parameter_type == "stop_loss":
            return value * self.persona.stop_loss_multiplier
        elif parameter_type == "profit_target":
            return value * (2 - risk_factor)  # Conservative = lower targets
        else:
            return value
