"""Add audit logs table for capability execution tracking.

Revision ID: 019_add_audit_logs
Revises: 018_add_phase4_auth_fields
Create Date: 2024-12-20

This migration is compatible with both PostgreSQL and SQLite:
- Uses dialect-aware UUID type (CHAR(36) for SQLite, native UUID for PostgreSQL)
- Avoids PostgreSQL-specific features that would break SQLite
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision = "019_add_audit_logs"
down_revision = "018_add_phase4_auth_fields"
branch_labels = None
depends_on = None


def _get_uuid_type():
    """Get UUID column type based on database dialect."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID
        return UUID(as_uuid=True)
    else:
        # SQLite and others: use CHAR(36) for UUID storage
        return sa.String(36)


def upgrade() -> None:
    """Create audit_logs table for capability execution tracking."""
    uuid_type = _get_uuid_type()

    op.create_table(
        "audit_logs",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("event_type", sa.String(50), nullable=False, index=True),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), nullable=False, index=True
        ),
        # Execution context
        sa.Column("execution_id", uuid_type, index=True),
        sa.Column("capability_id", sa.String(100), index=True),
        sa.Column("user_id", sa.String(100), index=True),
        sa.Column("correlation_id", sa.String(100), index=True),
        # Event data (stored as JSON text)
        sa.Column("input_data", sa.Text),
        sa.Column("output_data", sa.Text),
        sa.Column("error", sa.Text),
        sa.Column("error_type", sa.String(100)),
        # Metrics
        sa.Column("duration_ms", sa.Integer),
        # Agent info (stored as JSON text)
        sa.Column("agents_consulted", sa.Text),
        sa.Column("reasoning_trace", sa.Text),
        # Business data
        sa.Column("ticker", sa.String(20), index=True),
        sa.Column("recommendation", sa.String(50)),
        sa.Column("confidence", sa.Float),
        # Additional metadata (JSON text)
        sa.Column("extra_metadata", sa.Text),
        # Timestamps
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
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create composite indexes for common query patterns
    op.create_index(
        "ix_audit_execution_time",
        "audit_logs",
        ["execution_id", "timestamp"],
    )
    op.create_index(
        "ix_audit_capability_time",
        "audit_logs",
        ["capability_id", "timestamp"],
    )
    op.create_index(
        "ix_audit_ticker_time",
        "audit_logs",
        ["ticker", "timestamp"],
    )


def downgrade() -> None:
    """Drop audit_logs table."""
    op.drop_index("ix_audit_ticker_time", table_name="audit_logs")
    op.drop_index("ix_audit_capability_time", table_name="audit_logs")
    op.drop_index("ix_audit_execution_time", table_name="audit_logs")
    op.drop_table("audit_logs")
