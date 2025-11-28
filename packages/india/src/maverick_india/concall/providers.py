"""
Conference Call Data Providers.

Data source providers for fetching transcripts from various sources.

Available Providers:
    - ConcallProvider: Abstract base interface
    - CompanyIRProvider: Fetch from company IR websites
    - NSEProvider: Fetch from NSE exchange filings

Design:
    All providers implement ConcallProvider interface for consistency.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from maverick_india.concall.utils import TranscriptLoaderFactory

if TYPE_CHECKING:
    from maverick_data.models import CompanyIRMapping

logger = logging.getLogger(__name__)


class ConcallProvider(ABC):
    """
    Abstract base class for conference call data providers.

    All providers (IR, NSE, Screener, YouTube) must implement this interface.
    This ensures consistency and allows easy swapping of providers.

    Design: Interface Segregation - minimal interface with only essential methods.
    """

    @abstractmethod
    async def fetch_transcript(
        self, ticker: str, quarter: str, fiscal_year: int
    ) -> dict[str, Any] | None:
        """
        Fetch conference call transcript for given company and quarter.

        Args:
            ticker: Stock symbol (e.g., "RELIANCE.NS", "AAPL")
            quarter: Quarter identifier (e.g., "Q1", "Q2", "Q3", "Q4")
            fiscal_year: Fiscal year (e.g., 2025)

        Returns:
            dict with keys:
                - transcript_text: Full transcript content
                - source_url: URL where transcript was found
                - transcript_format: Format (pdf, html, txt)
                - metadata: Additional info (call_date, etc.)
            None if transcript not found

        Raises:
            Exception: If fetching fails due to network/parsing errors
        """
        pass

    @abstractmethod
    def is_available(self, ticker: str) -> bool:
        """
        Check if this provider supports the given ticker.

        Args:
            ticker: Stock symbol to check

        Returns:
            bool: True if provider can fetch data for this ticker
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get provider name for logging/debugging."""
        pass


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
        session_factory: Any | None = None,
    ):
        """
        Initialize Company IR provider.

        Args:
            timeout: HTTP request timeout in seconds
            max_retries: Number of retry attempts for failed requests
            rate_limit_delay: Delay between requests in seconds
            session_factory: Optional callable returning database session
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self._session_factory = session_factory
        self._mappings_cache: dict[str, CompanyIRMapping] = {}
        self._load_mappings()

    def _load_mappings(self) -> None:
        """Load IR mappings from database into memory cache."""
        if self._session_factory is None:
            self._load_from_seed_file()
            return

        try:
            from maverick_data.models import CompanyIRMapping

            session = self._session_factory()
            mappings = (
                session.query(CompanyIRMapping)
                .filter(CompanyIRMapping.is_active == True)  # noqa: E712
                .all()
            )
            self._mappings_cache = {m.ticker: m for m in mappings}
            logger.info(f"Loaded {len(self._mappings_cache)} IR mappings from database")
        except Exception as e:
            logger.warning(f"Failed to load IR mappings from database: {e}")
            # Fallback to seed file
            self._load_from_seed_file()
        finally:
            if self._session_factory is not None:
                try:
                    session.close()
                except Exception:
                    pass

    def _load_from_seed_file(self) -> None:
        """Fallback: Load mappings from seed JSON file."""
        try:
            # Try multiple possible seed file locations
            possible_paths = [
                Path(__file__).parent / "data" / "company_ir_seed.json",
                Path(__file__).parent.parent / "data" / "company_ir_seed.json",
            ]

            seed_file = None
            for path in possible_paths:
                if path.exists():
                    seed_file = path
                    break

            if seed_file is None:
                logger.warning("No seed file found for IR mappings")
                return

            with open(seed_file) as f:
                data = json.load(f)

            # Create mapping objects without database
            for company in data.get("companies", []):
                # Create a simple mapping dict (not SQLAlchemy model)
                mapping = type(
                    "IRMapping",
                    (),
                    {
                        "ticker": company["ticker"],
                        "company_name": company["company_name"],
                        "ir_base_url": company.get("ir_base_url"),
                        "concall_url_pattern": company.get("concall_url_pattern"),
                        "concall_section_xpath": company.get("concall_section_xpath"),
                        "concall_section_css": company.get("concall_section_css"),
                        "market": company.get("market"),
                        "country": company.get("country"),
                        "is_active": company.get("is_active", True),
                        "notes": company.get("notes"),
                    },
                )()
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

    def get_mapping(self, ticker: str) -> Any | None:
        """
        Get IR mapping for ticker.

        Args:
            ticker: Stock symbol

        Returns:
            Mapping object or None if not found
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

    def _build_concall_url(self, mapping: Any, quarter: str, fiscal_year: int) -> str:
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

    def _parse_transcript_link(self, html: str, mapping: Any) -> str | None:
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
        Fetch actual transcript content (PDF, HTML, or TXT).

        Args:
            url: URL of transcript file

        Returns:
            str: Transcript text content or None

        Algorithm:
            1. Detect format from URL
            2. Use TranscriptLoaderFactory to get appropriate loader
            3. Load and parse transcript
            4. Return cleaned text
        """
        try:
            # Use factory to auto-select and load
            loader_factory = TranscriptLoaderFactory()
            text = loader_factory.load(url)

            logger.info(f"Successfully loaded transcript from: {url}")
            return text

        except Exception as e:
            logger.error(f"Failed to load transcript from {url}: {e}")
            return None

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


