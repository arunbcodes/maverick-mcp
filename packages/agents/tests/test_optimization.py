"""Tests for research optimization modules."""

import pytest


class TestOptimizationImports:
    """Test that optimization modules can be imported."""

    def test_import_optimization_package(self):
        """Test optimization package import."""
        from maverick_agents.research import optimization
        assert optimization is not None

    def test_import_adaptive_model_selector(self):
        """Test AdaptiveModelSelector import."""
        from maverick_agents.research.optimization import AdaptiveModelSelector
        assert AdaptiveModelSelector is not None

    def test_import_model_configuration(self):
        """Test ModelConfiguration import."""
        from maverick_agents.research.optimization import ModelConfiguration
        assert ModelConfiguration is not None

    def test_import_progressive_token_budgeter(self):
        """Test ProgressiveTokenBudgeter import."""
        from maverick_agents.research.optimization import ProgressiveTokenBudgeter
        assert ProgressiveTokenBudgeter is not None

    def test_import_research_phase(self):
        """Test ResearchPhase import."""
        from maverick_agents.research.optimization import ResearchPhase
        assert ResearchPhase is not None

    def test_import_token_allocation(self):
        """Test TokenAllocation import."""
        from maverick_agents.research.optimization import TokenAllocation
        assert TokenAllocation is not None

    def test_import_confidence_tracker(self):
        """Test ConfidenceTracker import."""
        from maverick_agents.research.optimization import ConfidenceTracker
        assert ConfidenceTracker is not None

    def test_import_intelligent_content_filter(self):
        """Test IntelligentContentFilter import."""
        from maverick_agents.research.optimization import IntelligentContentFilter
        assert IntelligentContentFilter is not None

    def test_import_optimized_prompt_engine(self):
        """Test OptimizedPromptEngine import."""
        from maverick_agents.research.optimization import OptimizedPromptEngine
        assert OptimizedPromptEngine is not None

    def test_import_parallel_llm_processor(self):
        """Test ParallelLLMProcessor import."""
        from maverick_agents.research.optimization import ParallelLLMProcessor
        assert ParallelLLMProcessor is not None


class TestOptimizedAgentImports:
    """Test that optimized agent modules can be imported."""

    def test_import_optimized_package(self):
        """Test optimized package import."""
        from maverick_agents.research import optimized
        assert optimized is not None

    def test_import_optimized_content_analyzer(self):
        """Test OptimizedContentAnalyzer import."""
        from maverick_agents.research.optimized import OptimizedContentAnalyzer
        assert OptimizedContentAnalyzer is not None

    def test_import_optimized_deep_research_agent(self):
        """Test OptimizedDeepResearchAgent import."""
        from maverick_agents.research.optimized import OptimizedDeepResearchAgent
        assert OptimizedDeepResearchAgent is not None

    def test_import_create_optimized_research_agent(self):
        """Test create_optimized_research_agent import."""
        from maverick_agents.research.optimized import create_optimized_research_agent
        assert create_optimized_research_agent is not None

    def test_import_from_research_module(self):
        """Test imports from research module."""
        from maverick_agents.research import (
            AdaptiveModelSelector,
            ConfidenceTracker,
            IntelligentContentFilter,
            OptimizedContentAnalyzer,
            OptimizedDeepResearchAgent,
            OptimizedPromptEngine,
            ParallelLLMProcessor,
            ProgressiveTokenBudgeter,
            create_optimized_research_agent,
        )
        assert AdaptiveModelSelector is not None
        assert ConfidenceTracker is not None
        assert IntelligentContentFilter is not None
        assert OptimizedContentAnalyzer is not None
        assert OptimizedDeepResearchAgent is not None
        assert OptimizedPromptEngine is not None
        assert ParallelLLMProcessor is not None
        assert ProgressiveTokenBudgeter is not None
        assert create_optimized_research_agent is not None


