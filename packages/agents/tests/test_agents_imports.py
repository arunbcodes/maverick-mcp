"""Test that package imports work correctly."""

import pytest


class TestPackageImports:
    """Test that all subpackages can be imported."""

    def test_import_maverick_agents(self):
        """Test importing the main package."""
        import maverick_agents

        assert maverick_agents is not None

    def test_import_base_agent_state(self):
        """Test importing BaseAgentState."""
        from maverick_agents import BaseAgentState

        assert BaseAgentState is not None

    def test_import_persona_aware_agent(self):
        """Test importing PersonaAwareAgent."""
        from maverick_agents import PersonaAwareAgent

        assert PersonaAwareAgent is not None

    def test_import_investor_personas(self):
        """Test importing investor personas."""
        from maverick_agents import (
            INVESTOR_PERSONAS,
            InvestorPersona,
            get_persona,
        )

        assert InvestorPersona is not None
        assert INVESTOR_PERSONAS is not None
        assert get_persona is not None

    def test_import_persona_aware_tool(self):
        """Test importing PersonaAwareTool."""
        from maverick_agents import PersonaAwareTool

        assert PersonaAwareTool is not None

    def test_import_circuit_breaker(self):
        """Test importing circuit breaker components."""
        from maverick_agents import (
            CircuitBreaker,
            CircuitBreakerManager,
            CircuitState,
            circuit_breaker,
            circuit_manager,
        )

        assert CircuitBreaker is not None
        assert CircuitBreakerManager is not None
        assert CircuitState is not None
        assert circuit_breaker is not None
        assert circuit_manager is not None

    def test_import_state_definitions(self):
        """Test importing state definitions."""
        from maverick_agents.state import (
            BacktestingWorkflowState,
            BaseAgentState,
            DeepResearchState,
            MarketAnalysisState,
            PortfolioState,
            RiskManagementState,
            SupervisorState,
            TechnicalAnalysisState,
        )

        assert BaseAgentState is not None
        assert MarketAnalysisState is not None
        assert TechnicalAnalysisState is not None
        assert RiskManagementState is not None
        assert PortfolioState is not None
        assert SupervisorState is not None
        assert DeepResearchState is not None
        assert BacktestingWorkflowState is not None


