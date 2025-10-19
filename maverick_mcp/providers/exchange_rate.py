"""
Exchange Rate Provider - Real-time Currency Conversion

Provides real-time exchange rates with multiple fallback options:
1. Exchange Rate API (primary, free tier available)
2. Yahoo Finance (fallback)
3. Cached rates (if APIs unavailable)

Free API: https://www.exchangerate-api.com/
- 1,500 requests/month free tier
- No credit card required
- Real-time rates updated daily
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import requests
from cachetools import TTLCache

from maverick_mcp.config import settings

logger = logging.getLogger(__name__)


class ExchangeRateSource(Enum):
    """Sources for exchange rate data"""
    EXCHANGE_RATE_API = "exchangerate-api"
    YAHOO_FINANCE = "yahoo_finance"
    FALLBACK_CACHE = "fallback_cache"
    APPROXIMATE = "approximate"


class ExchangeRateProvider:
    """
    Provider for real-time exchange rates.
    
    Features:
    - Primary: Exchange Rate API (free tier)
    - Fallback: Yahoo Finance
    - Caching with 1-hour TTL
    - Graceful degradation to approximate rates
    
    Supported currency pairs:
    - INR/USD (primary use case)
    - USD/INR
    - Additional currencies available
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        use_fallback: bool = True
    ):
        """
        Initialize exchange rate provider.
        
        Args:
            api_key: Optional Exchange Rate API key
            use_fallback: Whether to use fallback sources
        """
        self.api_key = api_key or getattr(settings, "EXCHANGE_RATE_API_KEY", None)
        self.use_fallback = use_fallback
        
        # Cache with 1-hour TTL (rates don't change frequently)
        self.cache = TTLCache(maxsize=100, ttl=3600)
        
        # Default approximate rate (used as last resort)
        self.default_usd_inr_rate = 83.0
        
        # API endpoints
        self.exchange_rate_api_base = "https://v6.exchangerate-api.com/v6"
        
        logger.info(
            f"ExchangeRateProvider initialized (API key: {'configured' if self.api_key else 'not configured'})"
        )
    
    def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code (e.g., "USD")
            to_currency: Target currency code (e.g., "INR")
            force_refresh: Force API call instead of using cache
            
        Returns:
            Dict with rate, source, and timestamp
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Same currency
        if from_currency == to_currency:
            return {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": 1.0,
                "source": "same_currency",
                "timestamp": datetime.now().isoformat(),
                "cached": False
            }
        
        # Check cache
        cache_key = f"{from_currency}_{to_currency}"
        if not force_refresh and cache_key in self.cache:
            cached_result = self.cache[cache_key]
            cached_result["cached"] = True
            logger.debug(f"Returning cached rate for {cache_key}")
            return cached_result
        
        # Try primary source: Exchange Rate API
        if self.api_key:
            result = self._fetch_from_exchange_rate_api(from_currency, to_currency)
            if result:
                self.cache[cache_key] = result
                return result
        
        # Fallback: Yahoo Finance
        if self.use_fallback:
            result = self._fetch_from_yahoo_finance(from_currency, to_currency)
            if result:
                self.cache[cache_key] = result
                return result
        
        # Last resort: Approximate rate
        logger.warning(
            f"All APIs failed for {from_currency}/{to_currency}, using approximate rate"
        )
        return self._get_approximate_rate(from_currency, to_currency)
    
    def _fetch_from_exchange_rate_api(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch rate from Exchange Rate API.
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Dict with rate data or None if failed
        """
        try:
            url = f"{self.exchange_rate_api_base}/{self.api_key}/pair/{from_currency}/{to_currency}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("result") == "success":
                rate = data.get("conversion_rate")
                
                logger.info(
                    f"Fetched rate from Exchange Rate API: {from_currency}/{to_currency} = {rate}"
                )
                
                return {
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "rate": rate,
                    "source": ExchangeRateSource.EXCHANGE_RATE_API.value,
                    "timestamp": datetime.now().isoformat(),
                    "last_update": data.get("time_last_update_utc"),
                    "next_update": data.get("time_next_update_utc"),
                    "cached": False
                }
            else:
                logger.warning(f"Exchange Rate API returned error: {data.get('error-type')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Exchange Rate API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with Exchange Rate API: {e}")
            return None
    
    def _fetch_from_yahoo_finance(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch rate from Yahoo Finance as fallback.
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Dict with rate data or None if failed
        """
        try:
            # Yahoo Finance currency pair format: CURRENCY1CURRENCY2=X
            symbol = f"{from_currency}{to_currency}=X"
            
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            rate = info.get("regularMarketPrice") or info.get("ask") or info.get("bid")
            
            if rate:
                logger.info(
                    f"Fetched rate from Yahoo Finance: {from_currency}/{to_currency} = {rate}"
                )
                
                return {
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "rate": rate,
                    "source": ExchangeRateSource.YAHOO_FINANCE.value,
                    "timestamp": datetime.now().isoformat(),
                    "cached": False
                }
            else:
                logger.warning(f"Yahoo Finance returned no rate for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Yahoo Finance fetch failed: {e}")
            return None
    
    def _get_approximate_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Dict[str, Any]:
        """
        Get approximate rate as last resort.
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Dict with approximate rate
        """
        # Only support USD/INR and INR/USD approximation
        if from_currency == "USD" and to_currency == "INR":
            rate = self.default_usd_inr_rate
        elif from_currency == "INR" and to_currency == "USD":
            rate = 1.0 / self.default_usd_inr_rate
        else:
            # For other pairs, return error indication
            logger.error(f"No approximate rate available for {from_currency}/{to_currency}")
            rate = None
        
        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "source": ExchangeRateSource.APPROXIMATE.value,
            "timestamp": datetime.now().isoformat(),
            "warning": "Using approximate rate. Configure API key for real-time rates.",
            "cached": False
        }
    
    def get_supported_currencies(self) -> List[str]:
        """
        Get list of supported currencies.
        
        Returns:
            List of currency codes
        """
        # Common currencies (Exchange Rate API supports 160+ currencies)
        return [
            "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF",
            "INR", "CNY", "HKD", "SGD", "KRW", "MXN", "BRL"
        ]
    
    def is_rate_stale(self, rate_data: Dict[str, Any], max_age_hours: int = 24) -> bool:
        """
        Check if cached rate data is stale.
        
        Args:
            rate_data: Rate data dict with timestamp
            max_age_hours: Maximum age in hours before considered stale
            
        Returns:
            True if stale, False otherwise
        """
        try:
            timestamp_str = rate_data.get("timestamp")
            if not timestamp_str:
                return True
            
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age = datetime.now() - timestamp.replace(tzinfo=None)
            
            return age > timedelta(hours=max_age_hours)
            
        except Exception as e:
            logger.error(f"Error checking rate staleness: {e}")
            return True


# Convenience functions

def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    api_key: Optional[str] = None
) -> float:
    """
    Quick function to get exchange rate.
    
    Args:
        from_currency: Source currency code
        to_currency: Target currency code
        api_key: Optional API key
        
    Returns:
        Exchange rate as float
    """
    provider = ExchangeRateProvider(api_key=api_key)
    result = provider.get_rate(from_currency, to_currency)
    return result.get("rate", 0.0)


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    api_key: Optional[str] = None
) -> float:
    """
    Quick function to convert currency amount.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency
        to_currency: Target currency
        api_key: Optional API key
        
    Returns:
        Converted amount
    """
    rate = get_exchange_rate(from_currency, to_currency, api_key)
    return amount * rate


__all__ = [
    "ExchangeRateProvider",
    "ExchangeRateSource",
    "get_exchange_rate",
    "convert_currency",
]

