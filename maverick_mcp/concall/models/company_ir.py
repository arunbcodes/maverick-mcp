"""
Company IR Mapping Model.

Single Responsibility: Store company IR website URL mappings.
Open/Closed: Extensible for new URL patterns without modifications.
Liskov Substitution: Can be used as Base model anywhere.
Interface Segregation: Focused interface for URL mapping only.
Dependency Inversion: Depends on Base abstraction.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text

from maverick_mcp.database.base import Base
from maverick_mcp.data.models import TimestampMixin


class CompanyIRMapping(TimestampMixin, Base):
    """
    Company Investor Relations website URL mappings.

    Maintains a curated database of company IR pages for automatic transcript
    fetching. This is the PRIMARY data source (legal, reliable, structured).

    Design Philosophy:
        - Legal-first: No ToS violations, uses public IR pages
        - Manual curation: Quality over quantity
        - Pattern-based: Supports URL templates for automation
        - Verification-aware: Tracks broken/changed URLs

    Attributes:
        ticker (str): Stock symbol (primary key, e.g., "AAPL", "RELIANCE.NS")
        company_name (str): Full legal name
        ir_base_url (str): Base IR section URL
        concall_url_pattern (str): Template for concall URLs
        concall_section_xpath (str): XPath selector for scraping
        concall_section_css (str): CSS selector for scraping

        last_verified (datetime): Last successful verification
        verification_status (str): Status (active, broken, changed, pending)
        notes (str): Manual notes about IR structure

        market (str): Market identifier (US, NSE, BSE)
        country (str): Country code (US, IN)
        is_active (bool): Whether actively tracked

    Indexes:
        - Primary: ticker
        - Performance: verification_status, market, is_active

    Example:
        >>> mapping = CompanyIRMapping(
        ...     ticker="BAJFINANCE",
        ...     company_name="Bajaj Finance Limited",
        ...     ir_base_url="https://www.bajajfinserv.in/investor-relations",
        ...     concall_url_pattern="/concalls/{year}/Q{quarter}",
        ...     market="NSE",
        ...     country="IN"
        ... )
    """

    __tablename__ = "mcp_company_ir_mappings"

    # ==================== Primary Identification ====================
    ticker = Column(String(20), primary_key=True, comment="Stock ticker symbol")
    company_name = Column(String(200), nullable=False, comment="Full company name")

    # ==================== IR Website URLs ====================
    ir_base_url = Column(
        Text,
        nullable=True,
        comment="Base URL of investor relations section",
    )
    concall_url_pattern = Column(
        Text,
        nullable=True,
        comment="URL template: /ir/concalls/{year}/{quarter}",
    )
    concall_section_xpath = Column(
        Text,
        nullable=True,
        comment="XPath selector for finding concall links",
    )
    concall_section_css = Column(
        Text,
        nullable=True,
        comment="CSS selector alternative to XPath",
    )

    # ==================== Verification Metadata ====================
    last_verified = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful URL verification",
    )
    verification_status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="Status: active, broken, changed, pending",
    )
    notes = Column(
        Text,
        nullable=True,
        comment="Manual notes about IR structure or issues",
    )

    # ==================== Multi-Market Support ====================
    market = Column(
        String(10),
        nullable=True,
        index=True,
        comment="Market: US, NSE, BSE",
    )
    country = Column(
        String(2),
        nullable=True,
        index=True,
        comment="Country code: US, IN",
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether company is actively tracked",
    )

    # ==================== Database Constraints ====================
    __table_args__ = (
        Index("idx_ir_mapping_status", "verification_status"),
        Index("idx_ir_mapping_market", "market"),
        Index("idx_ir_mapping_country", "country"),
        Index("idx_ir_mapping_active", "is_active"),
        # Composite index for multi-market queries
        Index("idx_ir_mapping_country_active", "country", "is_active"),
    )

    def __repr__(self):
        """String representation for debugging."""
        return (
            f"<CompanyIRMapping("
            f"ticker='{self.ticker}', "
            f"company='{self.company_name}', "
            f"status='{self.verification_status}'"
            f")>"
        )

    def to_dict(self) -> dict:
        """
        Convert model to dictionary for API responses.

        Returns:
            dict: Model data as dictionary

        Example:
            >>> mapping.to_dict()
            {'ticker': 'AAPL', 'company_name': 'Apple Inc.', ...}
        """
        return {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "ir_base_url": self.ir_base_url,
            "concall_url_pattern": self.concall_url_pattern,
            "verification_status": self.verification_status,
            "last_verified": (
                self.last_verified.isoformat() if self.last_verified else None
            ),
            "market": self.market,
            "country": self.country,
            "is_active": self.is_active,
            "notes": self.notes,
        }

    @property
    def is_verified(self) -> bool:
        """Check if URLs are verified and working."""
        return self.verification_status == "active"

    @property
    def needs_verification(self) -> bool:
        """Check if mapping needs URL verification."""
        if self.verification_status in ["broken", "pending"]:
            return True

        # Re-verify if not checked in 90 days
        if self.last_verified is None:
            return True

        from datetime import UTC, timedelta

        ninety_days_ago = datetime.now(UTC) - timedelta(days=90)
        return self.last_verified < ninety_days_ago

    def mark_verified(self, status: str = "active") -> None:
        """
        Mark mapping as verified with given status.

        Args:
            status: Verification status (active, broken, changed)
        """
        from datetime import UTC

        self.verification_status = status
        self.last_verified = datetime.now(UTC)

    def mark_broken(self, reason: str | None = None) -> None:
        """
        Mark mapping as broken with optional reason.

        Args:
            reason: Why the mapping is broken (added to notes)
        """
        self.verification_status = "broken"
        if reason:
            timestamp = datetime.now().strftime("%Y-%m-%d")
            self.notes = f"[{timestamp}] Broken: {reason}\n{self.notes or ''}"
