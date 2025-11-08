"""
Company IR Website Provider.

Single Responsibility: Fetch transcripts from company IR websites.
Open/Closed: Extensible via configuration, not code changes.
Liskov Substitution: Fully implements ConcallProvider interface.
Interface Segregation: Implements only necessary methods.
Dependency Inversion: Depends on ConcallProvider abstraction.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

from maverick_mcp.concall.models import CompanyIRMapping
from maverick_mcp.concall.providers.base_provider import ConcallProvider
from maverick_mcp.data.models import get_session

logger = logging.getLogger(__name__)


class CompanyIRProvider(ConcallProvider):
    """
    Fetch conference call transcripts from company IR websites.

    This is the PRIMARY data source (legal, reliable, official).
    Uses curated CompanyIRMapping database for URL patterns.

    Design Philosophy:
        - Legal-first: No ToS violations
        - Manual curation: Quality over quantity
        - Rate-limited: Respectful of company servers
        - Retry logic: Handles temporary failures

    Attributes:
        timeout: HTTP request timeout (default 30s)
        max_retries: Number of retry attempts (default 3)
        rate_limit_delay: Delay between requests in seconds (default 2s)

    Example:
        >>> provider = CompanyIRProvider()
        >>> transcript = await provider.fetch_transcript("RELIANCE.NS", "Q1", 2025)
        >>> if transcript:
        ...     print(transcript["transcript_text"][:100])
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 2.0,
    ):
        """
        Initialize Company IR provider.

        Args:
            timeout: HTTP request timeout in seconds
            max_retries: Number of retry attempts for failed requests
            rate_limit_delay: Delay between requests in seconds
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self._mappings_cache: dict[str, CompanyIRMapping] = {}
        self._load_mappings()

    def _load_mappings(self) -> None:
        """Load IR mappings from database into memory cache."""
        try:
            session = get_session()
            mappings = (
                session.query(CompanyIRMapping)
                .filter(CompanyIRMapping.is_active == True)
                .all()
            )
            self._mappings_cache = {m.ticker: m for m in mappings}
            logger.info(f"Loaded {len(self._mappings_cache)} IR mappings from database")
        except Exception as e:
            logger.warning(f"Failed to load IR mappings from database: {e}")
            # Fallback to seed file
            self._load_from_seed_file()
        finally:
            session.close()

    def _load_from_seed_file(self) -> None:
        """Fallback: Load mappings from seed JSON file."""
        try:
            seed_file = (
                Path(__file__).parent.parent / "data" / "company_ir_seed.json"
            )
            if not seed_file.exists():
                logger.warning(f"Seed file not found: {seed_file}")
                return

            with open(seed_file) as f:
                data = json.load(f)

            for company in data.get("companies", []):
                mapping = CompanyIRMapping(
                    ticker=company["ticker"],
                    company_name=company["company_name"],
                    ir_base_url=company.get("ir_base_url"),
                    concall_url_pattern=company.get("concall_url_pattern"),
                    concall_section_xpath=company.get("concall_section_xpath"),
                    concall_section_css=company.get("concall_section_css"),
                    market=company.get("market"),
                    country=company.get("country"),
                    is_active=company.get("is_active", True),
                    notes=company.get("notes"),
                )
                self._mappings_cache[mapping.ticker] = mapping

            logger.info(
                f"Loaded {len(self._mappings_cache)} IR mappings from seed file"
            )
        except Exception as e:
            logger.error(f"Failed to load seed file: {e}")

    @property
    def name(self) -> str:
        """Provider name."""
        return "company_ir"

    def is_available(self, ticker: str) -> bool:
        """
        Check if IR mapping exists for ticker.

        Args:
            ticker: Stock symbol to check

        Returns:
            bool: True if mapping exists and is active
        """
        mapping = self._mappings_cache.get(ticker)
        return mapping is not None and mapping.is_active

    def get_mapping(self, ticker: str) -> CompanyIRMapping | None:
        """
        Get IR mapping for ticker.

        Args:
            ticker: Stock symbol

        Returns:
            CompanyIRMapping object or None if not found
        """
        return self._mappings_cache.get(ticker)

    async def fetch_transcript(
        self, ticker: str, quarter: str, fiscal_year: int
    ) -> dict[str, Any] | None:
        """
        Fetch transcript from company IR website.

        Args:
            ticker: Stock symbol (e.g., "RELIANCE.NS")
            quarter: Quarter (e.g., "Q1", "Q2")
            fiscal_year: Year (e.g., 2025)

        Returns:
            dict with transcript data or None if not found

        Algorithm:
            1. Get IR mapping from cache
            2. Build URL using pattern
            3. Fetch page with rate limiting
            4. Parse HTML for transcript links
            5. Download transcript content
            6. Return structured data
        """
        if not self.is_available(ticker):
            logger.warning(f"No IR mapping for {ticker}")
            return None

        mapping = self.get_mapping(ticker)
        if not mapping:
            return None

        try:
            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)

            # Build URL for concall page
            url = self._build_concall_url(mapping, quarter, fiscal_year)
            logger.info(f"Fetching transcript from: {url}")

            # Fetch page
            html = await self._fetch_page(url)
            if not html:
                return None

            # Parse page for transcript links
            transcript_url = self._parse_transcript_link(html, mapping)
            if not transcript_url:
                logger.warning(f"No transcript link found on page: {url}")
                return None

            # Make transcript URL absolute
            if not transcript_url.startswith("http"):
                from urllib.parse import urljoin

                transcript_url = urljoin(url, transcript_url)

            # Fetch transcript content
            transcript_content = await self._fetch_transcript_content(transcript_url)
            if not transcript_content:
                return None

            # Determine format from URL/content
            transcript_format = self._detect_format(transcript_url)

            return {
                "transcript_text": transcript_content,
                "source_url": transcript_url,
                "transcript_format": transcript_format,
                "metadata": {
                    "ticker": ticker,
                    "quarter": quarter,
                    "fiscal_year": fiscal_year,
                    "company_name": mapping.company_name,
                    "ir_base_url": mapping.ir_base_url,
                },
            }

        except Exception as e:
            logger.error(f"Failed to fetch transcript for {ticker}: {e}")
            return None

    def _build_concall_url(
        self, mapping: CompanyIRMapping, quarter: str, fiscal_year: int
    ) -> str:
        """
        Build URL for concall page using pattern.

        Args:
            mapping: IR mapping with URL pattern
            quarter: Quarter string (Q1, Q2, etc.)
            fiscal_year: Year

        Returns:
            str: Complete URL for concall page
        """
        # If pattern has placeholders, replace them
        url = mapping.concall_url_pattern or mapping.ir_base_url or ""

        # Extract quarter number (Q1 -> 1)
        quarter_num = quarter.replace("Q", "")

        # Common replacements
        url = url.replace("{year}", str(fiscal_year))
        url = url.replace("{quarter}", quarter_num)
        url = url.replace("{quarter_full}", quarter)

        return url

    async def _fetch_page(self, url: str) -> str | None:
        """
        Fetch HTML page with retry logic.

        Args:
            url: URL to fetch

        Returns:
            str: HTML content or None if failed
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.get(
                        url,
                        headers={
                            "User-Agent": "MaverickMCP/1.0 (Educational Research)",
                            "Accept": "text/html,application/xhtml+xml",
                        },
                        follow_redirects=True,
                    )
                    response.raise_for_status()
                    return response.text

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        logger.warning(f"Page not found (404): {url}")
                        return None
                    logger.warning(f"HTTP error on attempt {attempt + 1}: {e}")

                except Exception as e:
                    logger.warning(f"Fetch failed on attempt {attempt + 1}: {e}")

                # Wait before retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff

        return None

    def _parse_transcript_link(
        self, html: str, mapping: CompanyIRMapping
    ) -> str | None:
        """
        Parse HTML to find transcript download link.

        Args:
            html: HTML content
            mapping: IR mapping with selectors

        Returns:
            str: Transcript URL or None
        """
        soup = BeautifulSoup(html, "html.parser")

        # Try CSS selector first
        if mapping.concall_section_css:
            try:
                elements = soup.select(mapping.concall_section_css)
                if elements:
                    # Look for PDF or transcript links
                    for elem in elements:
                        href = elem.get("href", "")
                        text = elem.get_text().lower()
                        if "transcript" in text or href.endswith(".pdf"):
                            return href
            except Exception as e:
                logger.debug(f"CSS selector failed: {e}")

        # Try XPath-like search (simplified)
        if mapping.concall_section_xpath:
            try:
                # Find all links with "transcript" in text or href
                links = soup.find_all("a", href=True)
                for link in links:
                    href = link.get("href", "")
                    text = link.get_text().lower()
                    if "transcript" in text or "transcript" in href.lower():
                        return href
            except Exception as e:
                logger.debug(f"XPath search failed: {e}")

        # Fallback: Look for any PDF link containing "transcript"
        links = soup.find_all("a", href=True)
        for link in links:
            href = link.get("href", "")
            if "transcript" in href.lower() and href.endswith(".pdf"):
                return href

        return None

    async def _fetch_transcript_content(self, url: str) -> str | None:
        """
        Fetch actual transcript content (PDF or HTML).

        Args:
            url: URL of transcript file

        Returns:
            str: Transcript text content or None

        Note:
            PDF parsing will be implemented in utils/transcript_loader.py
            For now, returns placeholder for PDF files.
        """
        if url.endswith(".pdf"):
            # TODO: Implement PDF parsing in Commit 3
            logger.info(f"PDF transcript found: {url}")
            return f"[PDF TRANSCRIPT - TO BE PARSED]\nURL: {url}\nImplement PDF parser in Commit 3"

        # For HTML transcripts
        html = await self._fetch_page(url)
        if not html:
            return None

        # Extract text from HTML
        soup = BeautifulSoup(html, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        return text

    def _detect_format(self, url: str) -> str:
        """
        Detect transcript format from URL.

        Args:
            url: Transcript URL

        Returns:
            str: Format (pdf, html, txt)
        """
        url_lower = url.lower()
        if url_lower.endswith(".pdf"):
            return "pdf"
        elif url_lower.endswith(".txt"):
            return "txt"
        else:
            return "html"

    def reload_mappings(self) -> None:
        """Reload IR mappings from database (for testing/updates)."""
        self._mappings_cache.clear()
        self._load_mappings()