class NSEProvider(ConcallProvider):
    """
    Fetch conference call transcripts from NSE exchange filings.

    This is a FALLBACK data source when company IR websites fail.
    NSE requires corporate filings including earnings call transcripts.

    Design Philosophy:
        - Secondary source: Use only when IR provider fails
        - Rate-limited: Respectful scraping with delays
        - User-agent rotation: Avoid detection
        - Robust parsing: Handle various NSE page formats

    Attributes:
        timeout: HTTP request timeout (default 30s)
        max_retries: Number of retry attempts (default 3)
        rate_limit_delay: Delay between requests in seconds (default 3s)
        user_agents: List of user agents for rotation

    Example:
        >>> provider = NSEProvider()
        >>> transcript = await provider.fetch_transcript("RELIANCE", "Q1", 2025)
        >>> if transcript:
        ...     print(transcript["transcript_text"][:100])
    """

    # NSE endpoints
    NSE_BASE_URL = "https://www.nseindia.com"
    NSE_CORPORATE_URL = "https://www.nseindia.com/api/corporates-corporateActions"
    NSE_ANNOUNCEMENTS_URL = "https://www.nseindia.com/api/corporate-announcements"

    # Common user agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101",
    ]

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 3.0,
    ):
        """
        Initialize NSE provider.

        Args:
            timeout: HTTP request timeout in seconds
            max_retries: Number of retry attempts for failed requests
            rate_limit_delay: Delay between requests in seconds
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self._session_cookies: dict[str, str] = {}

    @property
    def name(self) -> str:
        """Provider name."""
        return "nse"

    def is_available(self, ticker: str) -> bool:
        """
        Check if ticker is an NSE-listed stock.

        Args:
            ticker: Stock symbol to check

        Returns:
            bool: True if ticker ends with .NS (NSE symbol)

        Note:
            NSE symbols use .NS suffix (e.g., RELIANCE.NS)
            BSE symbols use .BO suffix (not supported)
        """
        ticker_upper = ticker.upper()
        # Support both RELIANCE.NS and RELIANCE formats
        return ticker_upper.endswith(".NS") or (
            not ticker_upper.endswith(".BO") and len(ticker_upper) <= 20
        )

    def _normalize_ticker(self, ticker: str) -> str:
        """
        Normalize ticker for NSE API.

        Args:
            ticker: Stock symbol (e.g., "RELIANCE.NS" or "RELIANCE")

        Returns:
            str: NSE format symbol (e.g., "RELIANCE")
        """
        # Remove .NS suffix if present
        return ticker.upper().replace(".NS", "").replace(".BO", "")

    def _get_random_user_agent(self) -> str:
        """Get random user agent for rotation."""
        return random.choice(self.USER_AGENTS)

    async def _initialize_session(self) -> None:
        """
        Initialize NSE session by visiting homepage.

        NSE requires valid cookies from homepage before API calls.
        This prevents 401 errors.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.NSE_BASE_URL,
                    headers={
                        "User-Agent": self._get_random_user_agent(),
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                    follow_redirects=True,
                )
                response.raise_for_status()

                # Store cookies for API calls
                self._session_cookies = dict(response.cookies)
                logger.debug("NSE session initialized successfully")

        except Exception as e:
            logger.warning(f"Failed to initialize NSE session: {e}")
            # Continue anyway, some endpoints may work without cookies

    async def fetch_transcript(
        self, ticker: str, quarter: str, fiscal_year: int
    ) -> dict[str, Any] | None:
        """
        Fetch transcript from NSE corporate filings.

        Args:
            ticker: Stock symbol (e.g., "RELIANCE.NS")
            quarter: Quarter (e.g., "Q1", "Q2")
            fiscal_year: Year (e.g., 2025)

        Returns:
            dict with transcript data or None if not found

        Algorithm:
            1. Initialize NSE session (get cookies)
            2. Normalize ticker to NSE format
            3. Search corporate announcements for quarter
            4. Find transcript/earnings call PDFs
            5. Download and parse transcript
            6. Return structured data
        """
        if not self.is_available(ticker):
            logger.warning(f"NSE does not support ticker: {ticker}")
            return None

        # Normalize ticker
        nse_symbol = self._normalize_ticker(ticker)

        try:
            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)

            # Initialize session
            await self._initialize_session()

            # Search for announcements
            announcements = await self._fetch_announcements(
                nse_symbol, quarter, fiscal_year
            )

            if not announcements:
                logger.info(
                    f"No announcements found for {nse_symbol} {quarter} FY{fiscal_year}"
                )
                return None

            # Find transcript links
            transcript_link = self._find_transcript_link(announcements)

            if not transcript_link:
                logger.info(
                    f"No transcript link found in announcements for {nse_symbol}"
                )
                return None

            # Make absolute URL
            if not transcript_link.startswith("http"):
                transcript_link = urljoin(self.NSE_BASE_URL, transcript_link)

            logger.info(f"Found NSE transcript: {transcript_link}")

            # For now, return metadata (actual parsing will use TranscriptLoaderFactory)
            return {
                "transcript_text": f"[NSE TRANSCRIPT LINK]\n{transcript_link}",
                "source_url": transcript_link,
                "transcript_format": self._detect_format(transcript_link),
                "metadata": {
                    "ticker": ticker,
                    "nse_symbol": nse_symbol,
                    "quarter": quarter,
                    "fiscal_year": fiscal_year,
                    "announcement_count": len(announcements),
                },
            }

        except Exception as e:
            logger.error(f"Failed to fetch transcript from NSE for {ticker}: {e}")
            return None

    async def _fetch_announcements(
        self, symbol: str, quarter: str, fiscal_year: int
    ) -> list[dict[str, Any]]:
        """
        Fetch corporate announcements for symbol and period.

        Args:
            symbol: NSE symbol (e.g., "RELIANCE")
            quarter: Quarter string
            fiscal_year: Year

        Returns:
            list of announcement dicts
        """
        try:
            # Build query parameters
            params = {
                "symbol": symbol,
                "index": "equities",
                # NSE API expects date range (approximate quarter dates)
                "from_date": self._get_quarter_start_date(quarter, fiscal_year),
                "to_date": self._get_quarter_end_date(quarter, fiscal_year),
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.NSE_ANNOUNCEMENTS_URL,
                    params=params,
                    headers={
                        "User-Agent": self._get_random_user_agent(),
                        "Accept": "application/json",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Referer": self.NSE_BASE_URL,
                    },
                    cookies=self._session_cookies,
                    follow_redirects=True,
                )

                response.raise_for_status()
                data = response.json()

                # Extract announcements array
                announcements = (
                    data.get("data", []) if isinstance(data, dict) else data
                )

                logger.info(
                    f"Found {len(announcements)} announcements for {symbol} {quarter} FY{fiscal_year}"
                )
                return announcements

        except Exception as e:
            logger.warning(f"Failed to fetch NSE announcements for {symbol}: {e}")
            return []

    def _get_quarter_start_date(self, quarter: str, fiscal_year: int) -> str:
        """
        Get approximate start date for quarter.

        Args:
            quarter: Quarter (Q1, Q2, Q3, Q4)
            fiscal_year: Year

        Returns:
            str: Date in DD-MM-YYYY format
        """
        # Indian fiscal year: Apr 1 - Mar 31
        quarter_map = {
            "Q1": (4, 1),  # Apr 1
            "Q2": (7, 1),  # Jul 1
            "Q3": (10, 1),  # Oct 1
            "Q4": (1, 1),  # Jan 1
        }

        month, day = quarter_map.get(quarter.upper(), (1, 1))

        # Q4 is in next calendar year
        year = fiscal_year if quarter.upper() != "Q4" else fiscal_year + 1

        return f"{day:02d}-{month:02d}-{year}"

    def _get_quarter_end_date(self, quarter: str, fiscal_year: int) -> str:
        """
        Get approximate end date for quarter.

        Args:
            quarter: Quarter (Q1, Q2, Q3, Q4)
            fiscal_year: Year

        Returns:
            str: Date in DD-MM-YYYY format
        """
        # Add 3 months to start date
        quarter_map = {
            "Q1": (6, 30),  # Jun 30
            "Q2": (9, 30),  # Sep 30
            "Q3": (12, 31),  # Dec 31
            "Q4": (3, 31),  # Mar 31
        }

        month, day = quarter_map.get(quarter.upper(), (12, 31))

        # Q4 ends in next calendar year
        year = fiscal_year if quarter.upper() != "Q4" else fiscal_year + 1

        return f"{day:02d}-{month:02d}-{year}"

    def _find_transcript_link(
        self, announcements: list[dict[str, Any]]
    ) -> str | None:
        """
        Find transcript link in announcements.

        Args:
            announcements: List of announcement dicts

        Returns:
            str: Transcript URL or None
        """
        # Keywords indicating earnings call transcript
        transcript_keywords = [
            "earnings call",
            "investor call",
            "conference call",
            "earnings transcript",
            "concall",
            "analyst meet",
        ]

        for announcement in announcements:
            # Check announcement subject/description
            subject = announcement.get("subject", "").lower()
            desc = announcement.get("desc", "").lower()

            # Check if it's a transcript
            is_transcript = any(
                keyword in subject or keyword in desc
                for keyword in transcript_keywords
            )

            if is_transcript:
                # Look for attachment/link
                link = announcement.get("attchmntFile") or announcement.get("an_dt")

                if link:
                    logger.debug(f"Found transcript link: {link}")
                    return link

        return None

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


__all__ = ["ConcallProvider", "CompanyIRProvider", "NSEProvider"]
