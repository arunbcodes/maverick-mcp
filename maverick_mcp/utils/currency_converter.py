"""
Currency Converter - INR/USD Conversion

Provides basic currency conversion between INR and USD with fallback to approximate rates.
Can be enhanced with real-time APIs in production.
"""

import logging
from typing import Optional
from datetime import datetime, date
import pandas as pd

logger = logging.getLogger(__name__)


class CurrencyConverter:
    """
    Basic currency converter for INR/USD.
    
    Uses approximate exchange rate with fallback options.
    Can be enhanced with real-time API integration (Exchange Rate API, RBI, etc.)
    """
    
    def __init__(self):
        """Initialize currency converter with approximate rates."""
        # Approximate USD/INR rate (as of late 2024)
        self.default_usd_inr_rate = 83.0
        logger.info("CurrencyConverter initialized with approximate rates")
    
    def get_exchange_rate(
        self,
        from_currency: str = "INR",
        to_currency: str = "USD"
    ) -> float:
        """
        Get current exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code (INR or USD)
            to_currency: Target currency code (INR or USD)
            
        Returns:
            Exchange rate
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return 1.0
        
        if from_currency == "USD" and to_currency == "INR":
            return self.default_usd_inr_rate
        elif from_currency == "INR" and to_currency == "USD":
            return 1.0 / self.default_usd_inr_rate
        else:
            raise ValueError(f"Unsupported currency pair: {from_currency}/{to_currency}")
    
    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> float:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Converted amount
        """
        if amount == 0:
            return 0.0
        
        rate = self.get_exchange_rate(from_currency, to_currency)
        return amount * rate
    
    def get_historical_rates(
        self,
        from_currency: str,
        to_currency: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Get historical exchange rates (placeholder implementation).
        
        In production, this would fetch from:
        - Exchange Rate API
        - RBI official rates
        - Yahoo Finance
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with historical rates
        """
        # Placeholder: return constant rate
        # In production, fetch real historical data
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        rate = self.get_exchange_rate(from_currency, to_currency)
        
        df = pd.DataFrame({
            'date': dates,
            'rate': rate,
            'from_currency': from_currency,
            'to_currency': to_currency
        })
        
        logger.warning("Using approximate constant historical rates. Integrate real API for production.")
        return df
    
    def convert_timeseries(
        self,
        amounts: pd.Series,
        from_currency: str,
        to_currency: str,
        dates: Optional[pd.DatetimeIndex] = None
    ) -> pd.Series:
        """
        Convert a time series of amounts.
        
        Args:
            amounts: Series of amounts to convert
            from_currency: Source currency
            to_currency: Target currency
            dates: Optional dates for historical rates
            
        Returns:
            Converted amounts series
        """
        rate = self.get_exchange_rate(from_currency, to_currency)
        return amounts * rate


def convert_currency(
    amount: float,
    from_currency: str = "INR",
    to_currency: str = "USD"
) -> float:
    """
    Quick function to convert currency.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency (default: INR)
        to_currency: Target currency (default: USD)
        
    Returns:
        Converted amount
    """
    converter = CurrencyConverter()
    return converter.convert(amount, from_currency, to_currency)


__all__ = [
    "CurrencyConverter",
    "convert_currency",
]

