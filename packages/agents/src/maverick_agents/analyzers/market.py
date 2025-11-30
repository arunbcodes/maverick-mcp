"""
Market Analysis Agent using LangGraph best practices with professional features.

Provides comprehensive market analysis including:
- Multi-strategy screening
- Sector rotation analysis
- Market regime detection
- Risk-adjusted recommendations
"""

import hashlib
import logging
from datetime import datetime
from typing import Any, Protocol

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from maverick_agents.base import PersonaAwareAgent
from maverick_agents.circuit_breaker import circuit_manager
from maverick_agents.exceptions import AgentInitializationError
from maverick_agents.state import MarketAnalysisState

logger = logging.getLogger(__name__)


class ConversationStoreProtocol(Protocol):
    """Protocol for conversation storage."""

    def store(self, session_id: str, messages: list) -> None:
        """Store conversation messages."""
        ...

    def retrieve(self, session_id: str) -> list:
        """Retrieve conversation messages."""
        ...

    def save_analysis(
        self, session_id: str, symbol: str, analysis_type: str, data: dict
    ) -> None:
        """Save analysis data."""
        ...

    def get_analysis(
        self, session_id: str, symbol: str, analysis_type: str
    ) -> dict | None:
        """Get cached analysis data."""
        ...


class ToolRegistryProtocol(Protocol):
    """Protocol for tool registry access."""

    def get_tool(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        ...


class PersonaConfigurationError(Exception):
    """Exception for invalid persona configuration."""

    def __init__(self, persona: str, valid_personas: list[str]):
        self.persona = persona
        self.valid_personas = valid_personas
        super().__init__(
            f"Invalid persona '{persona}'. Valid personas: {valid_personas}"
        )


class MarketAnalysisAgent(PersonaAwareAgent):
    """
    Professional market analysis agent with advanced screening and risk assessment.

    Features:
    - Multi-strategy screening (momentum, mean reversion, breakout)
    - Sector rotation analysis
    - Market regime detection
    - Risk-adjusted recommendations
    - Real-time sentiment integration
    - Circuit breaker protection for API calls
    """

    VALID_PERSONAS = ["conservative", "moderate", "aggressive", "day_trader"]

    def __init__(
        self,
        llm: BaseChatModel,
        tools: list[BaseTool] | None = None,
        tool_registry: ToolRegistryProtocol | None = None,
        persona: str = "moderate",
        ttl_hours: int = 1,
        conversation_store: ConversationStoreProtocol | None = None,
        checkpointer: MemorySaver | None = None,
    ):
        """
        Initialize market analysis agent.

        Args:
            llm: Language model
            tools: Optional list of tools (if not using registry)
            tool_registry: Optional tool registry for getting tools by name
            persona: Investor persona
            ttl_hours: Cache TTL in hours
            conversation_store: Optional conversation storage
            checkpointer: Optional memory checkpointer

        Raises:
            PersonaConfigurationError: If persona is invalid
            AgentInitializationError: If initialization fails
        """
        try:
            # Validate persona
            if persona.lower() not in self.VALID_PERSONAS:
                raise PersonaConfigurationError(
                    persona=persona, valid_personas=self.VALID_PERSONAS
                )

            self._temp_persona = persona.lower()
            self._tool_registry = tool_registry

            # Get tools from registry or use provided tools
            if tools is not None:
                resolved_tools = tools
            elif tool_registry is not None:
                resolved_tools = self._get_tools_from_registry(tool_registry)
            else:
                resolved_tools = self._create_mock_tools()

            if not resolved_tools:
                raise AgentInitializationError(
                    agent_type="MarketAnalysisAgent",
                    reason="No tools available for initialization",
                )

            super().__init__(
                llm=llm,
                tools=resolved_tools,
                persona=persona,
                checkpointer=checkpointer or MemorySaver(),
                ttl_hours=ttl_hours,
            )

        except (PersonaConfigurationError, AgentInitializationError):
            raise
        except Exception as e:
            logger.error(f"Failed to initialize MarketAnalysisAgent: {str(e)}")
            raise AgentInitializationError(
                agent_type="MarketAnalysisAgent",
                reason=str(e),
            )

        self.conversation_store = conversation_store
        self.ttl_hours = ttl_hours

        # Circuit breakers for external APIs
        self.circuit_breakers = {
            "screening": None,
            "sentiment": None,
            "market_data": None,
        }

    def _get_tools_from_registry(
        self, registry: ToolRegistryProtocol
    ) -> list[BaseTool]:
        """Get comprehensive set of market analysis tools from registry."""
        tool_names = [
            # Core screening tools
            "get_maverick_stocks",
            "get_maverick_bear_stocks",
            "get_supply_demand_breakouts",
            "get_all_screening_recommendations",
            # Technical analysis tools
            "get_technical_indicators",
            "calculate_support_resistance",
            "detect_chart_patterns",
            # Market data tools
            "get_market_movers",
            "get_sector_performance",
            "get_market_indices",
            # Risk management tools
            "calculate_position_size",
            "calculate_technical_stops",
            "calculate_risk_metrics",
            # Sentiment analysis tools
            "analyze_news_sentiment",
            "analyze_market_breadth",
            "analyze_sector_sentiment",
        ]

        tools = []
        for name in tool_names:
            tool = registry.get_tool(name)
            if tool is not None:
                # Configure persona if supported
                if hasattr(tool, "set_persona"):
                    tool.set_persona(self._temp_persona)
                tools.append(tool)

        if not tools:
            logger.warning("No tools available from registry for market analysis")
            return self._create_mock_tools()

        logger.info(f"Loaded {len(tools)} tools for {self._temp_persona} persona")
        return tools

    def get_state_schema(self) -> type:
        """Return enhanced state schema for market analysis."""
        return MarketAnalysisState

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for professional market analysis."""
        base_prompt = super()._build_system_prompt()

        market_prompt = f"""

You are a professional market analyst specializing in systematic screening and analysis.
Current market date: {datetime.now().strftime("%Y-%m-%d")}

## Core Responsibilities:

1. **Multi-Strategy Screening**:
   - Momentum: High RS stocks breaking out on volume
   - Mean Reversion: Oversold quality stocks at support
   - Breakout: Stocks clearing resistance with volume surge
   - Trend Following: Stocks in established uptrends

2. **Market Regime Analysis**:
   - Identify current market regime (bull/bear/sideways)
   - Analyze sector rotation patterns
   - Monitor breadth indicators and sentiment
   - Detect risk-on vs risk-off environments

3. **Risk-Adjusted Selection**:
   - Filter stocks by persona risk tolerance
   - Calculate position sizes using Kelly Criterion
   - Set appropriate stop losses using ATR
   - Consider correlation and portfolio heat

4. **Professional Reporting**:
   - Provide actionable entry/exit levels
   - Include risk/reward ratios
   - Highlight key catalysts and risks
   - Suggest portfolio allocation

## Screening Criteria by Persona:

**Conservative ({self.persona.name if self.persona.name == "Conservative" else "N/A"})**:
- Large-cap stocks (>$10B market cap)
- Dividend yield > 2%
- Low debt/equity < 1.5
- Beta < 1.2
- Established uptrends only

**Moderate ({self.persona.name if self.persona.name == "Moderate" else "N/A"})**:
- Mid to large-cap stocks (>$2B)
- Balanced growth/value metrics
- Moderate volatility accepted
- Mix of dividend and growth stocks

**Aggressive ({self.persona.name if self.persona.name == "Aggressive" else "N/A"})**:
- All market caps considered
- High growth rates prioritized
- Momentum and relative strength focus
- Higher volatility tolerated

**Day Trader ({self.persona.name if self.persona.name == "Day Trader" else "N/A"})**:
- High liquidity (>1M avg volume)
- Tight spreads (<0.1%)
- High ATR for movement
- Technical patterns emphasized

## Analysis Framework:

1. Start with market regime assessment
2. Identify leading/lagging sectors
3. Screen for stocks matching criteria
4. Apply technical analysis filters
5. Calculate risk metrics
6. Generate recommendations with specific levels

Remember to:
- Cite specific data points
- Explain your reasoning
- Highlight risks clearly
- Provide actionable insights
- Consider time horizon
"""

        return base_prompt + market_prompt

    def _build_graph(self):
        """Build enhanced graph with multiple analysis nodes."""
        workflow = StateGraph(MarketAnalysisState)

        # Add specialized nodes with unique names
        workflow.add_node("analyze_market_regime", self._analyze_market_regime)
        workflow.add_node("analyze_sectors", self._analyze_sectors)
        workflow.add_node("run_screening", self._run_screening)
        workflow.add_node("assess_risks", self._assess_risks)
        workflow.add_node("agent", self._agent_node)

        # Create tool node if tools available
        if self.tools:
            tool_node = ToolNode(self.tools)
            workflow.add_node("tools", tool_node)

        # Define flow
        workflow.add_edge(START, "analyze_market_regime")
        workflow.add_edge("analyze_market_regime", "analyze_sectors")
        workflow.add_edge("analyze_sectors", "run_screening")
        workflow.add_edge("run_screening", "assess_risks")
        workflow.add_edge("assess_risks", "agent")

        if self.tools:
            workflow.add_conditional_edges(
                "agent",
                self._should_continue,
                {
                    "continue": "tools",
                    "end": END,
                },
            )
            workflow.add_edge("tools", "agent")
        else:
            workflow.add_edge("agent", END)

        return workflow.compile(checkpointer=self.checkpointer)

    async def _analyze_market_regime(
        self, state: MarketAnalysisState
    ) -> dict[str, Any]:
        """Analyze current market regime."""
        try:
            # Use market breadth tool
            breadth_tool = next(
                (t for t in self.tools if "breadth" in t.name.lower()), None
            )

            if breadth_tool:
                circuit_breaker = await circuit_manager.get_or_create("market_data")

                async def get_breadth():
                    return await breadth_tool.ainvoke({"index": "SPY"})

                breadth_data = await circuit_breaker.call(get_breadth)

                # Parse results to determine regime
                if isinstance(breadth_data, str):
                    if "Bullish" in breadth_data:
                        state["market_regime"] = "bullish"
                    elif "Bearish" in breadth_data:
                        state["market_regime"] = "bearish"
                    else:
                        state["market_regime"] = "neutral"
                elif isinstance(breadth_data, dict) and "market_breadth" in breadth_data:
                    sentiment = breadth_data["market_breadth"].get("sentiment", "Neutral")
                    state["market_regime"] = sentiment.lower()
                else:
                    state["market_regime"] = "neutral"
            else:
                state["market_regime"] = "neutral"

        except Exception as e:
            logger.error(f"Error analyzing market regime: {e}")
            state["market_regime"] = "unknown"

        state["api_calls_made"] = state.get("api_calls_made", 0) + 1
        return {"market_regime": state.get("market_regime", "neutral")}

    async def _analyze_sectors(self, state: MarketAnalysisState) -> dict[str, Any]:
        """Analyze sector rotation patterns."""
        try:
            # Use sector sentiment tool
            sector_tool = next(
                (t for t in self.tools if "sector" in t.name.lower()), None
            )

            if sector_tool:
                circuit_breaker = await circuit_manager.get_or_create("market_data")

                async def get_sectors():
                    return await sector_tool.ainvoke({})

                sector_data = await circuit_breaker.call(get_sectors)

                if isinstance(sector_data, dict) and "sector_rotation" in sector_data:
                    state["sector_rotation"] = sector_data["sector_rotation"]

                    # Extract leading sectors
                    leading = sector_data["sector_rotation"].get("leading_sectors", [])
                    if leading and state.get("sector_filter"):
                        # Prioritize screening in leading sectors
                        state["sector_filter"] = leading[0].get("name", "")

        except Exception as e:
            logger.error(f"Error analyzing sectors: {e}")

        state["api_calls_made"] = state.get("api_calls_made", 0) + 1
        return {"sector_rotation": state.get("sector_rotation", {})}

    async def _run_screening(self, state: MarketAnalysisState) -> dict[str, Any]:
        """Run multi-strategy screening."""
        try:
            # Determine which screening strategy based on market regime
            strategy = state.get("screening_strategy", "momentum")

            # Adjust strategy based on regime
            if state.get("market_regime") == "bearish" and strategy == "momentum":
                strategy = "mean_reversion"

            # Get appropriate screening tool
            tool_map = {
                "momentum": "maverick_stocks",
                "supply_demand_breakout": "supply_demand_breakouts",
                "bearish": "maverick_bear",
            }

            tool_keyword = tool_map.get(strategy, "maverick")
            screening_tool = next(
                (t for t in self.tools if tool_keyword in t.name.lower()), None
            )

            if screening_tool:
                circuit_breaker = await circuit_manager.get_or_create("screening")

                async def run_screen():
                    return await screening_tool.ainvoke(
                        {"limit": state.get("max_results", 20)}
                    )

                results = await circuit_breaker.call(run_screen)

                if isinstance(results, dict) and "stocks" in results:
                    symbols = [s.get("symbol") for s in results["stocks"]]
                    scores = {
                        s.get("symbol"): s.get("combined_score", 0)
                        for s in results["stocks"]
                    }

                    state["screened_symbols"] = symbols
                    state["screening_scores"] = scores
                    state["cache_hits"] = state.get("cache_hits", 0) + 1

        except Exception as e:
            logger.error(f"Error running screening: {e}")
            state["cache_misses"] = state.get("cache_misses", 0) + 1

        state["api_calls_made"] = state.get("api_calls_made", 0) + 1
        return {
            "screened_symbols": state.get("screened_symbols", []),
            "screening_scores": state.get("screening_scores", {}),
        }

    async def _assess_risks(self, state: MarketAnalysisState) -> dict[str, Any]:
        """Assess risks for screened symbols."""
        symbols = state.get("screened_symbols", [])[:5]  # Top 5 only

        if not symbols:
            return {}

        try:
            # Get risk metrics tool
            risk_tool = next(
                (t for t in self.tools if "risk" in t.name.lower()), None
            )

            if risk_tool and len(symbols) > 1:
                # Calculate portfolio risk metrics
                risk_data = await risk_tool.ainvoke(
                    {"symbols": symbols, "lookback_days": 252}
                )

                # Store risk assessment
                if "conversation_context" not in state:
                    state["conversation_context"] = {}
                state["conversation_context"]["risk_metrics"] = risk_data

        except Exception as e:
            logger.error(f"Error assessing risks: {e}")

        return {}

    async def analyze_market(
        self,
        query: str,
        session_id: str,
        screening_strategy: str = "momentum",
        max_results: int = 20,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Analyze market with specific screening parameters.

        Enhanced with caching, circuit breakers, and comprehensive analysis.

        Args:
            query: Analysis query
            session_id: Session identifier
            screening_strategy: Strategy to use (momentum, supply_demand_breakout, bearish)
            max_results: Maximum number of results
            **kwargs: Additional parameters

        Returns:
            Comprehensive market analysis results
        """
        start_time = datetime.now()

        # Check cache first
        cached = self._check_enhanced_cache(query, session_id, screening_strategy)
        if cached:
            return cached

        # Prepare initial state
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "persona": self.persona.name,
            "session_id": session_id,
            "screening_strategy": screening_strategy,
            "max_results": max_results,
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
        }

        # Update with any additional parameters
        initial_state.update(kwargs)

        # Run the analysis
        result = await self.ainvoke(query, session_id, initial_state=initial_state)

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        result["execution_time_ms"] = execution_time

        # Extract and cache results
        analysis_results = self._extract_enhanced_results(result)

        # Cache results if conversation store available
        if self.conversation_store:
            query_hash = hashlib.sha256(query.lower().encode()).hexdigest()[:8]
            cache_key = f"{screening_strategy}_{query_hash}"

            self.conversation_store.save_analysis(
                session_id=session_id,
                symbol=cache_key,
                analysis_type=f"{screening_strategy}_analysis",
                data=analysis_results,
            )

        return analysis_results

    def _check_enhanced_cache(
        self, query: str, session_id: str, strategy: str
    ) -> dict[str, Any] | None:
        """Check for cached analysis with strategy awareness."""
        if not self.conversation_store:
            return None

        # Create a hash of the query to use as cache key
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()[:8]
        cache_key = f"{strategy}_{query_hash}"

        cached = self.conversation_store.get_analysis(
            session_id=session_id,
            symbol=cache_key,
            analysis_type=f"{strategy}_analysis",
        )

        if cached and cached.get("data"):
            # Check cache age based on strategy
            try:
                timestamp = datetime.fromisoformat(cached["timestamp"])
                age_minutes = (datetime.now() - timestamp).total_seconds() / 60

                # Different cache durations for different strategies
                cache_durations = {
                    "momentum": 15,  # 15 minutes for fast-moving
                    "trending": 60,  # 1 hour for trend following
                    "mean_reversion": 30,  # 30 minutes
                }

                max_age = cache_durations.get(strategy, 30)

                if age_minutes < max_age:
                    logger.info(f"Using cached {strategy} analysis")
                    return cached["data"]
            except (KeyError, ValueError):
                pass

        return None

    def _extract_enhanced_results(self, result: dict[str, Any]) -> dict[str, Any]:
        """Extract comprehensive results from agent output."""
        state = result.get("state", {})

        # Get final message content
        messages = result.get("messages", [])
        content = messages[-1].content if messages else ""

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "query_type": "professional_market_analysis",
            "execution_metrics": {
                "execution_time_ms": result.get("execution_time_ms", 0),
                "api_calls": state.get("api_calls_made", 0),
                "cache_hits": state.get("cache_hits", 0),
                "cache_misses": state.get("cache_misses", 0),
            },
            "market_analysis": {
                "regime": state.get("market_regime", "unknown"),
                "sector_rotation": state.get("sector_rotation", {}),
                "breadth": state.get("market_breadth", {}),
                "sentiment": state.get("sentiment_indicators", {}),
            },
            "screening_results": {
                "strategy": state.get("screening_strategy", "momentum"),
                "symbols": state.get("screened_symbols", [])[:20],
                "scores": state.get("screening_scores", {}),
                "count": len(state.get("screened_symbols", [])),
                "metadata": state.get("symbol_metadata", {}),
            },
            "risk_assessment": state.get("conversation_context", {}).get(
                "risk_metrics", {}
            ),
            "recommendations": {
                "summary": content,
                "persona_adjusted": True,
                "risk_level": self.persona.name,
                "position_sizing": f"Max {self.persona.position_size_max * 100:.1f}% per position",
            },
        }

    def _create_mock_tools(self) -> list[BaseTool]:
        """Create mock tools for testing."""
        from langchain_core.tools import tool

        @tool
        def mock_maverick_stocks(limit: int = 20) -> dict:
            """Mock maverick stocks screening tool."""
            return {
                "stocks": [
                    {"symbol": "AAPL", "combined_score": 85},
                    {"symbol": "MSFT", "combined_score": 82},
                    {"symbol": "NVDA", "combined_score": 90},
                ],
                "count": 3,
            }

        @tool
        def mock_market_breadth(index: str = "SPY") -> dict:
            """Mock market breadth analysis tool."""
            return {
                "market_breadth": {
                    "sentiment": "Bullish",
                    "advance_decline_ratio": 1.5,
                    "new_highs_lows": 150,
                }
            }

        @tool
        def mock_sector_sentiment() -> dict:
            """Mock sector sentiment analysis tool."""
            return {
                "sector_rotation": {
                    "leading_sectors": [
                        {"name": "Technology", "score": 85},
                        {"name": "Healthcare", "score": 72},
                    ],
                    "lagging_sectors": [
                        {"name": "Energy", "score": 45},
                    ],
                }
            }

        return [mock_maverick_stocks, mock_market_breadth, mock_sector_sentiment]
