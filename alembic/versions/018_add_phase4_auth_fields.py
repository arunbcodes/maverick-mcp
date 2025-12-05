"""Add Phase 4 authentication and onboarding fields.

Revision ID: 018_phase4_auth
Revises: 017_add_user_apikey
Create Date: 2024-12-05

This migration adds:
- onboarding_completed, is_demo_user, is_admin fields to users
- password_reset_tokens table for password reset flow
- name field to users for profile
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "018_phase4_auth"
down_revision = "017_add_user_apikey"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column(
        "users",
        sa.Column("name", sa.String(100), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "is_demo_user",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )

    # Create password_reset_tokens table
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_password_reset_tokens_user",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "idx_password_reset_token_user",
        "password_reset_tokens",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_password_reset_token_expires",
        "password_reset_tokens",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop password_reset_tokens table
    op.drop_index("idx_password_reset_token_expires", table_name="password_reset_tokens")
    op.drop_index("idx_password_reset_token_user", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")

    # Remove columns from users
    op.drop_column("users", "is_admin")
    op.drop_column("users", "is_demo_user")
    op.drop_column("users", "onboarding_completed")
    op.drop_column("users", "name")

