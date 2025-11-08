"""
Tests for Transcript Loaders.

Tests cover:
- Loader factory pattern
- PDF loading with LangChain
- HTML text extraction
- Text file loading
- Format detection
- Error handling
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from maverick_mcp.concall.utils import (
    HTMLTranscriptLoader,
    PDFTranscriptLoader,
    TextTranscriptLoader,
    TranscriptLoaderFactory,
)


class TestPDFTranscriptLoader:
    """Test PDF transcript loading."""

    def test_supports_pdf(self):
        """Test PDF format detection."""
        loader = PDFTranscriptLoader()

        assert loader.supports("transcript.pdf") is True
        assert loader.supports("TRANSCRIPT.PDF") is True
        assert loader.supports("https://example.com/file.pdf") is True
        assert loader.supports("transcript.html") is False
        assert loader.supports("transcript.txt") is False

    @patch("maverick_mcp.concall.utils.transcript_loader.PyPDFLoader")
    def test_extract_text_langchain(self, mock_loader_class):
        """Test text extraction using LangChain."""
        # Mock LangChain loader
        mock_page1 = MagicMock()
        mock_page1.page_content = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.page_content = "Page 2 content"

        mock_loader = MagicMock()
        mock_loader.load.return_value = [mock_page1, mock_page2]
        mock_loader_class.return_value = mock_loader

        loader = PDFTranscriptLoader()

        # Create temp PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = Path(f.name)
            f.write(b"dummy pdf content")

        try:
            # Mock the extraction
            text = loader._extract_text_langchain(temp_path)
            assert "Page 1 content" in text
            assert "Page 2 content" in text
        finally:
            temp_path.unlink()

    def test_clean_text(self):
        """Test text cleaning."""
        loader = PDFTranscriptLoader()

        dirty_text = """
        Page 1 of 10
        Some    text   with    spaces


        And extra blank lines

        Page 2 of 10
        More content
        """

        cleaned = loader._clean_text(dirty_text)

        assert "Page 1 of 10" not in cleaned
        assert "Page 2 of 10" not in cleaned
        assert "Some text with spaces" in cleaned
        assert cleaned.count("\n\n") <= 2  # Max double newlines


class TestHTMLTranscriptLoader:
    """Test HTML transcript loading."""

    def test_supports_html(self):
        """Test HTML format detection."""
        loader = HTMLTranscriptLoader()

        assert loader.supports("transcript.html") is True
        assert loader.supports("transcript.htm") is True
        assert loader.supports("https://example.com/page.html") is True
        assert loader.supports("https://example.com/transcript") is True
        assert loader.supports("<html><body>content</body></html>") is True
        assert loader.supports("transcript.pdf") is False

    def test_extract_text_from_html(self):
        """Test HTML text extraction."""
        loader = HTMLTranscriptLoader()

        html = """
        <html>
            <head><title>Transcript</title></head>
            <body>
                <nav>Navigation menu</nav>
                <script>alert('test');</script>
                <style>.class { color: red; }</style>
                <div class="content">
                    <h1>Q1 2025 Earnings Call</h1>
                    <p>Good morning, everyone.</p>
                    <p>Our revenue grew 25%.</p>
                </div>
                <footer>Copyright 2025</footer>
            </body>
        </html>
        """

        text = loader._extract_text(html)

        # Should include main content
        assert "Q1 2025 Earnings Call" in text
        assert "Good morning" in text
        assert "revenue grew 25%" in text

        # Should exclude removed elements
        assert "Navigation menu" not in text
        assert "alert('test')" not in text
        assert ".class { color: red; }" not in text
        assert "Copyright 2025" not in text

    def test_clean_text(self):
        """Test HTML text cleaning."""
        loader = HTMLTranscriptLoader()

        messy_text = """
        Title

        Some  text  with    extra   spaces


        And    multiple    words
        """

        cleaned = loader._clean_text(messy_text)

        assert "Title" in cleaned
        assert "Some text with extra spaces" in cleaned
        assert "And multiple words" in cleaned
        # Should not have excessive blank lines
        assert "\n\n\n" not in cleaned


class TestTextTranscriptLoader:
    """Test plain text transcript loading."""

    def test_supports_txt(self):
        """Test text format detection."""
        loader = TextTranscriptLoader()

        assert loader.supports("transcript.txt") is True
        assert loader.supports("TRANSCRIPT.TXT") is True
        assert loader.supports("transcript.pdf") is False
        assert loader.supports("transcript.html") is False

    def test_load_local_file(self):
        """Test loading local text file."""
        loader = TextTranscriptLoader()

        # Create temp text file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            temp_path = Path(f.name)
            f.write("Q1 2025 Earnings Call\n\nRevenue: $100M\n\n\n\nThank you.")

        try:
            text = loader.load(temp_path)

            assert "Q1 2025 Earnings Call" in text
            assert "Revenue: $100M" in text
            assert "Thank you" in text
            # Should remove excessive blank lines
            assert "\n\n\n\n" not in text
        finally:
            temp_path.unlink()

    def test_clean_text(self):
        """Test text cleaning."""
        loader = TextTranscriptLoader()

        text_with_blanks = """
        Line 1


        Line 2



        Line 3
        """

        cleaned = loader._clean_text(text_with_blanks)

        assert "Line 1" in cleaned
        assert "Line 2" in cleaned
        assert "Line 3" in cleaned
        # Should reduce to max double newlines
        assert "\n\n\n" not in cleaned


class TestTranscriptLoaderFactory:
    """Test loader factory."""

    def test_factory_initialization(self):
        """Test factory creates all loaders."""
        factory = TranscriptLoaderFactory()

        assert len(factory._loaders) == 3
        assert any(isinstance(l, PDFTranscriptLoader) for l in factory._loaders)
        assert any(isinstance(l, HTMLTranscriptLoader) for l in factory._loaders)
        assert any(isinstance(l, TextTranscriptLoader) for l in factory._loaders)

    def test_get_loader_for_pdf(self):
        """Test factory selects PDF loader."""
        factory = TranscriptLoaderFactory()

        loader = factory.get_loader("transcript.pdf")
        assert isinstance(loader, PDFTranscriptLoader)

    def test_get_loader_for_html(self):
        """Test factory selects HTML loader."""
        factory = TranscriptLoaderFactory()

        loader = factory.get_loader("transcript.html")
        assert isinstance(loader, HTMLTranscriptLoader)

        loader = factory.get_loader("https://example.com/transcript")
        assert isinstance(loader, HTMLTranscriptLoader)

    def test_get_loader_for_text(self):
        """Test factory selects text loader."""
        factory = TranscriptLoaderFactory()

        loader = factory.get_loader("transcript.txt")
        assert isinstance(loader, TextTranscriptLoader)

    def test_get_loader_unsupported_format(self):
        """Test factory raises error for unsupported format."""
        factory = TranscriptLoaderFactory()

        with pytest.raises(ValueError, match="No loader supports"):
            factory.get_loader("transcript.docx")

    def test_factory_load_convenience_method(self):
        """Test factory's convenience load method."""
        factory = TranscriptLoaderFactory()

        # Create temp text file to test
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            temp_path = Path(f.name)
            f.write("Test content")

        try:
            text = factory.load(temp_path)
            assert "Test content" in text
        finally:
            temp_path.unlink()


class TestTranscriptLoaderIntegration:
    """Integration tests for loaders."""

    def test_pdf_load_end_to_end(self):
        """Test complete PDF loading workflow."""
        # Note: This would require a real PDF file
        # For now, we test that the error handling works
        loader = PDFTranscriptLoader()

        with pytest.raises(Exception):
            loader.load("nonexistent.pdf")

    def test_html_load_from_string(self):
        """Test loading HTML from string."""
        loader = HTMLTranscriptLoader()

        html_string = """
        <html>
            <body>
                <h1>Earnings Call</h1>
                <p>Revenue increased 20%.</p>
            </body>
        </html>
        """

        text = loader.load(html_string)

        assert "Earnings Call" in text
        assert "Revenue increased 20%" in text

    def test_text_load_from_file(self):
        """Test complete text loading workflow."""
        loader = TextTranscriptLoader()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            temp_path = Path(f.name)
            f.write("Complete transcript content\n\nWith multiple paragraphs.")

        try:
            text = loader.load(temp_path)
            assert "Complete transcript content" in text
            assert "With multiple paragraphs" in text
        finally:
            temp_path.unlink()
