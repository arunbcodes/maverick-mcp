"""
Cryptocurrency Backtesting Engine.

Provides VectorBT-powered backtesting specifically optimized for
cryptocurrency markets with proper handling of 24/7 trading.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

logger = logging.getLogger(__name__)

# Try to import vectorbt
try:
    import vectorbt as vbt
    HAS_VECTORBT = True
except ImportError:
    HAS_VECTORBT = False
    vbt = None


class CryptoBacktestEngine:
    """
    Backtesting engine optimized for cryptocurrency.
    
    Key differences from stock backtesting:
        - No market hours restriction (24/7 trading)
        - Higher default fees (crypto exchanges typically 0.1-0.5%)
        - Adjusted risk parameters for volatility
        - All calendar days are trading days
    
    Example:
        >>> engine = CryptoBacktestEngine()
        >>> result = await engine.run_backtest(
        ...     symbol="BTC",
        ...     strategy="crypto_momentum",
        ...     days=90,
        ... )
        >>> print(f"Return: {result['total_return']:.2%}")
    """
    
    # Default crypto trading parameters
    DEFAULT_FEES = 0.001  # 0.1% per trade (typical crypto exchange)
    DEFAULT_SLIPPAGE = 0.002  # 0.2% slippage (higher than stocks)
    DEFAULT_CAPITAL = 10000.0
    
    def __init__(
        self,
        data_provider: Any | None = None,
        fees: float = DEFAULT_FEES,
        slippage: float = DEFAULT_SLIPPAGE,
    ):
        """
        Initialize crypto backtesting engine.
        
        Args:
            data_provider: Optional data provider (uses CryptoDataProvider if None)
            fees: Trading fees per transaction (default: 0.1%)
            slippage: Expected slippage (default: 0.2%)
        """
        if not HAS_VECTORBT:
            logger.warning("VectorBT not available. Install with: pip install vectorbt")
        
        self.data_provider = data_provider
        self.fees = fees
        self.slippage = slippage
        
        # Configure VectorBT if available
        if HAS_VECTORBT:
            try:
                vbt.settings.array_wrapper["freq"] = "D"
                vbt.settings.caching["enabled"] = True
            except Exception as e:
                logger.warning(f"Could not configure VectorBT settings: {e}")
        
        logger.info("CryptoBacktestEngine initialized")
    
    async def get_data(
        self,
        symbol: str,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        days: int | None = None,
    ) -> DataFrame:
        """
        Fetch cryptocurrency data for backtesting.
        
        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH")
            start_date: Start date
            end_date: End date
            days: Alternative to dates - fetch last N days
            
        Returns:
            DataFrame with OHLCV data
        """
        # Use provided data provider or create default
        if self.data_provider is None:
            from maverick_crypto.providers import CryptoDataProvider
            self.data_provider = CryptoDataProvider()
        
        df = await self.data_provider.get_crypto_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            days=days,
        )
        
        # Ensure timezone-naive index
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        return df
    
    async def run_backtest(
        self,
        symbol: str,
        strategy: str,
        parameters: dict[str, Any] | None = None,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        days: int = 90,
        initial_capital: float = DEFAULT_CAPITAL,
        fees: float | None = None,
        slippage: float | None = None,
    ) -> dict[str, Any]:
        """
        Run a backtest on cryptocurrency data.
        
        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH", "SOL")
            strategy: Strategy name (e.g., "crypto_momentum", "crypto_rsi")
            parameters: Optional strategy parameters to override defaults
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            days: Number of days if dates not specified (default: 90)
            initial_capital: Starting capital (default: $10,000)
            fees: Trading fees (default: 0.1%)
            slippage: Slippage (default: 0.2%)
            
        Returns:
            Dictionary with backtest results:
                - total_return: Total return percentage
                - sharpe_ratio: Risk-adjusted return
                - max_drawdown: Maximum drawdown
                - win_rate: Percentage of winning trades
                - num_trades: Number of trades
                - trades: List of individual trades
                - metrics: Detailed performance metrics
        """
        if not HAS_VECTORBT:
            return {
                "error": "VectorBT not installed",
                "help": "Install with: pip install vectorbt",
            }
        
        # Use instance defaults if not specified
        fees = fees if fees is not None else self.fees
        slippage = slippage if slippage is not None else self.slippage
        
        try:
            # Fetch data
            logger.info(f"Fetching {symbol} data for backtest")
            data = await self.get_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                days=days,
            )
            
            if data.empty:
                return {"error": f"No data available for {symbol}"}
            
            # Get strategy
            from maverick_crypto.backtesting.strategies import get_crypto_strategy
            strat = get_crypto_strategy(strategy, parameters)
            
            logger.info(f"Running {strat.name} backtest on {symbol}")
            
            # Generate signals
            entries, exits = strat.generate_signals(data)
            
            # Get close price
            close = data["Close"] if "Close" in data.columns else data["close"]
            
            # Run VectorBT portfolio simulation
            portfolio = vbt.Portfolio.from_signals(
                close=close,
                entries=entries,
                exits=exits,
                init_cash=initial_capital,
                fees=fees,
                slippage=slippage,
                freq="D",
            )
            
            # Extract metrics
            stats = portfolio.stats()
            
            # Get trades
            trades_df = portfolio.trades.records_readable
            trades_list = []
            if len(trades_df) > 0:
                for _, trade in trades_df.iterrows():
                    trades_list.append({
                        "entry_date": str(trade.get("Entry Timestamp", "")),
                        "exit_date": str(trade.get("Exit Timestamp", "")),
                        "entry_price": float(trade.get("Avg Entry Price", 0)),
                        "exit_price": float(trade.get("Avg Exit Price", 0)),
                        "return_pct": float(trade.get("Return", 0)) * 100,
                        "pnl": float(trade.get("PnL", 0)),
                    })
            
            # Helper to safely get numeric values
            def safe_float(val, default=0.0):
                """Safely convert to float, handling NaN."""
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    return default
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return default
            
            def safe_int(val, default=0):
                """Safely convert to int, handling NaN."""
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    return default
                try:
                    return int(val)
                except (TypeError, ValueError):
                    return default
            
            # Build result
            total_trades = safe_int(stats.get("Total Trades", 0))
            win_rate = safe_float(stats.get("Win Rate [%]", 0))
            
            result = {
                "symbol": symbol,
                "strategy": strat.name,
                "parameters": strat.parameters,
                "period": {
                    "start": str(data.index[0].date()),
                    "end": str(data.index[-1].date()),
                    "days": len(data),
                },
                "initial_capital": initial_capital,
                "final_value": safe_float(stats.get("End Value", initial_capital), initial_capital),
                "total_return": safe_float(stats.get("Total Return", 0)),
                "total_return_pct": safe_float(stats.get("Total Return", 0)) * 100,
                "sharpe_ratio": safe_float(stats.get("Sharpe Ratio"), None),
                "sortino_ratio": safe_float(stats.get("Sortino Ratio"), None),
                "max_drawdown": safe_float(stats.get("Max Drawdown [%]", 0)),
                "win_rate": win_rate,
                "num_trades": total_trades,
                "avg_trade_return": (safe_float(stats.get("Avg Winning Trade [%]", 0)) + safe_float(stats.get("Avg Losing Trade [%]", 0))) / 2 if total_trades > 0 else 0,
                "profit_factor": safe_float(stats.get("Profit Factor"), None),
                "fees_paid": fees * initial_capital * total_trades * 2,  # Estimate
                "trades": trades_list[-20:],  # Last 20 trades
                "metrics": {
                    "total_trades": total_trades,
                    "winning_trades": safe_int(win_rate * total_trades / 100) if total_trades > 0 else 0,
                    "losing_trades": total_trades - safe_int(win_rate * total_trades / 100) if total_trades > 0 else 0,
                    "best_trade": safe_float(stats.get("Best Trade [%]", 0)),
                    "worst_trade": safe_float(stats.get("Worst Trade [%]", 0)),
                    "avg_winning_trade": safe_float(stats.get("Avg Winning Trade [%]", 0)),
                    "avg_losing_trade": safe_float(stats.get("Avg Losing Trade [%]", 0)),
                    "exposure_time": safe_float(stats.get("Exposure Time [%]", 0)),
                },
            }
            
            logger.info(f"Backtest complete: {result['total_return_pct']:.2f}% return, {result['num_trades']} trades")
            return result
            
        except Exception as e:
            logger.error(f"Backtest failed for {symbol}: {e}")
            return {
                "error": str(e),
                "symbol": symbol,
                "strategy": strategy,
            }
    
    async def compare_strategies(
        self,
        symbol: str,
        strategies: list[str] | None = None,
        days: int = 90,
        initial_capital: float = DEFAULT_CAPITAL,
    ) -> dict[str, Any]:
        """
        Compare multiple strategies on the same symbol.
        
        Args:
            symbol: Crypto symbol
            strategies: List of strategy names (default: all)
            days: Number of days for backtest
            initial_capital: Starting capital
            
        Returns:
            Dictionary with comparison results
        """
        from maverick_crypto.backtesting.strategies import CRYPTO_STRATEGIES
        
        if strategies is None:
            strategies = list(CRYPTO_STRATEGIES.keys())
        
        results = {}
        for strategy in strategies:
            try:
                result = await self.run_backtest(
                    symbol=symbol,
                    strategy=strategy,
                    days=days,
                    initial_capital=initial_capital,
                )
                results[strategy] = result
            except Exception as e:
                results[strategy] = {"error": str(e)}
        
        # Find best performer
        valid_results = {k: v for k, v in results.items() if "total_return" in v}
        best_strategy = max(valid_results.keys(), key=lambda x: valid_results[x]["total_return"]) if valid_results else None
        
        return {
            "symbol": symbol,
            "period_days": days,
            "initial_capital": initial_capital,
            "results": results,
            "best_strategy": best_strategy,
            "best_return": valid_results[best_strategy]["total_return_pct"] if best_strategy else None,
            "comparison_summary": [
                {
                    "strategy": k,
                    "return_pct": v.get("total_return_pct"),
                    "sharpe": v.get("sharpe_ratio"),
                    "max_drawdown": v.get("max_drawdown"),
                    "win_rate": v.get("win_rate"),
                    "trades": v.get("num_trades"),
                }
                for k, v in results.items()
                if "total_return_pct" in v
            ],
        }
    
    async def optimize_strategy(
        self,
        symbol: str,
        strategy: str,
        param_grid: dict[str, list[Any]],
        days: int = 90,
        initial_capital: float = DEFAULT_CAPITAL,
        metric: str = "sharpe_ratio",
    ) -> dict[str, Any]:
        """
        Optimize strategy parameters using grid search.
        
        Args:
            symbol: Crypto symbol
            strategy: Strategy name
            param_grid: Parameter grid (e.g., {"fast_period": [5, 10, 15]})
            days: Number of days for backtest
            initial_capital: Starting capital
            metric: Metric to optimize (sharpe_ratio, total_return, etc.)
            
        Returns:
            Dictionary with optimization results
        """
        import itertools
        
        # Generate all parameter combinations
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(itertools.product(*values))
        
        logger.info(f"Optimizing {strategy} with {len(combinations)} parameter combinations")
        
        results = []
        for combo in combinations:
            params = dict(zip(keys, combo))
            try:
                result = await self.run_backtest(
                    symbol=symbol,
                    strategy=strategy,
                    parameters=params,
                    days=days,
                    initial_capital=initial_capital,
                )
                if metric in result:
                    results.append({
                        "parameters": params,
                        "metric_value": result.get(metric),
                        "total_return_pct": result.get("total_return_pct"),
                        "sharpe_ratio": result.get("sharpe_ratio"),
                        "max_drawdown": result.get("max_drawdown"),
                        "win_rate": result.get("win_rate"),
                        "num_trades": result.get("num_trades"),
                    })
            except Exception as e:
                logger.warning(f"Failed with params {params}: {e}")
        
        if not results:
            return {"error": "No valid results from optimization"}
        
        # Sort by metric
        results.sort(key=lambda x: x.get("metric_value") or float("-inf"), reverse=True)
        
        return {
            "symbol": symbol,
            "strategy": strategy,
            "optimization_metric": metric,
            "combinations_tested": len(combinations),
            "best_parameters": results[0]["parameters"],
            "best_metric_value": results[0]["metric_value"],
            "top_10_results": results[:10],
        }

