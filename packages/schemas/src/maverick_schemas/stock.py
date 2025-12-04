"""
Stock and market data models.

Models for stock quotes, historical data, and market information.
"""

from datetime import date as Date, datetime as DateTime
from decimal import Decimal

from pydantic import Field

from maverick_schemas.base import Market, MaverickBaseModel


class StockQuote(MaverickBaseModel):
    """Real-time stock quote."""
    
    ticker: str = Field(description="Stock ticker symbol")
    price: Decimal = Field(description="Current price")
    change: Decimal = Field(description="Price change from previous close")
    change_percent: Decimal = Field(description="Percentage change")
    volume: int = Field(description="Trading volume")
    timestamp: DateTime = Field(description="Quote timestamp")
    
    # Optional fields for detailed quotes
    open: Decimal | None = Field(default=None, description="Opening price")
    high: Decimal | None = Field(default=None, description="Day high")
    low: Decimal | None = Field(default=None, description="Day low")
    previous_close: Decimal | None = Field(default=None, description="Previous close")
    bid: Decimal | None = Field(default=None, description="Bid price")
    ask: Decimal | None = Field(default=None, description="Ask price")


class StockInfo(MaverickBaseModel):
    """Stock company information."""
    
    ticker: str = Field(description="Stock ticker symbol")
    name: str = Field(description="Company name")
    market: Market = Field(description="Market (US, NSE, BSE)")
    sector: str | None = Field(default=None, description="Business sector")
    industry: str | None = Field(default=None, description="Industry classification")
    
    # Valuation metrics
    market_cap: Decimal | None = Field(default=None, description="Market capitalization")
    pe_ratio: Decimal | None = Field(default=None, description="Price-to-earnings ratio")
    forward_pe: Decimal | None = Field(default=None, description="Forward P/E ratio")
    peg_ratio: Decimal | None = Field(default=None, description="PEG ratio")
    price_to_book: Decimal | None = Field(default=None, description="Price-to-book ratio")
    
    # Dividend info
    dividend_yield: Decimal | None = Field(default=None, description="Dividend yield")
    dividend_rate: Decimal | None = Field(default=None, description="Annual dividend rate")
    
    # Trading info
    avg_volume: int | None = Field(default=None, description="Average trading volume")
    fifty_two_week_high: Decimal | None = Field(default=None, description="52-week high")
    fifty_two_week_low: Decimal | None = Field(default=None, description="52-week low")
    
    # Company details
    description: str | None = Field(default=None, description="Company description")
    website: str | None = Field(default=None, description="Company website")
    employees: int | None = Field(default=None, description="Number of employees")


class OHLCV(MaverickBaseModel):
    """Single OHLCV (Open, High, Low, Close, Volume) data point."""
    
    date: Date = Field(description="Trading date")
    open: Decimal = Field(description="Opening price")
    high: Decimal = Field(description="High price")
    low: Decimal = Field(description="Low price")
    close: Decimal = Field(description="Closing price")
    volume: int = Field(description="Trading volume")
    
    # Optional adjusted prices
    adj_close: Decimal | None = Field(default=None, description="Adjusted close price")


class StockHistory(MaverickBaseModel):
    """Historical stock data."""
    
    ticker: str = Field(description="Stock ticker symbol")
    data: list[OHLCV] = Field(description="Historical OHLCV data")
    start_date: Date = Field(description="Start date of data range")
    end_date: Date = Field(description="End date of data range")
    data_points: int = Field(description="Number of data points")
    interval: str = Field(default="1d", description="Data interval")


class BatchQuoteRequest(MaverickBaseModel):
    """Request for batch stock quotes."""
    
    tickers: list[str] = Field(
        min_length=1,
        max_length=50,
        description="List of ticker symbols"
    )
    fields: list[str] | None = Field(
        default=None,
        description="Specific fields to return (for bandwidth optimization)"
    )


class BatchQuoteResponse(MaverickBaseModel):
    """Response for batch stock quotes."""
    
    quotes: dict[str, StockQuote] = Field(description="Quotes by ticker")
    errors: dict[str, str] = Field(
        default_factory=dict,
        description="Errors by ticker"
    )


class StockSearchResult(MaverickBaseModel):
    """Stock search result."""
    
    ticker: str = Field(description="Stock ticker symbol")
    name: str = Field(description="Company name")
    market: Market = Field(description="Market")
    exchange: str | None = Field(default=None, description="Exchange name")


__all__ = [
    "StockQuote",
    "StockInfo",
    "OHLCV",
    "StockHistory",
    "BatchQuoteRequest",
    "BatchQuoteResponse",
    "StockSearchResult",
]

