"""
Tests for CompanyIRProvider.

Tests cover:
- Provider initialization and configuration
- IR mapping loading from database and seed file
- URL building with patterns
- HTML parsing for transcript links
- Rate limiting and retry logic
- Format detection
- Error handling
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maverick_mcp.concall.models import CompanyIRMapping
from maverick_mcp.concall.providers import CompanyIRProvider


class TestCompanyIRProviderInit:
    """Test provider initialization."""

    def test_default_initialization(self):
        """Test provider with default settings."""
        provider = CompanyIRProvider()

        assert provider.timeout == 30
        assert provider.max_retries == 3
        assert provider.rate_limit_delay == 2.0
        assert provider.name == "company_ir"

    def test_custom_initialization(self):
        """Test provider with custom settings."""
        provider = CompanyIRProvider(
            timeout=60, max_retries=5, rate_limit_delay=1.0
        )

        assert provider.timeout == 60
        assert provider.max_retries == 5
        assert provider.rate_limit_delay == 1.0

    @patch("maverick_mcp.concall.providers.company_ir_provider.get_session")
    def test_load_mappings_from_database(self, mock_get_session):
        """Test loading mappings from database."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock query results
        mock_mapping = CompanyIRMapping(
            ticker="TEST.NS",
            company_name="Test Company",
            ir_base_url="https://test.com/ir",
            is_active=True,
        )
        mock_session.query().filter().all.return_value = [mock_mapping]

        provider = CompanyIRProvider()

        assert "TEST.NS" in provider._mappings_cache
        assert provider._mappings_cache["TEST.NS"].company_name == "Test Company"
        mock_session.close.assert_called_once()

    def test_load_mappings_from_seed_file(self):
        """Test loading mappings from seed JSON file."""
        provider = CompanyIRProvider()

        # Should load from seed file (fallback)
        assert len(provider._mappings_cache) > 0
        # Check top 3 companies from seed
        assert "RELIANCE.NS" in provider._mappings_cache
        assert "TCS.NS" in provider._mappings_cache
        assert "WIPRO.NS" in provider._mappings_cache


class TestCompanyIRProviderAvailability:
    """Test provider availability checks."""

    def test_is_available_for_existing_ticker(self):
        """Test availability check for ticker in cache."""
        provider = CompanyIRProvider()

        # Should be available (from seed file)
        assert provider.is_available("RELIANCE.NS") is True
        assert provider.is_available("TCS.NS") is True

    def test_is_available_for_missing_ticker(self):
        """Test availability check for ticker not in cache."""
        provider = CompanyIRProvider()

        assert provider.is_available("NOTEXIST.NS") is False
        assert provider.is_available("FAKE_TICKER") is False

    def test_get_mapping(self):
        """Test getting mapping for ticker."""
        provider = CompanyIRProvider()

        mapping = provider.get_mapping("RELIANCE.NS")
        assert mapping is not None
        assert mapping.ticker == "RELIANCE.NS"
        assert mapping.company_name == "Reliance Industries Limited"

        missing = provider.get_mapping("NOTEXIST.NS")
        assert missing is None


class TestCompanyIRProviderURLBuilding:
    """Test URL building functionality."""

    def test_build_url_with_pattern(self):
        """Test building URL from pattern."""
        provider = CompanyIRProvider()

        mapping = CompanyIRMapping(
            ticker="TEST.NS",
            company_name="Test",
            concall_url_pattern="https://test.com/ir/{year}/Q{quarter}",
        )

        url = provider._build_concall_url(mapping, "Q1", 2025)
        assert url == "https://test.com/ir/2025/Q1"

    def test_build_url_with_quarter_number(self):
        """Test URL building extracts quarter number."""
        provider = CompanyIRProvider()

        mapping = CompanyIRMapping(
            ticker="TEST.NS",
            company_name="Test",
            concall_url_pattern="https://test.com/concalls/{year}/quarter-{quarter}",
        )

        url = provider._build_concall_url(mapping, "Q2", 2024)
        assert url == "https://test.com/concalls/2024/quarter-2"

    def test_build_url_fallback_to_base(self):
        """Test URL building falls back to base URL."""
        provider = CompanyIRProvider()

        mapping = CompanyIRMapping(
            ticker="TEST.NS",
            company_name="Test",
            ir_base_url="https://test.com/ir",
            concall_url_pattern=None,
        )

        url = provider._build_concall_url(mapping, "Q1", 2025)
        assert url == "https://test.com/ir"


