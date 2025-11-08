"""
Conference Call Data Providers.

Data source providers for fetching transcripts from various sources.

Available Providers:
    - CompanyIRProvider (Priority 1) - Company IR websites [IMPLEMENTED]
    - NSEProvider (Priority 2) - NSE exchange filings [TODO]
    - ScreenerProvider (Priority 3) - Screener.in [TODO]
    - YouTubeProvider (Priority 4) - YouTube audio transcription [TODO]

Design:
    All providers implement ConcallProvider interface for consistency.
"""

from maverick_mcp.concall.providers.base_provider import ConcallProvider
from maverick_mcp.concall.providers.company_ir_provider import CompanyIRProvider

__all__ = ["ConcallProvider", "CompanyIRProvider"]