class TestModelConfiguration:
    """Test ModelConfiguration class."""

    def test_create_model_configuration(self):
        """Test creating ModelConfiguration."""
        from maverick_agents.research.optimization import ModelConfiguration

        config = ModelConfiguration(
            model_id="test/model",
            max_tokens=1000,
            temperature=0.5,
            timeout_seconds=30.0,
        )
        assert config.model_id == "test/model"
        assert config.max_tokens == 1000
        assert config.temperature == 0.5
        assert config.timeout_seconds == 30.0
        assert config.parallel_batch_size == 1  # Default

    def test_model_configuration_with_batch_size(self):
        """Test ModelConfiguration with custom batch size."""
        from maverick_agents.research.optimization import ModelConfiguration

        config = ModelConfiguration(
            model_id="test/model",
            max_tokens=2000,
            temperature=0.3,
            timeout_seconds=45.0,
            parallel_batch_size=4,
        )
        assert config.parallel_batch_size == 4


class TestResearchPhase:
    """Test ResearchPhase enum."""

    def test_research_phases_exist(self):
        """Test that all research phases exist."""
        from maverick_agents.research.optimization import ResearchPhase

        assert ResearchPhase.SEARCH == "search"
        assert ResearchPhase.CONTENT_ANALYSIS == "content_analysis"
        assert ResearchPhase.SYNTHESIS == "synthesis"
        assert ResearchPhase.VALIDATION == "validation"


class TestTokenAllocation:
    """Test TokenAllocation class."""

    def test_create_token_allocation(self):
        """Test creating TokenAllocation."""
        from maverick_agents.research.optimization import TokenAllocation

        allocation = TokenAllocation(
            input_tokens=5000,
            output_tokens=1000,
            per_source_tokens=500,
            emergency_reserve=200,
            timeout_seconds=30.0,
        )
        assert allocation.input_tokens == 5000
        assert allocation.output_tokens == 1000
        assert allocation.per_source_tokens == 500
        assert allocation.emergency_reserve == 200
        assert allocation.timeout_seconds == 30.0


class TestProgressiveTokenBudgeter:
    """Test ProgressiveTokenBudgeter class."""

    def test_create_token_budgeter(self):
        """Test creating ProgressiveTokenBudgeter."""
        from maverick_agents.research.optimization import ProgressiveTokenBudgeter

        budgeter = ProgressiveTokenBudgeter(
            total_time_budget_seconds=120.0,
            confidence_target=0.75,
        )
        assert budgeter.total_time_budget == 120.0
        assert budgeter.confidence_target == 0.75
        assert budgeter.phase_budgets is not None

    def test_budgeter_emergency_mode(self):
        """Test budgeter in emergency mode (short time budget)."""
        from maverick_agents.research.optimization import (
            ProgressiveTokenBudgeter,
            ResearchPhase,
        )

        budgeter = ProgressiveTokenBudgeter(
            total_time_budget_seconds=20.0,
        )
        assert budgeter.phase_budgets[ResearchPhase.SEARCH] == 500

    def test_budgeter_standard_mode(self):
        """Test budgeter in standard mode (long time budget)."""
        from maverick_agents.research.optimization import (
            ProgressiveTokenBudgeter,
            ResearchPhase,
        )

        budgeter = ProgressiveTokenBudgeter(
            total_time_budget_seconds=120.0,
        )
        assert budgeter.phase_budgets[ResearchPhase.SEARCH] == 1500


class TestConfidenceTracker:
    """Test ConfidenceTracker class."""

    def test_create_confidence_tracker(self):
        """Test creating ConfidenceTracker."""
        from maverick_agents.research.optimization import ConfidenceTracker

        tracker = ConfidenceTracker(
            target_confidence=0.8,
            min_sources=3,
            max_sources=15,
        )
        assert tracker.target_confidence == 0.8
        assert tracker.min_sources == 3
        assert tracker.max_sources == 15

    def test_update_confidence(self):
        """Test updating confidence."""
        from maverick_agents.research.optimization import ConfidenceTracker

        tracker = ConfidenceTracker()
        evidence = {
            "sentiment": {"direction": "bullish", "confidence": 0.7},
            "insights": ["insight1", "insight2"],
            "risk_factors": ["risk1"],
            "opportunities": ["opportunity1"],
            "relevance_score": 0.8,
        }
        result = tracker.update_confidence(evidence, source_credibility=0.8)

        assert "current_confidence" in result
        assert "should_continue" in result
        assert "sources_processed" in result
        assert result["sources_processed"] == 1

    def test_confidence_trend(self):
        """Test confidence trend calculation."""
        from maverick_agents.research.optimization import ConfidenceTracker

        tracker = ConfidenceTracker()
        evidence = {
            "sentiment": {"direction": "bullish", "confidence": 0.7},
        }

        # First update - insufficient data
        result = tracker.update_confidence(evidence, source_credibility=0.8)
        assert result["confidence_trend"] == "insufficient_data"


