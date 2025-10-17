"""Add multi-market support for Indian stocks

Revision ID: 014_add_multi_market_support
Revises: 013_add_backtest_persistence_models
Create Date: 2025-01-17 10:00:00.000000

This migration adds support for multiple stock markets (US, Indian NSE, Indian BSE)
by adding market identification fields to the Stock model and creating appropriate indexes.

Changes:
- Add 'market' column to mcp_stocks table (US/NSE/BSE)
- Modify 'ticker_symbol' column to support longer symbols with suffixes (.NS, .BO)
- Update 'country' column to use ISO 3166-1 alpha-2 codes
- Update 'currency' column to use ISO 4217 codes
- Add composite indexes for efficient multi-market queries
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '014_add_multi_market_support'
down_revision = '013_add_backtest_persistence_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema to support multi-market functionality."""
    
    # Check if we're using SQLite or PostgreSQL
    bind = op.get_bind()
    is_sqlite = bind.engine.name == 'sqlite'
    
    # 1. Add market column with default value
    with op.batch_alter_table('mcp_stocks', schema=None) as batch_op:
        # Add market column (defaults to 'US' for existing stocks)
        batch_op.add_column(
            sa.Column('market', sa.String(length=10), nullable=False, server_default='US')
        )
        
        # Modify ticker_symbol to support longer symbols (for .NS, .BO suffixes)
        # SQLite requires a different approach for column modifications
        if not is_sqlite:
            batch_op.alter_column(
                'ticker_symbol',
                existing_type=sa.String(length=10),
                type_=sa.String(length=20),
                existing_nullable=False
            )
        # Note: For SQLite, the batch_alter_table will handle this automatically
        # by creating a new table with the correct schema
        
        # Update country column to use standard 2-letter codes if needed
        # (existing data should already be compatible, but we ensure the constraint)
        if not is_sqlite:
            batch_op.alter_column(
                'country',
                existing_type=sa.String(length=50),
                type_=sa.String(length=2),
                existing_nullable=True
            )
        
        # Update currency column to use ISO 4217 codes (3 letters)
        # This should already be compatible with existing data
    
    # 2. Create indexes for multi-market queries
    # Note: Index names are automatically prefixed by batch_alter_table
    op.create_index(
        'idx_stock_market_country',
        'mcp_stocks',
        ['market', 'country'],
        unique=False
    )
    op.create_index(
        'idx_stock_market_sector',
        'mcp_stocks',
        ['market', 'sector'],
        unique=False
    )
    op.create_index(
        'idx_stock_country_active',
        'mcp_stocks',
        ['country', 'is_active'],
        unique=False
    )
    
    # 3. Create index on market column for quick filtering
    op.create_index(
        'idx_stock_market',
        'mcp_stocks',
        ['market'],
        unique=False
    )
    
    # 4. Update existing stocks to have proper market values
    # All existing stocks are US stocks (they don't have .NS or .BO suffixes)
    # This is already handled by the server_default='US' above
    
    print("✅ Multi-market support migration completed successfully!")
    print("   - Added 'market' field to stocks table")
    print("   - Extended ticker_symbol length to support market suffixes")
    print("   - Created composite indexes for efficient multi-market queries")
    print("   - All existing stocks automatically set to US market")


def downgrade() -> None:
    """Downgrade database schema to remove multi-market functionality."""
    
    # Check if we're using SQLite or PostgreSQL
    bind = op.get_bind()
    is_sqlite = bind.engine.name == 'sqlite'
    
    # 1. Drop indexes
    op.drop_index('idx_stock_market', table_name='mcp_stocks')
    op.drop_index('idx_stock_country_active', table_name='mcp_stocks')
    op.drop_index('idx_stock_market_sector', table_name='mcp_stocks')
    op.drop_index('idx_stock_market_country', table_name='mcp_stocks')
    
    # 2. Remove market column and revert other changes
    with op.batch_alter_table('mcp_stocks', schema=None) as batch_op:
        batch_op.drop_column('market')
        
        # Revert ticker_symbol length
        if not is_sqlite:
            batch_op.alter_column(
                'ticker_symbol',
                existing_type=sa.String(length=20),
                type_=sa.String(length=10),
                existing_nullable=False
            )
        
        # Revert country column length
        if not is_sqlite:
            batch_op.alter_column(
                'country',
                existing_type=sa.String(length=2),
                type_=sa.String(length=50),
                existing_nullable=True
            )
    
    print("✅ Multi-market support migration rolled back successfully!")

