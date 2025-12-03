"""Tests for TechnicalService."""

import pytest
from decimal import Decimal

from maverick_services.technical_service import TechnicalService
from maverick_services.exceptions import StockNotFoundError, InsufficientDataError
from maverick_schemas.technical import (
    RSIAnalysis,
    MACDAnalysis,
    BollingerBands,
    MovingAverages,
    TechnicalSummary,
)


class TestTechnicalService:
    """Tests for TechnicalService."""

    @pytest.fixture
    def service(self, mock_provider):
        return TechnicalService(provider=mock_provider)

    async def test_get_rsi_returns_analysis(self, service, sample_ticker):
        rsi = await service.get_rsi(sample_ticker)

        assert isinstance(rsi, RSIAnalysis)
        assert rsi.ticker == sample_ticker.upper()
        assert 0 <= float(rsi.current_rsi) <= 100
        assert rsi.signal in ["oversold", "neutral", "overbought"]

    async def test_get_rsi_with_custom_period(self, service, sample_ticker):
        rsi = await service.get_rsi(sample_ticker, period=21)

        assert rsi.period == 21

    async def test_get_macd_returns_analysis(self, service, sample_ticker):
        macd = await service.get_macd(sample_ticker)

        assert isinstance(macd, MACDAnalysis)
        assert macd.ticker == sample_ticker.upper()
        assert macd.macd_line is not None
        assert macd.signal_line is not None
        assert macd.histogram is not None

    async def test_get_macd_with_custom_periods(self, service, sample_ticker):
        macd = await service.get_macd(
            sample_ticker,
            fast_period=8,
            slow_period=21,
            signal_period=5,
        )

        assert macd.fast_period == 8
        assert macd.slow_period == 21
        assert macd.signal_period == 5

    async def test_get_bollinger_returns_bands(self, service, sample_ticker):
        bb = await service.get_bollinger(sample_ticker)

        assert isinstance(bb, BollingerBands)
        assert bb.ticker == sample_ticker.upper()
        assert bb.upper_band > bb.middle_band > bb.lower_band
        assert bb.percent_b is not None
        assert bb.bandwidth is not None

    async def test_get_moving_averages_returns_averages(self, service, sample_ticker):
        ma = await service.get_moving_averages(sample_ticker)

        assert isinstance(ma, MovingAverages)
        assert ma.ticker == sample_ticker.upper()
        assert ma.current_price is not None
        assert ma.sma_20 is not None
        assert ma.sma_50 is not None

    async def test_get_summary_returns_complete_analysis(self, service, sample_ticker):
        summary = await service.get_summary(sample_ticker)

        assert isinstance(summary, TechnicalSummary)
        assert summary.ticker == sample_ticker.upper()
        assert summary.rsi is not None
        assert summary.macd is not None
        assert summary.bollinger is not None
        assert summary.moving_averages is not None
        assert summary.recommendation in [
            "strong_buy",
            "buy",
            "hold",
            "sell",
            "strong_sell",
        ]

    async def test_get_rsi_insufficient_data_raises(self, mock_provider):
        # Return only 10 data points
        import pandas as pd

        mock_provider.get_stock_data.return_value = pd.DataFrame(
            {
                "Open": [150.0] * 10,
                "High": [152.0] * 10,
                "Low": [148.0] * 10,
                "Close": [151.0] * 10,
                "Volume": [50000000] * 10,
            },
            index=pd.date_range(start="2024-01-01", periods=10, freq="D"),
        )

        service = TechnicalService(provider=mock_provider)

        with pytest.raises(InsufficientDataError):
            await service.get_rsi("AAPL", period=14)

    async def test_get_technical_not_found_raises(self, mock_provider):
        mock_provider.get_stock_data.return_value = None

        service = TechnicalService(provider=mock_provider)

        with pytest.raises(StockNotFoundError):
            await service.get_rsi("INVALID")