class TestIntelligentContentFilter:
    """Test IntelligentContentFilter class."""

    def test_create_content_filter(self):
        """Test creating IntelligentContentFilter."""
        from maverick_agents.research.optimization import IntelligentContentFilter

        filter_obj = IntelligentContentFilter()
        assert filter_obj is not None
        assert filter_obj.relevance_keywords is not None
        assert filter_obj.domain_credibility_scores is not None

    def test_relevance_keywords_structure(self):
        """Test that relevance keywords have correct structure."""
        from maverick_agents.research.optimization import IntelligentContentFilter

        filter_obj = IntelligentContentFilter()
        assert "fundamental" in filter_obj.relevance_keywords
        assert "technical" in filter_obj.relevance_keywords
        assert "sentiment" in filter_obj.relevance_keywords
        assert "competitive" in filter_obj.relevance_keywords

        for category in filter_obj.relevance_keywords.values():
            assert "high" in category
            assert "medium" in category
            assert "context" in category

    def test_domain_credibility_scores(self):
        """Test that domain credibility scores are set."""
        from maverick_agents.research.optimization import IntelligentContentFilter

        filter_obj = IntelligentContentFilter()
        assert "reuters.com" in filter_obj.domain_credibility_scores
        assert "bloomberg.com" in filter_obj.domain_credibility_scores
        assert filter_obj.domain_credibility_scores["reuters.com"] == 0.95


class TestOptimizedPromptEngine:
    """Test OptimizedPromptEngine class."""

    def test_create_prompt_engine(self):
        """Test creating OptimizedPromptEngine."""
        from maverick_agents.research.optimization import OptimizedPromptEngine

        engine = OptimizedPromptEngine()
        assert engine is not None
        assert engine.prompt_templates is not None
        assert engine.prompt_cache == {}

    def test_prompt_templates_structure(self):
        """Test that prompt templates have correct structure."""
        from maverick_agents.research.optimization import OptimizedPromptEngine

        engine = OptimizedPromptEngine()
        assert "emergency" in engine.prompt_templates
        assert "fast" in engine.prompt_templates
        assert "standard" in engine.prompt_templates

        for category in engine.prompt_templates.values():
            assert "content_analysis" in category
            assert "synthesis" in category

    def test_get_optimized_prompt_emergency(self):
        """Test getting emergency prompt."""
        from maverick_agents.research.optimization import OptimizedPromptEngine

        engine = OptimizedPromptEngine()
        prompt = engine.get_optimized_prompt(
            prompt_type="content_analysis",
            time_remaining=5.0,
            confidence_level=0.5,
            content="Test content",
            persona="moderate",
            focus_areas="fundamental",
        )
        assert "URGENT" in prompt

    def test_get_optimized_prompt_standard(self):
        """Test getting standard prompt."""
        from maverick_agents.research.optimization import OptimizedPromptEngine

        engine = OptimizedPromptEngine()
        prompt = engine.get_optimized_prompt(
            prompt_type="content_analysis",
            time_remaining=60.0,
            confidence_level=0.5,
            content="Test content",
            persona="moderate",
            focus_areas="fundamental",
        )
        assert "Structured analysis" in prompt

    def test_prompt_caching(self):
        """Test that prompts are cached."""
        from maverick_agents.research.optimization import OptimizedPromptEngine

        engine = OptimizedPromptEngine()
        prompt1 = engine.get_optimized_prompt(
            prompt_type="content_analysis",
            time_remaining=60.0,
            confidence_level=0.5,
            content="Test content",
            persona="moderate",
            focus_areas="fundamental",
        )

        # Cache should have entry now
        assert len(engine.prompt_cache) == 1

        prompt2 = engine.get_optimized_prompt(
            prompt_type="content_analysis",
            time_remaining=60.0,
            confidence_level=0.5,
            content="Test content",
            persona="moderate",
            focus_areas="fundamental",
        )

        # Should return same prompt from cache
        assert prompt1 == prompt2
        assert len(engine.prompt_cache) == 1
