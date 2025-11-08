"""
Tests for Conference Call Analysis Router.

Tests cover:
- Tool registration
- Fetch transcript tool
- Summarize transcript tool
- Analyze sentiment tool
- Query transcript tool (RAG)
- Compare quarters tool
- Error handling
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maverick_mcp.api.routers.concall import (
    analyze_sentiment,
    compare_quarters,
    fetch_transcript,
    query_transcript,
    summarize_transcript,
)


class TestFetchTranscriptTool:
    """Test fetch_transcript MCP tool."""

    @patch("maverick_mcp.api.routers.concall.TranscriptFetcher")
    @patch("maverick_mcp.api.routers.concall.asyncio.run")
    def test_fetch_transcript_success(self, mock_asyncio_run, mock_fetcher_class):
        """Test successful transcript fetching."""
        # Mock fetcher
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_transcript = AsyncMock(return_value={
            "ticker": "RELIANCE.NS",
            "quarter": "Q1",
            "fiscal_year": 2025,
            "transcript_text": "Sample transcript",
            "source": "IR_WEBSITE",
            "word_count": 2,
        })
        mock_fetcher_class.return_value = mock_fetcher

        # Mock asyncio.run to execute the async function
        mock_asyncio_run.return_value = {
            "ticker": "RELIANCE.NS",
            "quarter": "Q1",
            "fiscal_year": 2025,
            "transcript_text": "Sample transcript",
            "source": "IR_WEBSITE",
            "word_count": 2,
        }

        result = fetch_transcript(
            ticker="RELIANCE.NS",
            quarter="Q1",
            fiscal_year=2025,
        )

        assert result["ticker"] == "RELIANCE.NS"
        assert result["quarter"] == "Q1"
        assert result["fiscal_year"] == 2025
        assert "transcript_text" in result

    @patch("maverick_mcp.api.routers.concall.TranscriptFetcher")
    def test_fetch_transcript_error(self, mock_fetcher_class):
        """Test error handling in fetch_transcript."""
        # Mock fetcher to raise error
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_transcript = AsyncMock(side_effect=ValueError("No transcript found"))
        mock_fetcher_class.return_value = mock_fetcher

        result = fetch_transcript(
            ticker="INVALID.NS",
            quarter="Q1",
            fiscal_year=2025,
        )

        assert "error" in result
        assert result["ticker"] == "INVALID.NS"


class TestSummarizeTranscriptTool:
    """Test summarize_transcript MCP tool."""

    @patch("maverick_mcp.api.routers.concall.ConcallSummarizer")
    @patch("maverick_mcp.api.routers.concall.asyncio.run")
    @patch("maverick_mcp.api.routers.concall.os.getenv")
    def test_summarize_transcript_success(
        self, mock_getenv, mock_asyncio_run, mock_summarizer_class
    ):
        """Test successful summarization."""
        # Mock environment
        mock_getenv.return_value = "test-api-key"

        # Mock summarizer
        mock_summarizer = MagicMock()
        summary_data = {
            "executive_summary": "Strong quarter with revenue growth",
            "key_metrics": {"revenue": "$10B", "growth": "15%"},
            "sentiment": "positive",
        }
        mock_summarizer.summarize_transcript = AsyncMock(return_value=summary_data)
        mock_summarizer_class.return_value = mock_summarizer

        # Mock asyncio.run
        mock_asyncio_run.return_value = summary_data

        result = summarize_transcript(
            ticker="RELIANCE.NS",
            quarter="Q1",
            fiscal_year=2025,
        )

        assert result["executive_summary"] == "Strong quarter with revenue growth"
        assert "key_metrics" in result

    @patch("maverick_mcp.api.routers.concall.os.getenv")
    def test_summarize_transcript_no_api_key(self, mock_getenv):
        """Test error when API key not configured."""
        mock_getenv.return_value = None

        result = summarize_transcript(
            ticker="RELIANCE.NS",
            quarter="Q1",
            fiscal_year=2025,
        )

        assert "error" in result
        assert "OPENROUTER_API_KEY" in result["error"]

    @patch("maverick_mcp.api.routers.concall.ConcallSummarizer")
    @patch("maverick_mcp.api.routers.concall.os.getenv")
    def test_summarize_transcript_error(self, mock_getenv, mock_summarizer_class):
        """Test error handling in summarization."""
        mock_getenv.return_value = "test-api-key"

        # Mock summarizer to raise error
        mock_summarizer = MagicMock()
        mock_summarizer.summarize_transcript = AsyncMock(
            side_effect=ValueError("No transcript found")
        )
        mock_summarizer_class.return_value = mock_summarizer

        result = summarize_transcript(
            ticker="INVALID.NS",
            quarter="Q1",
            fiscal_year=2025,
        )

        assert "error" in result


class TestAnalyzeSentimentTool:
    """Test analyze_sentiment MCP tool."""

    @patch("maverick_mcp.api.routers.concall.SentimentAnalyzer")
    @patch("maverick_mcp.api.routers.concall.asyncio.run")
    @patch("maverick_mcp.api.routers.concall.os.getenv")
    def test_analyze_sentiment_success(
        self, mock_getenv, mock_asyncio_run, mock_analyzer_class
    ):
        """Test successful sentiment analysis."""
        # Mock environment
        mock_getenv.return_value = "test-api-key"

        # Mock analyzer
        mock_analyzer = MagicMock()
        sentiment_data = {
            "overall_sentiment": "bullish",
            "sentiment_score": 4,
            "confidence_score": 0.85,
            "management_tone": "confident",
        }
        mock_analyzer.analyze_sentiment = AsyncMock(return_value=sentiment_data)
        mock_analyzer_class.return_value = mock_analyzer

        # Mock asyncio.run
        mock_asyncio_run.return_value = sentiment_data

        result = analyze_sentiment(
            ticker="RELIANCE.NS",
            quarter="Q1",
            fiscal_year=2025,
        )

        assert result["overall_sentiment"] == "bullish"
        assert result["sentiment_score"] == 4
        assert result["confidence_score"] == 0.85

    @patch("maverick_mcp.api.routers.concall.os.getenv")
    def test_analyze_sentiment_no_api_key(self, mock_getenv):
        """Test error when API key not configured."""
        mock_getenv.return_value = None

        result = analyze_sentiment(
            ticker="RELIANCE.NS",
            quarter="Q1",
            fiscal_year=2025,
        )

        assert "error" in result
        assert "OPENROUTER_API_KEY" in result["error"]


class TestQueryTranscriptTool:
    """Test query_transcript MCP tool (RAG)."""

    @patch("maverick_mcp.api.routers.concall.ConcallRAGEngine")
    @patch("maverick_mcp.api.routers.concall.asyncio.run")
    @patch("maverick_mcp.api.routers.concall.os.getenv")
    def test_query_transcript_success(
        self, mock_getenv, mock_asyncio_run, mock_rag_class
    ):
        """Test successful RAG query."""
        # Mock environment
        def getenv_side_effect(key):
            if key == "OPENROUTER_API_KEY":
                return "openrouter-key"
            elif key == "OPENAI_API_KEY":
                return "openai-key"
            return None

        mock_getenv.side_effect = getenv_side_effect

        # Mock RAG engine
        mock_rag = MagicMock()
        query_result = {
            "answer": "Revenue grew 15% year-over-year",
            "sources": [
                {"content": "Revenue was $10.5B", "score": 0.85, "chunk_index": 5}
            ],
            "metadata": {"ticker": "RELIANCE.NS", "chunks_retrieved": 1},
        }
        mock_rag.query = AsyncMock(return_value=query_result)
        mock_rag_class.return_value = mock_rag

        # Mock asyncio.run
        mock_asyncio_run.return_value = query_result

        result = query_transcript(
            question="What was the revenue growth?",
            ticker="RELIANCE.NS",
            quarter="Q1",
            fiscal_year=2025,
        )

        assert "Revenue grew" in result["answer"]
        assert len(result["sources"]) > 0

    @patch("maverick_mcp.api.routers.concall.os.getenv")
    def test_query_transcript_no_openrouter_key(self, mock_getenv):
        """Test error when OpenRouter API key not configured."""
        def getenv_side_effect(key):
            if key == "OPENROUTER_API_KEY":
                return None
            elif key == "OPENAI_API_KEY":
                return "openai-key"
            return None

        mock_getenv.side_effect = getenv_side_effect

        result = query_transcript(
            question="What was the revenue?",
            ticker="RELIANCE.NS",
            quarter="Q1",
            fiscal_year=2025,
        )

        assert "error" in result
        assert "OPENROUTER_API_KEY" in result["error"]

    @patch("maverick_mcp.api.routers.concall.os.getenv")
    def test_query_transcript_no_openai_key(self, mock_getenv):
        """Test error when OpenAI API key not configured."""
        def getenv_side_effect(key):
            if key == "OPENROUTER_API_KEY":
                return "openrouter-key"
            elif key == "OPENAI_API_KEY":
                return None
            return None

        mock_getenv.side_effect = getenv_side_effect

        result = query_transcript(
            question="What was the revenue?",
            ticker="RELIANCE.NS",
            quarter="Q1",
            fiscal_year=2025,
        )

        assert "error" in result
        assert "OPENAI_API_KEY" in result["error"]


class TestCompareQuartersTool:
    """Test compare_quarters MCP tool."""

    @patch("maverick_mcp.api.routers.concall.SentimentAnalyzer")
    @patch("maverick_mcp.api.routers.concall.asyncio.run")
    @patch("maverick_mcp.api.routers.concall.os.getenv")
    def test_compare_quarters_success(
        self, mock_getenv, mock_asyncio_run, mock_analyzer_class
    ):
        """Test successful quarter comparison."""
        # Mock environment
        mock_getenv.return_value = "test-api-key"

        # Mock analyzer
        mock_analyzer = MagicMock()
        comparison_result = {
            "ticker": "RELIANCE.NS",
            "quarters_analyzed": 2,
            "sentiment_trend": "improving",
            "score_change": 1,
            "sentiments": [
                {"overall_sentiment": "neutral", "sentiment_score": 3},
                {"overall_sentiment": "bullish", "sentiment_score": 4},
            ],
        }
        mock_analyzer.compare_sentiment = AsyncMock(return_value=comparison_result)
        mock_analyzer_class.return_value = mock_analyzer

        # Mock asyncio.run
        mock_asyncio_run.return_value = comparison_result

        result = compare_quarters(
            ticker="RELIANCE.NS",
            quarters=[("Q4", 2024), ("Q1", 2025)],
        )

        assert result["ticker"] == "RELIANCE.NS"
        assert result["sentiment_trend"] == "improving"
        assert result["quarters_analyzed"] == 2

    @patch("maverick_mcp.api.routers.concall.os.getenv")
    def test_compare_quarters_no_api_key(self, mock_getenv):
        """Test error when API key not configured."""
        mock_getenv.return_value = None

        result = compare_quarters(
            ticker="RELIANCE.NS",
            quarters=[("Q4", 2024), ("Q1", 2025)],
        )

        assert "error" in result
        assert "OPENROUTER_API_KEY" in result["error"]


class TestToolRegistration:
    """Test tool registration with FastMCP."""

    def test_tools_have_proper_names(self):
        """Test that tools have descriptive names."""
        assert fetch_transcript.__name__ == "fetch_transcript"
        assert summarize_transcript.__name__ == "summarize_transcript"
        assert analyze_sentiment.__name__ == "analyze_sentiment"
        assert query_transcript.__name__ == "query_transcript"
        assert compare_quarters.__name__ == "compare_quarters"

    def test_tools_have_docstrings(self):
        """Test that all tools have documentation."""
        assert fetch_transcript.__doc__ is not None
        assert summarize_transcript.__doc__ is not None
        assert analyze_sentiment.__doc__ is not None
        assert query_transcript.__doc__ is not None
        assert compare_quarters.__doc__ is not None

        # Check docstrings contain key information
        assert "Fetch earnings call transcript" in fetch_transcript.__doc__
        assert "AI-powered summary" in summarize_transcript.__doc__
        assert "sentiment" in analyze_sentiment.__doc__.lower()
        assert "RAG" in query_transcript.__doc__
        assert "Compare sentiment" in compare_quarters.__doc__
