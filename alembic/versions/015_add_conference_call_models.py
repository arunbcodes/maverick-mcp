"""Add conference call models

Revision ID: 015_add_conference_call_models
Revises: 014_add_portfolio_models
Create Date: 2025-11-08 00:00:00.000000

This migration adds conference call analysis models for Indian and US markets:
1. ConferenceCall - Transcript storage with AI analysis caching
2. CompanyIRMapping - Company IR website URL mappings

Features:
- Multi-market support (US, NSE, BSE)
- AI analysis caching (summaries, sentiment, key insights)
- RAG integration (vector store references)
- Source tracking (company_ir, nse, bse, screener, youtube)
- URL verification for IR mappings
- Comprehensive indexes for screening queries

Design:
- Modular: Separate maverick_mcp/concall/ module
- Extractable: Can be moved to standalone repo
- SOLID: Single responsibility, dependency inversion
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "015_add_conference_call_models"
down_revision = "014_add_portfolio_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create conference call tables."""

    # ==================== Table 1: ConferenceCall ====================
    op.create_table(
        "mcp_conference_calls",
        # Primary identification
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("quarter", sa.String(10), nullable=False),
        sa.Column("fiscal_year", sa.Integer, nullable=False),
        sa.Column("call_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "call_type",
            sa.String(30),
            nullable=False,
            server_default="earnings",
            comment="Type: earnings, investor_meet, agm, analyst_day",
        ),
        # Source tracking
        sa.Column(
            "source",
            sa.String(50),
            nullable=False,
            comment="Source: company_ir, nse, bse, screener, youtube",
        ),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("transcript_text", sa.Text, nullable=True),
        sa.Column("transcript_pdf_path", sa.String(500), nullable=True),
        sa.Column("transcript_format", sa.String(20), nullable=True),
        # AI Analysis (cached)
        sa.Column("summary", sa.JSON, nullable=True),
        sa.Column("sentiment", sa.String(20), nullable=True),
        sa.Column("key_insights", sa.JSON, nullable=True),
        sa.Column("management_tone", sa.String(20), nullable=True),
        # RAG integration
        sa.Column("vector_store_id", sa.String(100), nullable=True),
        sa.Column("embedding_model", sa.String(100), nullable=True),
        # Processing metadata
        sa.Column("is_processed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("processing_error", sa.Text, nullable=True),
        sa.Column("last_accessed", sa.DateTime(timezone=True), nullable=True),
        # Timestamps (from TimestampMixin)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Indexes for ConferenceCall
    op.create_unique_constraint(
        "uq_concall_ticker_quarter",
        "mcp_conference_calls",
        ["ticker", "quarter", "fiscal_year"],
    )
    op.create_index("idx_concall_ticker", "mcp_conference_calls", ["ticker"])
    op.create_index(
        "idx_concall_ticker_year", "mcp_conference_calls", ["ticker", "fiscal_year"]
    )
    op.create_index(
        "idx_concall_quarter_year", "mcp_conference_calls", ["quarter", "fiscal_year"]
    )
    op.create_index("idx_concall_date", "mcp_conference_calls", ["call_date"])
    op.create_index("idx_concall_source", "mcp_conference_calls", ["source"])
    op.create_index("idx_concall_sentiment", "mcp_conference_calls", ["sentiment"])
    op.create_index("idx_concall_processed", "mcp_conference_calls", ["is_processed"])
    op.create_index(
        "idx_concall_vector_store_id", "mcp_conference_calls", ["vector_store_id"]
    )
    op.create_index(
        "idx_concall_last_accessed", "mcp_conference_calls", ["last_accessed"]
    )
    # Composite indexes for screening
    op.create_index(
        "idx_concall_ticker_sentiment",
        "mcp_conference_calls",
        ["ticker", "sentiment"],
    )
    op.create_index(
        "idx_concall_source_processed",
        "mcp_conference_calls",
        ["source", "is_processed"],
    )

    # ==================== Table 2: CompanyIRMapping ====================
    op.create_table(
        "mcp_company_ir_mappings",
        # Primary identification
        sa.Column("ticker", sa.String(20), primary_key=True),
        sa.Column("company_name", sa.String(200), nullable=False),
        # IR website URLs
        sa.Column("ir_base_url", sa.Text, nullable=True),
        sa.Column("concall_url_pattern", sa.Text, nullable=True),
        sa.Column("concall_section_xpath", sa.Text, nullable=True),
        sa.Column("concall_section_css", sa.Text, nullable=True),
        # Verification metadata
        sa.Column("last_verified", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "verification_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("notes", sa.Text, nullable=True),
        # Multi-market support
        sa.Column("market", sa.String(10), nullable=True),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        # Timestamps (from TimestampMixin)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Indexes for CompanyIRMapping
    op.create_index(
        "idx_ir_mapping_status", "mcp_company_ir_mappings", ["verification_status"]
    )
    op.create_index("idx_ir_mapping_market", "mcp_company_ir_mappings", ["market"])
    op.create_index("idx_ir_mapping_country", "mcp_company_ir_mappings", ["country"])
    op.create_index("idx_ir_mapping_active", "mcp_company_ir_mappings", ["is_active"])
    # Composite index for multi-market queries
    op.create_index(
        "idx_ir_mapping_country_active",
        "mcp_company_ir_mappings",
        ["country", "is_active"],
    )


def downgrade() -> None:
    """Drop conference call tables."""

    # Drop indexes first (reverse order)
    op.drop_index("idx_ir_mapping_country_active", table_name="mcp_company_ir_mappings")
    op.drop_index("idx_ir_mapping_active", table_name="mcp_company_ir_mappings")
    op.drop_index("idx_ir_mapping_country", table_name="mcp_company_ir_mappings")
    op.drop_index("idx_ir_mapping_market", table_name="mcp_company_ir_mappings")
    op.drop_index("idx_ir_mapping_status", table_name="mcp_company_ir_mappings")

    op.drop_index("idx_concall_source_processed", table_name="mcp_conference_calls")
    op.drop_index("idx_concall_ticker_sentiment", table_name="mcp_conference_calls")
    op.drop_index("idx_concall_last_accessed", table_name="mcp_conference_calls")
    op.drop_index("idx_concall_vector_store_id", table_name="mcp_conference_calls")
    op.drop_index("idx_concall_processed", table_name="mcp_conference_calls")
    op.drop_index("idx_concall_sentiment", table_name="mcp_conference_calls")
    op.drop_index("idx_concall_source", table_name="mcp_conference_calls")
    op.drop_index("idx_concall_date", table_name="mcp_conference_calls")
    op.drop_index("idx_concall_quarter_year", table_name="mcp_conference_calls")
    op.drop_index("idx_concall_ticker_year", table_name="mcp_conference_calls")
    op.drop_index("idx_concall_ticker", table_name="mcp_conference_calls")

    op.drop_constraint(
        "uq_concall_ticker_quarter", "mcp_conference_calls", type_="unique"
    )

    # Drop tables (reverse order of creation)
    op.drop_table("mcp_company_ir_mappings")
    op.drop_table("mcp_conference_calls")