class TestCompanyIRProviderHTMLParsing:
    """Test HTML parsing for transcript links."""

    def test_parse_transcript_link_with_css_selector(self):
        """Test parsing transcript link using CSS selector."""
        provider = CompanyIRProvider()

        html = """
        <html>
            <div class="transcripts">
                <a href="/transcripts/q1-2025-transcript.pdf">Q1 2025 Transcript</a>
            </div>
        </html>
        """

        mapping = CompanyIRMapping(
            ticker="TEST.NS",
            company_name="Test",
            concall_section_css=".transcripts a",
        )

        link = provider._parse_transcript_link(html, mapping)
        assert link == "/transcripts/q1-2025-transcript.pdf"

    def test_parse_transcript_link_keyword_search(self):
        """Test parsing using keyword search fallback."""
        provider = CompanyIRProvider()

        html = """
        <html>
            <a href="/files/earnings-call-transcript.pdf">Download Transcript</a>
        </html>
        """

        mapping = CompanyIRMapping(
            ticker="TEST.NS", company_name="Test", concall_section_css=None
        )

        link = provider._parse_transcript_link(html, mapping)
        assert link == "/files/earnings-call-transcript.pdf"

    def test_parse_transcript_link_not_found(self):
        """Test parsing when no transcript link found."""
        provider = CompanyIRProvider()

        html = """
        <html>
            <a href="/about-us">About Us</a>
            <a href="/products">Products</a>
        </html>
        """

        mapping = CompanyIRMapping(
            ticker="TEST.NS", company_name="Test", concall_section_css=None
        )

        link = provider._parse_transcript_link(html, mapping)
        assert link is None


class TestCompanyIRProviderFormatDetection:
    """Test format detection."""

    def test_detect_pdf_format(self):
        """Test detecting PDF format."""
        provider = CompanyIRProvider()

        assert provider._detect_format("https://test.com/transcript.pdf") == "pdf"
        assert provider._detect_format("https://test.com/TRANSCRIPT.PDF") == "pdf"

    def test_detect_txt_format(self):
        """Test detecting TXT format."""
        provider = CompanyIRProvider()

        assert provider._detect_format("https://test.com/transcript.txt") == "txt"

    def test_detect_html_format(self):
        """Test detecting HTML format (default)."""
        provider = CompanyIRProvider()

        assert provider._detect_format("https://test.com/transcript.html") == "html"
        assert provider._detect_format("https://test.com/transcript") == "html"


class TestCompanyIRProviderFetchPage:
    """Test HTTP fetching with retries."""

    @pytest.mark.asyncio
    async def test_fetch_page_success(self):
        """Test successful page fetch."""
        provider = CompanyIRProvider()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.text = "<html>Test content</html>"
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            html = await provider._fetch_page("https://test.com")
            assert html == "<html>Test content</html>"

    @pytest.mark.asyncio
    async def test_fetch_page_404(self):
        """Test handling 404 errors."""
        provider = CompanyIRProvider()

        with patch("httpx.AsyncClient") as mock_client:
            import httpx

            mock_response = MagicMock()
            mock_response.status_code = 404
            error = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=mock_response
            )
            mock_client.return_value.__aenter__.return_value.get.side_effect = error

            html = await provider._fetch_page("https://test.com/notfound")
            assert html is None

    @pytest.mark.asyncio
    async def test_fetch_page_retry_logic(self):
        """Test retry logic on failures."""
        provider = CompanyIRProvider(max_retries=3)

        with patch("httpx.AsyncClient") as mock_client:
            # Fail twice, then succeed
            mock_response = AsyncMock()
            mock_response.text = "<html>Success</html>"
            mock_response.raise_for_status = MagicMock()

            mock_get = mock_client.return_value.__aenter__.return_value.get
            mock_get.side_effect = [
                Exception("Timeout"),
                Exception("Connection error"),
                mock_response,
            ]

            html = await provider._fetch_page("https://test.com")
            assert html == "<html>Success</html>"
            assert mock_get.call_count == 3


class TestCompanyIRProviderIntegration:
    """Integration tests for full fetch workflow."""

    @pytest.mark.asyncio
    async def test_fetch_transcript_ticker_not_available(self):
        """Test fetching for unavailable ticker."""
        provider = CompanyIRProvider()

        result = await provider.fetch_transcript("NOTEXIST.NS", "Q1", 2025)
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_transcript_pdf_placeholder(self):
        """Test fetching PDF transcript (placeholder for now)."""
        provider = CompanyIRProvider()

        # Mock successful page fetch returning PDF link
        with patch.object(provider, "_fetch_page") as mock_fetch:
            mock_fetch.return_value = """
                <html>
                    <a href="https://test.com/transcript.pdf">Q1 2025 Transcript</a>
                </html>
            """

            result = await provider.fetch_transcript("RELIANCE.NS", "Q1", 2025)

            assert result is not None
            assert "transcript_text" in result
            assert "PDF TRANSCRIPT - TO BE PARSED" in result["transcript_text"]
            assert result["source_url"] == "https://test.com/transcript.pdf"
            assert result["transcript_format"] == "pdf"

    def test_reload_mappings(self):
        """Test reloading mappings."""
        provider = CompanyIRProvider()

        initial_count = len(provider._mappings_cache)
        provider.reload_mappings()

        # Should have same or more mappings after reload
        assert len(provider._mappings_cache) >= initial_count
