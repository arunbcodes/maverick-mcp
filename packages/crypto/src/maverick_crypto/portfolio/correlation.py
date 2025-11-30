"""
Correlation Analysis for Mixed Portfolios.

Provides correlation analysis between stocks and cryptocurrencies
to help with diversification and risk management.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from pandas import DataFrame

from maverick_crypto.portfolio.mixed_portfolio import (
    AssetType,
    MixedPortfolioService,
    PortfolioAsset,
)

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """
    Analyzes correlation between assets in a portfolio.
    
    Features:
        - Correlation matrix calculation
        - Rolling correlation analysis
        - Asset class correlation (stocks vs crypto)
        - Diversification score
    
    Example:
        >>> analyzer = CorrelationAnalyzer()
        >>> correlation = await analyzer.calculate_correlation(
        ...     stocks=["AAPL", "MSFT", "GOOGL"],
        ...     cryptos=["BTC", "ETH"],
        ...     days=90,
        ... )
    """
    
    def __init__(self):
        """Initialize correlation analyzer."""
        self.portfolio_service = MixedPortfolioService()
    
    async def calculate_correlation_matrix(
        self,
        stocks: list[str],
        cryptos: list[str],
        days: int = 90,
    ) -> dict[str, Any]:
        """
        Calculate correlation matrix between all assets.
        
        Args:
            stocks: List of stock symbols
            cryptos: List of crypto symbols
            days: Number of days for analysis
            
        Returns:
            Dictionary with correlation matrix and analysis
        """
        # Create portfolio assets
        assets = [
            PortfolioAsset(symbol=s, asset_type=AssetType.STOCK, weight=0)
            for s in stocks
        ] + [
            PortfolioAsset(symbol=c, asset_type=AssetType.CRYPTO, weight=0)
            for c in cryptos
        ]
        
        # Get returns
        returns_df = await self.portfolio_service.calculate_returns(assets, days)
        
        if returns_df.empty:
            return {"error": "No data available for correlation analysis"}
        
        # Calculate correlation matrix
        corr_matrix = returns_df.corr()
        
        # Calculate stock-crypto correlation
        stock_symbols = [s for s in stocks if s in returns_df.columns]
        crypto_symbols = [c for c in cryptos if c in returns_df.columns]
        
        stock_crypto_corr = None
        if stock_symbols and crypto_symbols:
            stock_returns = returns_df[stock_symbols].mean(axis=1)
            crypto_returns = returns_df[crypto_symbols].mean(axis=1)
            stock_crypto_corr = stock_returns.corr(crypto_returns)
        
        # Diversification score (lower avg correlation = better diversification)
        avg_correlation = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
        diversification_score = 1 - abs(avg_correlation)
        
        # Identify highly correlated pairs
        high_corr_pairs = []
        for i, col1 in enumerate(corr_matrix.columns):
            for j, col2 in enumerate(corr_matrix.columns):
                if i < j:
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) > 0.7:
                        high_corr_pairs.append({
                            "asset1": col1,
                            "asset2": col2,
                            "correlation": round(corr_val, 3),
                        })
        
        return {
            "correlation_matrix": corr_matrix.round(3).to_dict(),
            "stock_crypto_correlation": round(stock_crypto_corr, 3) if stock_crypto_corr else None,
            "average_correlation": round(avg_correlation, 3),
            "diversification_score": round(diversification_score, 3),
            "high_correlation_pairs": high_corr_pairs,
            "interpretation": self._interpret_correlation(stock_crypto_corr, diversification_score),
            "assets_analyzed": {
                "stocks": stock_symbols,
                "cryptos": crypto_symbols,
            },
            "period_days": days,
        }
    
    def _interpret_correlation(
        self,
        stock_crypto_corr: float | None,
        diversification_score: float,
    ) -> dict[str, str]:
        """Interpret correlation results."""
        interpretation = {}
        
        # Stock-crypto relationship
        if stock_crypto_corr is not None:
            if stock_crypto_corr > 0.5:
                interpretation["stock_crypto"] = "High positive correlation - crypto moves with stocks"
            elif stock_crypto_corr > 0.2:
                interpretation["stock_crypto"] = "Moderate positive correlation - some co-movement"
            elif stock_crypto_corr > -0.2:
                interpretation["stock_crypto"] = "Low correlation - good diversification potential"
            elif stock_crypto_corr > -0.5:
                interpretation["stock_crypto"] = "Moderate negative correlation - some hedge potential"
            else:
                interpretation["stock_crypto"] = "Strong negative correlation - potential hedge"
        
        # Diversification
        if diversification_score > 0.7:
            interpretation["diversification"] = "Excellent diversification - assets are uncorrelated"
        elif diversification_score > 0.5:
            interpretation["diversification"] = "Good diversification - moderate correlation"
        elif diversification_score > 0.3:
            interpretation["diversification"] = "Fair diversification - consider adding uncorrelated assets"
        else:
            interpretation["diversification"] = "Poor diversification - assets are highly correlated"
        
        return interpretation
    
    async def rolling_correlation(
        self,
        asset1: str,
        asset1_type: str,
        asset2: str,
        asset2_type: str,
        days: int = 365,
        window: int = 30,
    ) -> dict[str, Any]:
        """
        Calculate rolling correlation between two assets.
        
        Args:
            asset1: First asset symbol
            asset1_type: "stock" or "crypto"
            asset2: Second asset symbol
            asset2_type: "stock" or "crypto"
            days: Total days of data
            window: Rolling window size
            
        Returns:
            Dictionary with rolling correlation data
        """
        assets = [
            PortfolioAsset(symbol=asset1, asset_type=AssetType(asset1_type), weight=0),
            PortfolioAsset(symbol=asset2, asset_type=AssetType(asset2_type), weight=0),
        ]
        
        returns_df = await self.portfolio_service.calculate_returns(assets, days)
        
        if returns_df.empty or len(returns_df.columns) < 2:
            return {"error": "Insufficient data for rolling correlation"}
        
        # Calculate rolling correlation
        rolling_corr = returns_df[asset1].rolling(window=window).corr(returns_df[asset2])
        rolling_corr = rolling_corr.dropna()
        
        # Statistics
        current_corr = rolling_corr.iloc[-1] if len(rolling_corr) > 0 else None
        avg_corr = rolling_corr.mean()
        max_corr = rolling_corr.max()
        min_corr = rolling_corr.min()
        
        return {
            "asset1": asset1,
            "asset2": asset2,
            "window_days": window,
            "current_correlation": round(current_corr, 3) if current_corr else None,
            "average_correlation": round(avg_corr, 3),
            "max_correlation": round(max_corr, 3),
            "min_correlation": round(min_corr, 3),
            "correlation_range": round(max_corr - min_corr, 3),
            "data_points": len(rolling_corr),
            "rolling_correlation": {
                str(d.date()): round(v, 3)
                for d, v in list(rolling_corr.items())[-30:]  # Last 30 data points
            },
        }
    
    async def asset_class_comparison(
        self,
        stocks: list[str],
        cryptos: list[str],
        days: int = 90,
    ) -> dict[str, Any]:
        """
        Compare performance of stocks vs crypto as asset classes.
        
        Args:
            stocks: Stock symbols
            cryptos: Crypto symbols
            days: Analysis period
            
        Returns:
            Asset class comparison
        """
        # Create equal-weighted portfolios for each class
        stock_assets = [
            PortfolioAsset(symbol=s, asset_type=AssetType.STOCK, weight=1/len(stocks))
            for s in stocks
        ]
        crypto_assets = [
            PortfolioAsset(symbol=c, asset_type=AssetType.CRYPTO, weight=1/len(cryptos))
            for c in cryptos
        ]
        
        # Calculate performance
        stock_perf = await self.portfolio_service.calculate_performance(stock_assets, days)
        crypto_perf = await self.portfolio_service.calculate_performance(crypto_assets, days)
        
        # Extract metrics
        stock_return = stock_perf.get("portfolio", {}).get("total_return_pct", 0)
        crypto_return = crypto_perf.get("portfolio", {}).get("total_return_pct", 0)
        
        stock_vol = stock_perf.get("portfolio", {}).get("volatility_pct", 0)
        crypto_vol = crypto_perf.get("portfolio", {}).get("volatility_pct", 0)
        
        stock_sharpe = stock_perf.get("portfolio", {}).get("sharpe_ratio", 0)
        crypto_sharpe = crypto_perf.get("portfolio", {}).get("sharpe_ratio", 0)
        
        # Recommendation
        if crypto_sharpe > stock_sharpe * 1.5:
            recommendation = "Crypto shows significantly better risk-adjusted returns"
        elif stock_sharpe > crypto_sharpe * 1.5:
            recommendation = "Stocks show significantly better risk-adjusted returns"
        else:
            recommendation = "Consider a mixed portfolio for diversification"
        
        return {
            "stocks": {
                "symbols": stocks,
                "return_pct": round(stock_return, 2),
                "volatility_pct": round(stock_vol, 2),
                "sharpe_ratio": round(stock_sharpe, 3) if stock_sharpe else None,
            },
            "crypto": {
                "symbols": cryptos,
                "return_pct": round(crypto_return, 2),
                "volatility_pct": round(crypto_vol, 2),
                "sharpe_ratio": round(crypto_sharpe, 3) if crypto_sharpe else None,
            },
            "comparison": {
                "return_difference_pct": round(crypto_return - stock_return, 2),
                "volatility_difference_pct": round(crypto_vol - stock_vol, 2),
                "higher_return": "crypto" if crypto_return > stock_return else "stocks",
                "higher_volatility": "crypto" if crypto_vol > stock_vol else "stocks",
                "better_sharpe": "crypto" if crypto_sharpe > stock_sharpe else "stocks",
            },
            "recommendation": recommendation,
            "period_days": days,
        }

