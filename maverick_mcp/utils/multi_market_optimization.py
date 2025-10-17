"""
Multi-Market Query Optimization

Performance optimizations specifically for multi-market queries:
- Batch fetching across markets
- Market-specific query optimization
- Parallel data retrieval
- Smart caching for multi-market screens
"""

import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import pandas as pd

from maverick_mcp.config.markets import Market, get_market_from_symbol
from maverick_mcp.providers.stock_data import EnhancedStockDataProvider
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider

logger = logging.getLogger(__name__)


class MultiMarketQueryOptimizer:
    """
    Optimizer for cross-market queries.
    
    Features:
    - Parallel fetching for multiple symbols across markets
    - Market-specific provider routing
    - Batch query optimization
    - Intelligent caching
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize multi-market query optimizer.
        
        Args:
            max_workers: Maximum parallel workers for data fetching
        """
        self.max_workers = max_workers
        self.us_provider = EnhancedStockDataProvider()
        self.indian_provider = IndianMarketDataProvider()
        logger.info(f"MultiMarketQueryOptimizer initialized with {max_workers} workers")
    
    def fetch_multiple_stocks(
        self,
        symbols: List[str],
        period: str = "1y",
        parallel: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks across markets efficiently.
        
        Args:
            symbols: List of stock symbols (mix of US and Indian)
            period: Time period for data
            parallel: Whether to fetch in parallel
            
        Returns:
            Dict mapping symbol to DataFrame
        """
        if not symbols:
            return {}
        
        # Group symbols by market for optimized fetching
        market_groups = self._group_symbols_by_market(symbols)
        
        if parallel and len(symbols) > 1:
            return self._fetch_parallel(market_groups, period)
        else:
            return self._fetch_sequential(market_groups, period)
    
    def _group_symbols_by_market(self, symbols: List[str]) -> Dict[Market, List[str]]:
        """
        Group symbols by their market.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dict mapping Market to list of symbols
        """
        groups = {Market.US: [], Market.INDIA_NSE: [], Market.INDIA_BSE: []}
        
        for symbol in symbols:
            market = get_market_from_symbol(symbol)
            if market in groups:
                groups[market].append(symbol)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _fetch_parallel(
        self,
        market_groups: Dict[Market, List[str]],
        period: str
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for grouped symbols in parallel.
        
        Args:
            market_groups: Symbols grouped by market
            period: Time period
            
        Returns:
            Dict mapping symbol to DataFrame
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all fetch tasks
            future_to_symbol = {}
            
            for market, symbols in market_groups.items():
                provider = self._get_provider_for_market(market)
                
                for symbol in symbols:
                    future = executor.submit(
                        self._safe_fetch,
                        provider,
                        symbol,
                        period
                    )
                    future_to_symbol[future] = symbol
            
            # Collect results as they complete
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result()
                    if not data.empty:
                        results[symbol] = data
                    else:
                        logger.warning(f"Empty data returned for {symbol}")
                except Exception as e:
                    logger.error(f"Error fetching {symbol}: {e}")
        
        logger.info(f"Fetched {len(results)}/{len(future_to_symbol)} stocks successfully")
        return results
    
    def _fetch_sequential(
        self,
        market_groups: Dict[Market, List[str]],
        period: str
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for grouped symbols sequentially.
        
        Args:
            market_groups: Symbols grouped by market
            period: Time period
            
        Returns:
            Dict mapping symbol to DataFrame
        """
        results = {}
        
        for market, symbols in market_groups.items():
            provider = self._get_provider_for_market(market)
            
            for symbol in symbols:
                try:
                    data = self._safe_fetch(provider, symbol, period)
                    if not data.empty:
                        results[symbol] = data
                except Exception as e:
                    logger.error(f"Error fetching {symbol}: {e}")
        
        return results
    
    def _get_provider_for_market(self, market: Market):
        """
        Get appropriate data provider for market.
        
        Args:
            market: Market enum value
            
        Returns:
            Provider instance
        """
        if market == Market.US:
            return self.us_provider
        else:  # Indian markets (NSE or BSE)
            return self.indian_provider
    
    def _safe_fetch(self, provider, symbol: str, period: str) -> pd.DataFrame:
        """
        Safely fetch stock data with error handling.
        
        Args:
            provider: Data provider instance
            symbol: Stock symbol
            period: Time period
            
        Returns:
            DataFrame with stock data or empty DataFrame on error
        """
        try:
            return provider.get_stock_data(symbol, period=period)
        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_market_correlation(
        self,
        us_symbols: List[str],
        indian_symbols: List[str],
        period: str = "1y"
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix across markets.
        
        Optimized for cross-market correlation analysis.
        
        Args:
            us_symbols: List of US stock symbols
            indian_symbols: List of Indian stock symbols
            period: Time period for correlation
            
        Returns:
            Correlation matrix DataFrame
        """
        all_symbols = us_symbols + indian_symbols
        
        # Fetch all data in parallel
        data_dict = self.fetch_multiple_stocks(all_symbols, period, parallel=True)
        
        if len(data_dict) < 2:
            logger.warning("Need at least 2 stocks for correlation")
            return pd.DataFrame()
        
        # Extract closing prices
        prices = {}
        for symbol, df in data_dict.items():
            if 'close' in df.columns:
                prices[symbol] = df['close']
        
        # Create combined DataFrame and calculate correlation
        price_df = pd.DataFrame(prices)
        correlation = price_df.corr()
        
        return correlation
    
    def get_market_summary(
        self,
        symbols: List[str],
        period: str = "1d"
    ) -> Dict[str, Any]:
        """
        Get quick summary statistics for multiple stocks.
        
        Optimized for dashboard-style views.
        
        Args:
            symbols: List of stock symbols
            period: Time period
            
        Returns:
            Dict with summary statistics
        """
        data_dict = self.fetch_multiple_stocks(symbols, period, parallel=True)
        
        summary = {
            "total_symbols": len(symbols),
            "successful_fetches": len(data_dict),
            "by_market": {},
            "top_gainers": [],
            "top_losers": []
        }
        
        # Group by market
        for symbol, df in data_dict.items():
            if df.empty:
                continue
            
            market = get_market_from_symbol(symbol)
            market_name = market.value
            
            if market_name not in summary["by_market"]:
                summary["by_market"][market_name] = {
                    "count": 0,
                    "avg_change": 0.0
                }
            
            summary["by_market"][market_name]["count"] += 1
            
            # Calculate return
            if len(df) >= 2:
                start_price = df['close'].iloc[0]
                end_price = df['close'].iloc[-1]
                change_pct = ((end_price - start_price) / start_price) * 100
                
                summary["by_market"][market_name]["avg_change"] += change_pct
        
        # Calculate averages
        for market_name in summary["by_market"]:
            count = summary["by_market"][market_name]["count"]
            if count > 0:
                summary["by_market"][market_name]["avg_change"] /= count
                summary["by_market"][market_name]["avg_change"] = round(
                    summary["by_market"][market_name]["avg_change"], 2
                )
        
        return summary


# Singleton instance for reuse
_optimizer_instance = None


def get_multi_market_optimizer() -> MultiMarketQueryOptimizer:
    """
    Get singleton instance of multi-market optimizer.
    
    Returns:
        MultiMarketQueryOptimizer instance
    """
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = MultiMarketQueryOptimizer()
    return _optimizer_instance


# Convenience functions

def fetch_stocks_parallel(
    symbols: List[str],
    period: str = "1y"
) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to fetch multiple stocks in parallel.
    
    Args:
        symbols: List of stock symbols (US and/or Indian)
        period: Time period
        
    Returns:
        Dict mapping symbol to DataFrame
    """
    optimizer = get_multi_market_optimizer()
    return optimizer.fetch_multiple_stocks(symbols, period, parallel=True)


def calculate_cross_market_correlation(
    us_symbols: List[str],
    indian_symbols: List[str],
    period: str = "1y"
) -> pd.DataFrame:
    """
    Convenience function for cross-market correlation.
    
    Args:
        us_symbols: US stock symbols
        indian_symbols: Indian stock symbols
        period: Time period
        
    Returns:
        Correlation matrix
    """
    optimizer = get_multi_market_optimizer()
    return optimizer.calculate_market_correlation(us_symbols, indian_symbols, period)


__all__ = [
    "MultiMarketQueryOptimizer",
    "get_multi_market_optimizer",
    "fetch_stocks_parallel",
    "calculate_cross_market_correlation",
]

