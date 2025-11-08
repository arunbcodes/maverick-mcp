"""
NSE Provider for Conference Call Transcripts.

Single Responsibility: Fetch transcripts from NSE exchange filings.
Open/Closed: Extensible via configuration, not code changes.
Liskov Substitution: Fully implements ConcallProvider interface.
Interface Segregation: Implements only necessary methods.
Dependency Inversion: Depends on ConcallProvider abstraction.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

import httpx
from bs4 import BeautifulSoup

from maverick_mcp.concall.providers.base_provider import ConcallProvider

logger = logging.getLogger(__name__)


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
                logger.info(f"No transcript link found in announcements for {nse_symbol}")
                return None

            # Make absolute URL
            if not transcript_link.startswith("http"):
                from urllib.parse import urljoin

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
                announcements = data.get("data", []) if isinstance(data, dict) else data

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
