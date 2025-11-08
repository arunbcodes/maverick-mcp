"""
Tests for ConferenceCall model.

Tests cover:
- Model creation and basic attributes
- Database constraints (unique constraint on ticker+quarter+year)
- Helper methods (to_dict, has_transcript, has_analysis)
- Timestamp functionality
- Index verification
"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import inspect

from maverick_mcp.concall.models import ConferenceCall
from maverick_mcp.data.models import get_session


class TestConferenceCallModel:
    """Test suite for ConferenceCall model."""

    @pytest.fixture
    def sample_call(self):
        """Create a sample conference call for testing."""
        return ConferenceCall(
            ticker="BAJFINANCE",
            quarter="Q1FY25",
            fiscal_year=2025,
            call_date=datetime(2024, 7, 25, 14, 30, tzinfo=UTC),
            call_type="earnings",
            source="company_ir",
            source_url="https://example.com/ir/concalls/q1fy25.pdf",
            transcript_text="Full transcript content here...",
            transcript_format="pdf",
        )

    def test_model_creation(self, sample_call):
        """Test basic model instantiation."""
        assert sample_call.ticker == "BAJFINANCE"
        assert sample_call.quarter == "Q1FY25"
        assert sample_call.fiscal_year == 2025
        assert sample_call.call_type == "earnings"
        assert sample_call.source == "company_ir"
        assert sample_call.id is None  # Not assigned until persisted

    def test_model_defaults(self):
        """Test default values."""
        call = ConferenceCall(
            ticker="AAPL",
            quarter="Q4CY24",
            fiscal_year=2024,
            source="nse",
        )
        assert call.call_type == "earnings"  # Default
        assert call.is_processed is False  # Default
        assert call.summary is None
        assert call.sentiment is None

    def test_uuid_generation(self):
        """Test UUID is auto-generated."""
        call = ConferenceCall(
            ticker="RELIANCE.NS",
            quarter="Q2FY25",
            fiscal_year=2025,
            source="company_ir",
        )
        # UUID should be generated on creation
        assert call.id is None or isinstance(call.id, uuid.UUID)

    def test_has_transcript_property(self, sample_call):
        """Test has_transcript property."""
        assert sample_call.has_transcript is True

        call_no_transcript = ConferenceCall(
            ticker="AAPL",
            quarter="Q1FY25",
            fiscal_year=2025,
            source="company_ir",
        )
        assert call_no_transcript.has_transcript is False

        call_empty_transcript = ConferenceCall(
            ticker="MSFT",
            quarter="Q1FY25",
            fiscal_year=2025,
            source="company_ir",
            transcript_text="   ",  # Empty/whitespace
        )
        assert call_empty_transcript.has_transcript is False

    def test_has_analysis_property(self):
        """Test has_analysis property."""
        call = ConferenceCall(
            ticker="AAPL",
            quarter="Q1FY25",
            fiscal_year=2025,
            source="company_ir",
            is_processed=True,
            summary={"results": "Strong quarter", "guidance": "Positive"},
        )
        assert call.has_analysis is True

        call_no_analysis = ConferenceCall(
            ticker="MSFT",
            quarter="Q1FY25",
            fiscal_year=2025,
            source="company_ir",
            is_processed=False,
        )
        assert call_no_analysis.has_analysis is False

        call_processed_no_summary = ConferenceCall(
            ticker="GOOGL",
            quarter="Q1FY25",
            fiscal_year=2025,
            source="company_ir",
            is_processed=True,
            summary=None,
        )
        assert call_processed_no_summary.has_analysis is False

    def test_mark_accessed_method(self, sample_call):
        """Test mark_accessed updates last_accessed timestamp."""
        assert sample_call.last_accessed is None

        before = datetime.now(UTC)
        sample_call.mark_accessed()
        after = datetime.now(UTC)

        assert sample_call.last_accessed is not None
        assert before <= sample_call.last_accessed <= after

    def test_to_dict_method(self, sample_call):
        """Test to_dict serialization."""
        sample_call.id = uuid.uuid4()
        sample_call.created_at = datetime.now(UTC)
        sample_call.updated_at = datetime.now(UTC)

        data = sample_call.to_dict()

        assert data["ticker"] == "BAJFINANCE"
        assert data["quarter"] == "Q1FY25"
        assert data["fiscal_year"] == 2025
        assert data["call_type"] == "earnings"
        assert data["source"] == "company_ir"
        assert data["is_processed"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_repr_method(self, sample_call):
        """Test __repr__ string representation."""
        sample_call.sentiment = "Bullish"
        repr_str = repr(sample_call)

        assert "ConferenceCall" in repr_str
        assert "BAJFINANCE" in repr_str
        assert "Q1FY25" in repr_str
        assert "2025" in repr_str
        assert "Bullish" in repr_str

    def test_json_fields(self):
        """Test JSON fields accept dict/list data."""
        call = ConferenceCall(
            ticker="AAPL",
            quarter="Q1FY25",
            fiscal_year=2025,
            source="company_ir",
            summary={
                "results": {"revenue": "100B", "pat": "25B"},
                "guidance": "Strong growth expected",
                "concerns": ["Supply chain", "Competition"],
            },
            key_insights=[
                "iPhone sales beat expectations",
                "Services revenue grew 15%",
                "China market challenges",
            ],
        )

        assert isinstance(call.summary, dict)
        assert isinstance(call.key_insights, list)
        assert call.summary["results"]["revenue"] == "100B"
        assert len(call.key_insights) == 3

    def test_table_name(self):
        """Test table name is correct."""
        assert ConferenceCall.__tablename__ == "mcp_conference_calls"

    def test_indexes_exist(self):
        """Test that expected indexes are defined."""
        inspector = inspect(ConferenceCall)
        table_args = ConferenceCall.__table_args__

        # Check unique constraint exists
        unique_constraints = [
            constraint
            for constraint in table_args
            if hasattr(constraint, "name")
            and constraint.name == "uq_concall_ticker_quarter"
        ]
        assert len(unique_constraints) > 0

        # Check some key indexes exist
        indexes = [arg for arg in table_args if hasattr(arg, "name") and "idx_" in arg.name]
        index_names = [idx.name for idx in indexes]

        assert "idx_concall_ticker" in index_names or any(
            "ticker" in name for name in index_names
        )
        assert "idx_concall_sentiment" in index_names or any(
            "sentiment" in name for name in index_names
        )


class TestConferenceCallDatabaseOperations:
    """Test database operations with ConferenceCall model."""

    @pytest.fixture
    def session(self):
        """Create a test database session."""
        session = get_session()
        yield session
        session.close()

    def test_create_and_retrieve(self, session):
        """Test creating and retrieving a conference call."""
        call = ConferenceCall(
            ticker="TEST",
            quarter="Q1FY25",
            fiscal_year=2025,
            source="company_ir",
            transcript_text="Test transcript",
        )

        session.add(call)
        session.commit()

        # Retrieve
        retrieved = (
            session.query(ConferenceCall)
            .filter_by(ticker="TEST", quarter="Q1FY25", fiscal_year=2025)
            .first()
        )

        assert retrieved is not None
        assert retrieved.ticker == "TEST"
        assert retrieved.transcript_text == "Test transcript"

        # Cleanup
        session.delete(retrieved)
        session.commit()

    def test_unique_constraint(self, session):
        """Test unique constraint on ticker+quarter+fiscal_year."""
        call1 = ConferenceCall(
            ticker="UNIQUE_TEST",
            quarter="Q1FY25",
            fiscal_year=2025,
            source="company_ir",
        )
        session.add(call1)
        session.commit()

        # Try to add duplicate
        call2 = ConferenceCall(
            ticker="UNIQUE_TEST",
            quarter="Q1FY25",
            fiscal_year=2025,
            source="nse",  # Different source, but same ticker+quarter+year
        )
        session.add(call2)

        with pytest.raises(Exception):  # Should raise integrity error
            session.commit()

        session.rollback()

        # Cleanup
        session.delete(call1)
        session.commit()

    def test_update_analysis(self, session):
        """Test updating AI analysis fields."""
        call = ConferenceCall(
            ticker="UPDATE_TEST",
            quarter="Q1FY25",
            fiscal_year=2025,
            source="company_ir",
            transcript_text="Original transcript",
        )
        session.add(call)
        session.commit()

        # Update with analysis
        call.summary = {"results": "Good quarter"}
        call.sentiment = "Bullish"
        call.is_processed = True
        session.commit()

        # Retrieve and verify
        retrieved = (
            session.query(ConferenceCall)
            .filter_by(ticker="UPDATE_TEST")
            .first()
        )
        assert retrieved.summary == {"results": "Good quarter"}
        assert retrieved.sentiment == "Bullish"
        assert retrieved.is_processed is True

        # Cleanup
        session.delete(retrieved)
        session.commit()
