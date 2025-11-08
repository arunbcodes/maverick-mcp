"""
Transcript Loader Utilities.

Single Responsibility: Parse and extract text from various transcript formats.
Open/Closed: Extensible for new formats without modifying existing code.
"""

from __future__ import annotations

import logging
import re
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class TranscriptLoader(ABC):
    """
    Abstract base class for transcript loaders.

    All format-specific loaders (PDF, HTML, TXT) implement this interface.
    Design: Open/Closed Principle - extend via subclasses, don't modify.
    """

    @abstractmethod
    def load(self, source: str | Path) -> str:
        """
        Load and parse transcript from source.

        Args:
            source: File path or URL to transcript

        Returns:
            str: Cleaned transcript text

        Raises:
            Exception: If loading/parsing fails
        """
        pass

    @abstractmethod
    def supports(self, source: str | Path) -> bool:
        """
        Check if loader supports this source format.

        Args:
            source: File path or URL to check

        Returns:
            bool: True if this loader can handle the source
        """
        pass


class PDFTranscriptLoader(TranscriptLoader):
    """
    Load transcripts from PDF files using LangChain.

    Uses PyPDF for extraction with fallback to pdfplumber if available.
    Handles both local files and URLs.

    Example:
        >>> loader = PDFTranscriptLoader()
        >>> text = loader.load("transcript.pdf")
        >>> print(text[:100])
    """

    def supports(self, source: str | Path) -> bool:
        """Check if source is a PDF."""
        source_str = str(source).lower()
        return source_str.endswith(".pdf") or "pdf" in source_str

    def load(self, source: str | Path) -> str:
        """
        Load PDF transcript.

        Args:
            source: File path or URL to PDF

        Returns:
            str: Extracted and cleaned text

        Algorithm:
            1. Download PDF if URL
            2. Load with LangChain PyPDFLoader
            3. Extract text from all pages
            4. Clean and normalize text
            5. Return combined result
        """
        try:
            # Handle URL vs local file
            if str(source).startswith("http"):
                pdf_path = self._download_pdf(str(source))
            else:
                pdf_path = Path(source)

            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            # Load PDF with LangChain
            text = self._extract_text_langchain(pdf_path)

            # Clean up downloaded file if it was a URL
            if str(source).startswith("http"):
                pdf_path.unlink()

            # Clean and normalize text
            cleaned = self._clean_text(text)
            return cleaned

        except Exception as e:
            logger.error(f"Failed to load PDF {source}: {e}")
            raise

    def _download_pdf(self, url: str) -> Path:
        """
        Download PDF from URL to temp file.

        Args:
            url: PDF URL

        Returns:
            Path: Path to downloaded temp file
        """
        try:
            with httpx.Client(timeout=60) as client:
                response = client.get(
                    url,
                    headers={"User-Agent": "MaverickMCP/1.0"},
                    follow_redirects=True,
                )
                response.raise_for_status()

                # Create temp file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                )
                temp_file.write(response.content)
                temp_file.close()

                return Path(temp_file.name)

        except Exception as e:
            logger.error(f"Failed to download PDF from {url}: {e}")
            raise

    def _extract_text_langchain(self, pdf_path: Path) -> str:
        """
        Extract text using LangChain PyPDFLoader.

        Args:
            pdf_path: Path to PDF file

        Returns:
            str: Extracted text
        """
        try:
            from langchain_community.document_loaders import PyPDFLoader

            loader = PyPDFLoader(str(pdf_path))
            pages = loader.load()

            # Combine all pages
            text = "\n\n".join(page.page_content for page in pages)
            return text

        except ImportError:
            logger.warning("langchain_community not available, using fallback")
            return self._extract_text_pypdf(pdf_path)

    def _extract_text_pypdf(self, pdf_path: Path) -> str:
        """
        Fallback: Extract text using PyPDF2 directly.

        Args:
            pdf_path: Path to PDF file

        Returns:
            str: Extracted text
        """
        try:
            import pypdf

            text_parts = []
            with open(pdf_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())

            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"PyPDF extraction failed: {e}")
            raise

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.

        Args:
            text: Raw extracted text

        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove page numbers (common pattern: "Page X of Y")
        text = re.sub(r"Page \d+ of \d+", "", text, flags=re.IGNORECASE)

        # Remove extra blank lines
        text = re.sub(r"\n\s*\n", "\n\n", text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text


class HTMLTranscriptLoader(TranscriptLoader):
    """
    Load transcripts from HTML pages.

    Uses BeautifulSoup for parsing and text extraction.
    Removes scripts, styles, and navigation elements.

    Example:
        >>> loader = HTMLTranscriptLoader()
        >>> text = loader.load("https://example.com/transcript.html")
    """

    def supports(self, source: str | Path) -> bool:
        """Check if source is HTML."""
        source_str = str(source).lower()
        return (
            source_str.endswith((".html", ".htm"))
            or source_str.startswith("http")
            or "<html" in source_str
        )

    def load(self, source: str | Path) -> str:
        """
        Load HTML transcript.

        Args:
            source: File path, URL, or HTML string

        Returns:
            str: Extracted and cleaned text
        """
        try:
            # Get HTML content
            if str(source).startswith("http"):
                html = self._fetch_html(str(source))
            elif Path(source).exists():
                html = Path(source).read_text()
            else:
                # Assume it's HTML string
                html = str(source)

            # Extract text
            text = self._extract_text(html)

            # Clean and normalize
            cleaned = self._clean_text(text)
            return cleaned

        except Exception as e:
            logger.error(f"Failed to load HTML {source}: {e}")
            raise

    def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML from URL.

        Args:
            url: HTML page URL

        Returns:
            str: HTML content
        """
        with httpx.Client(timeout=30) as client:
            response = client.get(
                url,
                headers={
                    "User-Agent": "MaverickMCP/1.0",
                    "Accept": "text/html",
                },
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.text

    def _extract_text(self, html: str) -> str:
        """
        Extract text from HTML using BeautifulSoup.

        Args:
            html: HTML content

        Returns:
            str: Extracted text
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()

        # Get text
        text = soup.get_text()
        return text

    def _clean_text(self, text: str) -> str:
        """Clean extracted HTML text."""
        # Remove excessive whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        return text


class TextTranscriptLoader(TranscriptLoader):
    """
    Load transcripts from plain text files.

    Simplest loader - minimal processing required.

    Example:
        >>> loader = TextTranscriptLoader()
        >>> text = loader.load("transcript.txt")
    """

    def supports(self, source: str | Path) -> bool:
        """Check if source is plain text."""
        source_str = str(source).lower()
        return source_str.endswith(".txt")

    def load(self, source: str | Path) -> str:
        """
        Load text transcript.

        Args:
            source: File path or URL to text file

        Returns:
            str: Cleaned text
        """
        try:
            # Get text content
            if str(source).startswith("http"):
                text = self._fetch_text(str(source))
            else:
                text = Path(source).read_text()

            # Basic cleaning
            cleaned = self._clean_text(text)
            return cleaned

        except Exception as e:
            logger.error(f"Failed to load text {source}: {e}")
            raise

    def _fetch_text(self, url: str) -> str:
        """Fetch text from URL."""
        with httpx.Client(timeout=30) as client:
            response = client.get(
                url,
                headers={"User-Agent": "MaverickMCP/1.0"},
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.text

    def _clean_text(self, text: str) -> str:
        """Basic text cleaning."""
        # Remove excessive blank lines
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()


class TranscriptLoaderFactory:
    """
    Factory for creating appropriate transcript loaders.

    Design: Factory Pattern for easy loader selection.

    Example:
        >>> factory = TranscriptLoaderFactory()
        >>> loader = factory.get_loader("transcript.pdf")
        >>> text = loader.load("transcript.pdf")
    """

    def __init__(self):
        """Initialize factory with available loaders."""
        self._loaders = [
            PDFTranscriptLoader(),
            HTMLTranscriptLoader(),
            TextTranscriptLoader(),
        ]

    def get_loader(self, source: str | Path) -> TranscriptLoader:
        """
        Get appropriate loader for source.

        Args:
            source: File path or URL

        Returns:
            TranscriptLoader: Loader that supports the source

        Raises:
            ValueError: If no loader supports the source
        """
        for loader in self._loaders:
            if loader.supports(source):
                return loader

        raise ValueError(f"No loader supports source: {source}")

    def load(self, source: str | Path) -> str:
        """
        Convenience method: Auto-select loader and load transcript.

        Args:
            source: File path or URL

        Returns:
            str: Extracted and cleaned transcript text
        """
        loader = self.get_loader(source)
        return loader.load(source)
