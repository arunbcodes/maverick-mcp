"""
Tests for ConcallSummarizer service.

Tests cover:
- Service initialization
- Transcript summarization
- Sentiment analysis
- Database caching
- OpenRouter integration
- Error handling
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maverick_mcp.concall.models import ConferenceCall
from maverick_mcp.concall.services.concall_summarizer import ConcallSummarizer


class TestConcallSummarizerInit:
    """Test service initialization."""

    def test_initialization_with_api_key(self):
        """Test initialization with explicit API key."""
        summarizer = ConcallSummarizer(api_key="test-key")

        assert summarizer.openrouter is not None
        assert summarizer.save_to_db is True
        assert summarizer.use_cache is True

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "env-key"})
    def test_initialization_from_env(self):
        """Test initialization from environment variable."""
        summarizer = ConcallSummarizer()

        assert summarizer.openrouter is not None

    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="OpenRouter API key required"):
                ConcallSummarizer()

    def test_custom_configuration(self):
        """Test custom configuration."""
        summarizer = ConcallSummarizer(
            api_key="test-key", save_to_db=False, use_cache=False
        )

        assert summarizer.save_to_db is False
        assert summarizer.use_cache is False


class TestConcallSummarizerSummarization:
    """Test transcript summarization."""

    @pytest.fixture
    def mock_summary(self):
        """Mock summary response."""
        return {
            "executive_summary": "Strong quarter with 15% revenue growth.",
            "key_metrics": {
                "revenue": "$10.5B, up 15% YoY",
                "profit": "$2.1B, up 20% YoY",
                "margins": "Operating margin 35%",
                "growth_rates": "15% YoY revenue growth",
                "guidance": "Q2 revenue $11-11.5B",
            },
            "business_highlights": [
                "New product launch successful",
                "Expanded to 3 new markets",
                "Customer base grew 25%",
            ],
            "management_guidance": {
                "revenue_guidance": "$11-11.5B for Q2",
                "earnings_guidance": "$2.2-2.4B for Q2",
                "strategic_initiatives": "AI investments continue",
                "market_outlook": "Positive near-term outlook",
            },
            "sentiment": "positive",
            "sentiment_explanation": "Strong results with beat on all metrics",
            "key_risks": ["Supply chain", "Currency headwinds"],
            "opportunities": ["AI adoption", "Market expansion"],
            "qa_insights": {
                "most_discussed": ["AI strategy", "Margin expansion"],
                "surprises": "Faster than expected AI adoption",
                "confidence_level": "high",
            },
            "market_context": {
                "competitive_landscape": "Gaining market share",
                "industry_trends": "AI driving growth",
                "macroeconomic_factors": "Stable environment",
                "regulatory_environment": "No major changes",
            },
            "analyst_focus": ["AI monetization", "Margin sustainability"],
        }

    @pytest.mark.asyncio
    @patch.object(ConcallSummarizer, "_get_from_cache")
    @patch.object(ConcallSummarizer, "_save_to_db")
    async def test_summarize_with_cache(
        self, mock_save, mock_get_cache, mock_summary
    ):
        """Test summarization returns cached result."""
        mock_get_cache.return_value = mock_summary

        summarizer = ConcallSummarizer(api_key="test-key")
        result = await summarizer.summarize_transcript(
            "TEST.NS", "Q1", 2025, "Sample transcript"
        )

        assert result == mock_summary
        mock_get_cache.assert_called_once()
        mock_save.assert_not_called()

    @pytest.mark.asyncio
    @patch.object(ConcallSummarizer, "_get_from_cache")
    @patch.object(ConcallSummarizer, "_save_to_db")
    @patch("maverick_mcp.concall.services.concall_summarizer.OpenRouterProvider")
    async def test_summarize_without_cache(
        self, mock_openrouter_class, mock_save, mock_get_cache, mock_summary
    ):
        """Test summarization generates new summary."""
        mock_get_cache.return_value = None

        # Mock LLM response
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps(mock_summary)
        mock_llm.ainvoke.return_value = mock_response
        mock_llm.model_name = "test-model"

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        summarizer = ConcallSummarizer(api_key="test-key")
        result = await summarizer.summarize_transcript(
            "TEST.NS", "Q1", 2025, "Sample transcript", company_name="Test Company"
        )

        assert result is not None
        assert result["executive_summary"] == mock_summary["executive_summary"]
        assert result["sentiment"] == "positive"
        assert "_metadata" in result
        mock_save.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(ConcallSummarizer, "_get_from_cache")
    @patch("maverick_mcp.concall.services.concall_summarizer.OpenRouterProvider")
    async def test_summarize_with_markdown_json(
        self, mock_openrouter_class, mock_get_cache, mock_summary
    ):
        """Test summarization handles markdown-wrapped JSON."""
        mock_get_cache.return_value = None

        # Mock LLM response with markdown
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = f"```json\n{json.dumps(mock_summary)}\n```"
        mock_llm.ainvoke.return_value = mock_response
        mock_llm.model_name = "test-model"

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        summarizer = ConcallSummarizer(api_key="test-key", save_to_db=False)
        result = await summarizer.summarize_transcript(
            "TEST.NS", "Q1", 2025, "Sample transcript"
        )

        assert result is not None
        assert result["sentiment"] == "positive"

    @pytest.mark.asyncio
    @patch.object(ConcallSummarizer, "_get_from_cache")
    @patch("maverick_mcp.concall.services.concall_summarizer.OpenRouterProvider")
    async def test_summarize_modes(
        self, mock_openrouter_class, mock_get_cache, mock_summary
    ):
        """Test different summarization modes."""
        mock_get_cache.return_value = None

        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps(mock_summary)
        mock_llm.ainvoke.return_value = mock_response
        mock_llm.model_name = "test-model"

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        summarizer = ConcallSummarizer(api_key="test-key", save_to_db=False)

        # Test different modes
        for mode in ["concise", "standard", "detailed"]:
            result = await summarizer.summarize_transcript(
                "TEST.NS", "Q1", 2025, "Sample transcript", mode=mode
            )
            assert result is not None
            assert result["_metadata"]["mode"] == mode

    @pytest.mark.asyncio
    @patch.object(ConcallSummarizer, "_get_from_cache")
    @patch("maverick_mcp.concall.services.concall_summarizer.OpenRouterProvider")
    async def test_summarize_force_refresh(
        self, mock_openrouter_class, mock_get_cache, mock_summary
    ):
        """Test force refresh bypasses cache."""
        mock_get_cache.return_value = {"cached": "data"}

        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps(mock_summary)
        mock_llm.ainvoke.return_value = mock_response
        mock_llm.model_name = "test-model"

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        summarizer = ConcallSummarizer(api_key="test-key", save_to_db=False)
        result = await summarizer.summarize_transcript(
            "TEST.NS", "Q1", 2025, "Sample transcript", force_refresh=True
        )

        # Should not return cached data
        assert result != {"cached": "data"}
        assert result["sentiment"] == "positive"

    @pytest.mark.asyncio
    @patch.object(ConcallSummarizer, "_get_from_cache")
    @patch("maverick_mcp.concall.services.concall_summarizer.OpenRouterProvider")
    async def test_summarize_llm_error(self, mock_openrouter_class, mock_get_cache):
        """Test summarization handles LLM errors gracefully."""
        mock_get_cache.return_value = None

        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("LLM API error")

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        summarizer = ConcallSummarizer(api_key="test-key")
        result = await summarizer.summarize_transcript(
            "TEST.NS", "Q1", 2025, "Sample transcript"
        )

        assert result is None


class TestConcallSummarizerSentiment:
    """Test sentiment analysis."""

    @pytest.fixture
    def mock_sentiment(self):
        """Mock sentiment response."""
        return {
            "sentiment": "positive",
            "confidence_score": 0.85,
            "explanation": "Strong results with positive outlook",
            "key_positive_signals": ["Revenue beat", "Guidance raise"],
            "key_negative_signals": ["Margin pressure"],
            "management_confidence": "high",
            "analyst_sentiment": "positive",
        }

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_summarizer.OpenRouterProvider")
    async def test_analyze_sentiment(self, mock_openrouter_class, mock_sentiment):
        """Test sentiment analysis."""
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps(mock_sentiment)
        mock_llm.ainvoke.return_value = mock_response

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        summarizer = ConcallSummarizer(api_key="test-key")
        result = await summarizer.analyze_sentiment("Sample transcript")

        assert result is not None
        assert result["sentiment"] == "positive"
        assert result["confidence_score"] == 0.85
        assert len(result["key_positive_signals"]) == 2

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_summarizer.OpenRouterProvider")
    async def test_analyze_sentiment_with_markdown(
        self, mock_openrouter_class, mock_sentiment
    ):
        """Test sentiment analysis with markdown-wrapped JSON."""
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = f"```json\n{json.dumps(mock_sentiment)}\n```"
        mock_llm.ainvoke.return_value = mock_response

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        summarizer = ConcallSummarizer(api_key="test-key")
        result = await summarizer.analyze_sentiment("Sample transcript")

        assert result is not None
        assert result["sentiment"] == "positive"

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_summarizer.OpenRouterProvider")
    async def test_analyze_sentiment_error(self, mock_openrouter_class):
        """Test sentiment analysis handles errors."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("API error")

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        summarizer = ConcallSummarizer(api_key="test-key")
        result = await summarizer.analyze_sentiment("Sample transcript")

        assert result is None


