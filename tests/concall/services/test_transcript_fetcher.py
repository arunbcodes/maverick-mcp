"""
Tests for TranscriptFetcher service.

Tests cover:
- Service initialization
- Cascading fallback logic
- Database caching
- Provider management
- Cache clearing
- Error handling
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maverick_mcp.concall.models import ConferenceCall
from maverick_mcp.concall.providers import ConcallProvider
from maverick_mcp.concall.services import TranscriptFetcher


class MockProvider(ConcallProvider):
    """Mock provider for testing."""

    def __init__(self, name: str, should_succeed: bool = True):
        self._name = name
        self._should_succeed = should_succeed
        self._available_tickers = {"TEST.NS", "AAPL", "RELIANCE.NS"}

    @property
    def name(self) -> str:
        return self._name

    def is_available(self, ticker: str) -> bool:
        return ticker.upper() in self._available_tickers

    async def fetch_transcript(self, ticker: str, quarter: str, fiscal_year: int):
        if self._should_succeed:
            return {
                "transcript_text": f"Transcript from {self._name}",
                "source_url": f"https://{self._name}.com/transcript.pdf",
                "transcript_format": "pdf",
                "metadata": {},
            }
        return None


class TestTranscriptFetcherInit:
    """Test service initialization."""

    def test_default_initialization(self):
        """Test default fetcher setup."""
        fetcher = TranscriptFetcher()

        assert len(fetcher.providers) == 1  # CompanyIRProvider
        assert fetcher.save_to_db is True
        assert fetcher.use_cache is True

    def test_custom_providers(self):
        """Test with custom provider list."""
        mock_provider = MockProvider("test")
        fetcher = TranscriptFetcher(providers=[mock_provider])

        assert len(fetcher.providers) == 1
        assert fetcher.providers[0].name == "test"

    def test_disable_caching(self):
        """Test disabling cache and save."""
        fetcher = TranscriptFetcher(save_to_db=False, use_cache=False)

        assert fetcher.save_to_db is False
        assert fetcher.use_cache is False


class TestTranscriptFetcherCascadingFallback:
    """Test cascading fallback logic."""

    @pytest.mark.asyncio
    async def test_first_provider_succeeds(self):
        """Test successful fetch from first provider."""
        provider1 = MockProvider("provider1", should_succeed=True)
        provider2 = MockProvider("provider2", should_succeed=True)

        fetcher = TranscriptFetcher(
            providers=[provider1, provider2],
            save_to_db=False,
            use_cache=False,
        )

        result = await fetcher.fetch_transcript("TEST.NS", "Q1", 2025)

        assert result is not None
        assert result["transcript_text"] == "Transcript from provider1"
        assert result["source"] == "provider1"

    @pytest.mark.asyncio
    async def test_fallback_to_second_provider(self):
        """Test fallback when first provider fails."""
        provider1 = MockProvider("provider1", should_succeed=False)
        provider2 = MockProvider("provider2", should_succeed=True)

        fetcher = TranscriptFetcher(
            providers=[provider1, provider2],
            save_to_db=False,
            use_cache=False,
        )

        result = await fetcher.fetch_transcript("TEST.NS", "Q1", 2025)

        assert result is not None
        assert result["transcript_text"] == "Transcript from provider2"
        assert result["source"] == "provider2"

    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Test when all providers fail."""
        provider1 = MockProvider("provider1", should_succeed=False)
        provider2 = MockProvider("provider2", should_succeed=False)

        fetcher = TranscriptFetcher(
            providers=[provider1, provider2],
            save_to_db=False,
            use_cache=False,
        )

        result = await fetcher.fetch_transcript("TEST.NS", "Q1", 2025)

        assert result is None

    @pytest.mark.asyncio
    async def test_skip_unavailable_provider(self):
        """Test skipping providers that don't support ticker."""
        provider1 = MockProvider("provider1", should_succeed=True)
        provider1._available_tickers = {"AAPL"}  # Only supports AAPL

        provider2 = MockProvider("provider2", should_succeed=True)
        provider2._available_tickers = {"TEST.NS"}  # Only supports TEST.NS

        fetcher = TranscriptFetcher(
            providers=[provider1, provider2],
            save_to_db=False,
            use_cache=False,
        )

        result = await fetcher.fetch_transcript("TEST.NS", "Q1", 2025)

        # Should skip provider1, use provider2
        assert result is not None
        assert result["source"] == "provider2"


