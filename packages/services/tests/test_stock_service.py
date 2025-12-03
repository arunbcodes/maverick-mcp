"""Tests for StockService."""

import pytest
from decimal import Decimal

from maverick_services import StockService, StockNotFoundError
from maverick_schemas.stock import StockQuote, StockHistory, StockInfo


class TestStockService:
    """Tests for StockService."""

    @pytest.fixture
    def service(self, mock_provider, mock_cache):
        return StockService(provider=mock_provider, cache=mock_cache)

    async def test_get_quote_returns_stock_quote(self, service, sample_ticker):
        quote = await service.get_quote(sample_ticker)

        assert isinstance(quote, StockQuote)
        assert quote.ticker == sample_ticker.upper()
        assert quote.price > 0

    async def test_get_quote_caches_result(self, service, mock_cache, sample_ticker):
        await service.get_quote(sample_ticker)

        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert f"quote:{sample_ticker.upper()}" in call_args[0][0]

    async def test_get_quote_uses_cache(self, mock_provider, mock_cache, sample_ticker):
        # Setup cache hit
        mock_cache.get.return_value = {
            "ticker": sample_ticker,
            "price": "150.00",
            "change": "2.50",
            "change_percent": "1.69",
            "volume": 50000000,
            "timestamp": "2024-01-15T10:00:00Z",
        }

        service = StockService(provider=mock_provider, cache=mock_cache)
        quote = await service.get_quote(sample_ticker)

        assert quote.ticker == sample_ticker
        # Provider should not be called when cache hit
        mock_provider.get_stock_data.assert_not_called()

    async def test_get_quote_not_found_raises(self, mock_provider, mock_cache):
        mock_provider.get_stock_data.return_value = None

        service = StockService(provider=mock_provider, cache=mock_cache)

        with pytest.raises(StockNotFoundError):
            await service.get_quote("INVALID")

    async def test_get_history_returns_stock_history(self, service, sample_ticker):
        history = await service.get_history(sample_ticker)

        assert isinstance(history, StockHistory)
        assert history.ticker == sample_ticker.upper()
        assert len(history.data) > 0
        assert history.data_points == len(history.data)

    async def test_get_history_with_date_range(self, service, sample_ticker):
        history = await service.get_history(
            sample_ticker,
            start_date="2024-01-01",
            end_date="2024-03-01",
        )

        assert isinstance(history, StockHistory)
        assert history.start_date is not None
        assert history.end_date is not None

    async def test_get_info_returns_stock_info(self, service, sample_ticker):
        info = await service.get_info(sample_ticker)

        assert isinstance(info, StockInfo)
        assert info.ticker == sample_ticker.upper()
        assert info.name == "Apple Inc."
        assert info.sector == "Technology"

    async def test_get_batch_quotes(self, service):
        tickers = ["AAPL", "MSFT", "GOOGL"]
        response = await service.get_batch_quotes(tickers)

        assert len(response.quotes) == 3
        assert all(t in response.quotes for t in tickers)