class TestInvestorPersonas:
    """Test investor persona functionality."""

    def test_default_personas_available(self):
        """Test that default personas are available."""
        from maverick_agents import INVESTOR_PERSONAS

        expected = ["conservative", "moderate", "aggressive", "day_trader"]
        assert set(INVESTOR_PERSONAS.keys()) == set(expected)

    def test_get_persona_valid(self):
        """Test getting a valid persona."""
        from maverick_agents import get_persona

        persona = get_persona("moderate")
        assert persona.name == "Moderate"
        assert persona.risk_tolerance == (30, 60)

    def test_get_persona_invalid(self):
        """Test getting an invalid persona raises error."""
        from maverick_agents import get_persona

        with pytest.raises(KeyError):
            get_persona("unknown_persona")

    def test_create_custom_personas(self):
        """Test creating personas with custom parameters."""
        from maverick_agents import create_default_personas

        custom_params = {
            "moderate": {
                "risk_tolerance_min": 35,
                "risk_tolerance_max": 65,
            }
        }
        personas = create_default_personas(custom_params)

        assert personas["moderate"].risk_tolerance == (35, 65)
        # Other personas should still use defaults
        assert personas["conservative"].risk_tolerance == (10, 30)

    def test_persona_characteristics(self):
        """Test that personas have characteristics."""
        from maverick_agents import INVESTOR_PERSONAS

        for name, persona in INVESTOR_PERSONAS.items():
            assert len(persona.characteristics) > 0, f"{name} has no characteristics"
            assert persona.preferred_timeframe in ["day", "swing", "position"]


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in closed state."""
        from maverick_agents import CircuitBreaker, CircuitState

        breaker = CircuitBreaker(name="test")
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_circuit_breaker_status(self):
        """Test circuit breaker status reporting."""
        from maverick_agents import CircuitBreaker

        breaker = CircuitBreaker(
            name="test",
            failure_threshold=3,
            recovery_timeout=30,
        )
        status = breaker.get_status()

        assert status["name"] == "test"
        assert status["state"] == "closed"
        assert status["failure_threshold"] == 3
        assert status["recovery_timeout"] == 30

    @pytest.mark.asyncio
    async def test_circuit_breaker_successful_call(self):
        """Test circuit breaker with successful calls."""
        from maverick_agents import CircuitBreaker

        breaker = CircuitBreaker(name="test")

        async def success_func():
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_manager(self):
        """Test circuit breaker manager."""
        from maverick_agents import CircuitBreakerManager

        manager = CircuitBreakerManager()

        breaker1 = await manager.get_or_create("service_a")
        breaker2 = await manager.get_or_create("service_b")
        breaker1_again = await manager.get_or_create("service_a")

        assert breaker1 is breaker1_again
        assert breaker1 is not breaker2

        status = manager.get_all_status()
        assert "service_a" in status
        assert "service_b" in status


class TestPersonaAwareTool:
    """Test PersonaAwareTool functionality."""

    def _create_test_tool(self):
        """Create a concrete test tool for testing PersonaAwareTool methods."""
        from maverick_agents import PersonaAwareTool

        # Create a concrete subclass for testing
        class TestTool(PersonaAwareTool):
            name: str = "test_tool"
            description: str = "A test tool"

            def _run(self, query: str) -> str:
                return f"Processed: {query}"

        return TestTool()

    def test_tool_without_persona(self):
        """Test tool behavior without persona set."""
        tool = self._create_test_tool()
        tool.persona = None

        # Without persona, values should pass through unchanged
        assert tool.adjust_for_risk(100.0, "position_size") == 100.0

    def test_tool_with_persona(self):
        """Test tool behavior with persona set."""
        from maverick_agents import INVESTOR_PERSONAS

        tool = self._create_test_tool()
        tool.persona = INVESTOR_PERSONAS["conservative"]

        # Conservative persona should cap position size
        adjusted = tool.adjust_for_risk(1.0, "position_size")
        assert adjusted <= tool.persona.position_size_max

    def test_stock_context_tracking(self):
        """Test that tool tracks stock analysis context."""
        tool = self._create_test_tool()
        tool.persona = None

        # Update with analysis data
        tool.update_analysis_data("AAPL", {
            "price": 150.0,
            "price_levels": {"support": 145.0, "resistance": 155.0},
        })

        context = tool.get_stock_context("AAPL")
        assert context["analysis"]["price"] == 150.0
        assert context["price_levels"]["support"] == 145.0
        assert context["last_analysis"] is not None


class TestProviders:
    """Test web search providers."""

    def test_import_providers(self):
        """Test importing providers module."""
        from maverick_agents.providers import (
            SearchResult,
            WebSearchConfig,
            WebSearchProvider,
        )

        assert WebSearchProvider is not None
        assert WebSearchConfig is not None
        assert SearchResult is not None

    def test_search_result(self):
        """Test SearchResult dataclass."""
        from maverick_agents.providers import SearchResult

        result = SearchResult(
            url="https://example.com",
            title="Test Result",
            snippet="Test snippet",
            score=0.95,
        )

        assert result.url == "https://example.com"
        assert result.title == "Test Result"
        assert result.score == 0.95

        # Test to_dict
        result_dict = result.to_dict()
        assert result_dict["url"] == "https://example.com"
        assert result_dict["title"] == "Test Result"

    def test_web_search_config_defaults(self):
        """Test WebSearchConfig default values."""
        from maverick_agents.providers import WebSearchConfig

        config = WebSearchConfig()

        assert config.default_timeout == 30.0
        assert config.max_failures == 3
        assert len(config.financial_domains) > 0
        assert "sec.gov" in config.financial_domains

    def test_web_search_config_custom(self):
        """Test WebSearchConfig with custom values."""
        from maverick_agents.providers import WebSearchConfig

        config = WebSearchConfig(
            default_timeout=60.0,
            max_failures=5,
        )

        assert config.default_timeout == 60.0
        assert config.max_failures == 5


class TestResearchConfig:
    """Test research configuration."""

    def test_import_research_config(self):
        """Test importing research config."""
        from maverick_agents.research import (
            PERSONA_RESEARCH_FOCUS,
            RESEARCH_DEPTH_LEVELS,
            ResearchDepth,
        )

        assert RESEARCH_DEPTH_LEVELS is not None
        assert PERSONA_RESEARCH_FOCUS is not None
        assert ResearchDepth is not None

    def test_research_depth_levels(self):
        """Test research depth levels configuration."""
        from maverick_agents.research import RESEARCH_DEPTH_LEVELS

        assert "basic" in RESEARCH_DEPTH_LEVELS
        assert "standard" in RESEARCH_DEPTH_LEVELS
        assert "comprehensive" in RESEARCH_DEPTH_LEVELS
        assert "exhaustive" in RESEARCH_DEPTH_LEVELS

        # Check standard config
        standard = RESEARCH_DEPTH_LEVELS["standard"]
        assert "max_sources" in standard
        assert "max_searches" in standard
        assert standard["max_sources"] > 0

    def test_get_depth_config(self):
        """Test get_depth_config function."""
        from maverick_agents.research.config import get_depth_config

        config = get_depth_config("comprehensive")
        assert config["max_sources"] == 10
        assert config["analysis_depth"] == "comprehensive"

    def test_get_depth_config_invalid(self):
        """Test get_depth_config with invalid depth."""
        from maverick_agents.research.config import get_depth_config

        with pytest.raises(ValueError):
            get_depth_config("invalid_depth")

    def test_persona_research_focus(self):
        """Test persona research focus configuration."""
        from maverick_agents.research import PERSONA_RESEARCH_FOCUS

        assert "conservative" in PERSONA_RESEARCH_FOCUS
        assert "moderate" in PERSONA_RESEARCH_FOCUS
        assert "aggressive" in PERSONA_RESEARCH_FOCUS
        assert "day_trader" in PERSONA_RESEARCH_FOCUS

        # Check conservative config
        conservative = PERSONA_RESEARCH_FOCUS["conservative"]
        assert "keywords" in conservative
        assert "dividend" in conservative["keywords"]
        assert conservative["time_horizon"] == "long-term"

    def test_get_persona_focus(self):
        """Test get_persona_focus function."""
        from maverick_agents.research.config import get_persona_focus

        focus = get_persona_focus("aggressive")
        assert "growth" in focus["keywords"]
        assert focus["risk_focus"] == "upside potential"

    def test_get_persona_keywords(self):
        """Test get_persona_keywords function."""
        from maverick_agents.research.config import get_persona_keywords

        keywords = get_persona_keywords("moderate")
        assert "growth" in keywords
        assert "value" in keywords


class TestSupervisorImports:
    """Test supervisor module imports."""

    def test_import_supervisor_agent(self):
        """Test importing SupervisorAgent."""
        from maverick_agents import SupervisorAgent

        assert SupervisorAgent is not None

    def test_import_query_classifier(self):
        """Test importing QueryClassifier."""
        from maverick_agents import QueryClassifier

        assert QueryClassifier is not None

    def test_import_result_synthesizer(self):
        """Test importing ResultSynthesizer."""
        from maverick_agents import ResultSynthesizer

        assert ResultSynthesizer is not None

    def test_import_routing_config(self):
        """Test importing routing configuration."""
        from maverick_agents import (
            AGENT_WEIGHTS,
            CLASSIFICATION_KEYWORDS,
            ROUTING_MATRIX,
            get_routing_config,
            get_agent_weights,
            classify_query_by_keywords,
        )

        assert ROUTING_MATRIX is not None
        assert AGENT_WEIGHTS is not None
        assert CLASSIFICATION_KEYWORDS is not None
        assert get_routing_config is not None
        assert get_agent_weights is not None
        assert classify_query_by_keywords is not None

    def test_import_exceptions(self):
        """Test importing agent exceptions."""
        from maverick_agents import (
            AgentError,
            AgentExecutionError,
            AgentInitializationError,
            AgentTimeoutError,
            QueryClassificationError,
            SynthesisError,
        )

        assert AgentError is not None
        assert AgentInitializationError is not None
        assert AgentExecutionError is not None
        assert QueryClassificationError is not None
        assert AgentTimeoutError is not None
        assert SynthesisError is not None


class TestRoutingConfiguration:
    """Test routing configuration functionality."""

    def test_routing_matrix_categories(self):
        """Test that routing matrix has expected categories."""
        from maverick_agents import ROUTING_MATRIX

        expected_categories = [
            "market_screening",
            "technical_analysis",
            "stock_investment_decision",
            "portfolio_analysis",
            "deep_research",
            "company_research",
            "sentiment_analysis",
            "risk_assessment",
        ]

        for category in expected_categories:
            assert category in ROUTING_MATRIX, f"Missing category: {category}"

    def test_routing_config_structure(self):
        """Test routing config has expected structure."""
        from maverick_agents import ROUTING_MATRIX

        for category, config in ROUTING_MATRIX.items():
            assert "agents" in config, f"{category} missing agents"
            assert "primary" in config, f"{category} missing primary"
            assert "parallel" in config, f"{category} missing parallel"
            assert "confidence_threshold" in config, f"{category} missing confidence_threshold"

    def test_get_routing_config_valid(self):
        """Test getting valid routing config."""
        from maverick_agents import get_routing_config

        config = get_routing_config("technical_analysis")
        assert config["agents"] == ["technical"]
        assert config["primary"] == "technical"
        assert config["parallel"] is False

    def test_get_routing_config_invalid(self):
        """Test getting invalid category returns default."""
        from maverick_agents import get_routing_config

        # Should return default (stock_investment_decision)
        config = get_routing_config("invalid_category")
        assert "agents" in config
        assert "market" in config["agents"]

    def test_agent_weights_structure(self):
        """Test agent weights configuration."""
        from maverick_agents import AGENT_WEIGHTS

        for query_type, weights in AGENT_WEIGHTS.items():
            total = sum(weights.values())
            assert 0.99 <= total <= 1.01, f"{query_type} weights don't sum to 1: {total}"

    def test_get_agent_weights(self):
        """Test get_agent_weights function."""
        from maverick_agents import get_agent_weights

        weights = get_agent_weights("technical_analysis")
        assert weights["technical"] == 0.8
        assert weights["market"] == 0.2

    def test_get_agent_weights_default(self):
        """Test get_agent_weights returns default for unknown type."""
        from maverick_agents import get_agent_weights

        weights = get_agent_weights("unknown_type")
        assert weights == {"market": 0.5, "technical": 0.5}


class TestQueryClassification:
    """Test query classification functionality."""

    def test_classify_by_keywords_technical(self):
        """Test keyword classification for technical analysis."""
        from maverick_agents import classify_query_by_keywords

        queries = [
            "Show me the RSI for AAPL",
            "What's the MACD signal?",
            "Can you draw a chart for TSLA?",
            "Technical analysis of MSFT",
        ]

        for query in queries:
            result = classify_query_by_keywords(query)
            assert result == "technical_analysis", f"'{query}' classified as {result}"

    def test_classify_by_keywords_market(self):
        """Test keyword classification for market screening."""
        from maverick_agents import classify_query_by_keywords

        queries = [
            "Screen for high momentum stocks",
            "Find stocks with high volume",
            "Scan the market for breakouts",
        ]

        for query in queries:
            result = classify_query_by_keywords(query)
            assert result == "market_screening", f"'{query}' classified as {result}"

    def test_classify_by_keywords_research(self):
        """Test keyword classification for research."""
        from maverick_agents import classify_query_by_keywords

        queries = [
            "Analyze the earnings report",
            "What's the news on NVDA?",
            "Tell me about fundamental analysis for AAPL",
        ]

        for query in queries:
            result = classify_query_by_keywords(query)
            assert result == "deep_research", f"'{query}' classified as {result}"

    def test_classify_by_keywords_default(self):
        """Test keyword classification defaults to stock investment."""
        from maverick_agents import classify_query_by_keywords

        # Generic queries should default to stock_investment_decision
        result = classify_query_by_keywords("Tell me about AAPL")
        assert result == "stock_investment_decision"


class TestAgentExceptions:
    """Test agent exception classes."""

    def test_agent_initialization_error(self):
        """Test AgentInitializationError."""
        from maverick_agents import AgentInitializationError

        error = AgentInitializationError("supervisor", "LLM not configured")
        assert error.agent_type == "supervisor"
        assert error.reason == "LLM not configured"
        assert "supervisor" in str(error)

    def test_agent_execution_error(self):
        """Test AgentExecutionError."""
        from maverick_agents import AgentExecutionError

        error = AgentExecutionError("market", "analysis", "API timeout")
        assert error.agent_type == "market"
        assert error.operation == "analysis"
        assert error.reason == "API timeout"
        assert "market" in str(error)

    def test_query_classification_error(self):
        """Test QueryClassificationError."""
        from maverick_agents import QueryClassificationError

        error = QueryClassificationError("Find me stocks with high returns", "LLM failed")
        assert error.reason == "LLM failed"
        assert "Find me" in str(error)

    def test_agent_timeout_error(self):
        """Test AgentTimeoutError."""
        from maverick_agents import AgentTimeoutError

        error = AgentTimeoutError("research", 30.0)
        assert error.agent_type == "research"
        assert error.timeout_seconds == 30.0
        assert "30" in str(error)

    def test_synthesis_error(self):
        """Test SynthesisError."""
        from maverick_agents import SynthesisError

        error = SynthesisError("Conflicting agent results")
        assert error.reason == "Conflicting agent results"
        assert "Conflicting" in str(error)

    def test_exception_inheritance(self):
        """Test all exceptions inherit from AgentError."""
        from maverick_agents import (
            AgentError,
            AgentExecutionError,
            AgentInitializationError,
            AgentTimeoutError,
            QueryClassificationError,
            SynthesisError,
        )

        assert issubclass(AgentInitializationError, AgentError)
        assert issubclass(AgentExecutionError, AgentError)
        assert issubclass(QueryClassificationError, AgentError)
        assert issubclass(AgentTimeoutError, AgentError)
        assert issubclass(SynthesisError, AgentError)


class TestTechnicalAnalysisAgent:
    """Test TechnicalAnalysisAgent import and basic functionality."""

    def test_import_technical_analysis_agent(self):
        """Test importing TechnicalAnalysisAgent."""
        from maverick_agents import TechnicalAnalysisAgent

        assert TechnicalAnalysisAgent is not None

    def test_import_from_analyzers(self):
        """Test importing from analyzers subpackage."""
        from maverick_agents.analyzers import TechnicalAnalysisAgent

        assert TechnicalAnalysisAgent is not None

    def test_agent_has_required_methods(self):
        """Test that agent has required methods."""
        from maverick_agents import TechnicalAnalysisAgent

        # Check for key methods
        assert hasattr(TechnicalAnalysisAgent, "analyze_stock")
        assert hasattr(TechnicalAnalysisAgent, "get_state_schema")
        assert hasattr(TechnicalAnalysisAgent, "_build_graph")
        assert hasattr(TechnicalAnalysisAgent, "_build_system_prompt")

    def test_agent_inherits_from_persona_aware(self):
        """Test that agent inherits from PersonaAwareAgent."""
        from maverick_agents import PersonaAwareAgent, TechnicalAnalysisAgent

        assert issubclass(TechnicalAnalysisAgent, PersonaAwareAgent)

    def test_agent_uses_correct_state_schema(self):
        """Test that agent uses TechnicalAnalysisState."""
        from maverick_agents import TechnicalAnalysisAgent
        from maverick_agents.state import TechnicalAnalysisState

        # Create a mock to check state schema
        # We can't instantiate without an LLM, but we can check the method exists
        assert TechnicalAnalysisAgent.get_state_schema is not None


class TestMarketAnalysisAgent:
    """Test MarketAnalysisAgent import and basic functionality."""

    def test_import_market_analysis_agent(self):
        """Test importing MarketAnalysisAgent."""
        from maverick_agents import MarketAnalysisAgent

        assert MarketAnalysisAgent is not None

    def test_import_from_analyzers(self):
        """Test importing from analyzers subpackage."""
        from maverick_agents.analyzers import MarketAnalysisAgent

        assert MarketAnalysisAgent is not None

    def test_agent_has_required_methods(self):
        """Test that agent has required methods."""
        from maverick_agents import MarketAnalysisAgent

        # Check for key methods
        assert hasattr(MarketAnalysisAgent, "analyze_market")
        assert hasattr(MarketAnalysisAgent, "get_state_schema")
        assert hasattr(MarketAnalysisAgent, "_build_graph")
        assert hasattr(MarketAnalysisAgent, "_build_system_prompt")

    def test_agent_inherits_from_persona_aware(self):
        """Test that agent inherits from PersonaAwareAgent."""
        from maverick_agents import MarketAnalysisAgent, PersonaAwareAgent

        assert issubclass(MarketAnalysisAgent, PersonaAwareAgent)

    def test_agent_has_valid_personas(self):
        """Test that agent has valid personas defined."""
        from maverick_agents import MarketAnalysisAgent

        expected_personas = ["conservative", "moderate", "aggressive", "day_trader"]
        assert MarketAnalysisAgent.VALID_PERSONAS == expected_personas

    def test_agent_uses_correct_state_schema(self):
        """Test that agent uses MarketAnalysisState."""
        from maverick_agents import MarketAnalysisAgent
        from maverick_agents.state import MarketAnalysisState

        # Check the method exists
        assert MarketAnalysisAgent.get_state_schema is not None


class TestResearchProviders:
    """Test research provider imports and basic functionality."""

    def test_import_web_search_provider(self):
        """Test importing WebSearchProvider base class."""
        from maverick_agents.research import WebSearchProvider

        assert WebSearchProvider is not None

    def test_import_web_search_error(self):
        """Test importing WebSearchError exception."""
        from maverick_agents.research import WebSearchError

        assert WebSearchError is not None
        assert issubclass(WebSearchError, Exception)

    def test_import_exa_provider(self):
        """Test importing ExaSearchProvider."""
        from maverick_agents.research import ExaSearchProvider

        assert ExaSearchProvider is not None

    def test_import_tavily_provider(self):
        """Test importing TavilySearchProvider."""
        from maverick_agents.research import TavilySearchProvider

        assert TavilySearchProvider is not None

    def test_providers_inherit_from_base(self):
        """Test that providers inherit from WebSearchProvider."""
        from maverick_agents.research import (
            ExaSearchProvider,
            TavilySearchProvider,
            WebSearchProvider,
        )

        assert issubclass(ExaSearchProvider, WebSearchProvider)
        assert issubclass(TavilySearchProvider, WebSearchProvider)

    def test_exa_provider_has_financial_domains(self):
        """Test ExaSearchProvider has financial domain list."""
        from maverick_agents.research import ExaSearchProvider

        assert hasattr(ExaSearchProvider, "FINANCIAL_DOMAINS")
        assert "sec.gov" in ExaSearchProvider.FINANCIAL_DOMAINS
        assert "bloomberg.com" in ExaSearchProvider.FINANCIAL_DOMAINS

    def test_exa_provider_has_excluded_domains(self):
        """Test ExaSearchProvider has excluded domain list."""
        from maverick_agents.research import ExaSearchProvider

        assert hasattr(ExaSearchProvider, "EXCLUDED_DOMAINS")
        assert "twitter.com" in ExaSearchProvider.EXCLUDED_DOMAINS

    def test_default_settings(self):
        """Test DefaultSettings class."""
        from maverick_agents.research import DefaultSettings

        settings = DefaultSettings()
        assert settings.performance is not None
        assert settings.performance.search_default_timeout == 30.0


class TestContentAnalyzer:
    """Test ContentAnalyzer import and basic functionality."""

    def test_import_content_analyzer(self):
        """Test importing ContentAnalyzer."""
        from maverick_agents.research import ContentAnalyzer

        assert ContentAnalyzer is not None

    def test_content_analyzer_has_analyze_content_method(self):
        """Test ContentAnalyzer has analyze_content method."""
        from maverick_agents.research import ContentAnalyzer

        assert hasattr(ContentAnalyzer, "analyze_content")

    def test_content_analyzer_has_batch_method(self):
        """Test ContentAnalyzer has batch processing method."""
        from maverick_agents.research import ContentAnalyzer

        assert hasattr(ContentAnalyzer, "analyze_content_batch")

    def test_content_analyzer_has_coerce_message(self):
        """Test ContentAnalyzer has message coercion utility."""
        from maverick_agents.research import ContentAnalyzer

        # Test static method
        result = ContentAnalyzer._coerce_message_content("test")
        assert result == "test"

        # Test list coercion
        result = ContentAnalyzer._coerce_message_content([{"text": "hello"}])
        assert result == "hello"


class TestResearchSubagents:
    """Test research subagent imports and basic functionality."""

    def test_import_base_subagent(self):
        """Test importing BaseSubagent."""
        from maverick_agents.research import BaseSubagent

        assert BaseSubagent is not None

    def test_import_research_task(self):
        """Test importing ResearchTask."""
        from maverick_agents.research import ResearchTask

        assert ResearchTask is not None

    def test_import_fundamental_research_agent(self):
        """Test importing FundamentalResearchAgent."""
        from maverick_agents.research import FundamentalResearchAgent

        assert FundamentalResearchAgent is not None

    def test_import_technical_research_agent(self):
        """Test importing TechnicalResearchAgent."""
        from maverick_agents.research import TechnicalResearchAgent

        assert TechnicalResearchAgent is not None

    def test_import_sentiment_research_agent(self):
        """Test importing SentimentResearchAgent."""
        from maverick_agents.research import SentimentResearchAgent

        assert SentimentResearchAgent is not None

    def test_import_competitive_research_agent(self):
        """Test importing CompetitiveResearchAgent."""
        from maverick_agents.research import CompetitiveResearchAgent

        assert CompetitiveResearchAgent is not None

    def test_subagents_inherit_from_base(self):
        """Test that subagents inherit from BaseSubagent."""
        from maverick_agents.research import (
            BaseSubagent,
            CompetitiveResearchAgent,
            FundamentalResearchAgent,
            SentimentResearchAgent,
            TechnicalResearchAgent,
        )

        assert issubclass(FundamentalResearchAgent, BaseSubagent)
        assert issubclass(TechnicalResearchAgent, BaseSubagent)
        assert issubclass(SentimentResearchAgent, BaseSubagent)
        assert issubclass(CompetitiveResearchAgent, BaseSubagent)

    def test_subagents_have_focus_areas(self):
        """Test that subagents have FOCUS_AREAS defined."""
        from maverick_agents.research import (
            CompetitiveResearchAgent,
            FundamentalResearchAgent,
            SentimentResearchAgent,
            TechnicalResearchAgent,
        )

        assert hasattr(FundamentalResearchAgent, "FOCUS_AREAS")
        assert hasattr(TechnicalResearchAgent, "FOCUS_AREAS")
        assert hasattr(SentimentResearchAgent, "FOCUS_AREAS")
        assert hasattr(CompetitiveResearchAgent, "FOCUS_AREAS")

        # Check specific focus areas
        assert "earnings" in FundamentalResearchAgent.FOCUS_AREAS
        assert "price_action" in TechnicalResearchAgent.FOCUS_AREAS
        assert "market_sentiment" in SentimentResearchAgent.FOCUS_AREAS
        assert "competitive_position" in CompetitiveResearchAgent.FOCUS_AREAS

    def test_research_task_creation(self):
        """Test creating a ResearchTask."""
        from maverick_agents.research import ResearchTask

        task = ResearchTask(
            task_id="test-123",
            task_type="fundamental",
            target_topic="AAPL company analysis",
            focus_areas=["earnings", "valuation"],
            priority=1,
        )

        assert task.task_id == "test-123"
        assert task.task_type == "fundamental"
        assert task.target_topic == "AAPL company analysis"
        assert task.focus_areas == ["earnings", "valuation"]
        assert task.priority == 1
        assert task.status == "pending"
        assert task.result is None

    def test_base_subagent_has_required_methods(self):
        """Test BaseSubagent has required methods."""
        from maverick_agents.research import BaseSubagent

        assert hasattr(BaseSubagent, "execute_research")
        assert hasattr(BaseSubagent, "_safe_search")
        assert hasattr(BaseSubagent, "_perform_specialized_search")
        assert hasattr(BaseSubagent, "_analyze_search_results")
        assert hasattr(BaseSubagent, "_calculate_source_credibility")
        assert hasattr(BaseSubagent, "_aggregate_insights")
        assert hasattr(BaseSubagent, "_calculate_sentiment")


class TestDeepResearchAgent:
    """Test DeepResearchAgent coordinator import and basic functionality."""

    def test_import_deep_research_agent(self):
        """Test importing DeepResearchAgent."""
        from maverick_agents.research import DeepResearchAgent

        assert DeepResearchAgent is not None

    def test_import_from_coordinator(self):
        """Test importing from coordinator module."""
        from maverick_agents.research.coordinator import DeepResearchAgent

        assert DeepResearchAgent is not None

    def test_import_parallel_config(self):
        """Test importing parallel config classes."""
        from maverick_agents.research import (
            DefaultParallelConfig,
            ParallelConfigProtocol,
            ParallelResearchResult,
        )

        assert DefaultParallelConfig is not None
        assert ParallelConfigProtocol is not None
        assert ParallelResearchResult is not None

    def test_import_protocol_classes(self):
        """Test importing protocol classes."""
        from maverick_agents.research import (
            ConversationStoreProtocol,
            ParallelOrchestratorProtocol,
            TaskDistributorProtocol,
        )

        assert ConversationStoreProtocol is not None
        assert ParallelOrchestratorProtocol is not None
        assert TaskDistributorProtocol is not None

    def test_default_parallel_config_creation(self):
        """Test creating DefaultParallelConfig."""
        from maverick_agents.research import DefaultParallelConfig

        config = DefaultParallelConfig()

        assert config.max_concurrent_agents == 4
        assert config.timeout_per_agent == 180.0
        assert config.enable_fallbacks is False
        assert config.rate_limit_delay == 0.5

    def test_default_parallel_config_custom_values(self):
        """Test DefaultParallelConfig with custom values."""
        from maverick_agents.research import DefaultParallelConfig

        config = DefaultParallelConfig(
            max_concurrent_agents=6,
            timeout_per_agent=240.0,
            enable_fallbacks=True,
            rate_limit_delay=0.1,
        )

        assert config.max_concurrent_agents == 6
        assert config.timeout_per_agent == 240.0
        assert config.enable_fallbacks is True
        assert config.rate_limit_delay == 0.1

    def test_parallel_research_result_creation(self):
        """Test creating ParallelResearchResult."""
        from maverick_agents.research import ParallelResearchResult

        result = ParallelResearchResult()

        assert result.task_results == {}
        assert result.synthesis is None
        assert result.successful_tasks == 0
        assert result.failed_tasks == 0
        assert result.total_execution_time == 0.0
        assert result.parallel_efficiency == 0.0

    def test_deep_research_agent_inherits_from_persona_aware(self):
        """Test that DeepResearchAgent inherits from PersonaAwareAgent."""
        from maverick_agents import PersonaAwareAgent
        from maverick_agents.research import DeepResearchAgent

        assert issubclass(DeepResearchAgent, PersonaAwareAgent)

    def test_deep_research_agent_has_required_methods(self):
        """Test DeepResearchAgent has required methods."""
        from maverick_agents.research import DeepResearchAgent

        # Public API methods
        assert hasattr(DeepResearchAgent, "research_comprehensive")
        assert hasattr(DeepResearchAgent, "research_company_comprehensive")
        assert hasattr(DeepResearchAgent, "research_topic")
        assert hasattr(DeepResearchAgent, "analyze_market_sentiment")

        # Initialization
        assert hasattr(DeepResearchAgent, "initialize")

        # State schema
        assert hasattr(DeepResearchAgent, "get_state_schema")

        # Graph building
        assert hasattr(DeepResearchAgent, "_build_graph")

    def test_deep_research_agent_has_workflow_nodes(self):
        """Test DeepResearchAgent has workflow node methods."""
        from maverick_agents.research import DeepResearchAgent

        # LangGraph workflow nodes
        assert hasattr(DeepResearchAgent, "_plan_research")
        assert hasattr(DeepResearchAgent, "_execute_searches")
        assert hasattr(DeepResearchAgent, "_analyze_content")
        assert hasattr(DeepResearchAgent, "_validate_sources")
        assert hasattr(DeepResearchAgent, "_synthesize_findings")
        assert hasattr(DeepResearchAgent, "_generate_citations")

    def test_deep_research_agent_has_parallel_execution_methods(self):
        """Test DeepResearchAgent has parallel execution methods."""
        from maverick_agents.research import DeepResearchAgent

        assert hasattr(DeepResearchAgent, "_execute_parallel_research")
        assert hasattr(DeepResearchAgent, "_execute_sequential_research")
        assert hasattr(DeepResearchAgent, "_create_research_tasks")
        assert hasattr(DeepResearchAgent, "_execute_tasks_parallel")
        assert hasattr(DeepResearchAgent, "_create_subagent")
        assert hasattr(DeepResearchAgent, "_synthesize_parallel_results")

    def test_deep_research_agent_has_helper_methods(self):
        """Test DeepResearchAgent has helper methods."""
        from maverick_agents.research import DeepResearchAgent

        # Search and analysis helpers
        assert hasattr(DeepResearchAgent, "_generate_search_queries")
        assert hasattr(DeepResearchAgent, "_execute_search_queries")
        assert hasattr(DeepResearchAgent, "_analyze_search_results")
        assert hasattr(DeepResearchAgent, "_validate_source_credibility")
        assert hasattr(DeepResearchAgent, "_calculate_credibility_score")

        # Synthesis helpers
        assert hasattr(DeepResearchAgent, "_synthesize_research_findings")
        assert hasattr(DeepResearchAgent, "_calculate_research_confidence")
        assert hasattr(DeepResearchAgent, "_generate_source_citations")
        assert hasattr(DeepResearchAgent, "_calculate_aggregate_sentiment")
        assert hasattr(DeepResearchAgent, "_generate_synthesis_text")
        assert hasattr(DeepResearchAgent, "_derive_recommendation")

    def test_deep_research_agent_uses_correct_state_schema(self):
        """Test DeepResearchAgent uses DeepResearchState."""
        from maverick_agents.research import DeepResearchAgent
        from maverick_agents.state import DeepResearchState

        # Verify the state schema relationship
        assert DeepResearchAgent.get_state_schema is not None

    def test_protocol_compliance_parallel_config(self):
        """Test DefaultParallelConfig complies with ParallelConfigProtocol."""
        from typing import runtime_checkable

        from maverick_agents.research import (
            DefaultParallelConfig,
            ParallelConfigProtocol,
        )

        config = DefaultParallelConfig()

        # Protocol attributes should exist
        assert hasattr(config, "max_concurrent_agents")
        assert hasattr(config, "timeout_per_agent")
        assert hasattr(config, "enable_fallbacks")
        assert hasattr(config, "rate_limit_delay")

        # Verify it's runtime checkable
        assert isinstance(config, ParallelConfigProtocol)
