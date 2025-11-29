"""
Comprehensive tests for StockDataFetcher service.

Tests cover:
- Initialization
- Fetching historical stock data
- Fetching stock information
- Real-time data fetching (single and multiple symbols)
- News fetching
- Earnings and recommendations fetching
- ETF detection
- Error handling and edge cases
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Try new package structure first, fall back to legacy
try:
    from maverick_data.services.stock_fetcher import StockDataFetcher
    MODULE_PATH = 'maverick_data.services.stock_fetcher'
except ImportError:
    from maverick_mcp.services.stock_data_fetcher import StockDataFetcher
    MODULE_PATH = 'maverick_mcp.services.stock_data_fetcher'


class TestStockDataFetcherInitialization:
    """Test initialization and setup."""
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_initializes_with_yfinance_pool(self, mock_get_pool):
        """Test that fetcher initializes with yfinance pool."""
        mock_pool = Mock()
        mock_get_pool.return_value = mock_pool
        
        fetcher = StockDataFetcher()
        
        assert fetcher._yf_pool == mock_pool
        mock_get_pool.assert_called_once()
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_logs_initialization(self, mock_get_pool, caplog):
        """Test that initialization is logged."""
        mock_get_pool.return_value = Mock()
        
        StockDataFetcher()
        
        assert "StockDataFetcher initialized" in caplog.text


class TestFetchStockData:
    """Test historical stock data fetching."""
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_fetches_historical_data_successfully(self, mock_get_pool):
        """Test successful historical data fetch."""
        mock_df = pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [102.0, 103.0],
            'Low': [99.0, 100.0],
            'Close': [101.0, 102.0],
            'Volume': [1000000, 1100000]
        }, index=pd.date_range('2024-01-01', periods=2))
        
        mock_pool = Mock()
        mock_pool.get_history.return_value = mock_df
        mock_get_pool.return_value = mock_pool
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_stock_data("AAPL", start_date="2024-01-01", end_date="2024-01-31")
        
        assert not result.empty
        assert len(result) == 2
        assert "Open" in result.columns
        assert result.index.name == "Date"
        mock_pool.get_history.assert_called_once()
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_handles_empty_dataframe(self, mock_get_pool):
        """Test handling of empty DataFrame response."""
        mock_pool = Mock()
        mock_pool.get_history.return_value = pd.DataFrame()
        mock_get_pool.return_value = mock_pool
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_stock_data("INVALID")
        
        assert result.empty
        assert list(result.columns) == ["Open", "High", "Low", "Close", "Volume"]
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_adds_missing_columns(self, mock_get_pool):
        """Test that missing columns are added with default values."""
        # DataFrame missing some columns
        mock_df = pd.DataFrame({
            'Open': [100.0],
            'Close': [101.0]
        }, index=pd.date_range('2024-01-01', periods=1))
        
        mock_pool = Mock()
        mock_pool.get_history.return_value = mock_df
        mock_get_pool.return_value = mock_pool
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_stock_data("AAPL")
        
        assert "High" in result.columns
        assert "Low" in result.columns
        assert "Volume" in result.columns
        assert result["High"].iloc[0] == 0.0
        assert result["Volume"].iloc[0] == 0
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_supports_period_parameter(self, mock_get_pool):
        """Test data fetching with period parameter."""
        mock_df = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1))
        
        mock_pool = Mock()
        mock_pool.get_history.return_value = mock_df
        mock_get_pool.return_value = mock_pool
        
        fetcher = StockDataFetcher()
        fetcher.fetch_stock_data("AAPL", period="1mo")
        
        # Verify period was passed to get_history
        call_kwargs = mock_pool.get_history.call_args.kwargs
        assert call_kwargs.get("period") == "1mo"
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_supports_interval_parameter(self, mock_get_pool):
        """Test data fetching with different intervals."""
        mock_df = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1, freq='5min'))
        
        mock_pool = Mock()
        mock_pool.get_history.return_value = mock_df
        mock_get_pool.return_value = mock_pool
        
        fetcher = StockDataFetcher()
        fetcher.fetch_stock_data("AAPL", period="1d", interval="5m")
        
        # Verify interval was passed
        call_kwargs = mock_pool.get_history.call_args.kwargs
        assert call_kwargs.get("interval") == "5m"


class TestFetchStockInfo:
    """Test stock information fetching."""
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_fetches_stock_info_successfully(self, mock_get_pool):
        """Test successful stock info fetch."""
        mock_info = {
            "symbol": "AAPL",
            "longName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "marketCap": 3000000000000,
            "previousClose": 180.0
        }
        
        mock_pool = Mock()
        mock_pool.get_info.return_value = mock_info
        mock_get_pool.return_value = mock_pool
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_stock_info("AAPL")
        
        assert result == mock_info
        assert result["symbol"] == "AAPL"
        assert result["longName"] == "Apple Inc."
        mock_pool.get_info.assert_called_once_with("AAPL")


class TestFetchRealtimeData:
    """Test real-time data fetching."""
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_fetches_realtime_data_successfully(self, mock_get_pool):
        """Test successful real-time data fetch."""
        mock_df = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-31', periods=1))
        
        mock_info = {"previousClose": 100.0}
        
        mock_pool = Mock()
        mock_pool.get_history.return_value = mock_df
        mock_pool.get_info.return_value = mock_info
        mock_get_pool.return_value = mock_pool
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_realtime_data("AAPL")
        
        assert result is not None
        assert result["symbol"] == "AAPL"
        assert result["price"] == 101.0
        assert result["change"] == 1.0  # 101 - 100
        assert result["change_percent"] == 1.0  # (1/100) * 100
        assert result["volume"] == 1000000
        assert "timestamp" in result
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_handles_missing_previous_close(self, mock_get_pool):
        """Test handling when previousClose is not available."""
        mock_df_2d = pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [102.0, 103.0],
            'Low': [99.0, 100.0],
            'Close': [100.0, 102.0],
            'Volume': [1000000, 1100000]
        }, index=pd.date_range('2024-01-30', periods=2))
        
        mock_pool = Mock()
        # First call returns 1-day data, second call returns 2-day data
        mock_pool.get_history.side_effect = [
            mock_df_2d.tail(1),  # Latest day only
            mock_df_2d  # 2-day history for previous close
        ]
        mock_pool.get_info.return_value = {}  # No previousClose
        mock_get_pool.return_value = mock_pool
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_realtime_data("AAPL")
        
        assert result is not None
        assert result["price"] == 102.0
        assert result["change"] == 2.0  # 102 - 100
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_returns_none_for_empty_data(self, mock_get_pool):
        """Test that None is returned for empty real-time data."""
        mock_pool = Mock()
        mock_pool.get_history.return_value = pd.DataFrame()
        mock_get_pool.return_value = mock_pool
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_realtime_data("INVALID")
        
        assert result is None
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_handles_errors_gracefully(self, mock_get_pool):
        """Test error handling in real-time data fetch."""
        mock_pool = Mock()
        mock_pool.get_history.side_effect = Exception("API error")
        mock_get_pool.return_value = mock_pool
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_realtime_data("AAPL")
        
        assert result is None


class TestFetchMultipleRealtime:
    """Test batch real-time data fetching."""
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_fetches_multiple_symbols(self, mock_get_pool):
        """Test fetching real-time data for multiple symbols."""
        mock_df1 = pd.DataFrame({
            'Close': [100.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-31', periods=1))
        
        mock_df2 = pd.DataFrame({
            'Close': [200.0],
            'Volume': [2000000]
        }, index=pd.date_range('2024-01-31', periods=1))
        
        mock_pool = Mock()
        mock_pool.get_history.side_effect = [mock_df1, mock_df2]
        mock_pool.get_info.return_value = {"previousClose": 100.0}
        mock_get_pool.return_value = mock_pool
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_multiple_realtime(["AAPL", "GOOGL"])
        
        assert len(result) == 2
        assert "AAPL" in result
        assert "GOOGL" in result
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    def test_skips_failed_symbols(self, mock_get_pool):
        """Test that failed symbols are skipped."""
        mock_df = pd.DataFrame({
            'Close': [100.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-31', periods=1))
        
        mock_pool = Mock()
        mock_pool.get_history.side_effect = [mock_df, Exception("Failed")]
        mock_pool.get_info.return_value = {"previousClose": 100.0}
        mock_get_pool.return_value = mock_pool
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_multiple_realtime(["AAPL", "INVALID"])
        
        # Only AAPL should be in results
        assert len(result) == 1
        assert "AAPL" in result
        assert "INVALID" not in result


class TestFetchNews:
    """Test news fetching."""
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_fetches_news_successfully(self, mock_ticker_class, mock_get_pool):
        """Test successful news fetch."""
        mock_news = [
            {
                "title": "Apple releases new product",
                "publisher": "TechNews",
                "link": "https://example.com/news1",
                "providerPublishTime": 1704067200,  # Unix timestamp
                "type": "NEWS"
            },
            {
                "title": "Apple stock rises",
                "publisher": "FinanceDaily",
                "link": "https://example.com/news2",
                "providerPublishTime": 1704153600,
                "type": "NEWS"
            }
        ]
        
        mock_ticker = Mock()
        mock_ticker.news = mock_news
        mock_ticker_class.return_value = mock_ticker
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_news("AAPL", limit=10)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "title" in result.columns
        assert "publisher" in result.columns
        assert result.iloc[0]["title"] == "Apple releases new product"
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_handles_no_news_available(self, mock_ticker_class, mock_get_pool):
        """Test handling when no news is available."""
        mock_ticker = Mock()
        mock_ticker.news = []
        mock_ticker_class.return_value = mock_ticker
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_news("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert result.empty
        assert "title" in result.columns
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_respects_limit_parameter(self, mock_ticker_class, mock_get_pool):
        """Test that limit parameter is respected."""
        mock_news = [
            {"title": f"News {i}", "publisher": "Publisher", "link": "url", 
             "providerPublishTime": 1704067200 + i, "type": "NEWS"}
            for i in range(20)
        ]
        
        mock_ticker = Mock()
        mock_ticker.news = mock_news
        mock_ticker_class.return_value = mock_ticker
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_news("AAPL", limit=5)
        
        assert len(result) == 5
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_handles_errors_gracefully(self, mock_ticker_class, mock_get_pool):
        """Test error handling in news fetch."""
        mock_ticker_class.side_effect = Exception("API error")
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_news("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert result.empty


class TestFetchEarnings:
    """Test earnings data fetching."""
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_fetches_earnings_successfully(self, mock_ticker_class, mock_get_pool):
        """Test successful earnings fetch."""
        mock_earnings = pd.DataFrame({"Earnings": [1.5, 1.7]})
        mock_earnings_dates = pd.DataFrame({"Date": ["2024-01-01", "2024-04-01"]})
        
        mock_ticker = Mock()
        mock_ticker.earnings = mock_earnings
        mock_ticker.earnings_dates = mock_earnings_dates
        mock_ticker.earnings_trend = {"trend": "positive"}
        mock_ticker_class.return_value = mock_ticker
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_earnings("AAPL")
        
        assert "earnings" in result
        assert "earnings_dates" in result
        assert "earnings_trend" in result
        assert result["earnings_trend"] == {"trend": "positive"}
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_handles_missing_earnings_data(self, mock_ticker_class, mock_get_pool):
        """Test handling when earnings data is missing."""
        mock_ticker = Mock()
        mock_ticker.earnings = pd.DataFrame()
        mock_ticker.earnings_dates = pd.DataFrame()
        del mock_ticker.earnings_trend  # Attribute doesn't exist
        mock_ticker_class.return_value = mock_ticker
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_earnings("AAPL")
        
        assert result["earnings"] == {}
        assert result["earnings_dates"] == {}
        assert result["earnings_trend"] == {}
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_handles_errors_gracefully(self, mock_ticker_class, mock_get_pool):
        """Test error handling in earnings fetch."""
        mock_ticker_class.side_effect = Exception("API error")
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_earnings("AAPL")
        
        assert result == {"earnings": {}, "earnings_dates": {}, "earnings_trend": {}}


class TestFetchRecommendations:
    """Test analyst recommendations fetching."""
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_fetches_recommendations_successfully(self, mock_ticker_class, mock_get_pool):
        """Test successful recommendations fetch."""
        mock_recommendations = pd.DataFrame({
            "firm": ["Goldman Sachs", "Morgan Stanley"],
            "toGrade": ["Buy", "Hold"],
            "fromGrade": ["Hold", "Sell"],
            "action": ["upgrade", "upgrade"]
        })
        
        mock_ticker = Mock()
        mock_ticker.recommendations = mock_recommendations
        mock_ticker_class.return_value = mock_ticker
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_recommendations("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "firm" in result.columns
        assert result.iloc[0]["firm"] == "Goldman Sachs"
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_handles_no_recommendations(self, mock_ticker_class, mock_get_pool):
        """Test handling when no recommendations are available."""
        mock_ticker = Mock()
        mock_ticker.recommendations = None
        mock_ticker_class.return_value = mock_ticker
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_recommendations("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert result.empty
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_handles_errors_gracefully(self, mock_ticker_class, mock_get_pool):
        """Test error handling in recommendations fetch."""
        mock_ticker_class.side_effect = Exception("API error")
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.fetch_recommendations("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert result.empty


class TestIsETF:
    """Test ETF detection."""
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_detects_etf_from_quote_type(self, mock_ticker_class, mock_get_pool):
        """Test ETF detection from quoteType field."""
        mock_ticker = Mock()
        mock_ticker.info = {"quoteType": "ETF"}
        mock_ticker_class.return_value = mock_ticker
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.is_etf("SPY")
        
        assert result is True
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_detects_common_etf_symbols(self, mock_ticker_class, mock_get_pool):
        """Test ETF detection for common ETF symbols."""
        mock_ticker = Mock()
        mock_ticker.info = {}  # No quoteType
        mock_ticker_class.return_value = mock_ticker
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        
        # Test common ETF symbols
        assert fetcher.is_etf("SPY") is True
        assert fetcher.is_etf("QQQ") is True
        assert fetcher.is_etf("XLF") is True
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_detects_etf_from_name(self, mock_ticker_class, mock_get_pool):
        """Test ETF detection from long name."""
        mock_ticker = Mock()
        mock_ticker.info = {"longName": "Vanguard Total Stock Market ETF"}
        mock_ticker_class.return_value = mock_ticker
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.is_etf("VTI")
        
        assert result is True
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_returns_false_for_regular_stock(self, mock_ticker_class, mock_get_pool):
        """Test that regular stocks are not detected as ETFs."""
        mock_ticker = Mock()
        mock_ticker.info = {"quoteType": "EQUITY", "longName": "Apple Inc."}
        mock_ticker_class.return_value = mock_ticker
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.is_etf("AAPL")
        
        assert result is False
    
    @patch(f'{MODULE_PATH}.get_yfinance_pool')
    @patch(f'{MODULE_PATH}.yf.Ticker')
    def test_handles_errors_gracefully(self, mock_ticker_class, mock_get_pool):
        """Test error handling in ETF detection."""
        mock_ticker_class.side_effect = Exception("API error")
        mock_get_pool.return_value = Mock()
        
        fetcher = StockDataFetcher()
        result = fetcher.is_etf("AAPL")
        
        assert result is False


# Note: These are unit tests with mocked yfinance dependencies

