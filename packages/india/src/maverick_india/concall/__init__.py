"""
Conference Call Analysis.

Earnings call transcript fetching, summarization, and sentiment analysis.

This module provides:
- ConcallProvider: Abstract interface for transcript providers
- CompanyIRProvider: Fetch transcripts from company IR websites
- NSEProvider: Fetch transcripts from NSE exchange filings
- TranscriptLoader utilities: Parse PDF, HTML, and text transcripts

Models (from maverick-data):
- ConferenceCall: Main model for storing transcripts and analysis
- CompanyIRMapping: Model for company IR website URL mappings

Services (require LLM integration):
- TranscriptFetcher: Orchestrates transcript fetching with fallback
- ConcallSummarizer: AI-powered summarization (requires maverick-agents)
- SentimentAnalyzer: Sentiment analysis (requires maverick-agents)
- ConcallRAGEngine: RAG-based Q&A (requires maverick-agents)

Example:
    >>> from maverick_india.concall import CompanyIRProvider, NSEProvider
    >>>
    >>> # Fetch from company IR website
    >>> ir_provider = CompanyIRProvider()
    >>> transcript = await ir_provider.fetch_transcript("RELIANCE.NS", "Q1", 2025)
    >>>
    >>> # Fallback to NSE filings
    >>> nse_provider = NSEProvider()
    >>> transcript = await nse_provider.fetch_transcript("RELIANCE.NS", "Q1", 2025)
"""

from maverick_india.concall.providers import (
    CompanyIRProvider,
    ConcallProvider,
    NSEProvider,
)
from maverick_india.concall.services import (
    SENTIMENT_ANALYSIS_PROMPT,
    SUMMARIZATION_PROMPT,
    ConcallSummarizer,
    SentimentAnalyzer,
    TranscriptFetcher,
)
from maverick_india.concall.utils import (
    HTMLTranscriptLoader,
    PDFTranscriptLoader,
    TextTranscriptLoader,
    TranscriptLoader,
    TranscriptLoaderFactory,
)

__all__ = [
    # Providers
    "ConcallProvider",
    "CompanyIRProvider",
    "NSEProvider",
    # Services
    "TranscriptFetcher",
    "ConcallSummarizer",
    "SentimentAnalyzer",
    "SUMMARIZATION_PROMPT",
    "SENTIMENT_ANALYSIS_PROMPT",
    # Transcript Loaders
    "TranscriptLoader",
    "PDFTranscriptLoader",
    "HTMLTranscriptLoader",
    "TextTranscriptLoader",
    "TranscriptLoaderFactory",
]
