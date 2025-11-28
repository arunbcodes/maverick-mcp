"""
Indian Economic Indicators.

RBI data integration including policy rates, GDP, inflation, and forex reserves.
Also provides exchange rate functionality for INR/USD and other currency pairs.
"""

from maverick_india.economic.exchange_rate import (
    ExchangeRateProvider,
    ExchangeRateSource,
    convert_currency,
    get_exchange_rate,
)
from maverick_india.economic.rbi import (
    EconomicIndicator,
    RBIDataProvider,
    get_indian_economic_data,
)

__all__ = [
    # RBI Data Provider
    "RBIDataProvider",
    "EconomicIndicator",
    "get_indian_economic_data",
    # Exchange Rate Provider
    "ExchangeRateProvider",
    "ExchangeRateSource",
    "get_exchange_rate",
    "convert_currency",
]