class TestConcallSummarizerCaching:
    """Test database caching."""

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_summarizer.get_session")
    def test_get_from_cache(self, mock_get_session):
        """Test retrieving summary from cache."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock cached call
        cached_call = ConferenceCall(
            ticker="TEST.NS",
            quarter="Q1",
            fiscal_year=2025,
            summary={"executive_summary": "Cached summary"},
        )
        cached_call.mark_accessed = MagicMock()
        mock_session.query().filter().first.return_value = cached_call

        summarizer = ConcallSummarizer(api_key="test-key")
        result = summarizer._get_from_cache("TEST.NS", "Q1", 2025)

        assert result is not None
        assert result["executive_summary"] == "Cached summary"
        cached_call.mark_accessed.assert_called_once()

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_summarizer.get_session")
    def test_get_from_cache_miss(self, mock_get_session):
        """Test cache miss."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query().filter().first.return_value = None

        summarizer = ConcallSummarizer(api_key="test-key")
        result = summarizer._get_from_cache("TEST.NS", "Q1", 2025")

        assert result is None

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_summarizer.get_session")
    def test_save_to_db_update(self, mock_get_session):
        """Test saving summary updates existing record."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock existing call
        existing_call = ConferenceCall(
            ticker="TEST.NS", quarter="Q1", fiscal_year=2025
        )
        mock_session.query().filter().first.return_value = existing_call

        summarizer = ConcallSummarizer(api_key="test-key")
        summary = {"executive_summary": "New summary", "sentiment": "positive"}
        summarizer._save_to_db("TEST.NS", "Q1", 2025, summary)

        assert existing_call.summary == summary
        assert existing_call.sentiment == "positive"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_summarizer.get_session")
    def test_save_to_db_create(self, mock_get_session):
        """Test saving summary creates new record."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query().filter().first.return_value = None

        summarizer = ConcallSummarizer(api_key="test-key")
        summary = {"executive_summary": "New summary", "sentiment": "positive"}
        summarizer._save_to_db("TEST.NS", "Q1", 2025, summary)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestConcallSummarizerStatistics:
    """Test statistics methods."""

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.concall_summarizer.get_session")
    def test_get_summary_statistics(self, mock_get_session):
        """Test getting summary statistics."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock counts
        mock_session.query().filter().count.side_effect = [
            10,  # total
            3,  # very_positive
            5,  # positive
            2,  # neutral
            0,  # cautious
            0,  # negative
        ]

        summarizer = ConcallSummarizer(api_key="test-key")
        stats = summarizer.get_summary_statistics()

        assert stats["total_summaries"] == 10
        assert stats["by_sentiment"]["very_positive"] == 3
        assert stats["by_sentiment"]["positive"] == 5
        assert stats["by_sentiment"]["neutral"] == 2
        assert "cautious" not in stats["by_sentiment"]  # Zero count excluded
