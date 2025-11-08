"""
Tests for SentimentAnalyzer.

Tests cover:
- Analyzer initialization
- Sentiment analysis
- Multi-dimensional scoring
- Tone and confidence analysis
- Caching behavior
- Comparative analysis
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maverick_mcp.concall.models import ConferenceCall
from maverick_mcp.concall.services.sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzerInit:
    """Test analyzer initialization."""

    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    def test_initialization(self, mock_openrouter_class):
        """Test successful initialization."""
        analyzer = SentimentAnalyzer(openrouter_api_key="test-key")

        assert analyzer.openrouter is not None
        assert analyzer.save_to_db is True

    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    def test_initialization_no_save(self, mock_openrouter_class):
        """Test initialization without database saving."""
        analyzer = SentimentAnalyzer(openrouter_api_key="test-key", save_to_db=False)

        assert analyzer.save_to_db is False

    def test_sentiment_scale(self):
        """Test sentiment scale mapping."""
        assert SentimentAnalyzer.SENTIMENT_SCALE["very_bullish"] == 5
        assert SentimentAnalyzer.SENTIMENT_SCALE["bullish"] == 4
        assert SentimentAnalyzer.SENTIMENT_SCALE["neutral"] == 3
        assert SentimentAnalyzer.SENTIMENT_SCALE["bearish"] == 2
        assert SentimentAnalyzer.SENTIMENT_SCALE["very_bearish"] == 1

    def test_tone_categories(self):
        """Test tone categories defined."""
        assert "confident" in SentimentAnalyzer.TONE_CATEGORIES
        assert "cautious" in SentimentAnalyzer.TONE_CATEGORIES
        assert "defensive" in SentimentAnalyzer.TONE_CATEGORIES


class TestSentimentAnalysis:
    """Test sentiment analysis."""

    @pytest.fixture
    def mock_sentiment_response(self):
        """Mock sentiment analysis response."""
        return {
            "overall_sentiment": "bullish",
            "confidence_score": 0.85,
            "management_tone": "confident",
            "outlook_sentiment": "positive",
            "risk_sentiment": "low_risk",
            "key_positive_signals": [
                "Strong revenue growth of 15%",
                "Expanded profit margins",
                "Confident guidance for next quarter",
            ],
            "key_negative_signals": [
                "Supply chain challenges mentioned",
            ],
            "hedge_words_count": 5,
            "certainty_indicators": [
                "We will deliver",
                "Committed to growth",
                "Confident in our strategy",
            ],
            "sentiment_rationale": "Strong financial performance with confident management outlook",
            "tone_rationale": "Management expressed high confidence with minimal hedging",
        }

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    async def test_analyze_sentiment_with_text(
        self, mock_openrouter_class, mock_sentiment_response
    ):
        """Test sentiment analysis with provided text."""
        # Mock LLM
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = MagicMock(return_value=f'```json\n{mock_sentiment_response}\n```')
        mock_llm.ainvoke.return_value = mock_response

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        analyzer = SentimentAnalyzer(openrouter_api_key="test-key", save_to_db=False)

        # Mock JSON parsing to return our response
        with patch("json.loads", return_value=mock_sentiment_response):
            result = await analyzer.analyze_sentiment(
                "TEST.NS",
                "Q1",
                2025,
                transcript_text="Sample transcript text",
                use_cache=False,
            )

        assert result["overall_sentiment"] == "bullish"
        assert result["confidence_score"] == 0.85
        assert result["sentiment_score"] == 4  # bullish = 4
        assert result["ticker"] == "TEST.NS"
        assert result["quarter"] == "Q1"
        assert result["fiscal_year"] == 2025

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    @patch("maverick_mcp.concall.services.sentiment_analyzer.get_session")
    async def test_analyze_sentiment_from_database(
        self, mock_get_session, mock_openrouter_class, mock_sentiment_response
    ):
        """Test sentiment analysis fetches transcript from database."""
        # Mock database
        mock_session = MagicMock()
        mock_call = ConferenceCall(
            ticker="TEST.NS",
            quarter="Q1",
            fiscal_year=2025,
            transcript_text="Database transcript",
        )
        mock_session.query().filter().first.return_value = mock_call
        mock_get_session.return_value = mock_session

        # Mock LLM
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = MagicMock(return_value=f'```json\n{mock_sentiment_response}\n```')
        mock_llm.ainvoke.return_value = mock_response

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        analyzer = SentimentAnalyzer(openrouter_api_key="test-key", save_to_db=False)

        with patch("json.loads", return_value=mock_sentiment_response):
            result = await analyzer.analyze_sentiment("TEST.NS", "Q1", 2025, use_cache=False)

        assert result["overall_sentiment"] == "bullish"

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    async def test_analyze_sentiment_no_transcript(self, mock_openrouter_class):
        """Test error when no transcript available."""
        analyzer = SentimentAnalyzer(openrouter_api_key="test-key", save_to_db=False)

        # Mock _get_transcript_from_db to return None
        with patch.object(analyzer, "_get_transcript_from_db", return_value=None):
            with pytest.raises(ValueError, match="No transcript found"):
                await analyzer.analyze_sentiment("TEST.NS", "Q1", 2025, use_cache=False)


class TestSentimentCaching:
    """Test sentiment caching."""

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    @patch("maverick_mcp.concall.services.sentiment_analyzer.get_session")
    async def test_use_cached_sentiment(self, mock_get_session, mock_openrouter_class):
        """Test uses cached sentiment when available."""
        # Mock database with cached sentiment
        cached_sentiment = {
            "overall_sentiment": "bullish",
            "confidence_score": 0.85,
            "ticker": "TEST.NS",
        }
        mock_session = MagicMock()
        mock_call = ConferenceCall(
            ticker="TEST.NS",
            quarter="Q1",
            fiscal_year=2025,
            sentiment_data=cached_sentiment,
        )
        mock_session.query().filter().first.return_value = mock_call
        mock_get_session.return_value = mock_session

        analyzer = SentimentAnalyzer(openrouter_api_key="test-key")

        result = await analyzer.analyze_sentiment("TEST.NS", "Q1", 2025, use_cache=True)

        assert result == cached_sentiment
        # Should not call LLM if cached
        assert not mock_openrouter_class.called

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    @patch("maverick_mcp.concall.services.sentiment_analyzer.get_session")
    async def test_save_to_database(
        self, mock_get_session, mock_openrouter_class
    ):
        """Test saves sentiment to database."""
        # Mock database
        mock_session = MagicMock()
        mock_call = ConferenceCall(
            ticker="TEST.NS",
            quarter="Q1",
            fiscal_year=2025,
            transcript_text="Sample text",
        )
        mock_session.query().filter().first.return_value = mock_call
        mock_get_session.return_value = mock_session

        # Mock LLM
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        sentiment_data = {"overall_sentiment": "bullish", "confidence_score": 0.85}
        mock_response.content = MagicMock(return_value=f'```json\n{sentiment_data}\n```')
        mock_llm.ainvoke.return_value = mock_response

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        analyzer = SentimentAnalyzer(openrouter_api_key="test-key", save_to_db=True)

        with patch("json.loads", return_value=sentiment_data):
            await analyzer.analyze_sentiment(
                "TEST.NS", "Q1", 2025, transcript_text="Sample", use_cache=False
            )

        # Should have saved to database
        assert mock_call.sentiment_data is not None
        mock_session.commit.assert_called_once()


class TestSentimentScoring:
    """Test sentiment scoring."""

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    async def test_sentiment_score_calculation(self, mock_openrouter_class):
        """Test sentiment converted to numeric score."""
        test_cases = [
            ("very_bullish", 5),
            ("bullish", 4),
            ("neutral", 3),
            ("bearish", 2),
            ("very_bearish", 1),
        ]

        for sentiment, expected_score in test_cases:
            # Mock LLM response
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            sentiment_data = {
                "overall_sentiment": sentiment,
                "confidence_score": 0.8,
            }
            mock_response.content = MagicMock(return_value=f'```json\n{sentiment_data}\n```')
            mock_llm.ainvoke.return_value = mock_response

            mock_openrouter = MagicMock()
            mock_openrouter.get_llm.return_value = mock_llm
            mock_openrouter_class.return_value = mock_openrouter

            analyzer = SentimentAnalyzer(openrouter_api_key="test-key", save_to_db=False)

            with patch("json.loads", return_value=sentiment_data):
                result = await analyzer.analyze_sentiment(
                    "TEST.NS", "Q1", 2025, transcript_text="Sample", use_cache=False
                )

            assert result["sentiment_score"] == expected_score


class TestComparativeSentiment:
    """Test comparative sentiment analysis."""

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    async def test_compare_sentiment(self, mock_openrouter_class):
        """Test sentiment comparison across quarters."""
        analyzer = SentimentAnalyzer(openrouter_api_key="test-key")

        # Mock analyze_sentiment to return different sentiments
        sentiments = [
            {"overall_sentiment": "bearish", "sentiment_score": 2, "confidence_score": 0.8},
            {"overall_sentiment": "neutral", "sentiment_score": 3, "confidence_score": 0.85},
            {"overall_sentiment": "bullish", "sentiment_score": 4, "confidence_score": 0.9},
        ]

        with patch.object(
            analyzer, "analyze_sentiment", side_effect=AsyncMock(side_effect=sentiments)
        ):
            result = await analyzer.compare_sentiment(
                "TEST.NS",
                [("Q4", 2024), ("Q1", 2025), ("Q2", 2025)],
            )

        assert result["ticker"] == "TEST.NS"
        assert result["quarters_analyzed"] == 3
        assert result["sentiment_trend"] == "improving"
        assert result["score_change"] == 2  # 4 - 2

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    async def test_compare_sentiment_declining(self, mock_openrouter_class):
        """Test declining sentiment trend."""
        analyzer = SentimentAnalyzer(openrouter_api_key="test-key")

        sentiments = [
            {"overall_sentiment": "bullish", "sentiment_score": 4, "confidence_score": 0.9},
            {"overall_sentiment": "bearish", "sentiment_score": 2, "confidence_score": 0.8},
        ]

        with patch.object(
            analyzer, "analyze_sentiment", side_effect=AsyncMock(side_effect=sentiments)
        ):
            result = await analyzer.compare_sentiment(
                "TEST.NS",
                [("Q4", 2024), ("Q1", 2025)],
            )

        assert result["sentiment_trend"] == "declining"
        assert result["score_change"] == -2

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    async def test_compare_sentiment_stable(self, mock_openrouter_class):
        """Test stable sentiment trend."""
        analyzer = SentimentAnalyzer(openrouter_api_key="test-key")

        sentiments = [
            {"overall_sentiment": "neutral", "sentiment_score": 3, "confidence_score": 0.85},
            {"overall_sentiment": "neutral", "sentiment_score": 3, "confidence_score": 0.8},
        ]

        with patch.object(
            analyzer, "analyze_sentiment", side_effect=AsyncMock(side_effect=sentiments)
        ):
            result = await analyzer.compare_sentiment(
                "TEST.NS",
                [("Q4", 2024), ("Q1", 2025)],
            )

        assert result["sentiment_trend"] == "stable"
        assert result["score_change"] == 0

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    async def test_compare_sentiment_no_data(self, mock_openrouter_class):
        """Test comparison with no available data."""
        analyzer = SentimentAnalyzer(openrouter_api_key="test-key")

        # Mock analyze_sentiment to raise errors
        with patch.object(
            analyzer, "analyze_sentiment", side_effect=ValueError("No transcript")
        ):
            result = await analyzer.compare_sentiment(
                "TEST.NS",
                [("Q4", 2024), ("Q1", 2025)],
            )

        assert "error" in result
        assert result["ticker"] == "TEST.NS"


class TestPromptBuilding:
    """Test prompt construction."""

    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    def test_build_sentiment_prompt(self, mock_openrouter_class):
        """Test sentiment analysis prompt construction."""
        analyzer = SentimentAnalyzer(openrouter_api_key="test-key")

        prompt = analyzer._build_sentiment_prompt(
            ticker="TEST.NS",
            quarter="Q1",
            fiscal_year=2025,
            transcript_text="Sample transcript for testing",
        )

        assert "TEST.NS" in prompt
        assert "Q1" in prompt
        assert "2025" in prompt
        assert "Sample transcript" in prompt
        assert "overall_sentiment" in prompt
        assert "confidence_score" in prompt
        assert "management_tone" in prompt

    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    def test_build_sentiment_prompt_truncation(self, mock_openrouter_class):
        """Test prompt truncates long transcripts."""
        analyzer = SentimentAnalyzer(openrouter_api_key="test-key")

        long_transcript = "Sample text " * 5000  # Very long text

        prompt = analyzer._build_sentiment_prompt(
            ticker="TEST.NS",
            quarter="Q1",
            fiscal_year=2025,
            transcript_text=long_transcript,
        )

        # Should be truncated
        assert "[Transcript truncated for analysis]" in prompt
        assert len(prompt) < len(long_transcript)


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    async def test_invalid_json_response(self, mock_openrouter_class):
        """Test handles invalid JSON response."""
        # Mock LLM with invalid JSON
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "This is not valid JSON"
        mock_llm.ainvoke.return_value = mock_response

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        analyzer = SentimentAnalyzer(openrouter_api_key="test-key", save_to_db=False)

        with pytest.raises(ValueError, match="Invalid JSON response"):
            await analyzer.analyze_sentiment(
                "TEST.NS", "Q1", 2025, transcript_text="Sample", use_cache=False
            )

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.sentiment_analyzer.OpenRouterProvider")
    async def test_json_in_markdown_blocks(self, mock_openrouter_class):
        """Test extracts JSON from markdown code blocks."""
        # Mock LLM with JSON in markdown
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        sentiment_data = {"overall_sentiment": "bullish", "confidence_score": 0.85}
        mock_response.content = f"```json\n{sentiment_data}\n```"
        mock_llm.ainvoke.return_value = mock_response

        mock_openrouter = MagicMock()
        mock_openrouter.get_llm.return_value = mock_llm
        mock_openrouter_class.return_value = mock_openrouter

        analyzer = SentimentAnalyzer(openrouter_api_key="test-key", save_to_db=False)

        with patch("json.loads", return_value=sentiment_data):
            result = await analyzer.analyze_sentiment(
                "TEST.NS", "Q1", 2025, transcript_text="Sample", use_cache=False
            )

        assert result["overall_sentiment"] == "bullish"
