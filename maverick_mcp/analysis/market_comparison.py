"""
Market Comparison Analyzer

Tools for comparing US and Indian stock markets.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

import pandas as pd
import numpy as np

from maverick_mcp.providers.stock_data import EnhancedStockDataProvider
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider
from maverick_mcp.utils.currency_converter import CurrencyConverter

logger = logging.getLogger(__name__)


class MarketComparisonAnalyzer:
    """
    Analyzer for comparing US and Indian markets.
    
    Features:
    - Index comparison (S&P 500 vs Nifty 50)
    - Stock-to-stock comparison
    - Correlation analysis
    - Currency-adjusted returns
    """
    
    def __init__(self):
        """Initialize market comparison analyzer."""
        self.us_provider = EnhancedStockDataProvider()
        self.indian_provider = IndianMarketDataProvider()
        self.currency_converter = CurrencyConverter()
        logger.info("MarketComparisonAnalyzer initialized")
    
    def compare_indices(
        self,
        period: str = "1y"
    ) -> Dict[str, Any]:
        """
        Compare S&P 500 and Nifty 50 indices.
        
        Args:
            period: Time period for comparison (1m, 3m, 6m, 1y)
            
        Returns:
            Dict with comparison metrics
        """
        try:
            # Fetch S&P 500 data
            sp500_df = self.us_provider.get_stock_data("^GSPC", period=period)
            
            # Fetch Nifty 50 data
            nifty_df = self.indian_provider.get_stock_data("^NSEI", period=period)
            
            if sp500_df.empty or nifty_df.empty:
                return {
                    "error": "Unable to fetch index data",
                    "status": "error"
                }
            
            # Calculate returns
            sp500_return = ((sp500_df['close'].iloc[-1] - sp500_df['close'].iloc[0]) / 
                           sp500_df['close'].iloc[0] * 100)
            nifty_return = ((nifty_df['close'].iloc[-1] - nifty_df['close'].iloc[0]) / 
                           nifty_df['close'].iloc[0] * 100)
            
            # Calculate volatility
            sp500_volatility = sp500_df['close'].pct_change().std() * np.sqrt(252) * 100
            nifty_volatility = nifty_df['close'].pct_change().std() * np.sqrt(252) * 100
            
            # Calculate correlation
            correlation = self._calculate_correlation(
                sp500_df['close'],
                nifty_df['close']
            )
            
            return {
                "period": period,
                "sp500": {
                    "return_pct": round(sp500_return, 2),
                    "volatility_pct": round(sp500_volatility, 2),
                    "current_level": round(sp500_df['close'].iloc[-1], 2)
                },
                "nifty50": {
                    "return_pct": round(nifty_return, 2),
                    "volatility_pct": round(nifty_volatility, 2),
                    "current_level": round(nifty_df['close'].iloc[-1], 2)
                },
                "correlation": round(correlation, 3),
                "comparison": {
                    "return_difference_pct": round(nifty_return - sp500_return, 2),
                    "better_performer": "Nifty 50" if nifty_return > sp500_return else "S&P 500"
                },
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error comparing indices: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def compare_stocks(
        self,
        us_symbol: str,
        indian_symbol: str,
        period: str = "1y",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Compare a US stock with an Indian stock.
        
        Args:
            us_symbol: US stock symbol (e.g., "AAPL")
            indian_symbol: Indian stock symbol (e.g., "RELIANCE.NS")
            period: Time period for comparison
            currency: Currency for comparison (USD or INR)
            
        Returns:
            Dict with comparison metrics
        """
        try:
            # Fetch US stock data
            us_df = self.us_provider.get_stock_data(us_symbol, period=period)
            
            # Fetch Indian stock data
            indian_df = self.indian_provider.get_stock_data(indian_symbol, period=period)
            
            if us_df.empty or indian_df.empty:
                return {
                    "error": "Unable to fetch stock data",
                    "status": "error"
                }
            
            # Calculate returns
            us_return = ((us_df['close'].iloc[-1] - us_df['close'].iloc[0]) / 
                        us_df['close'].iloc[0] * 100)
            indian_return = ((indian_df['close'].iloc[-1] - indian_df['close'].iloc[0]) / 
                            indian_df['close'].iloc[0] * 100)
            
            # Currency adjustment for prices
            us_current_price = us_df['close'].iloc[-1]
            indian_current_price = indian_df['close'].iloc[-1]
            
            if currency == "USD":
                indian_current_price_adjusted = self.currency_converter.convert(
                    indian_current_price, "INR", "USD"
                )
                price_unit = "USD"
            else:
                us_current_price_adjusted = self.currency_converter.convert(
                    us_current_price, "USD", "INR"
                )
                price_unit = "INR"
            
            # Calculate correlation
            correlation = self._calculate_correlation(
                us_df['close'],
                indian_df['close']
            )
            
            result = {
                "period": period,
                "currency": currency,
                "us_stock": {
                    "symbol": us_symbol,
                    "return_pct": round(us_return, 2),
                    "current_price": round(us_current_price, 2) if currency == "USD" else round(us_current_price_adjusted, 2),
                    "price_unit": price_unit
                },
                "indian_stock": {
                    "symbol": indian_symbol,
                    "return_pct": round(indian_return, 2),
                    "current_price": round(indian_current_price_adjusted, 2) if currency == "USD" else round(indian_current_price, 2),
                    "price_unit": price_unit
                },
                "correlation": round(correlation, 3),
                "comparison": {
                    "return_difference_pct": round(indian_return - us_return, 2),
                    "better_performer": indian_symbol if indian_return > us_return else us_symbol
                },
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error comparing stocks: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def calculate_correlation(
        self,
        symbols: List[str],
        period: str = "1y"
    ) -> Dict[str, Any]:
        """
        Calculate correlation matrix for multiple stocks across markets.
        
        Args:
            symbols: List of stock symbols (US and Indian)
            period: Time period for correlation
            
        Returns:
            Dict with correlation matrix
        """
        try:
            # Fetch data for all symbols
            data_dict = {}
            
            for symbol in symbols:
                if symbol.endswith('.NS') or symbol.endswith('.BO'):
                    df = self.indian_provider.get_stock_data(symbol, period=period)
                else:
                    df = self.us_provider.get_stock_data(symbol, period=period)
                
                if not df.empty:
                    data_dict[symbol] = df['close']
            
            if len(data_dict) < 2:
                return {
                    "error": "Need at least 2 valid symbols",
                    "status": "error"
                }
            
            # Create DataFrame with all series
            combined_df = pd.DataFrame(data_dict)
            
            # Calculate correlation matrix
            corr_matrix = combined_df.corr()
            
            # Convert to dict format
            corr_dict = {}
            for idx in corr_matrix.index:
                corr_dict[idx] = {
                    col: round(corr_matrix.loc[idx, col], 3)
                    for col in corr_matrix.columns
                }
            
            return {
                "correlation_matrix": corr_dict,
                "symbols": symbols,
                "period": period,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def _calculate_correlation(
        self,
        series1: pd.Series,
        series2: pd.Series
    ) -> float:
        """
        Calculate correlation between two price series.
        
        Aligns series by index and calculates correlation.
        
        Args:
            series1: First price series
            series2: Second price series
            
        Returns:
            Correlation coefficient
        """
        # Align series by index
        combined = pd.DataFrame({
            's1': series1,
            's2': series2
        }).dropna()
        
        if len(combined) < 2:
            return 0.0
        
        return combined['s1'].corr(combined['s2'])


# Convenience functions

def compare_us_indian_markets(period: str = "1y") -> Dict[str, Any]:
    """
    Quick function to compare US and Indian markets.
    
    Args:
        period: Time period for comparison
        
    Returns:
        Comparison results
    """
    analyzer = MarketComparisonAnalyzer()
    return analyzer.compare_indices(period)


def compare_similar_companies(
    us_symbol: str,
    indian_symbol: str,
    currency: str = "USD"
) -> Dict[str, Any]:
    """
    Quick function to compare similar companies.
    
    Args:
        us_symbol: US stock symbol
        indian_symbol: Indian stock symbol
        currency: Currency for comparison
        
    Returns:
        Comparison results
    """
    analyzer = MarketComparisonAnalyzer()
    return analyzer.compare_stocks(us_symbol, indian_symbol, "1y", currency)


__all__ = [
    "MarketComparisonAnalyzer",
    "compare_us_indian_markets",
    "compare_similar_companies",
]