class TestTranscriptFetcherCaching:
    """Test database caching functionality."""

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.transcript_fetcher.get_session")
    async def test_use_cache(self, mock_get_session):
        """Test fetching from cache."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock cached transcript
        cached_call = ConferenceCall(
            ticker="TEST.NS",
            quarter="Q1",
            fiscal_year=2025,
            source="company_ir",
            source_url="https://test.com/transcript.pdf",
            transcript_text="Cached transcript",
            transcript_format="pdf",
        )
        cached_call.mark_accessed = MagicMock()
        mock_session.query().filter().first.return_value = cached_call

        provider = MockProvider("provider1", should_succeed=True)
        fetcher = TranscriptFetcher(providers=[provider], use_cache=True)

        result = await fetcher.fetch_transcript("TEST.NS", "Q1", 2025)

        assert result is not None
        assert result["transcript_text"] == "Cached transcript"
        assert result["metadata"]["cached"] is True
        # Provider should not be called
        cached_call.mark_accessed.assert_called_once()

    @pytest.mark.asyncio
    @patch("maverick_mcp.concall.services.transcript_fetcher.get_session")
    async def test_force_refresh_skips_cache(self, mock_get_session):
        """Test force_refresh bypasses cache."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Cache has data, but should be skipped
        cached_call = ConferenceCall(
            ticker="TEST.NS",
            quarter="Q1",
            fiscal_year=2025,
            transcript_text="Cached",
        )
        mock_session.query().filter().first.return_value = cached_call

        provider = MockProvider("provider1", should_succeed=True)
        fetcher = TranscriptFetcher(providers=[provider], use_cache=True, save_to_db=False)

        result = await fetcher.fetch_transcript("TEST.NS", "Q1", 2025, force_refresh=True)

        # Should get fresh data from provider, not cache
        assert result is not None
        assert result["transcript_text"] == "Transcript from provider1"


class TestTranscriptFetcherProviderManagement:
    """Test provider management methods."""

    def test_add_provider(self):
        """Test adding a provider."""
        fetcher = TranscriptFetcher(providers=[])
        provider = MockProvider("test")

        fetcher.add_provider(provider)

        assert len(fetcher.providers) == 1
        assert fetcher.providers[0].name == "test"

    def test_add_provider_with_priority(self):
        """Test adding provider at specific priority."""
        provider1 = MockProvider("provider1")
        fetcher = TranscriptFetcher(providers=[provider1])

        provider2 = MockProvider("provider2")
        fetcher.add_provider(provider2, priority=0)

        # provider2 should be first
        assert fetcher.providers[0].name == "provider2"
        assert fetcher.providers[1].name == "provider1"

    def test_get_provider_status(self):
        """Test getting provider status."""
        provider1 = MockProvider("provider1")
        provider2 = MockProvider("provider2")
        fetcher = TranscriptFetcher(providers=[provider1, provider2])

        status = fetcher.get_provider_status()

        assert len(status) == 2
        assert status[0]["priority"] == 0
        assert status[0]["name"] == "provider1"
        assert status[1]["priority"] == 1
        assert status[1]["name"] == "provider2"


class TestTranscriptFetcherUtilityMethods:
    """Test utility methods."""

    @patch("maverick_mcp.concall.services.transcript_fetcher.get_session")
    def test_get_available_transcripts(self, mock_get_session):
        """Test getting list of available transcripts."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock query results
        call1 = ConferenceCall(
            ticker="TEST.NS",
            quarter="Q2",
            fiscal_year=2025,
            transcript_text="Test",
        )
        call2 = ConferenceCall(
            ticker="TEST.NS",
            quarter="Q1",
            fiscal_year=2025,
            transcript_text="Test",
        )
        mock_session.query().filter().order_by().limit().all.return_value = [
            call1,
            call2,
        ]

        fetcher = TranscriptFetcher()
        results = fetcher.get_available_transcripts("TEST.NS")

        assert len(results) == 2
        assert results[0]["quarter"] == "Q2"
        assert results[1]["quarter"] == "Q1"

    @patch("maverick_mcp.concall.services.transcript_fetcher.get_session")
    def test_clear_cache_by_ticker(self, mock_get_session):
        """Test clearing cache for specific ticker."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 5  # 5 records deleted

        fetcher = TranscriptFetcher()
        count = fetcher.clear_cache(ticker="TEST.NS")

        assert count == 5
        mock_query.filter.assert_called()

    @patch("maverick_mcp.concall.services.transcript_fetcher.get_session")
    def test_clear_cache_older_than(self, mock_get_session):
        """Test clearing cache by age."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 3  # 3 records deleted

        fetcher = TranscriptFetcher()
        count = fetcher.clear_cache(older_than_days=90)

        assert count == 3
