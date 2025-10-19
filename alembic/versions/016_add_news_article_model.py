"""add news article model

Revision ID: 016_add_news_article_model
Revises: 015_add_exchange_rate_model
Create Date: 2025-10-19 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '016_add_news_article_model'
down_revision = '015_add_exchange_rate_model'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create news_articles table for storing financial news with sentiment analysis."""
    
    # Create mcp_news_articles table
    op.create_table(
        'mcp_news_articles',
        sa.Column('article_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('published_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('symbol', sa.String(length=20), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('sentiment', sa.String(length=20), nullable=True),
        sa.Column('sentiment_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('entities', sa.JSON(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('share_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('article_id'),
        sa.UniqueConstraint('url', name='mcp_news_article_url_unique')
    )
    
    # Create indexes for efficient querying
    op.create_index('mcp_news_article_symbol_date_idx', 'mcp_news_articles', ['symbol', 'published_date'])
    op.create_index('mcp_news_article_source_idx', 'mcp_news_articles', ['source'])
    op.create_index('mcp_news_article_sentiment_idx', 'mcp_news_articles', ['sentiment'])
    op.create_index('mcp_news_article_published_idx', 'mcp_news_articles', ['published_date'])
    op.create_index('mcp_news_article_symbol_sentiment_idx', 'mcp_news_articles', ['symbol', 'sentiment'])
    op.create_index('ix_mcp_news_articles_symbol', 'mcp_news_articles', ['symbol'])
    op.create_index('ix_mcp_news_articles_source', 'mcp_news_articles', ['source'])


def downgrade() -> None:
    """Remove news_articles table."""
    
    # Drop indexes
    op.drop_index('ix_mcp_news_articles_source', table_name='mcp_news_articles')
    op.drop_index('ix_mcp_news_articles_symbol', table_name='mcp_news_articles')
    op.drop_index('mcp_news_article_symbol_sentiment_idx', table_name='mcp_news_articles')
    op.drop_index('mcp_news_article_published_idx', table_name='mcp_news_articles')
    op.drop_index('mcp_news_article_sentiment_idx', table_name='mcp_news_articles')
    op.drop_index('mcp_news_article_source_idx', table_name='mcp_news_articles')
    op.drop_index('mcp_news_article_symbol_date_idx', table_name='mcp_news_articles')
    
    # Drop table
    op.drop_table('mcp_news_articles')

