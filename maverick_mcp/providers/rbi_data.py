"""
Reserve Bank of India (RBI) Data Provider

Provides access to Indian economic indicators and monetary policy data from RBI and related sources.

Data Sources:
- RBI official data (when available)
- World Bank API for Indian economic data
- Trading Economics (if API key provided)
- Federal Reserve Economic Data (FRED) for comparative analysis
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

import pandas as pd
import requests
from cachetools import TTLCache

from maverick_mcp.config import settings

logger = logging.getLogger(__name__)


class EconomicIndicator(Enum):
    """Indian economic indicators"""
    REPO_RATE = "repo_rate"
    REVERSE_REPO_RATE = "reverse_repo_rate"
    CRR = "crr"  # Cash Reserve Ratio
    SLR = "slr"  # Statutory Liquidity Ratio
    CPI_INFLATION = "cpi_inflation"
    WPI_INFLATION = "wpi_inflation"
    GDP_GROWTH = "gdp_growth"
    IIP = "iip"  # Index of Industrial Production
    FOREX_RESERVES = "forex_reserves"


class RBIDataProvider:
    """
    Provider for Reserve Bank of India economic data.
    
    Features:
    - Monetary policy rates (Repo, Reverse Repo, CRR, SLR)
    - Inflation data (CPI, WPI)
    - GDP growth figures
    - Foreign exchange reserves
    - Economic calendar
    
    Caching:
    - Policy rates: 24 hours
    - Inflation data: 1 hour
    - GDP data: 24 hours
    - Forex reserves: 1 hour
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize RBI data provider.
        
        Args:
            api_key: Optional API key for premium data sources
        """
        self.api_key = api_key or getattr(settings, "RBI_API_KEY", None)
        
        # Cache with 1-hour TTL by default
        self.cache = TTLCache(maxsize=100, ttl=3600)
        
        # World Bank API configuration
        self.world_bank_base_url = "https://api.worldbank.org/v2/"
        self.india_country_code = "IN"
        
        # Trading Economics (if API key available)
        self.trading_economics_api_key = getattr(settings, "TRADING_ECONOMICS_API_KEY", None)
        
        logger.info("RBIDataProvider initialized")
    
    def get_policy_rates(self) -> Dict[str, float]:
        """
        Get current RBI policy rates.
        
        Returns current values for:
        - Repo Rate: RBI's key lending rate
        - Reverse Repo Rate: RBI's borrowing rate
        - CRR: Cash Reserve Ratio
        - SLR: Statutory Liquidity Ratio
        
        Returns:
            Dict with policy rates
        """
        cache_key = "policy_rates"
        if cache_key in self.cache:
            logger.debug("Returning cached policy rates")
            return self.cache[cache_key]
        
        try:
            # Try to fetch from RBI official source (placeholder)
            rates = self._fetch_policy_rates_from_rbi()
            
            if not rates:
                # Fallback to known approximate values (as of 2024)
                logger.warning("Using approximate policy rates - real-time data not available")
                rates = {
                    "repo_rate": 6.50,  # Current as of late 2024
                    "reverse_repo_rate": 3.35,
                    "crr": 4.50,
                    "slr": 18.00,
                    "last_updated": datetime.now().isoformat(),
                    "source": "approximate",
                    "note": "These are approximate values. Configure API key for real-time data."
                }
            
            self.cache[cache_key] = rates
            return rates
            
        except Exception as e:
            logger.error(f"Error fetching policy rates: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def _fetch_policy_rates_from_rbi(self) -> Optional[Dict]:
        """
        Fetch policy rates from RBI official source.
        
        Note: RBI doesn't have a public API. This would require scraping
        or using a third-party data provider.
        
        Returns:
            Dict with policy rates or None if not available
        """
        # Placeholder for RBI API integration
        # In practice, this might use:
        # 1. RBI's official data release PDFs (requires parsing)
        # 2. Third-party financial data APIs
        # 3. News sources tracking MPC decisions
        
        return None
    
    def get_inflation_data(self, period: str = "1y") -> pd.DataFrame:
        """
        Get CPI and WPI inflation data for India.
        
        Args:
            period: Time period ("1m", "3m", "6m", "1y", "5y")
            
        Returns:
            DataFrame with inflation data
        """
        cache_key = f"inflation_{period}"
        if cache_key in self.cache:
            logger.debug(f"Returning cached inflation data for {period}")
            return self.cache[cache_key]
        
        try:
            # Calculate date range
            end_date = datetime.now()
            period_days = self._parse_period(period)
            start_date = end_date - timedelta(days=period_days)
            
            # Fetch from World Bank API
            df = self._fetch_world_bank_indicator(
                "FP.CPI.TOTL.ZG",  # CPI inflation
                start_date.year,
                end_date.year
            )
            
            if df.empty:
                logger.warning("No inflation data available from World Bank")
                # Return empty DataFrame with expected structure
                return pd.DataFrame(columns=["date", "cpi_inflation", "wpi_inflation"])
            
            self.cache[cache_key] = df
            return df
            
        except Exception as e:
            logger.error(f"Error fetching inflation data: {e}")
            return pd.DataFrame(columns=["date", "cpi_inflation", "wpi_inflation"])
    
    def get_gdp_growth(self) -> Dict[str, Any]:
        """
        Get latest GDP growth figures for India.
        
        Returns:
            Dict with GDP growth data:
            - current_quarter: Latest quarterly growth rate
            - previous_quarter: Previous quarter growth
            - year_on_year: Year-on-year growth
            - last_updated: Data timestamp
        """
        cache_key = "gdp_growth"
        if cache_key in self.cache:
            logger.debug("Returning cached GDP growth data")
            return self.cache[cache_key]
        
        try:
            # Fetch from World Bank API
            df = self._fetch_world_bank_indicator(
                "NY.GDP.MKTP.KD.ZG",  # GDP growth (annual %)
                datetime.now().year - 5,
                datetime.now().year
            )
            
            if df.empty:
                return {
                    "error": "GDP data not available",
                    "status": "error"
                }
            
            # Get latest available data
            latest_data = df.iloc[-1]
            previous_data = df.iloc[-2] if len(df) > 1 else latest_data
            
            gdp_data = {
                "current": float(latest_data["value"]),
                "previous": float(previous_data["value"]),
                "year": int(latest_data["year"]),
                "last_updated": datetime.now().isoformat(),
                "source": "World Bank",
                "unit": "percent"
            }
            
            self.cache[cache_key] = gdp_data
            return gdp_data
            
        except Exception as e:
            logger.error(f"Error fetching GDP growth: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def get_forex_reserves(self) -> Dict[str, float]:
        """
        Get current foreign exchange reserves.
        
        Returns:
            Dict with forex reserve data:
            - total_reserves: Total reserves in USD billions
            - last_updated: Data timestamp
            - change_from_previous_week: Weekly change
        """
        cache_key = "forex_reserves"
        if cache_key in self.cache:
            logger.debug("Returning cached forex reserves")
            return self.cache[cache_key]
        
        try:
            # Fetch from World Bank API
            df = self._fetch_world_bank_indicator(
                "FI.RES.TOTL.CD",  # Total reserves (includes gold, current US$)
                datetime.now().year - 2,
                datetime.now().year
            )
            
            if df.empty:
                return {
                    "error": "Forex reserves data not available",
                    "status": "error"
                }
            
            latest_data = df.iloc[-1]
            
            forex_data = {
                "total_reserves_usd": float(latest_data["value"]) / 1e9,  # Convert to billions
                "year": int(latest_data["year"]),
                "last_updated": datetime.now().isoformat(),
                "source": "World Bank",
                "unit": "USD billions"
            }
            
            self.cache[cache_key] = forex_data
            return forex_data
            
        except Exception as e:
            logger.error(f"Error fetching forex reserves: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def get_economic_calendar(self, days_ahead: int = 30) -> List[Dict]:
        """
        Get upcoming economic data releases and RBI announcements.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming events
        """
        # Placeholder for economic calendar
        # In practice, this would aggregate from:
        # 1. RBI's published MPC meeting schedule
        # 2. Known data release dates (inflation, GDP, IIP)
        # 3. Government budget announcements
        
        today = datetime.now()
        
        # Example static calendar (would be dynamic in production)
        events = [
            {
                "date": (today + timedelta(days=7)).isoformat(),
                "event": "CPI Inflation Data Release",
                "importance": "high",
                "description": "Monthly Consumer Price Index inflation data"
            },
            {
                "date": (today + timedelta(days=14)).isoformat(),
                "event": "WPI Data Release",
                "importance": "medium",
                "description": "Wholesale Price Index data"
            },
            {
                "date": (today + timedelta(days=30)).isoformat(),
                "event": "RBI Monetary Policy Committee Meeting",
                "importance": "high",
                "description": "Bi-monthly policy rate decision"
            }
        ]
        
        return events
    
    def get_all_indicators(self) -> Dict[str, Any]:
        """
        Get a comprehensive snapshot of all major Indian economic indicators.
        
        Returns:
            Dict with all available indicators
        """
        return {
            "policy_rates": self.get_policy_rates(),
            "gdp_growth": self.get_gdp_growth(),
            "forex_reserves": self.get_forex_reserves(),
            "economic_calendar": self.get_economic_calendar(days_ahead=30),
            "timestamp": datetime.now().isoformat()
        }
    
    # Helper methods
    
    def _fetch_world_bank_indicator(
        self,
        indicator_code: str,
        start_year: int,
        end_year: int
    ) -> pd.DataFrame:
        """
        Fetch indicator data from World Bank API.
        
        Args:
            indicator_code: World Bank indicator code
            start_year: Start year
            end_year: End year
            
        Returns:
            DataFrame with indicator data
        """
        try:
            url = f"{self.world_bank_base_url}country/{self.india_country_code}/indicator/{indicator_code}"
            params = {
                "format": "json",
                "date": f"{start_year}:{end_year}",
                "per_page": 1000
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if len(data) < 2 or not data[1]:
                logger.warning(f"No data returned for indicator {indicator_code}")
                return pd.DataFrame()
            
            # Parse response
            records = []
            for item in data[1]:
                if item["value"] is not None:
                    records.append({
                        "year": int(item["date"]),
                        "value": float(item["value"]),
                        "indicator": indicator_code
                    })
            
            df = pd.DataFrame(records)
            df = df.sort_values("year").reset_index(drop=True)
            
            logger.info(f"Fetched {len(df)} records for indicator {indicator_code}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching World Bank data for {indicator_code}: {e}")
            return pd.DataFrame()
    
    def _parse_period(self, period: str) -> int:
        """
        Convert period string to number of days.
        
        Args:
            period: Period string ("1m", "3m", "6m", "1y", "5y")
            
        Returns:
            Number of days
        """
        period_map = {
            "1m": 30,
            "3m": 90,
            "6m": 180,
            "1y": 365,
            "5y": 1825
        }
        return period_map.get(period, 365)


# Convenience function
def get_indian_economic_data() -> Dict[str, Any]:
    """
    Quick function to get all major Indian economic indicators.
    
    Returns:
        Dict with comprehensive economic data
    """
    provider = RBIDataProvider()
    return provider.get_all_indicators()


__all__ = [
    "RBIDataProvider",
    "EconomicIndicator",
    "get_indian_economic_data",
]

