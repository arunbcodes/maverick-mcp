"""
Conference Call Analysis Module for MaverickMCP.

A modular, standalone package for fetching, storing, and analyzing
conference call transcripts from Indian (NSE/BSE) and US markets.

Design Principles:
    - SOLID: Single responsibility, open/closed, dependency inversion
    - Modular: Can be extracted as standalone package
    - Extensible: Easy to add new data sources and analysis methods
    - Maintainable: Clean separation of concerns

Architecture:
    models/      - Database models for transcripts and IR mappings
    config/      - Module-specific configuration
    providers/   - Data source providers (IR, NSE, Screener, YouTube)
    services/    - Business logic (fetcher, summarizer, RAG engine)
    utils/       - Helper functions and utilities

Public API:
    Models:
        - ConferenceCall: Main transcript storage model
        - CompanyIRMapping: IR website URL mappings

    Services (to be added in future commits):
        - TranscriptFetcher: Fetch transcripts from multiple sources
        - ConcallSummarizer: AI-powered summarization
        - RAGEngine: Q&A over transcripts

Usage:
    >>> from maverick_mcp.concall.models import ConferenceCall, CompanyIRMapping
    >>> call = ConferenceCall(ticker="AAPL", quarter="Q1FY25", fiscal_year=2025)

Version: 0.1.0 (Phase 1: Foundation - Models Only)
"""

__version__ = "0.1.0"
__author__ = "Maverick MCP Contributors"

# Public API - Models
from maverick_mcp.concall.models import CompanyIRMapping, ConferenceCall

__all__ = [
    # Models
    "ConferenceCall",
    "CompanyIRMapping",
    # Version info
    "__version__",
]
