"""VectorBT backtesting engine implementation."""

from __future__ import annotations

import gc
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol

import numpy as np
import pandas as pd
import vectorbt as vbt
from pandas import DataFrame, Series

if TYPE_CHECKING:
    from maverick_core.interfaces import ICacheProvider

logger = logging.getLogger(__name__)


class IDataProvider(Protocol):
    """Protocol for stock data providers."""

    def get_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> DataFrame | None:
        """Fetch stock data."""
        ...


class VectorBTEngine:
    """High-performance backtesting engine using VectorBT.

    Features:
    - Multiple built-in strategies (SMA, RSI, MACD, Bollinger, etc.)
    - Parameter optimization with grid search
    - Memory-efficient processing
    - Comprehensive performance metrics
    """

    def __init__(
        self,
        data_provider: IDataProvider | None = None,
        cache: ICacheProvider | None = None,
        enable_memory_optimization: bool = True,
    ):
        """Initialize VectorBT engine.

        Args:
            data_provider: Stock data provider instance
            cache: Cache provider for data persistence
            enable_memory_optimization: Enable memory optimization features
        """
        self.data_provider = data_provider
        self.cache = cache
        self.enable_memory_optimization = enable_memory_optimization

        # Configure VectorBT settings for optimal performance
        try:
            vbt.settings.array_wrapper["freq"] = "D"
            vbt.settings.caching["enabled"] = True
        except (KeyError, Exception) as e:
            logger.warning(f"Could not configure VectorBT settings: {e}")

        logger.info("VectorBT engine initialized")

    def _ensure_timezone_naive(self, df: DataFrame) -> DataFrame:
        """Ensure DataFrame index is timezone-naive."""
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df

    async def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> DataFrame:
        """Fetch historical data for backtesting.

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval (1d, 1h, etc.)

        Returns:
            DataFrame with OHLCV data
        """
        # Generate cache key
        cache_key = f"backtest_data:{symbol}:{start_date}:{end_date}:{interval}"

        # Try cache first
        if self.cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data is not None:
                if isinstance(cached_data, pd.DataFrame):
                    df = self._ensure_timezone_naive(cached_data)
                else:
                    df = pd.DataFrame.from_dict(cached_data, orient="index")
                    df.index = pd.to_datetime(df.index)
                    df = self._ensure_timezone_naive(df)
                df.columns = [col.lower() for col in df.columns]
                return df

        # Fetch from provider
        if self.data_provider is None:
            raise ValueError("No data provider configured")

        data = self.data_provider.get_stock_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )

        if data is None or data.empty:
            raise ValueError(f"No data available for {symbol}")

        # Normalize column names
        data.columns = [col.lower() for col in data.columns]
        data = self._ensure_timezone_naive(data)

        # Cache the data
        if self.cache:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            days_old = (datetime.now() - end_dt).days
            ttl = 86400 if days_old > 7 else 3600
            await self.cache.set(cache_key, data, ttl=ttl)

        return data

    async def run_backtest(
        self,
        symbol: str,
        strategy_type: str,
        parameters: dict[str, Any],
        start_date: str,
        end_date: str,
        initial_capital: float = 10000.0,
        fees: float = 0.001,
        slippage: float = 0.001,
    ) -> dict[str, Any]:
        """Run a vectorized backtest.

        Args:
            symbol: Stock symbol
            strategy_type: Type of strategy (sma_cross, rsi, macd, etc.)
            parameters: Strategy parameters
            start_date: Start date
            end_date: End date
            initial_capital: Starting capital
            fees: Trading fees (percentage)
            slippage: Slippage (percentage)

        Returns:
            Dictionary with backtest results
        """
        # Fetch data
        data = await self.get_historical_data(symbol, start_date, end_date)

        # Generate signals based on strategy
        entries, exits = self._generate_signals(data, strategy_type, parameters)

        # Optimize memory usage
        close_prices = data["close"].astype(np.float32)
        entries = entries.astype(bool)
        exits = exits.astype(bool)

        if self.enable_memory_optimization:
            del data
            gc.collect()

        # Run VectorBT portfolio simulation
        portfolio = vbt.Portfolio.from_signals(
            close=close_prices,
            entries=entries,
            exits=exits,
            init_cash=initial_capital,
            fees=fees,
            slippage=slippage,
            freq="D",
            cash_sharing=False,
            call_seq="auto",
            group_by=False,
            broadcast_kwargs={"wrapper_kwargs": {"freq": "D"}},
        )

        # Extract metrics
        metrics = self._extract_metrics(portfolio)
        trades = self._extract_trades(portfolio)

        # Get equity curve
        equity_curve = {
            str(k): float(v) for k, v in portfolio.value().to_dict().items()
        }
        drawdown_series = {
            str(k): float(v) for k, v in portfolio.drawdown().to_dict().items()
        }

        if self.enable_memory_optimization:
            del portfolio, close_prices, entries, exits
            gc.collect()

        return {
            "symbol": symbol,
            "strategy": strategy_type,
            "parameters": parameters,
            "metrics": metrics,
            "trades": trades,
            "equity_curve": equity_curve,
            "drawdown_series": drawdown_series,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
        }

    def _generate_signals(
        self,
        data: DataFrame,
        strategy_type: str,
        parameters: dict[str, Any],
    ) -> tuple[Series, Series]:
        """Generate entry and exit signals based on strategy.

        Args:
            data: Price data
            strategy_type: Strategy type
            parameters: Strategy parameters

        Returns:
            Tuple of (entry_signals, exit_signals)
        """
        if "close" not in data.columns:
            raise ValueError(
                f"Missing 'close' column. Available: {list(data.columns)}"
            )

        close = data["close"]

        strategy_map = {
            "sma_cross": self._sma_crossover_signals,
            "sma_crossover": self._sma_crossover_signals,
            "rsi": self._rsi_signals,
            "macd": self._macd_signals,
            "bollinger": self._bollinger_bands_signals,
            "momentum": self._momentum_signals,
            "ema_cross": self._ema_crossover_signals,
            "mean_reversion": self._mean_reversion_signals,
            "breakout": self._breakout_signals,
            "volume_momentum": lambda c, p: self._volume_momentum_signals(data, p),
            "online_learning": lambda c, p: self._online_learning_signals(data, p),
            "regime_aware": lambda c, p: self._regime_aware_signals(data, p),
            "ensemble": lambda c, p: self._ensemble_signals(data, p),
        }

        if strategy_type not in strategy_map:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        return strategy_map[strategy_type](close, parameters)

    def _sma_crossover_signals(
        self, close: Series, params: dict[str, Any]
    ) -> tuple[Series, Series]:
        """Generate SMA crossover signals."""
        fast_period = params.get("fast_period", params.get("fast_window", 10))
        slow_period = params.get("slow_period", params.get("slow_window", 20))

        fast_sma = vbt.MA.run(close, fast_period, short_name="fast").ma.squeeze()
        slow_sma = vbt.MA.run(close, slow_period, short_name="slow").ma.squeeze()

        entries = (fast_sma > slow_sma) & (fast_sma.shift(1) <= slow_sma.shift(1))
        exits = (fast_sma < slow_sma) & (fast_sma.shift(1) >= slow_sma.shift(1))

        return entries, exits

    def _rsi_signals(
        self, close: Series, params: dict[str, Any]
    ) -> tuple[Series, Series]:
        """Generate RSI-based signals."""
        period = params.get("period", 14)
        oversold = params.get("oversold", 30)
        overbought = params.get("overbought", 70)

        rsi = vbt.RSI.run(close, period).rsi.squeeze()

        entries = (rsi < oversold) & (rsi.shift(1) >= oversold)
        exits = (rsi > overbought) & (rsi.shift(1) <= overbought)

        return entries, exits

    def _macd_signals(
        self, close: Series, params: dict[str, Any]
    ) -> tuple[Series, Series]:
        """Generate MACD signals."""
        fast_period = params.get("fast_period", 12)
        slow_period = params.get("slow_period", 26)
        signal_period = params.get("signal_period", 9)

        macd = vbt.MACD.run(
            close,
            fast_window=fast_period,
            slow_window=slow_period,
            signal_window=signal_period,
        )

        macd_line = macd.macd.squeeze()
        signal_line = macd.signal.squeeze()

        entries = (macd_line > signal_line) & (
            macd_line.shift(1) <= signal_line.shift(1)
        )
        exits = (macd_line < signal_line) & (
            macd_line.shift(1) >= signal_line.shift(1)
        )

        return entries, exits

    def _bollinger_bands_signals(
        self, close: Series, params: dict[str, Any]
    ) -> tuple[Series, Series]:
        """Generate Bollinger Bands signals."""
        period = params.get("period", 20)
        std_dev = params.get("std_dev", 2)

        bb = vbt.BBANDS.run(close, window=period, alpha=std_dev)
        upper = bb.upper.squeeze()
        lower = bb.lower.squeeze()

        entries = (close <= lower) & (close.shift(1) > lower.shift(1))
        exits = (close >= upper) & (close.shift(1) < upper.shift(1))

        return entries, exits

    def _momentum_signals(
        self, close: Series, params: dict[str, Any]
    ) -> tuple[Series, Series]:
        """Generate momentum-based signals."""
        lookback = params.get("lookback", 20)
        threshold = params.get("threshold", 0.05)

        returns = close.pct_change(lookback)

        entries = returns > threshold
        exits = returns < -threshold

        return entries, exits

    def _ema_crossover_signals(
        self, close: Series, params: dict[str, Any]
    ) -> tuple[Series, Series]:
        """Generate EMA crossover signals."""
        fast_period = params.get("fast_period", 12)
        slow_period = params.get("slow_period", 26)

        fast_ema = vbt.MA.run(close, fast_period, ewm=True).ma.squeeze()
        slow_ema = vbt.MA.run(close, slow_period, ewm=True).ma.squeeze()

        entries = (fast_ema > slow_ema) & (fast_ema.shift(1) <= slow_ema.shift(1))
        exits = (fast_ema < slow_ema) & (fast_ema.shift(1) >= slow_ema.shift(1))

        return entries, exits

    def _mean_reversion_signals(
        self, close: Series, params: dict[str, Any]
    ) -> tuple[Series, Series]:
        """Generate mean reversion signals."""
        ma_period = params.get("ma_period", 20)
        entry_threshold = params.get("entry_threshold", 0.02)
        exit_threshold = params.get("exit_threshold", 0.01)

        ma = vbt.MA.run(close, ma_period).ma.squeeze()

        with np.errstate(divide="ignore", invalid="ignore"):
            deviation = np.where(ma != 0, (close - ma) / ma, 0)

        entries = deviation < -entry_threshold
        exits = deviation > exit_threshold

        return entries, exits

    def _breakout_signals(
        self, close: Series, params: dict[str, Any]
    ) -> tuple[Series, Series]:
        """Generate channel breakout signals."""
        lookback = params.get("lookback", 20)
        exit_lookback = params.get("exit_lookback", 10)

        upper_channel = close.rolling(lookback).max()
        lower_channel = close.rolling(exit_lookback).min()

        entries = close > upper_channel.shift(1)
        exits = close < lower_channel.shift(1)

        return entries, exits

    def _volume_momentum_signals(
        self, data: DataFrame, params: dict[str, Any]
    ) -> tuple[Series, Series]:
        """Generate volume-weighted momentum signals."""
        momentum_period = params.get("momentum_period", 20)
        volume_period = params.get("volume_period", 20)
        momentum_threshold = params.get("momentum_threshold", 0.05)
        volume_multiplier = params.get("volume_multiplier", 1.5)

        close = data["close"]
        volume = data.get("volume")

        if volume is None:
            returns = close.pct_change(momentum_period)
            entries = returns > momentum_threshold
            exits = returns < -momentum_threshold
            return entries, exits

        returns = close.pct_change(momentum_period)
        avg_volume = volume.rolling(volume_period).mean()
        volume_surge = volume > (avg_volume * volume_multiplier)

        entries = (returns > momentum_threshold) & volume_surge
        exits = (returns < -momentum_threshold) | (volume < avg_volume * 0.8)

        return entries, exits

    def _online_learning_signals(
        self, data: DataFrame, params: dict[str, Any]
    ) -> tuple[Series, Series]:
        """Generate online learning ML strategy signals."""
        lookback = params.get("lookback", 20)
        learning_rate = params.get("learning_rate", 0.01)

        close = data["close"]
        returns = close.pct_change(lookback)

        rolling_mean = returns.rolling(window=lookback).mean()
        rolling_std = returns.rolling(window=lookback).std()

        entry_threshold = rolling_mean + learning_rate * rolling_std
        exit_threshold = rolling_mean - learning_rate * rolling_std

        entries = returns > entry_threshold
        exits = returns < exit_threshold

        entries = entries.fillna(False)
        exits = exits.fillna(False)

        return entries, exits

    def _regime_aware_signals(
        self, data: DataFrame, params: dict[str, Any]
    ) -> tuple[Series, Series]:
        """Generate regime-aware strategy signals."""
        regime_window = params.get("regime_window", 50)
        threshold = params.get("threshold", 0.02)

        close = data["close"]

        returns = close.pct_change()
        volatility = returns.rolling(window=regime_window).std()
        trend_strength = close.rolling(window=regime_window).apply(
            lambda x: (x.iloc[-1] - x.iloc[0]) / x.iloc[0] if x.iloc[0] != 0 else 0
        )

        is_trending = abs(trend_strength) > threshold

        sma_short = close.rolling(window=regime_window // 2).mean()
        sma_long = close.rolling(window=regime_window).mean()
        trend_entries = (close > sma_long) & (sma_short > sma_long)
        trend_exits = (close < sma_long) & (sma_short < sma_long)

        bb_upper = sma_long + 2 * volatility
        bb_lower = sma_long - 2 * volatility
        reversion_entries = close < bb_lower
        reversion_exits = close > bb_upper

        entries = (is_trending & trend_entries) | (~is_trending & reversion_entries)
        exits = (is_trending & trend_exits) | (~is_trending & reversion_exits)

        entries = entries.fillna(False)
        exits = exits.fillna(False)

        return entries, exits

    def _ensemble_signals(
        self, data: DataFrame, params: dict[str, Any]
    ) -> tuple[Series, Series]:
        """Generate ensemble strategy signals."""
        fast_period = params.get("fast_period", 10)
        slow_period = params.get("slow_period", 20)
        rsi_period = params.get("rsi_period", 14)

        close = data["close"]

        # Strategy 1: SMA Crossover
        fast_sma = close.rolling(window=fast_period).mean()
        slow_sma = close.rolling(window=slow_period).mean()
        sma_entries = (fast_sma > slow_sma) & (fast_sma.shift(1) <= slow_sma.shift(1))
        sma_exits = (fast_sma < slow_sma) & (fast_sma.shift(1) >= slow_sma.shift(1))

        # Strategy 2: RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        rsi_entries = (rsi < 30) & (rsi.shift(1) >= 30)
        rsi_exits = (rsi > 70) & (rsi.shift(1) <= 70)

        # Strategy 3: Momentum
        momentum = close.pct_change(20)
        mom_entries = momentum > 0.05
        mom_exits = momentum < -0.05

        # Ensemble voting
        entry_votes = (
            sma_entries.astype(int) + rsi_entries.astype(int) + mom_entries.astype(int)
        )
        exit_votes = (
            sma_exits.astype(int) + rsi_exits.astype(int) + mom_exits.astype(int)
        )

        entries = entry_votes >= 2
        exits = exit_votes >= 2

        entries = entries.fillna(False)
        exits = exits.fillna(False)

        return entries, exits

    def _extract_metrics(self, portfolio: vbt.Portfolio) -> dict[str, Any]:
        """Extract comprehensive metrics from portfolio."""

        def safe_float(func, default=0.0):
            try:
                value = func()
                if value is None or np.isnan(value) or np.isinf(value):
                    return default
                return float(value)
            except (ZeroDivisionError, ValueError, TypeError):
                return default

        return {
            "total_return": safe_float(portfolio.total_return),
            "annual_return": safe_float(portfolio.annualized_return),
            "sharpe_ratio": safe_float(portfolio.sharpe_ratio),
            "sortino_ratio": safe_float(portfolio.sortino_ratio),
            "calmar_ratio": safe_float(portfolio.calmar_ratio),
            "max_drawdown": safe_float(portfolio.max_drawdown),
            "win_rate": safe_float(lambda: portfolio.trades.win_rate()),
            "profit_factor": safe_float(lambda: portfolio.trades.profit_factor()),
            "expectancy": safe_float(lambda: portfolio.trades.expectancy()),
            "total_trades": int(portfolio.trades.count()),
            "winning_trades": (
                int(portfolio.trades.winning.count())
                if hasattr(portfolio.trades, "winning")
                else 0
            ),
            "losing_trades": (
                int(portfolio.trades.losing.count())
                if hasattr(portfolio.trades, "losing")
                else 0
            ),
            "kelly_criterion": self._calculate_kelly(portfolio),
            "recovery_factor": self._calculate_recovery_factor(portfolio),
            "risk_reward_ratio": self._calculate_risk_reward(portfolio),
        }

    def _extract_trades(self, portfolio: vbt.Portfolio) -> list:
        """Extract trade records from portfolio."""
        if portfolio.trades.count() == 0:
            return []

        trades = portfolio.trades.records_readable

        return [
            {
                "entry_date": str(trade.get("Entry Timestamp", "")),
                "exit_date": str(trade.get("Exit Timestamp", "")),
                "entry_price": float(trade.get("Avg Entry Price", 0)),
                "exit_price": float(trade.get("Avg Exit Price", 0)),
                "size": float(trade.get("Size", 0)),
                "pnl": float(trade.get("PnL", 0)),
                "return": float(trade.get("Return", 0)),
                "duration": str(trade.get("Duration", "")),
            }
            for _, trade in trades.iterrows()
        ]

    def _calculate_kelly(self, portfolio: vbt.Portfolio) -> float:
        """Calculate Kelly Criterion."""
        if portfolio.trades.count() == 0:
            return 0.0

        try:
            win_rate = portfolio.trades.win_rate()
            if win_rate is None or np.isnan(win_rate):
                return 0.0

            avg_win = (
                abs(portfolio.trades.winning.returns.mean() or 0)
                if hasattr(portfolio.trades, "winning")
                and portfolio.trades.winning.count() > 0
                else 0
            )
            avg_loss = (
                abs(portfolio.trades.losing.returns.mean() or 0)
                if hasattr(portfolio.trades, "losing")
                and portfolio.trades.losing.count() > 0
                else 0
            )

            if avg_loss == 0 or avg_win == 0:
                return 0.0

            kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win

            if np.isnan(kelly) or np.isinf(kelly):
                return 0.0

            return float(min(max(kelly, -1.0), 0.25))

        except (ZeroDivisionError, ValueError, TypeError):
            return 0.0

    def _calculate_recovery_factor(self, portfolio: vbt.Portfolio) -> float:
        """Calculate recovery factor (total return / max drawdown)."""
        try:
            max_dd = portfolio.max_drawdown()
            total_return = portfolio.total_return()

            if max_dd is None or np.isnan(max_dd) or max_dd == 0:
                return 0.0
            if total_return is None or np.isnan(total_return):
                return 0.0

            recovery_factor = total_return / abs(max_dd)

            if np.isnan(recovery_factor) or np.isinf(recovery_factor):
                return 0.0

            return float(recovery_factor)

        except (ZeroDivisionError, ValueError, TypeError):
            return 0.0

    def _calculate_risk_reward(self, portfolio: vbt.Portfolio) -> float:
        """Calculate risk-reward ratio."""
        if portfolio.trades.count() == 0:
            return 0.0

        try:
            avg_win = (
                abs(portfolio.trades.winning.pnl.mean() or 0)
                if hasattr(portfolio.trades, "winning")
                and portfolio.trades.winning.count() > 0
                else 0
            )
            avg_loss = (
                abs(portfolio.trades.losing.pnl.mean() or 0)
                if hasattr(portfolio.trades, "losing")
                and portfolio.trades.losing.count() > 0
                else 0
            )

            if avg_loss == 0 or avg_win == 0:
                return 0.0

            risk_reward = avg_win / avg_loss

            if np.isnan(risk_reward) or np.isinf(risk_reward):
                return 0.0

            return float(risk_reward)

        except (ZeroDivisionError, ValueError, TypeError):
            return 0.0

    async def optimize_parameters(
        self,
        symbol: str,
        strategy_type: str,
        param_grid: dict[str, list],
        start_date: str,
        end_date: str,
        optimization_metric: str = "sharpe_ratio",
        initial_capital: float = 10000.0,
        top_n: int = 10,
    ) -> dict[str, Any]:
        """Optimize strategy parameters using grid search.

        Args:
            symbol: Stock symbol
            strategy_type: Strategy type
            param_grid: Parameter grid for optimization
            start_date: Start date
            end_date: End date
            optimization_metric: Metric to optimize
            initial_capital: Starting capital
            top_n: Number of top results to return

        Returns:
            Optimization results with best parameters
        """
        # Fetch data once
        data = await self.get_historical_data(symbol, start_date, end_date)
        close_prices = data["close"].astype(np.float32)

        # Create parameter combinations
        param_combos = vbt.utils.params.create_param_combs(param_grid)
        total_combos = len(param_combos)

        logger.info(f"Optimizing {total_combos} parameter combinations for {symbol}")

        results = []
        for i, params in enumerate(param_combos):
            try:
                entries, exits = self._generate_signals(data, strategy_type, params)
                entries = entries.astype(bool)
                exits = exits.astype(bool)

                portfolio = vbt.Portfolio.from_signals(
                    close=close_prices,
                    entries=entries,
                    exits=exits,
                    init_cash=initial_capital,
                    fees=0.001,
                    freq="D",
                    cash_sharing=False,
                    call_seq="auto",
                    group_by=False,
                )

                metric_value = self._get_metric_value(portfolio, optimization_metric)

                results.append({
                    "parameters": params,
                    optimization_metric: metric_value,
                    "total_return": float(portfolio.total_return()),
                    "max_drawdown": float(portfolio.max_drawdown()),
                    "total_trades": int(portfolio.trades.count()),
                })

                del portfolio, entries, exits
                if i % 20 == 0:
                    gc.collect()

            except Exception as e:
                logger.debug(f"Skipping invalid parameter combination {i}: {e}")
                continue

        if self.enable_memory_optimization:
            del data, close_prices
            gc.collect()

        # Sort by optimization metric
        results.sort(key=lambda x: x[optimization_metric], reverse=True)
        top_results = results[:top_n]

        return {
            "symbol": symbol,
            "strategy": strategy_type,
            "optimization_metric": optimization_metric,
            "best_parameters": top_results[0]["parameters"] if top_results else {},
            "best_metric_value": (
                top_results[0][optimization_metric] if top_results else 0
            ),
            "top_results": top_results,
            "total_combinations_tested": total_combos,
            "valid_combinations": len(results),
        }

    def _get_metric_value(self, portfolio: vbt.Portfolio, metric_name: str) -> float:
        """Get specific metric value from portfolio."""
        metric_map = {
            "total_return": portfolio.total_return,
            "sharpe_ratio": portfolio.sharpe_ratio,
            "sortino_ratio": portfolio.sortino_ratio,
            "calmar_ratio": portfolio.calmar_ratio,
            "max_drawdown": lambda: -portfolio.max_drawdown(),
            "win_rate": lambda: portfolio.trades.win_rate() or 0,
            "profit_factor": lambda: portfolio.trades.profit_factor() or 0,
        }

        if metric_name not in metric_map:
            raise ValueError(f"Unknown metric: {metric_name}")

        try:
            value = metric_map[metric_name]()
            if value is None or np.isnan(value) or np.isinf(value):
                return 0.0
            return float(value)
        except (ZeroDivisionError, ValueError, TypeError):
            return 0.0


__all__ = ["VectorBTEngine", "IDataProvider"]
