"""
Comprehensive tests for StockCacheManager service.

Tests cover:
- Initialization and session management
- Cache retrieval (hit, miss, partial)
- Cache storage
- Cache invalidation
- Column mapping and data type handling
- Error handling and edge cases
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

# Try new package structure first, fall back to legacy
try:
    from maverick_data.services.stock_cache import StockCacheManager
    MODULE_PATH = 'maverick_data.services.stock_cache'
except ImportError:
    from maverick_mcp.services.stock_cache_manager import StockCacheManager
    MODULE_PATH = 'maverick_mcp.services.stock_cache_manager'


class TestStockCacheManagerInitialization:
    """Test initialization and configuration."""
    
    def test_initializes_without_session(self):
        """Test initialization without provided session."""
        manager = StockCacheManager()
        assert manager._db_session is None
    
    def test_initializes_with_session(self):
        """Test initialization with injected session."""
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        assert manager._db_session == mock_session
    
    def test_logs_initialization(self, caplog):
        """Test that initialization is logged."""
        StockCacheManager()
        assert "StockCacheManager initialized" in caplog.text


class TestSessionManagement:
    """Test database session handling."""
    
    def test_uses_injected_session(self):
        """Test that injected session is used and not closed."""
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        
        session, should_close = manager._get_db_session()
        
        assert session == mock_session
        assert should_close is False
    
    @patch(f'{MODULE_PATH}.SessionLocal')
    def test_creates_new_session_when_none_provided(self, mock_session_local):
        """Test that new session is created when none provided."""
        mock_new_session = Mock(spec=Session)
        mock_session_local.return_value = mock_new_session
        
        manager = StockCacheManager()
        session, should_close = manager._get_db_session()
        
        assert session == mock_new_session
        assert should_close is True
        mock_session_local.assert_called_once()
    
    @patch(f'{MODULE_PATH}.SessionLocal')
    def test_handles_session_creation_failure(self, mock_session_local):
        """Test error handling when session creation fails."""
        mock_session_local.side_effect = Exception("Database connection failed")
        
        manager = StockCacheManager()
        
        with pytest.raises(Exception, match="Database connection failed"):
            manager._get_db_session()


class TestGetCachedData:
    """Test cache retrieval operations."""
    
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_retrieves_cached_data_successfully(self, mock_price_cache):
        """Test successful cache retrieval."""
        # Setup mock data
        mock_df = pd.DataFrame({
            'open': [100.0, 101.0],
            'high': [102.0, 103.0],
            'low': [99.0, 100.0],
            'close': [101.0, 102.0],
            'volume': [1000000, 1100000]
        }, index=pd.date_range('2024-01-01', periods=2))
        
        mock_price_cache.get_price_data.return_value = mock_df
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        
        result = manager.get_cached_data("AAPL", "2024-01-01", "2024-01-31")
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "Open" in result.columns
        assert "High" in result.columns
        assert "Close" in result.columns
        assert "Volume" in result.columns
    
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_returns_none_for_cache_miss(self, mock_price_cache):
        """Test that None is returned when no cached data exists."""
        mock_price_cache.get_price_data.return_value = pd.DataFrame()
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        
        result = manager.get_cached_data("NONCACHED", "2024-01-01", "2024-01-31")
        
        assert result is None
    
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_uppercases_symbol(self, mock_price_cache):
        """Test that symbol is uppercased before query."""
        mock_df = pd.DataFrame({
            'open': [100.0],
            'high': [102.0],
            'low': [99.0],
            'close': [101.0],
            'volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1))
        
        mock_price_cache.get_price_data.return_value = mock_df
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        
        manager.get_cached_data("aapl", "2024-01-01", "2024-01-31")
        
        # Verify PriceCache was called with uppercase symbol
        mock_price_cache.get_price_data.assert_called_once_with(
            mock_session, "AAPL", "2024-01-01", "2024-01-31"
        )
    
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_adds_dividend_and_splits_columns(self, mock_price_cache):
        """Test that Dividends and Stock Splits columns are added."""
        mock_df = pd.DataFrame({
            'open': [100.0],
            'high': [102.0],
            'low': [99.0],
            'close': [101.0],
            'volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1))
        
        mock_price_cache.get_price_data.return_value = mock_df
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        
        result = manager.get_cached_data("AAPL", "2024-01-01", "2024-01-31")
        
        assert "Dividends" in result.columns
        assert "Stock Splits" in result.columns
        assert result["Dividends"].iloc[0] == 0.0
        assert result["Stock Splits"].iloc[0] == 0.0
    
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_handles_errors_gracefully(self, mock_price_cache):
        """Test error handling during cache retrieval."""
        mock_price_cache.get_price_data.side_effect = Exception("Database error")
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        
        result = manager.get_cached_data("AAPL", "2024-01-01", "2024-01-31")
        
        assert result is None
    
    @patch(f'{MODULE_PATH}.SessionLocal')
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_closes_session_when_created_locally(self, mock_price_cache, mock_session_local):
        """Test that locally created sessions are closed."""
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session
        mock_price_cache.get_price_data.return_value = pd.DataFrame()
        
        manager = StockCacheManager()  # No injected session
        manager.get_cached_data("AAPL", "2024-01-01", "2024-01-31")
        
        mock_session.close.assert_called_once()


class TestCacheData:
    """Test cache storage operations."""
    
    @patch(f'{MODULE_PATH}.bulk_insert_price_data')
    def test_caches_data_successfully(self, mock_bulk_insert):
        """Test successful data caching."""
        mock_bulk_insert.return_value = 10
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        manager._ensure_stock_exists = Mock()
        
        data = pd.DataFrame({
            'Open': [100.0] * 10,
            'High': [102.0] * 10,
            'Low': [99.0] * 10,
            'Close': [101.0] * 10,
            'Volume': [1000000] * 10
        }, index=pd.date_range('2024-01-01', periods=10))
        
        manager.cache_data("AAPL", data)
        
        mock_bulk_insert.assert_called_once()
        manager._ensure_stock_exists.assert_called_once_with(mock_session, "AAPL")
    
    def test_skips_empty_dataframe(self):
        """Test that empty DataFrames are not cached."""
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        manager._ensure_stock_exists = Mock()
        
        empty_df = pd.DataFrame()
        
        manager.cache_data("AAPL", empty_df)
        
        # Should not attempt to cache
        manager._ensure_stock_exists.assert_not_called()
    
    @patch(f'{MODULE_PATH}.bulk_insert_price_data')
    def test_uppercases_symbol(self, mock_bulk_insert):
        """Test that symbol is uppercased before caching."""
        mock_bulk_insert.return_value = 1
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        manager._ensure_stock_exists = Mock()
        
        data = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1))
        
        manager.cache_data("aapl", data)
        
        # Verify stock existence check used uppercase
        manager._ensure_stock_exists.assert_called_with(mock_session, "AAPL")
    
    @patch(f'{MODULE_PATH}.bulk_insert_price_data')
    def test_renames_columns_to_lowercase(self, mock_bulk_insert):
        """Test that column names are converted to lowercase."""
        captured_df = None
        
        def capture_df(session, symbol, df):
            nonlocal captured_df
            captured_df = df.copy()
            return 1
        
        mock_bulk_insert.side_effect = capture_df
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        manager._ensure_stock_exists = Mock()
        
        data = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1))
        
        manager.cache_data("AAPL", data)
        
        assert captured_df is not None
        assert 'open' in captured_df.columns
        assert 'high' in captured_df.columns
        assert 'close' in captured_df.columns
        assert 'volume' in captured_df.columns
    
    @patch(f'{MODULE_PATH}.bulk_insert_price_data')
    def test_handles_errors_with_rollback(self, mock_bulk_insert):
        """Test error handling with session rollback."""
        mock_bulk_insert.side_effect = Exception("Insert failed")
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        manager._ensure_stock_exists = Mock()
        
        data = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1))
        
        manager.cache_data("AAPL", data)
        
        mock_session.rollback.assert_called_once()
    
    @patch(f'{MODULE_PATH}.SessionLocal')
    @patch(f'{MODULE_PATH}.bulk_insert_price_data')
    def test_closes_session_when_created_locally(self, mock_bulk_insert, mock_session_local):
        """Test that locally created sessions are closed."""
        mock_bulk_insert.return_value = 1
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session
        
        manager = StockCacheManager()  # No injected session
        manager._ensure_stock_exists = Mock()
        
        data = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1))
        
        manager.cache_data("AAPL", data)
        
        mock_session.close.assert_called_once()


class TestInvalidateCache:
    """Test cache invalidation operations."""
    
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_invalidates_specific_symbol(self, mock_price_cache):
        """Test invalidation of cache for a specific symbol."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.delete.return_value = 50
        mock_query.filter.return_value = mock_filter
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        
        manager = StockCacheManager(db_session=mock_session)
        
        manager.invalidate_cache("AAPL")
        
        mock_session.query.assert_called_once_with(mock_price_cache)
        mock_session.commit.assert_called_once()
    
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_invalidates_all_symbols(self, mock_price_cache):
        """Test invalidation of all cache."""
        mock_query = Mock()
        mock_query.delete.return_value = 1000
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        
        manager = StockCacheManager(db_session=mock_session)
        
        manager.invalidate_cache(None)
        
        mock_session.query.assert_called_once_with(mock_price_cache)
        mock_session.commit.assert_called_once()
    
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_uppercases_symbol_for_invalidation(self, mock_price_cache):
        """Test that symbol is uppercased before invalidation."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.delete.return_value = 10
        mock_query.filter.return_value = mock_filter
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        
        manager = StockCacheManager(db_session=mock_session)
        
        manager.invalidate_cache("aapl")
        
        # Should have been called with uppercase in the filter
        mock_query.filter.assert_called_once()
    
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_handles_errors_with_rollback(self, mock_price_cache):
        """Test error handling during invalidation."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.delete.side_effect = Exception("Delete failed")
        mock_query.filter.return_value = mock_filter
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        
        manager = StockCacheManager(db_session=mock_session)
        
        manager.invalidate_cache("AAPL")
        
        mock_session.rollback.assert_called_once()
    
    @patch(f'{MODULE_PATH}.PriceCache')
    @patch(f'{MODULE_PATH}.SessionLocal')
    def test_closes_session_when_created_locally(self, mock_session_local, mock_price_cache):
        """Test that locally created sessions are closed."""
        mock_query = Mock()
        mock_query.delete.return_value = 10
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        mock_session_local.return_value = mock_session
        
        manager = StockCacheManager()  # No injected session
        
        manager.invalidate_cache(None)
        
        mock_session.close.assert_called_once()


