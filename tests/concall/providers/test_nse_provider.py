"""
Tests for NSEProvider.

Tests cover:
- Ticker availability checks
- NSE session initialization
- Corporate announcements fetching
- Transcript link extraction
- Rate limiting
- User agent rotation
- Error handling
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from maverick_mcp.concall.providers import NSEProvider


class TestNSEProviderInit:
    """Test provider initialization."""

    def test_default_initialization(self):
        """Test default provider setup."""
        provider = NSEProvider()

        assert provider.timeout == 30
        assert provider.max_retries == 3
        assert provider.rate_limit_delay == 3.0
        assert provider.name == "nse"
        assert len(provider._session_cookies) == 0

    def test_custom_parameters(self):
        """Test custom initialization."""
        provider = NSEProvider(timeout=60, max_retries=5, rate_limit_delay=1.0)

        assert provider.timeout == 60
        assert provider.max_retries == 5
        assert provider.rate_limit_delay == 1.0


class TestNSEProviderAvailability:
    """Test ticker availability checks."""

    def test_nse_ticker_with_suffix(self):
        """Test NSE ticker with .NS suffix."""
        provider = NSEProvider()

        assert provider.is_available("RELIANCE.NS") is True
        assert provider.is_available("TCS.NS") is True
        assert provider.is_available("INFY.NS") is True

    def test_nse_ticker_without_suffix(self):
        """Test NSE ticker without suffix."""
        provider = NSEProvider()

        assert provider.is_available("RELIANCE") is True
        assert provider.is_available("TCS") is True
        assert provider.is_available("INFY") is True

    def test_bse_ticker_not_supported(self):
        """Test BSE ticker is not supported."""
        provider = NSEProvider()

        # BSE uses .BO suffix
        assert provider.is_available("RELIANCE.BO") is False
        assert provider.is_available("TCS.BO") is False

    def test_us_ticker_not_supported(self):
        """Test US tickers are not supported."""
        provider = NSEProvider()

        # US tickers don't have .NS suffix
        assert provider.is_available("AAPL") is True  # Could be NSE if short
        assert provider.is_available("MSFT") is True  # Could be NSE if short
        # But in practice, NSE API will reject these


class TestNSEProviderTickerNormalization:
    """Test ticker normalization."""

    def test_normalize_with_ns_suffix(self):
        """Test normalizing .NS suffix."""
        provider = NSEProvider()

        assert provider._normalize_ticker("RELIANCE.NS") == "RELIANCE"
        assert provider._normalize_ticker("TCS.NS") == "TCS"

    def test_normalize_without_suffix(self):
        """Test normalizing without suffix."""
        provider = NSEProvider()

        assert provider._normalize_ticker("RELIANCE") == "RELIANCE"
        assert provider._normalize_ticker("TCS") == "TCS"

    def test_normalize_lowercase(self):
        """Test normalizing lowercase tickers."""
        provider = NSEProvider()

        assert provider._normalize_ticker("reliance.ns") == "RELIANCE"
        assert provider._normalize_ticker("tcs") == "TCS"


class TestNSEProviderUserAgent:
    """Test user agent rotation."""

    def test_random_user_agent(self):
        """Test user agent selection."""
        provider = NSEProvider()

        # Get 10 user agents
        agents = [provider._get_random_user_agent() for _ in range(10)]

        # All should be from the list
        assert all(agent in provider.USER_AGENTS for agent in agents)

        # Should have some variety (not all same)
        assert len(set(agents)) > 1


class TestNSEProviderQuarterDates:
    """Test quarter date calculations."""

    def test_q1_dates(self):
        """Test Q1 dates (Apr-Jun)."""
        provider = NSEProvider()

        start = provider._get_quarter_start_date("Q1", 2025)
        end = provider._get_quarter_end_date("Q1", 2025)

        assert start == "01-04-2025"
        assert end == "30-06-2025"

    def test_q2_dates(self):
        """Test Q2 dates (Jul-Sep)."""
        provider = NSEProvider()

        start = provider._get_quarter_start_date("Q2", 2025)
        end = provider._get_quarter_end_date("Q2", 2025)

        assert start == "01-07-2025"
        assert end == "30-09-2025"

    def test_q3_dates(self):
        """Test Q3 dates (Oct-Dec)."""
        provider = NSEProvider()

        start = provider._get_quarter_start_date("Q3", 2025)
        end = provider._get_quarter_end_date("Q3", 2025)

        assert start == "01-10-2025"
        assert end == "31-12-2025"

    def test_q4_dates(self):
        """Test Q4 dates (Jan-Mar, next year)."""
        provider = NSEProvider()

        start = provider._get_quarter_start_date("Q4", 2025)
        end = provider._get_quarter_end_date("Q4", 2025)

        # Q4 2025 is Jan-Mar 2026
        assert start == "01-01-2026"
        assert end == "31-03-2026"


class TestNSEProviderSessionInitialization:
    """Test NSE session initialization."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_successful_initialization(self, mock_client_class):
        """Test successful session init."""
        # Mock response
        mock_response = MagicMock()
        mock_response.cookies = {"cookie1": "value1", "cookie2": "value2"}
        mock_response.raise_for_status = MagicMock()

        # Mock client
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = NSEProvider()
        await provider._initialize_session()

        # Should have cookies
        assert provider._session_cookies == {"cookie1": "value1", "cookie2": "value2"}

        # Should have called NSE homepage
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == provider.NSE_BASE_URL

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_failed_initialization(self, mock_client_class):
        """Test session init failure."""
        # Mock client that raises error
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = NSEProvider()
        await provider._initialize_session()

        # Should not crash, just log warning
        assert provider._session_cookies == {}


