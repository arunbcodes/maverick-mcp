"""
Maverick India Package.

Indian market-specific functionality for Maverick stock analysis.
Supports NSE (.NS) and BSE (.BO) stocks.

Modules:
    - market: Indian market data provider and screening strategies
    - economic: RBI data and exchange rates
    - news: Financial news aggregation from Indian sources
    - concall: Conference call analysis interfaces
"""

# Market Provider and Screening
from maverick_india.market import (
    INDIAN_MARKET_CONFIG,
    IndianMarket,
    IndianMarketDataProvider,
    calculate_circuit_breaker_limits,
    fetch_bse_data,
    fetch_nse_data,
    format_indian_currency,
    get_maverick_bearish_india,
    get_maverick_bullish_india,
    get_nifty50_momentum,
    get_nifty_sector_rotation,
    get_nifty_sectors,
    get_smallcap_breakouts_india,
    get_value_picks_india,
)

# Economic Indicators
from maverick_india.economic import (
    EconomicIndicator,
    ExchangeRateProvider,
    ExchangeRateSource,
    RBIDataProvider,
    convert_currency,
    get_exchange_rate,
    get_indian_economic_data,
)

# News Aggregation
from maverick_india.news import (
    BaseNewsScraper,
    EconomicTimesScraper,
    IndianNewsProvider,
    IndianStockSymbolMapper,
    MoneyControlScraper,
    MultiSourceNewsAggregator,
    NewsArticleStore,
    analyze_stock_sentiment,
    fetch_economic_times_news,
    fetch_moneycontrol_news,
    get_aggregated_news,
    get_indian_stock_news,
    get_stock_sentiment,
)

# Conference Call Analysis
from maverick_india.concall import (
    CompanyIRProvider,
    ConcallProvider,
    ConcallSummarizer,
    HTMLTranscriptLoader,
    NSEProvider,
    PDFTranscriptLoader,
    SentimentAnalyzer,
    TextTranscriptLoader,
    TranscriptFetcher,
    TranscriptLoader,
    TranscriptLoaderFactory,
)

# Aliases for backward compatibility with router expectations
IndianMarketProvider = IndianMarketDataProvider
EconomicIndicatorsProvider = RBIDataProvider


class CurrencyConverter:
    """Currency converter wrapper for INR/USD conversions."""

    async def convert(
        self,
        amount: float,
        from_currency: str = "INR",
        to_currency: str = "USD",
    ) -> dict:
        """Convert between currencies."""
        rate = await get_exchange_rate(from_currency, to_currency)
        return {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "converted": amount * rate,
        }


class IndianMarketScreener:
    """Screener for Indian market stocks."""

    async def get_maverick_bullish(self, limit: int = 20) -> list:
        """Get bullish stocks from Indian market."""
        return await get_maverick_bullish_india(limit=limit)

    async def get_maverick_bearish(self, limit: int = 20) -> list:
        """Get bearish stocks from Indian market."""
        return await get_maverick_bearish_india(limit=limit)

    async def get_momentum(self, limit: int = 20) -> list:
        """Get momentum stocks from Nifty 50."""
        return await get_nifty50_momentum(limit=limit)

    async def get_sector_rotation(self) -> dict:
        """Get sector rotation analysis."""
        return await get_nifty_sector_rotation()

    async def get_value_picks(self, limit: int = 20) -> list:
        """Get value picks from Indian market."""
        return await get_value_picks_india(limit=limit)

    async def get_smallcap_breakouts(self, limit: int = 20) -> list:
        """Get smallcap breakout stocks."""
        return await get_smallcap_breakouts_india(limit=limit)

__all__ = [
    # Market Provider
    "IndianMarket",
    "IndianMarketDataProvider",
    "IndianMarketProvider",  # Alias
    "IndianMarketScreener",
    "INDIAN_MARKET_CONFIG",
    "calculate_circuit_breaker_limits",
    "format_indian_currency",
    "get_nifty_sectors",
    "fetch_nse_data",
    "fetch_bse_data",
    # Screening Strategies
    "get_maverick_bullish_india",
    "get_maverick_bearish_india",
    "get_nifty50_momentum",
    "get_nifty_sector_rotation",
    "get_value_picks_india",
    "get_smallcap_breakouts_india",
    # Economic Indicators
    "RBIDataProvider",
    "EconomicIndicatorsProvider",  # Alias
    "EconomicIndicator",
    "get_indian_economic_data",
    "ExchangeRateProvider",
    "ExchangeRateSource",
    "get_exchange_rate",
    "convert_currency",
    "CurrencyConverter",
    # News Aggregation
    "BaseNewsScraper",
    "NewsArticleStore",
    "IndianStockSymbolMapper",
    "MoneyControlScraper",
    "EconomicTimesScraper",
    "MultiSourceNewsAggregator",
    "IndianNewsProvider",
    "fetch_moneycontrol_news",
    "fetch_economic_times_news",
    "get_aggregated_news",
    "get_stock_sentiment",
    "get_indian_stock_news",
    "analyze_stock_sentiment",
    # Conference Call Analysis
    "ConcallProvider",
    "CompanyIRProvider",
    "NSEProvider",
    "TranscriptFetcher",
    "ConcallSummarizer",
    "SentimentAnalyzer",
    "TranscriptLoader",
    "PDFTranscriptLoader",
    "HTMLTranscriptLoader",
    "TextTranscriptLoader",
    "TranscriptLoaderFactory",
]