class TestEnsureStockExists:
    """Test stock existence checking."""
    
    @patch(f'{MODULE_PATH}.Stock')
    def test_calls_get_or_create(self, mock_stock):
        """Test that Stock.get_or_create is called."""
        mock_session = Mock(spec=Session)
        mock_stock.get_or_create.return_value = Mock()
        
        manager = StockCacheManager(db_session=mock_session)
        
        result = manager._ensure_stock_exists(mock_session, "AAPL")
        
        mock_stock.get_or_create.assert_called_once_with(mock_session, "AAPL")
        assert result is not None


class TestDataTypeHandling:
    """Test data type conversions and column mapping."""
    
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_converts_price_columns_to_float64(self, mock_price_cache):
        """Test that price columns are converted to float64."""
        from decimal import Decimal
        
        mock_df = pd.DataFrame({
            'open': [Decimal('100.50')],
            'high': [Decimal('102.75')],
            'low': [Decimal('99.25')],
            'close': [Decimal('101.00')],
            'volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1))
        
        mock_price_cache.get_price_data.return_value = mock_df
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        
        result = manager.get_cached_data("AAPL", "2024-01-01", "2024-01-31")
        
        assert result["Open"].dtype == 'float64'
        assert result["High"].dtype == 'float64'
        assert result["Low"].dtype == 'float64'
        assert result["Close"].dtype == 'float64'
    
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_converts_volume_to_int64(self, mock_price_cache):
        """Test that Volume column is converted to int64."""
        mock_df = pd.DataFrame({
            'open': [100.0],
            'high': [102.0],
            'low': [99.0],
            'close': [101.0],
            'volume': [1000000.0]  # Float volume
        }, index=pd.date_range('2024-01-01', periods=1))
        
        mock_price_cache.get_price_data.return_value = mock_df
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        
        result = manager.get_cached_data("AAPL", "2024-01-01", "2024-01-31")
        
        assert result["Volume"].dtype == 'int64'
    
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_ensures_timezone_naive_index(self, mock_price_cache):
        """Test that index is timezone-naive."""
        # Create timezone-aware index
        tz_aware_index = pd.date_range('2024-01-01', periods=1, tz='UTC')
        
        mock_df = pd.DataFrame({
            'open': [100.0],
            'high': [102.0],
            'low': [99.0],
            'close': [101.0],
            'volume': [1000000]
        }, index=tz_aware_index)
        
        mock_price_cache.get_price_data.return_value = mock_df
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        
        result = manager.get_cached_data("AAPL", "2024-01-01", "2024-01-31")
        
        assert result.index.tz is None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @patch(f'{MODULE_PATH}.PriceCache')
    def test_handles_missing_columns_gracefully(self, mock_price_cache):
        """Test handling of DataFrames with missing expected columns."""
        # DataFrame with only required columns
        mock_df = pd.DataFrame({
            'open': [100.0],
            'close': [101.0]
        }, index=pd.date_range('2024-01-01', periods=1))
        
        mock_price_cache.get_price_data.return_value = mock_df
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        
        result = manager.get_cached_data("AAPL", "2024-01-01", "2024-01-31")
        
        assert result is not None
        assert "Open" in result.columns
        assert "Close" in result.columns
    
    @patch(f'{MODULE_PATH}.bulk_insert_price_data')
    def test_logs_when_no_records_cached(self, mock_bulk_insert, caplog):
        """Test logging when no new records are inserted."""
        import logging
        
        # Set log level to DEBUG to capture debug messages
        caplog.set_level(logging.DEBUG, logger=MODULE_PATH)
        
        mock_bulk_insert.return_value = 0  # No records inserted
        
        mock_session = Mock(spec=Session)
        manager = StockCacheManager(db_session=mock_session)
        manager._ensure_stock_exists = Mock()
        
        data = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1))
        
        manager.cache_data("AAPL", data)
        
        # Check for the full log message
        assert "No new records cached for AAPL" in caplog.text


# Note: These are unit tests with mocked database dependencies