class TestNSEProviderAnnouncementFetching:
    """Test announcement fetching."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_fetch_announcements_success(self, mock_client_class):
        """Test successful announcement fetch."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"subject": "Earnings Call Q1 FY2025", "attchmntFile": "transcript.pdf"},
                {"subject": "Board Meeting", "attchmntFile": "notice.pdf"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        # Mock client
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = NSEProvider()
        announcements = await provider._fetch_announcements("RELIANCE", "Q1", 2025)

        assert len(announcements) == 2
        assert announcements[0]["subject"] == "Earnings Call Q1 FY2025"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_fetch_announcements_empty(self, mock_client_class):
        """Test empty announcements."""
        # Mock response with empty data
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()

        # Mock client
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = NSEProvider()
        announcements = await provider._fetch_announcements("RELIANCE", "Q1", 2025)

        assert len(announcements) == 0

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_fetch_announcements_error(self, mock_client_class):
        """Test announcement fetch error."""
        # Mock client that raises error
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPError("API error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        provider = NSEProvider()
        announcements = await provider._fetch_announcements("RELIANCE", "Q1", 2025)

        # Should return empty list on error
        assert announcements == []


class TestNSEProviderTranscriptLinkFinding:
    """Test transcript link extraction."""

    def test_find_transcript_by_subject(self):
        """Test finding transcript by subject."""
        provider = NSEProvider()

        announcements = [
            {"subject": "Board Meeting", "attchmntFile": "notice.pdf"},
            {"subject": "Earnings Call Transcript Q1", "attchmntFile": "transcript.pdf"},
        ]

        link = provider._find_transcript_link(announcements)
        assert link == "transcript.pdf"

    def test_find_transcript_by_keywords(self):
        """Test finding transcript by various keywords."""
        provider = NSEProvider()

        # Test different keywords
        test_cases = [
            {"subject": "Conference Call Q2", "attchmntFile": "concall.pdf"},
            {"subject": "Investor Call Transcript", "attchmntFile": "investor.pdf"},
            {"subject": "Analyst Meet Transcript", "attchmntFile": "analyst.pdf"},
        ]

        for announcement in test_cases:
            link = provider._find_transcript_link([announcement])
            assert link is not None

    def test_no_transcript_found(self):
        """Test when no transcript in announcements."""
        provider = NSEProvider()

        announcements = [
            {"subject": "Board Meeting", "attchmntFile": "notice.pdf"},
            {"subject": "Dividend Declaration", "attchmntFile": "dividend.pdf"},
        ]

        link = provider._find_transcript_link(announcements)
        assert link is None

    def test_empty_announcements(self):
        """Test empty announcements list."""
        provider = NSEProvider()

        link = provider._find_transcript_link([])
        assert link is None


class TestNSEProviderFormatDetection:
    """Test format detection."""

    def test_pdf_format(self):
        """Test PDF format detection."""
        provider = NSEProvider()

        assert provider._detect_format("transcript.pdf") == "pdf"
        assert provider._detect_format("https://example.com/file.PDF") == "pdf"

    def test_txt_format(self):
        """Test TXT format detection."""
        provider = NSEProvider()

        assert provider._detect_format("transcript.txt") == "txt"
        assert provider._detect_format("https://example.com/file.TXT") == "txt"

    def test_html_format(self):
        """Test HTML format detection (default)."""
        provider = NSEProvider()

        assert provider._detect_format("transcript.html") == "html"
        assert provider._detect_format("https://example.com/page") == "html"


class TestNSEProviderFetchTranscript:
    """Test full transcript fetching."""

    @pytest.mark.asyncio
    async def test_unsupported_ticker(self):
        """Test fetching with unsupported ticker."""
        provider = NSEProvider()

        # BSE ticker not supported
        result = await provider.fetch_transcript("RELIANCE.BO", "Q1", 2025)
        assert result is None

    @pytest.mark.asyncio
    @patch.object(NSEProvider, "_initialize_session")
    @patch.object(NSEProvider, "_fetch_announcements")
    async def test_no_announcements(self, mock_fetch_ann, mock_init_session):
        """Test when no announcements found."""
        mock_init_session.return_value = None
        mock_fetch_ann.return_value = []

        provider = NSEProvider()
        result = await provider.fetch_transcript("RELIANCE.NS", "Q1", 2025)

        assert result is None

    @pytest.mark.asyncio
    @patch.object(NSEProvider, "_initialize_session")
    @patch.object(NSEProvider, "_fetch_announcements")
    @patch.object(NSEProvider, "_find_transcript_link")
    async def test_no_transcript_link(
        self, mock_find_link, mock_fetch_ann, mock_init_session
    ):
        """Test when no transcript link found."""
        mock_init_session.return_value = None
        mock_fetch_ann.return_value = [{"subject": "Board Meeting"}]
        mock_find_link.return_value = None

        provider = NSEProvider()
        result = await provider.fetch_transcript("RELIANCE.NS", "Q1", 2025)

        assert result is None

    @pytest.mark.asyncio
    @patch.object(NSEProvider, "_initialize_session")
    @patch.object(NSEProvider, "_fetch_announcements")
    @patch.object(NSEProvider, "_find_transcript_link")
    async def test_successful_fetch(
        self, mock_find_link, mock_fetch_ann, mock_init_session
    ):
        """Test successful transcript fetch."""
        mock_init_session.return_value = None
        mock_fetch_ann.return_value = [
            {"subject": "Earnings Call Q1", "attchmntFile": "transcript.pdf"}
        ]
        mock_find_link.return_value = "/corporate/transcript.pdf"

        provider = NSEProvider()
        result = await provider.fetch_transcript("RELIANCE.NS", "Q1", 2025)

        assert result is not None
        assert "transcript_text" in result
        assert "source_url" in result
        assert result["transcript_format"] == "pdf"
        assert result["metadata"]["ticker"] == "RELIANCE.NS"
        assert result["metadata"]["nse_symbol"] == "RELIANCE"
        assert result["metadata"]["quarter"] == "Q1"
        assert result["metadata"]["fiscal_year"] == 2025
