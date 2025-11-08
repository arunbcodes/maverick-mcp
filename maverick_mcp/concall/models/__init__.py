"""
Conference Call Data Models.

This module provides database models for conference call transcript storage
and management. Designed to be independent and extractable as a separate package.

Public API:
    - ConferenceCall: Main model for storing transcripts and analysis
    - CompanyIRMapping: Model for company IR website URL mappings
"""

from maverick_mcp.concall.models.conference_call import ConferenceCall
from maverick_mcp.concall.models.company_ir import CompanyIRMapping

__all__ = ["ConferenceCall", "CompanyIRMapping"]
