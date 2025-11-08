"""
Tests for CompanyIRMapping model.

Tests cover:
- Model creation and basic attributes
- Helper methods (to_dict, is_verified, needs_verification)
- Verification status management
- URL pattern storage
- Multi-market support
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import inspect

from maverick_mcp.concall.models import CompanyIRMapping
from maverick_mcp.data.models import get_session


class TestCompanyIRMappingModel:
    """Test suite for CompanyIRMapping model."""

    @pytest.fixture
    def sample_mapping(self):
        """Create a sample IR mapping for testing."""
        return CompanyIRMapping(
            ticker="BAJFINANCE",
            company_name="Bajaj Finance Limited",
            ir_base_url="https://www.bajajfinserv.in/investor-relations",
            concall_url_pattern="/concalls/{year}/Q{quarter}",
            concall_section_xpath="//div[@class='concalls']/a",
            market="NSE",
            country="IN",
            verification_status="active",
        )

    def test_model_creation(self, sample_mapping):
        """Test basic model instantiation."""
        assert sample_mapping.ticker == "BAJFINANCE"
        assert sample_mapping.company_name == "Bajaj Finance Limited"
        assert sample_mapping.market == "NSE"
        assert sample_mapping.country == "IN"
        assert sample_mapping.verification_status == "active"

    def test_model_defaults(self):
        """Test default values."""
        mapping = CompanyIRMapping(
            ticker="AAPL",
            company_name="Apple Inc.",
        )
        assert mapping.verification_status == "pending"  # Default
        assert mapping.is_active is True  # Default
        assert mapping.market is None
        assert mapping.country is None

    def test_is_verified_property(self):
        """Test is_verified property."""
        mapping_active = CompanyIRMapping(
            ticker="AAPL",
            company_name="Apple Inc.",
            verification_status="active",
        )
        assert mapping_active.is_verified is True

        mapping_pending = CompanyIRMapping(
            ticker="MSFT",
            company_name="Microsoft Corp",
            verification_status="pending",
        )
        assert mapping_pending.is_verified is False

        mapping_broken = CompanyIRMapping(
            ticker="GOOGL",
            company_name="Alphabet Inc.",
            verification_status="broken",
        )
        assert mapping_broken.is_verified is False

    def test_needs_verification_property(self):
        """Test needs_verification property."""
        # Broken status needs verification
        mapping_broken = CompanyIRMapping(
            ticker="TEST1",
            company_name="Test Company 1",
            verification_status="broken",
        )
        assert mapping_broken.needs_verification is True

        # Pending status needs verification
        mapping_pending = CompanyIRMapping(
            ticker="TEST2",
            company_name="Test Company 2",
            verification_status="pending",
        )
        assert mapping_pending.needs_verification is True

        # No last_verified date needs verification
        mapping_no_date = CompanyIRMapping(
            ticker="TEST3",
            company_name="Test Company 3",
            verification_status="active",
            last_verified=None,
        )
        assert mapping_no_date.needs_verification is True

        # Old verification (>90 days) needs re-verification
        old_date = datetime.now(UTC) - timedelta(days=100)
        mapping_old = CompanyIRMapping(
            ticker="TEST4",
            company_name="Test Company 4",
            verification_status="active",
            last_verified=old_date,
        )
        assert mapping_old.needs_verification is True

        # Recent verification doesn't need re-verification
        recent_date = datetime.now(UTC) - timedelta(days=30)
        mapping_recent = CompanyIRMapping(
            ticker="TEST5",
            company_name="Test Company 5",
            verification_status="active",
            last_verified=recent_date,
        )
        assert mapping_recent.needs_verification is False

    def test_mark_verified_method(self, sample_mapping):
        """Test mark_verified method."""
        assert sample_mapping.last_verified is None

        before = datetime.now(UTC)
        sample_mapping.mark_verified(status="active")
        after = datetime.now(UTC)

        assert sample_mapping.verification_status == "active"
        assert sample_mapping.last_verified is not None
        assert before <= sample_mapping.last_verified <= after

    def test_mark_broken_method(self, sample_mapping):
        """Test mark_broken method."""
        sample_mapping.mark_broken(reason="404 Not Found")

        assert sample_mapping.verification_status == "broken"
        assert "404 Not Found" in sample_mapping.notes
        assert "Broken:" in sample_mapping.notes

        # Test marking broken again appends notes
        sample_mapping.mark_broken(reason="Connection timeout")
        assert "404 Not Found" in sample_mapping.notes
        assert "Connection timeout" in sample_mapping.notes

    def test_to_dict_method(self, sample_mapping):
        """Test to_dict serialization."""
        sample_mapping.created_at = datetime.now(UTC)
        sample_mapping.updated_at = datetime.now(UTC)
        sample_mapping.last_verified = datetime.now(UTC)

        data = sample_mapping.to_dict()

        assert data["ticker"] == "BAJFINANCE"
        assert data["company_name"] == "Bajaj Finance Limited"
        assert data["market"] == "NSE"
        assert data["country"] == "IN"
        assert data["verification_status"] == "active"
        assert data["is_active"] is True
        assert "last_verified" in data

    def test_repr_method(self, sample_mapping):
        """Test __repr__ string representation."""
        repr_str = repr(sample_mapping)

        assert "CompanyIRMapping" in repr_str
        assert "BAJFINANCE" in repr_str
        assert "Bajaj Finance Limited" in repr_str
        assert "active" in repr_str

    def test_url_pattern_storage(self):
        """Test storing URL patterns and selectors."""
        mapping = CompanyIRMapping(
            ticker="AAPL",
            company_name="Apple Inc.",
            ir_base_url="https://investor.apple.com",
            concall_url_pattern="/earnings-call-transcripts/{year}-q{quarter}",
            concall_section_xpath="//section[@id='transcripts']//a[@class='transcript-link']",
            concall_section_css="section#transcripts a.transcript-link",
        )

        assert mapping.concall_url_pattern == "/earnings-call-transcripts/{year}-q{quarter}"
        assert "section[@id='transcripts']" in mapping.concall_section_xpath
        assert "section#transcripts" in mapping.concall_section_css

    def test_multi_market_support(self):
        """Test multi-market attributes."""
        # US market
        us_mapping = CompanyIRMapping(
            ticker="AAPL",
            company_name="Apple Inc.",
            market="US",
            country="US",
        )
        assert us_mapping.market == "US"
        assert us_mapping.country == "US"

        # NSE market
        nse_mapping = CompanyIRMapping(
            ticker="RELIANCE.NS",
            company_name="Reliance Industries Limited",
            market="NSE",
            country="IN",
        )
        assert nse_mapping.market == "NSE"
        assert nse_mapping.country == "IN"

        # BSE market
        bse_mapping = CompanyIRMapping(
            ticker="TCS.BO",
            company_name="Tata Consultancy Services Limited",
            market="BSE",
            country="IN",
        )
        assert bse_mapping.market == "BSE"
        assert bse_mapping.country == "IN"

    def test_table_name(self):
        """Test table name is correct."""
        assert CompanyIRMapping.__tablename__ == "mcp_company_ir_mappings"

    def test_indexes_exist(self):
        """Test that expected indexes are defined."""
        table_args = CompanyIRMapping.__table_args__

        # Check indexes exist
        indexes = [arg for arg in table_args if hasattr(arg, "name") and "idx_" in arg.name]
        index_names = [idx.name for idx in indexes]

        assert "idx_ir_mapping_status" in index_names
        assert "idx_ir_mapping_market" in index_names
        assert "idx_ir_mapping_country" in index_names
        assert "idx_ir_mapping_active" in index_names


class TestCompanyIRMappingDatabaseOperations:
    """Test database operations with CompanyIRMapping model."""

    @pytest.fixture
    def session(self):
        """Create a test database session."""
        session = get_session()
        yield session
        session.close()

    def test_create_and_retrieve(self, session):
        """Test creating and retrieving an IR mapping."""
        mapping = CompanyIRMapping(
            ticker="DBTEST",
            company_name="Database Test Company",
            ir_base_url="https://example.com/ir",
            market="US",
            country="US",
        )

        session.add(mapping)
        session.commit()

        # Retrieve
        retrieved = session.query(CompanyIRMapping).filter_by(ticker="DBTEST").first()

        assert retrieved is not None
        assert retrieved.ticker == "DBTEST"
        assert retrieved.company_name == "Database Test Company"
        assert retrieved.market == "US"

        # Cleanup
        session.delete(retrieved)
        session.commit()

    def test_primary_key_uniqueness(self, session):
        """Test ticker is unique primary key."""
        mapping1 = CompanyIRMapping(
            ticker="PKTEST",
            company_name="PK Test Company 1",
            market="US",
        )
        session.add(mapping1)
        session.commit()

        # Try to add another with same ticker
        mapping2 = CompanyIRMapping(
            ticker="PKTEST",
            company_name="PK Test Company 2",
            market="NSE",
        )
        session.add(mapping2)

        with pytest.raises(Exception):  # Should raise integrity error
            session.commit()

        session.rollback()

        # Cleanup
        session.delete(mapping1)
        session.commit()

    def test_update_verification_status(self, session):
        """Test updating verification status."""
        mapping = CompanyIRMapping(
            ticker="VERTEST",
            company_name="Verification Test Company",
            verification_status="pending",
        )
        session.add(mapping)
        session.commit()

        # Update status
        mapping.mark_verified(status="active")
        session.commit()

        # Retrieve and verify
        retrieved = session.query(CompanyIRMapping).filter_by(ticker="VERTEST").first()
        assert retrieved.verification_status == "active"
        assert retrieved.last_verified is not None

        # Cleanup
        session.delete(retrieved)
        session.commit()

    def test_deactivate_mapping(self, session):
        """Test deactivating a mapping."""
        mapping = CompanyIRMapping(
            ticker="DEACTEST",
            company_name="Deactivation Test Company",
            is_active=True,
        )
        session.add(mapping)
        session.commit()

        # Deactivate
        mapping.is_active = False
        session.commit()

        # Retrieve and verify
        retrieved = session.query(CompanyIRMapping).filter_by(ticker="DEACTEST").first()
        assert retrieved.is_active is False

        # Cleanup
        session.delete(retrieved)
        session.commit()
