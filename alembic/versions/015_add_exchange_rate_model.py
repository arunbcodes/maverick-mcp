"""add exchange rate model

Revision ID: 015_add_exchange_rate_model
Revises: 014_add_multi_market_support
Create Date: 2025-10-19 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '015_add_exchange_rate_model'
down_revision = '014_add_multi_market_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create exchange_rates table for storing historical currency exchange rates."""
    
    # Create mcp_exchange_rates table
    op.create_table(
        'mcp_exchange_rates',
        sa.Column('rate_id', sa.Uuid(), nullable=False),
        sa.Column('from_currency', sa.String(length=3), nullable=False),
        sa.Column('to_currency', sa.String(length=3), nullable=False),
        sa.Column('rate', sa.Numeric(precision=15, scale=6), nullable=False),
        sa.Column('rate_date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('provider_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('rate_id'),
        sa.UniqueConstraint('from_currency', 'to_currency', 'rate_date', name='mcp_exchange_rate_unique')
    )
    
    # Create indexes for efficient querying
    op.create_index('mcp_exchange_rate_currencies_date_idx', 'mcp_exchange_rates', ['from_currency', 'to_currency', 'rate_date'])
    op.create_index('mcp_exchange_rate_date_idx', 'mcp_exchange_rates', ['rate_date'])
    op.create_index('mcp_exchange_rate_source_idx', 'mcp_exchange_rates', ['source'])
    op.create_index('ix_mcp_exchange_rates_from_currency', 'mcp_exchange_rates', ['from_currency'])
    op.create_index('ix_mcp_exchange_rates_to_currency', 'mcp_exchange_rates', ['to_currency'])


def downgrade() -> None:
    """Remove exchange_rates table."""
    
    # Drop indexes
    op.drop_index('ix_mcp_exchange_rates_to_currency', table_name='mcp_exchange_rates')
    op.drop_index('ix_mcp_exchange_rates_from_currency', table_name='mcp_exchange_rates')
    op.drop_index('mcp_exchange_rate_source_idx', table_name='mcp_exchange_rates')
    op.drop_index('mcp_exchange_rate_date_idx', table_name='mcp_exchange_rates')
    op.drop_index('mcp_exchange_rate_currencies_date_idx', table_name='mcp_exchange_rates')
    
    # Drop table
    op.drop_table('mcp_exchange_rates')

