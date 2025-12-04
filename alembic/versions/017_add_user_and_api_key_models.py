"""Add User and APIKey models for authentication.

Revision ID: 017_add_user_apikey
Revises: 016_add_news_article_model
Create Date: 2024-12-04

This migration adds:
- users table for authentication
- api_keys table for programmatic access
- Updates mcp_portfolios to add owner_id foreign key
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "017_add_user_apikey"
down_revision = None  # Will be set dynamically based on existing heads
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("idx_user_email", "users", ["email"], unique=False)
    op.create_index("idx_user_active", "users", ["is_active"], unique=False)
    op.create_index("idx_user_tier", "users", ["tier"], unique=False)

    # Create api_keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("key_prefix", sa.String(20), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("rate_limit", sa.Integer(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_api_keys_user", ondelete="CASCADE"
        ),
        sa.UniqueConstraint("key_prefix", name="uq_api_keys_prefix"),
    )
    op.create_index("idx_api_key_user", "api_keys", ["user_id"], unique=False)
    op.create_index("idx_api_key_prefix", "api_keys", ["key_prefix"], unique=False)
    op.create_index("idx_api_key_active", "api_keys", ["is_active"], unique=False)
    op.create_index("idx_api_key_expires", "api_keys", ["expires_at"], unique=False)

    # Add owner_id to mcp_portfolios (nullable for backward compatibility)
    op.add_column(
        "mcp_portfolios",
        sa.Column("owner_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_mcp_portfolios_owner",
        "mcp_portfolios",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("idx_portfolio_owner", "mcp_portfolios", ["owner_id"], unique=False)


def downgrade() -> None:
    # Remove owner_id from mcp_portfolios
    op.drop_index("idx_portfolio_owner", table_name="mcp_portfolios")
    op.drop_constraint("fk_mcp_portfolios_owner", "mcp_portfolios", type_="foreignkey")
    op.drop_column("mcp_portfolios", "owner_id")

    # Drop api_keys table
    op.drop_index("idx_api_key_expires", table_name="api_keys")
    op.drop_index("idx_api_key_active", table_name="api_keys")
    op.drop_index("idx_api_key_prefix", table_name="api_keys")
    op.drop_index("idx_api_key_user", table_name="api_keys")
    op.drop_table("api_keys")

    # Drop users table
    op.drop_index("idx_user_tier", table_name="users")
    op.drop_index("idx_user_active", table_name="users")
    op.drop_index("idx_user_email", table_name="users")
    op.drop_table("users")

