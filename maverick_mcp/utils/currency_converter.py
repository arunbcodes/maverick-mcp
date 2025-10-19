"""
Currency Converter - INR/USD Conversion

Provides currency conversion between INR and USD with real-time rates.

Now supports:
- Real-time rates via Exchange Rate API
- Automatic fallback to Yahoo Finance
- Graceful degradation to approximate rates
- Caching for performance
"""

import logging
from typing import Optional
from datetime import datetime, date
import pandas as pd

logger = logging.getLogger(__name__)


class CurrencyConverter:
    """
    Currency converter with real-time exchange rates.
    
    Features:
    - Real-time rates from Exchange Rate API (if API key configured)
    - Automatic fallback to Yahoo Finance
    - Graceful degradation to approximate rates
    - 1-hour caching for performance
    - Backward compatible with existing code
    
    Usage:
        # With real-time rates (if API key configured)
        converter = CurrencyConverter(use_live_rates=True)
        
        # With approximate rates (legacy behavior)
        converter = CurrencyConverter(use_live_rates=False)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        use_live_rates: bool = True
    ):
        """
        Initialize currency converter.
        
        Args:
            api_key: Optional Exchange Rate API key
            use_live_rates: Whether to use real-time rates (default: True)
        """
        self.use_live_rates = use_live_rates
        self.default_usd_inr_rate = 83.0
        
        # Initialize exchange rate provider if using live rates
        if self.use_live_rates:
            try:
                from maverick_mcp.providers.exchange_rate import ExchangeRateProvider
                self.rate_provider = ExchangeRateProvider(api_key=api_key)
                logger.info("CurrencyConverter initialized with real-time rates")
            except Exception as e:
                logger.warning(f"Failed to initialize rate provider: {e}. Using approximate rates.")
                self.use_live_rates = False
                self.rate_provider = None
        else:
            self.rate_provider = None
            logger.info("CurrencyConverter initialized with approximate rates")
    
    def get_exchange_rate(
        self,
        from_currency: str = "INR",
        to_currency: str = "USD",
        force_refresh: bool = False
    ) -> float:
        """
        Get current exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code (INR or USD)
            to_currency: Target currency code (INR or USD)
            force_refresh: Force fresh rate instead of cached
            
        Returns:
            Exchange rate
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return 1.0
        
        # Use live rates if available
        if self.use_live_rates and self.rate_provider:
            try:
                result = self.rate_provider.get_rate(
                    from_currency,
                    to_currency,
                    force_refresh=force_refresh
                )
                return result.get("rate", self._get_approximate_rate(from_currency, to_currency))
            except Exception as e:
                logger.warning(f"Failed to get live rate: {e}. Using approximate rate.")
                return self._get_approximate_rate(from_currency, to_currency)
        else:
            # Use approximate rates (legacy behavior)
            return self._get_approximate_rate(from_currency, to_currency)
    
    def _get_approximate_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Get approximate rate as fallback.
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Approximate exchange rate
        """
        if from_currency == "USD" and to_currency == "INR":
            return self.default_usd_inr_rate
        elif from_currency == "INR" and to_currency == "USD":
            return 1.0 / self.default_usd_inr_rate
        else:
            raise ValueError(f"Unsupported currency pair: {from_currency}/{to_currency}")
    
    def get_rate_info(
        self,
        from_currency: str,
        to_currency: str,
        force_refresh: bool = False
    ) -> dict:
        """
        Get detailed exchange rate information including source.
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            force_refresh: Force fresh rate
            
        Returns:
            Dict with rate, source, timestamp, and other metadata
        """
        if self.use_live_rates and self.rate_provider:
            try:
                return self.rate_provider.get_rate(
                    from_currency,
                    to_currency,
                    force_refresh=force_refresh
                )
            except Exception as e:
                logger.error(f"Failed to get rate info: {e}")
                # Return approximate info
                return {
                    "from_currency": from_currency.upper(),
                    "to_currency": to_currency.upper(),
                    "rate": self._get_approximate_rate(from_currency, to_currency),
                    "source": "approximate",
                    "timestamp": datetime.now().isoformat(),
                    "warning": "Using approximate rate due to API failure"
                }
        else:
            # Return approximate info
            return {
                "from_currency": from_currency.upper(),
                "to_currency": to_currency.upper(),
                "rate": self._get_approximate_rate(from_currency, to_currency),
                "source": "approximate",
                "timestamp": datetime.now().isoformat()
            }
    
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

