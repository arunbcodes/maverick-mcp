"""
Mixed Portfolio Service for stocks and cryptocurrencies.

Enables creating and managing portfolios that contain both
traditional stocks and cryptocurrencies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
from pandas import DataFrame

logger = logging.getLogger(__name__)


class AssetType(Enum):
    """Asset type classification."""
    STOCK = "stock"
    CRYPTO = "crypto"


@dataclass
class PortfolioAsset:
    """
    Represents an asset in a portfolio.
    
    Attributes:
        symbol: Asset symbol (e.g., "AAPL", "BTC")
        asset_type: Type of asset (stock or crypto)
        weight: Portfolio weight (0-1)
        shares: Number of shares/units (optional)
        cost_basis: Average cost per unit (optional)
    """
    symbol: str
    asset_type: AssetType
    weight: float = 0.0
    shares: float = 0.0
    cost_basis: float = 0.0
    
    @property
    def is_crypto(self) -> bool:
        """Check if asset is cryptocurrency."""
        return self.asset_type == AssetType.CRYPTO
    
    @property
    def is_stock(self) -> bool:
        """Check if asset is a stock."""
        return self.asset_type == AssetType.STOCK
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "asset_type": self.asset_type.value,
            "weight": self.weight,
            "shares": self.shares,
            "cost_basis": self.cost_basis,
        }


class MixedPortfolioService:
    """
    Service for managing mixed stock + crypto portfolios.
    
    Features:
        - Unified data fetching for stocks and crypto
        - Performance calculation across asset types
        - Risk metrics for mixed portfolios
        - Rebalancing recommendations
    
    Example:
        >>> service = MixedPortfolioService()
        >>> portfolio = await service.create_portfolio([
        ...     ("AAPL", "stock", 0.3),
        ...     ("MSFT", "stock", 0.3),
        ...     ("BTC", "crypto", 0.3),
        ...     ("ETH", "crypto", 0.1),
        ... ])
        >>> performance = await service.calculate_performance(portfolio, days=90)
    """
    
    def __init__(self):
        """Initialize the mixed portfolio service."""
        self._stock_provider = None
        self._crypto_provider = None
        logger.info("MixedPortfolioService initialized")
    
    async def _get_stock_provider(self):
        """Lazy load stock data provider."""
        if self._stock_provider is None:
            try:
                from maverick_data.providers import StockDataProvider
                self._stock_provider = StockDataProvider()
            except ImportError:
                # Fallback to yfinance directly
                import yfinance as yf
                self._stock_provider = yf
        return self._stock_provider
    
    async def _get_crypto_provider(self):
        """Lazy load crypto data provider."""
        if self._crypto_provider is None:
            from maverick_crypto.providers import CryptoDataProvider
            self._crypto_provider = CryptoDataProvider()
        return self._crypto_provider
    
    async def fetch_asset_data(
        self,
        symbol: str,
        asset_type: AssetType,
        days: int = 90,
    ) -> DataFrame:
        """
        Fetch historical data for an asset.
        
        Args:
            symbol: Asset symbol
            asset_type: Type of asset
            days: Number of days of history
            
        Returns:
            DataFrame with OHLCV data
        """
        if asset_type == AssetType.CRYPTO:
            provider = await self._get_crypto_provider()
            return await provider.get_crypto_data(symbol, days=days)
        else:
            # Stock data
            import yfinance as yf
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            df.columns = [col.capitalize() for col in df.columns]
            return df
    
    async def fetch_portfolio_data(
        self,
        assets: list[PortfolioAsset],
        days: int = 90,
    ) -> dict[str, DataFrame]:
        """
        Fetch data for all portfolio assets.
        
        Args:
            assets: List of portfolio assets
            days: Number of days of history
            
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        data = {}
        for asset in assets:
            try:
                df = await self.fetch_asset_data(asset.symbol, asset.asset_type, days)
                if not df.empty:
                    data[asset.symbol] = df
            except Exception as e:
                logger.warning(f"Failed to fetch {asset.symbol}: {e}")
        return data
    
    def create_portfolio(
        self,
        assets: list[tuple[str, str, float]],
    ) -> list[PortfolioAsset]:
        """
        Create a portfolio from asset specifications.
        
        Args:
            assets: List of (symbol, asset_type, weight) tuples
                   asset_type: "stock" or "crypto"
                   
        Returns:
            List of PortfolioAsset objects
            
        Example:
            >>> portfolio = service.create_portfolio([
            ...     ("AAPL", "stock", 0.25),
            ...     ("MSFT", "stock", 0.25),
            ...     ("BTC", "crypto", 0.30),
            ...     ("ETH", "crypto", 0.20),
            ... ])
        """
        portfolio = []
        total_weight = 0.0
        
        for symbol, asset_type_str, weight in assets:
            asset_type = AssetType(asset_type_str.lower())
            portfolio.append(PortfolioAsset(
                symbol=symbol.upper(),
                asset_type=asset_type,
                weight=weight,
            ))
            total_weight += weight
        
        # Normalize weights if they don't sum to 1
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total_weight}, normalizing to 1.0")
            for asset in portfolio:
                asset.weight /= total_weight
        
        return portfolio
    
    async def calculate_returns(
        self,
        assets: list[PortfolioAsset],
        days: int = 90,
    ) -> DataFrame:
        """
        Calculate daily returns for portfolio assets.
        
        Args:
            assets: Portfolio assets
            days: Number of days of history
            
        Returns:
            DataFrame with daily returns for each asset
        """
        data = await self.fetch_portfolio_data(assets, days)
        
        returns = {}
        for symbol, df in data.items():
            close = df["Close"] if "Close" in df.columns else df["close"]
            returns[symbol] = close.pct_change()
        
        return pd.DataFrame(returns).dropna()
    
    async def calculate_performance(
        self,
        assets: list[PortfolioAsset],
        days: int = 90,
        initial_capital: float = 10000.0,
    ) -> dict[str, Any]:
        """
        Calculate portfolio performance metrics.
        
        Args:
            assets: Portfolio assets
            days: Number of days for analysis
            initial_capital: Starting capital
            
        Returns:
            Dictionary with performance metrics
        """
        returns_df = await self.calculate_returns(assets, days)
        
        if returns_df.empty:
            return {"error": "No data available for portfolio"}
        
        # Build weight vector
        weights = np.array([
            assets[i].weight for i in range(len(assets))
            if assets[i].symbol in returns_df.columns
        ])
        
        # Align returns with weights
        symbols = [a.symbol for a in assets if a.symbol in returns_df.columns]
        returns_aligned = returns_df[symbols]
        
        # Portfolio returns
        portfolio_returns = returns_aligned.dot(weights)
        
        # Cumulative returns
        cumulative_returns = (1 + portfolio_returns).cumprod()
        
        # Metrics
        total_return = cumulative_returns.iloc[-1] - 1
        annualized_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
        volatility = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Max drawdown
        rolling_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Individual asset performance
        asset_performance = {}
        for symbol in symbols:
            asset_returns = returns_aligned[symbol]
            asset_total = (1 + asset_returns).prod() - 1
            asset_vol = asset_returns.std() * np.sqrt(252)
            asset_performance[symbol] = {
                "total_return_pct": asset_total * 100,
                "volatility_pct": asset_vol * 100,
                "contribution_pct": asset_total * weights[symbols.index(symbol)] * 100,
            }
        
        # Asset class breakdown
        stock_weight = sum(a.weight for a in assets if a.is_stock and a.symbol in symbols)
        crypto_weight = sum(a.weight for a in assets if a.is_crypto and a.symbol in symbols)
        
        return {
            "portfolio": {
                "total_return_pct": total_return * 100,
                "annualized_return_pct": annualized_return * 100,
                "volatility_pct": volatility * 100,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown_pct": max_drawdown * 100,
                "final_value": initial_capital * (1 + total_return),
            },
            "allocation": {
                "stock_weight_pct": stock_weight * 100,
                "crypto_weight_pct": crypto_weight * 100,
            },
            "assets": asset_performance,
            "period_days": len(portfolio_returns),
            "initial_capital": initial_capital,
        }
    
    async def compare_allocations(
        self,
        symbols: dict[str, str],  # symbol -> asset_type
        allocations: list[dict[str, float]],  # List of weight dicts
        days: int = 90,
        initial_capital: float = 10000.0,
    ) -> dict[str, Any]:
        """
        Compare different portfolio allocations.
        
        Args:
            symbols: Dict mapping symbol to asset type
            allocations: List of allocation dicts (symbol -> weight)
            days: Number of days for analysis
            initial_capital: Starting capital
            
        Returns:
            Comparison results for each allocation
        """
        results = []
        
        for i, alloc in enumerate(allocations):
            # Create portfolio
            assets = [
                PortfolioAsset(
                    symbol=symbol,
                    asset_type=AssetType(asset_type),
                    weight=alloc.get(symbol, 0),
                )
                for symbol, asset_type in symbols.items()
            ]
            
            # Calculate performance
            perf = await self.calculate_performance(assets, days, initial_capital)
            perf["allocation_id"] = i + 1
            perf["weights"] = alloc
            results.append(perf)
        
        # Find best allocation
        valid_results = [r for r in results if "portfolio" in r]
        if valid_results:
            best = max(valid_results, key=lambda x: x["portfolio"]["sharpe_ratio"])
            best_id = best["allocation_id"]
        else:
            best_id = None
        
        return {
            "allocations": results,
            "best_allocation_id": best_id,
            "symbols": symbols,
            "period_days": days,
        }

