"""
Conference Call Model.

Single Responsibility: Store and manage conference call transcript data.
Open/Closed: Extensible for new call types without modifying existing code.
Liskov Substitution: Can be used anywhere a Base model is expected.
Interface Segregation: Minimal, focused interface for transcript storage.
Dependency Inversion: Depends on abstractions (Base, TimestampMixin).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)

from maverick_mcp.database.base import Base
from maverick_mcp.data.models import TimestampMixin


class ConferenceCall(TimestampMixin, Base):
    """
    Conference call transcript storage with AI analysis caching.

    Stores transcripts from earnings calls, investor conferences, and annual
    general meetings for both Indian (NSE/BSE) and US market companies.

    Design Philosophy:
        - Self-contained: All transcript metadata in one place
        - Source-agnostic: Works with any data provider
        - AI-ready: Structured for RAG and LLM processing
        - Cache-friendly: Stores expensive AI analysis results

    Attributes:
        id (UUID): Unique identifier
        ticker (str): Stock symbol (e.g., "AAPL", "RELIANCE.NS")
        quarter (str): Quarter identifier (e.g., "Q1FY25", "Q4CY24")
        fiscal_year (int): Year of the call (e.g., 2025)
        call_date (datetime): When the call occurred
        call_type (str): Type of call (earnings, investor_meet, agm)

        source (str): Data source (company_ir, nse, bse, screener, youtube)
        source_url (str): Original URL of transcript
        transcript_text (str): Full transcript text
        transcript_pdf_path (str): Local path to PDF if downloaded
        transcript_format (str): Original format (pdf, html, txt, audio)

        summary (dict): AI-generated structured summary (JSON)
        sentiment (str): Overall sentiment (Bullish, Neutral, Bearish, Mixed)
        key_insights (list): Key takeaways array (JSON)
        management_tone (str): Management's tone (Confident, Cautious, Defensive)

        vector_store_id (str): Reference to vector embeddings for RAG
        embedding_model (str): Model used for embeddings

        is_processed (bool): Whether AI analysis completed
        processing_error (str): Error message if processing failed
        last_accessed (datetime): Last query time (for cache management)

    Indexes:
        - Unique: (ticker, quarter, fiscal_year)
        - Performance: ticker, fiscal_year, sentiment, is_processed
        - Composite: ticker+sentiment, source+processed for screening

    Example:
        >>> call = ConferenceCall(
        ...     ticker="BAJFINANCE",
        ...     quarter="Q1FY25",
        ...     fiscal_year=2025,
        ...     call_type="earnings",
        ...     source="company_ir"
        ... )
    """

    __tablename__ = "mcp_conference_calls"

    # ==================== Primary Identification ====================
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    ticker = Column(String(20), nullable=False, index=True)
    quarter = Column(String(10), nullable=False)  # Q1FY25, Q2FY24, Q4CY23
    fiscal_year = Column(Integer, nullable=False)
    call_date = Column(DateTime(timezone=True), nullable=True)
    call_type = Column(
        String(30),
        nullable=False,
        default="earnings",
        comment="Type: earnings, investor_meet, agm, analyst_day",
    )

    # ==================== Source Tracking ====================
    source = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Source: company_ir, nse, bse, screener, youtube",
    )
    source_url = Column(Text, nullable=True, comment="Original URL of transcript")
    transcript_text = Column(Text, nullable=True, comment="Full transcript content")
    transcript_pdf_path = Column(
        String(500), nullable=True, comment="Local file path if PDF stored"
    )
    transcript_format = Column(
        String(20), nullable=True, comment="Format: pdf, html, txt, audio_transcribed"
    )

    # ==================== AI Analysis (Cached) ====================
    summary = Column(
        JSON,
        nullable=True,
        comment="Structured summary: {results, guidance, concerns, outlook}",
    )
    sentiment = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Sentiment: Bullish, Neutral, Bearish, Mixed",
    )
    key_insights = Column(
        JSON, nullable=True, comment="Array of key insights and takeaways"
    )
    management_tone = Column(
        String(20),
        nullable=True,
        comment="Tone: Confident, Cautious, Defensive, Evasive",
    )

    # ==================== RAG Integration ====================
    vector_store_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Reference ID in vector database (Chroma/FAISS)",
    )
    embedding_model = Column(
        String(100),
        nullable=True,
        comment="Model used: all-MiniLM-L6-v2, text-embedding-ada-002",
    )

    # ==================== Processing Metadata ====================
    is_processed = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether AI analysis completed",
    )
    processing_error = Column(Text, nullable=True, comment="Error if processing failed")
    last_accessed = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last query time for cache eviction",
    )

    # ==================== Database Constraints ====================
    __table_args__ = (
        # Unique constraint: one transcript per company per quarter
        UniqueConstraint(
            "ticker",
            "quarter",
            "fiscal_year",
            name="uq_concall_ticker_quarter",
        ),
        # Single-column indexes for common queries
        Index("idx_concall_ticker_year", "ticker", "fiscal_year"),
        Index("idx_concall_quarter_year", "quarter", "fiscal_year"),
        Index("idx_concall_date", "call_date"),
        Index("idx_concall_sentiment", "sentiment"),
        Index("idx_concall_processed", "is_processed"),
        # Composite indexes for screening queries
        Index("idx_concall_ticker_sentiment", "ticker", "sentiment"),
        Index("idx_concall_source_processed", "source", "is_processed"),
        # Time-based index for cache management
        Index("idx_concall_last_accessed", "last_accessed"),
    )

    def __repr__(self):
        """String representation for debugging."""
        return (
            f"<ConferenceCall("
            f"ticker='{self.ticker}', "
            f"quarter='{self.quarter}', "
            f"year={self.fiscal_year}, "
            f"sentiment='{self.sentiment}'"
            f")>"
        )

    def to_dict(self) -> dict:
        """
        Convert model to dictionary for API responses.

        Returns:
            dict: Model data as dictionary

        Example:
            >>> call.to_dict()
            {'ticker': 'AAPL', 'quarter': 'Q1FY25', ...}
        """
        return {
            "id": str(self.id),
            "ticker": self.ticker,
            "quarter": self.quarter,
            "fiscal_year": self.fiscal_year,
            "call_date": self.call_date.isoformat() if self.call_date else None,
            "call_type": self.call_type,
            "source": self.source,
            "sentiment": self.sentiment,
            "management_tone": self.management_tone,
            "is_processed": self.is_processed,
            "summary": self.summary,
            "key_insights": self.key_insights,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def has_transcript(self) -> bool:
        """Check if transcript text is available."""
        return bool(self.transcript_text and len(self.transcript_text.strip()) > 0)

    @property
    def has_analysis(self) -> bool:
        """Check if AI analysis is available."""
        return self.is_processed and self.summary is not None

    def mark_accessed(self) -> None:
        """Update last_accessed timestamp for cache management."""
        from datetime import UTC

        self.last_accessed = datetime.now(UTC)
