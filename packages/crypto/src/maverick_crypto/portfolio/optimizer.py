"""
Portfolio Optimizer for Mixed Stock + Crypto Portfolios.

Provides mean-variance optimization using scipy.
Supports multiple optimization objectives.
"""

from __future__ import annotations

import logging
from enum import Enum
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

# Check for scipy
try:
    from scipy.optimize import minimize
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    minimize = None


class OptimizationObjective(Enum):
    """Portfolio optimization objectives."""
    MAX_SHARPE = "max_sharpe"  # Maximum Sharpe ratio
    MIN_VOLATILITY = "min_volatility"  # Minimum variance
    MAX_RETURN = "max_return"  # Maximum return
    RISK_PARITY = "risk_parity"  # Equal risk contribution


class PortfolioOptimizer:
    """
    Mean-variance portfolio optimizer for mixed portfolios.
    
    Implements Modern Portfolio Theory to find optimal
    asset allocations across stocks and cryptocurrencies.
    
    Features:
        - Multiple optimization objectives
        - Asset class constraints (min/max stock/crypto allocation)
        - Efficient frontier calculation
        - Risk parity allocation
    
    Example:
        >>> optimizer = PortfolioOptimizer()
        >>> result = await optimizer.optimize(
        ...     stocks=["AAPL", "MSFT"],
        ...     cryptos=["BTC", "ETH"],
        ...     objective="max_sharpe",
        ...     max_crypto_weight=0.3,
        ... )
    """
    
    # Annualization factor (trading days per year)
    ANNUALIZATION_FACTOR = 252
    
    # Risk-free rate assumption
    RISK_FREE_RATE = 0.05  # 5% annual
    
    def __init__(self):
        """Initialize portfolio optimizer."""
        if not HAS_SCIPY:
            logger.warning("scipy not available. Install with: pip install scipy")
        self.portfolio_service = MixedPortfolioService()
    
    async def optimize(
        self,
        stocks: list[str],
        cryptos: list[str],
        objective: str = "max_sharpe",
        days: int = 365,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
        min_stock_weight: float = 0.0,
        max_stock_weight: float = 1.0,
        min_crypto_weight: float = 0.0,
        max_crypto_weight: float = 1.0,
    ) -> dict[str, Any]:
        """
        Optimize portfolio allocation.
        
        Args:
            stocks: List of stock symbols
            cryptos: List of crypto symbols
            objective: Optimization objective (max_sharpe, min_volatility, max_return)
            days: Historical data period
            min_weight: Minimum weight per asset
            max_weight: Maximum weight per asset
            min_stock_weight: Minimum total stock allocation
            max_stock_weight: Maximum total stock allocation
            min_crypto_weight: Minimum total crypto allocation
            max_crypto_weight: Maximum total crypto allocation
            
        Returns:
            Dictionary with optimal weights and metrics
        """
        if not HAS_SCIPY:
            return {
                "error": "scipy not available",
                "help": "Install with: pip install scipy",
            }
        
        # Create assets
        all_assets = []
        asset_types = []
        
        for s in stocks:
            all_assets.append(PortfolioAsset(symbol=s, asset_type=AssetType.STOCK))
            asset_types.append("stock")
        for c in cryptos:
            all_assets.append(PortfolioAsset(symbol=c, asset_type=AssetType.CRYPTO))
            asset_types.append("crypto")
        
        n_assets = len(all_assets)
        if n_assets < 2:
            return {"error": "Need at least 2 assets for optimization"}
        
        # Get returns
        returns_df = await self.portfolio_service.calculate_returns(all_assets, days)
        
        if returns_df.empty:
            return {"error": "No data available for optimization"}
        
        # Calculate expected returns and covariance
        symbols = list(returns_df.columns)
        expected_returns = returns_df.mean() * self.ANNUALIZATION_FACTOR
        cov_matrix = returns_df.cov() * self.ANNUALIZATION_FACTOR
        
        # Map asset types to symbols
        symbol_to_type = {
            all_assets[i].symbol: asset_types[i]
            for i in range(len(all_assets))
            if all_assets[i].symbol in symbols
        }
        
        n_symbols = len(symbols)
        stock_indices = [i for i, s in enumerate(symbols) if symbol_to_type.get(s) == "stock"]
        crypto_indices = [i for i, s in enumerate(symbols) if symbol_to_type.get(s) == "crypto"]
        
        # Objective functions
        def portfolio_return(weights):
            return np.sum(expected_returns * weights)
        
        def portfolio_volatility(weights):
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        def neg_sharpe_ratio(weights):
            ret = portfolio_return(weights)
            vol = portfolio_volatility(weights)
            return -(ret - self.RISK_FREE_RATE) / vol if vol > 0 else float('inf')
        
        # Select objective
        objective_enum = OptimizationObjective(objective)
        if objective_enum == OptimizationObjective.MAX_SHARPE:
            obj_func = neg_sharpe_ratio
        elif objective_enum == OptimizationObjective.MIN_VOLATILITY:
            obj_func = portfolio_volatility
        elif objective_enum == OptimizationObjective.MAX_RETURN:
            obj_func = lambda w: -portfolio_return(w)
        else:
            obj_func = neg_sharpe_ratio
        
        # Constraints
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},  # Weights sum to 1
        ]
        
        # Stock allocation constraint
        if stock_indices:
            constraints.append({
                "type": "ineq",
                "fun": lambda w, idx=stock_indices: np.sum(w[idx]) - min_stock_weight
            })
            constraints.append({
                "type": "ineq",
                "fun": lambda w, idx=stock_indices: max_stock_weight - np.sum(w[idx])
            })
        
        # Crypto allocation constraint
        if crypto_indices:
            constraints.append({
                "type": "ineq",
                "fun": lambda w, idx=crypto_indices: np.sum(w[idx]) - min_crypto_weight
            })
            constraints.append({
                "type": "ineq",
                "fun": lambda w, idx=crypto_indices: max_crypto_weight - np.sum(w[idx])
            })
        
        # Bounds for individual weights
        bounds = tuple((min_weight, max_weight) for _ in range(n_symbols))
        
        # Initial guess (equal weight)
        init_weights = np.array([1/n_symbols] * n_symbols)
        
        # Optimize
        try:
            result = minimize(
                obj_func,
                init_weights,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": 1000},
            )
            
            if not result.success:
                logger.warning(f"Optimization may not have converged: {result.message}")
            
            optimal_weights = result.x
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return {"error": str(e)}
        
        # Calculate metrics for optimal portfolio
        opt_return = portfolio_return(optimal_weights)
        opt_volatility = portfolio_volatility(optimal_weights)
        opt_sharpe = (opt_return - self.RISK_FREE_RATE) / opt_volatility if opt_volatility > 0 else 0
        
        # Build result
        weights_dict = {
            symbols[i]: round(optimal_weights[i], 4)
            for i in range(n_symbols)
            if optimal_weights[i] > 0.001  # Only include non-trivial weights
        }
        
        stock_weight = sum(optimal_weights[i] for i in stock_indices)
        crypto_weight = sum(optimal_weights[i] for i in crypto_indices)
        
        return {
            "objective": objective,
            "optimal_weights": weights_dict,
            "metrics": {
                "expected_return_pct": round(opt_return * 100, 2),
                "volatility_pct": round(opt_volatility * 100, 2),
                "sharpe_ratio": round(opt_sharpe, 3),
            },
            "allocation": {
                "stock_weight_pct": round(stock_weight * 100, 2),
                "crypto_weight_pct": round(crypto_weight * 100, 2),
            },
            "constraints": {
                "min_weight": min_weight,
                "max_weight": max_weight,
                "min_stock_weight": min_stock_weight,
                "max_stock_weight": max_stock_weight,
                "min_crypto_weight": min_crypto_weight,
                "max_crypto_weight": max_crypto_weight,
            },
            "assets": {
                "stocks": [s for s in stocks if s in symbols],
                "cryptos": [c for c in cryptos if c in symbols],
            },
            "period_days": days,
        }
    
    async def efficient_frontier(
        self,
        stocks: list[str],
        cryptos: list[str],
        days: int = 365,
        num_portfolios: int = 50,
        min_crypto_weight: float = 0.0,
        max_crypto_weight: float = 1.0,
    ) -> dict[str, Any]:
        """
        Calculate efficient frontier points.
        
        Args:
            stocks: Stock symbols
            cryptos: Crypto symbols
            days: Historical period
            num_portfolios: Number of frontier points
            min_crypto_weight: Min crypto allocation
            max_crypto_weight: Max crypto allocation
            
        Returns:
            Efficient frontier data
        """
        if not HAS_SCIPY:
            return {
                "error": "scipy not available",
                "help": "Install with: pip install scipy",
            }
        
        # Create assets
        all_assets = [
            PortfolioAsset(symbol=s, asset_type=AssetType.STOCK)
            for s in stocks
        ] + [
            PortfolioAsset(symbol=c, asset_type=AssetType.CRYPTO)
            for c in cryptos
        ]
        
        # Get returns
        returns_df = await self.portfolio_service.calculate_returns(all_assets, days)
        
        if returns_df.empty:
            return {"error": "No data available"}
        
        symbols = list(returns_df.columns)
        expected_returns = returns_df.mean() * self.ANNUALIZATION_FACTOR
        cov_matrix = returns_df.cov() * self.ANNUALIZATION_FACTOR
        
        # Generate random portfolios
        frontier_points = []
        np.random.seed(42)
        
        for _ in range(num_portfolios * 10):  # Generate extra, filter to frontier
            weights = np.random.random(len(symbols))
            weights /= weights.sum()
            
            # Apply crypto constraint
            crypto_symbols = [c for c in cryptos if c in symbols]
            crypto_weight = sum(weights[symbols.index(c)] for c in crypto_symbols)
            
            if crypto_weight < min_crypto_weight or crypto_weight > max_crypto_weight:
                continue
            
            ret = np.sum(expected_returns * weights)
            vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe = (ret - self.RISK_FREE_RATE) / vol if vol > 0 else 0
            
            frontier_points.append({
                "return_pct": round(ret * 100, 2),
                "volatility_pct": round(vol * 100, 2),
                "sharpe_ratio": round(sharpe, 3),
                "weights": {symbols[i]: round(weights[i], 3) for i in range(len(symbols))},
            })
        
        # Sort by Sharpe ratio and keep best
        frontier_points.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
        frontier_points = frontier_points[:num_portfolios]
        
        # Find key portfolios
        max_sharpe = max(frontier_points, key=lambda x: x["sharpe_ratio"])
        min_vol = min(frontier_points, key=lambda x: x["volatility_pct"])
        max_ret = max(frontier_points, key=lambda x: x["return_pct"])
        
        return {
            "frontier_points": frontier_points,
            "key_portfolios": {
                "max_sharpe": max_sharpe,
                "min_volatility": min_vol,
                "max_return": max_ret,
            },
            "assets": {
                "stocks": [s for s in stocks if s in symbols],
                "cryptos": [c for c in cryptos if c in symbols],
            },
            "period_days": days,
        }
    
    async def suggest_allocation(
        self,
        stocks: list[str],
        cryptos: list[str],
        risk_tolerance: str = "moderate",
        days: int = 365,
    ) -> dict[str, Any]:
        """
        Suggest portfolio allocation based on risk tolerance.
        
        Args:
            stocks: Stock symbols
            cryptos: Crypto symbols
            risk_tolerance: "conservative", "moderate", or "aggressive"
            days: Historical period
            
        Returns:
            Suggested allocation
        """
        # Risk tolerance profiles
        profiles = {
            "conservative": {
                "objective": "min_volatility",
                "max_crypto_weight": 0.15,
                "max_weight": 0.30,
            },
            "moderate": {
                "objective": "max_sharpe",
                "max_crypto_weight": 0.30,
                "max_weight": 0.40,
            },
            "aggressive": {
                "objective": "max_return",
                "max_crypto_weight": 0.50,
                "max_weight": 0.50,
            },
        }
        
        profile = profiles.get(risk_tolerance, profiles["moderate"])
        
        result = await self.optimize(
            stocks=stocks,
            cryptos=cryptos,
            objective=profile["objective"],
            days=days,
            max_crypto_weight=profile["max_crypto_weight"],
            max_weight=profile["max_weight"],
        )
        
        if "error" in result:
            return result
        
        result["risk_profile"] = risk_tolerance
        result["profile_description"] = {
            "conservative": "Lower risk, stable returns, limited crypto exposure",
            "moderate": "Balanced risk/return, moderate crypto for diversification",
            "aggressive": "Higher risk tolerance, higher crypto allocation for growth",
        }.get(risk_tolerance, "Moderate risk profile")
        
        return result

