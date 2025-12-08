"""
Correlation Service.

Calculate portfolio correlation matrices and diversification metrics.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC, timedelta
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


# ============================================
# Data Classes
# ============================================


class CorrelationPeriod(Enum):
    """Time periods for correlation calculation."""
    
    DAYS_30 = 30
    DAYS_90 = 90
    DAYS_180 = 180
    YEAR_1 = 252  # Trading days
    YEAR_2 = 504


@dataclass
class CorrelationMatrix:
    """Correlation matrix result."""
    
    tickers: list[str]
    matrix: list[list[float]]  # 2D correlation matrix
    period_days: int
    calculated_at: datetime
    data_points: int  # Number of data points used
    
    def to_dict(self) -> dict:
        return {
            "tickers": self.tickers,
            "matrix": self.matrix,
            "period_days": self.period_days,
            "calculated_at": self.calculated_at.isoformat(),
            "data_points": self.data_points,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CorrelationMatrix":
        return cls(
            tickers=data["tickers"],
            matrix=data["matrix"],
            period_days=data["period_days"],
            calculated_at=datetime.fromisoformat(data["calculated_at"]),
            data_points=data["data_points"],
        )
    
    def get_correlation(self, ticker1: str, ticker2: str) -> float | None:
        """Get correlation between two tickers."""
        try:
            i1 = self.tickers.index(ticker1)
            i2 = self.tickers.index(ticker2)
            return self.matrix[i1][i2]
        except (ValueError, IndexError):
            return None
    
    def get_high_correlations(self, threshold: float = 0.8) -> list[tuple[str, str, float]]:
        """Get pairs with correlation above threshold."""
        high_pairs = []
        n = len(self.tickers)
        for i in range(n):
            for j in range(i + 1, n):
                corr = self.matrix[i][j]
                if abs(corr) >= threshold:
                    high_pairs.append((self.tickers[i], self.tickers[j], corr))
        return sorted(high_pairs, key=lambda x: abs(x[2]), reverse=True)


@dataclass
class PairCorrelation:
    """Correlation between two specific tickers."""
    
    ticker1: str
    ticker2: str
    correlation: float
    period_days: int
    data_points: int
    calculated_at: datetime
    
    def to_dict(self) -> dict:
        return {
            "ticker1": self.ticker1,
            "ticker2": self.ticker2,
            "correlation": self.correlation,
            "period_days": self.period_days,
            "data_points": self.data_points,
            "calculated_at": self.calculated_at.isoformat(),
        }


@dataclass
class CorrelationStats:
    """Statistics about correlation matrix."""
    
    avg_correlation: float
    max_correlation: float
    min_correlation: float
    high_correlation_count: int  # Pairs with |corr| > 0.7
    low_correlation_count: int   # Pairs with |corr| < 0.3
    
    def to_dict(self) -> dict:
        return {
            "avg_correlation": self.avg_correlation,
            "max_correlation": self.max_correlation,
            "min_correlation": self.min_correlation,
            "high_correlation_count": self.high_correlation_count,
            "low_correlation_count": self.low_correlation_count,
        }


# ============================================
# Correlation Service
# ============================================


class CorrelationService:
    """
    Service for calculating portfolio correlations.
    
    Features:
    - Correlation matrix for portfolio holdings
    - Pair-wise correlation between any two tickers
    - Multiple time periods (30d, 90d, 1y)
    - High correlation alerts
    - Redis caching for performance
    """
    
    # Redis keys
    MATRIX_CACHE_KEY = "correlation:matrix:{tickers_hash}:{period}"
    PAIR_CACHE_KEY = "correlation:pair:{ticker1}:{ticker2}:{period}"
    
    # Cache TTL
    CACHE_TTL = 3600  # 1 hour
    
    def __init__(
        self,
        redis_client: Redis | None = None,
        price_fetcher: Any = None,
    ):
        self.redis = redis_client
        self.price_fetcher = price_fetcher
    
    # ================================
    # Correlation Matrix
    # ================================
    
    async def calculate_correlation_matrix(
        self,
        tickers: list[str],
        period: CorrelationPeriod = CorrelationPeriod.DAYS_90,
        use_cache: bool = True,
    ) -> CorrelationMatrix:
        """
        Calculate correlation matrix for a list of tickers.
        
        Args:
            tickers: List of ticker symbols
            period: Time period for calculation
            use_cache: Whether to use cached results
        
        Returns:
            CorrelationMatrix with correlations between all pairs
        """
        if len(tickers) < 2:
            raise ValueError("Need at least 2 tickers for correlation")
        
        # Normalize and sort tickers
        tickers = sorted([t.upper() for t in tickers])
        period_days = period.value
        
        # Check cache
        if use_cache and self.redis:
            cached = await self._get_cached_matrix(tickers, period_days)
            if cached:
                return cached
        
        # Fetch price data and calculate returns
        returns_df = await self._get_returns_dataframe(tickers, period_days)
        
        if returns_df.empty or len(returns_df) < 10:
            raise ValueError("Insufficient price data for correlation calculation")
        
        # Calculate correlation matrix
        corr_matrix = returns_df.corr()
        
        # Convert to list of lists for JSON serialization
        matrix_list = corr_matrix.values.tolist()
        
        # Round values
        matrix_list = [[round(v, 4) for v in row] for row in matrix_list]
        
        result = CorrelationMatrix(
            tickers=tickers,
            matrix=matrix_list,
            period_days=period_days,
            calculated_at=datetime.now(UTC),
            data_points=len(returns_df),
        )
        
        # Cache result
        if self.redis:
            await self._cache_matrix(result)
        
        return result
    
    # ================================
    # Pair Correlation
    # ================================
    
    async def calculate_pair_correlation(
        self,
        ticker1: str,
        ticker2: str,
        period: CorrelationPeriod = CorrelationPeriod.DAYS_90,
        use_cache: bool = True,
    ) -> PairCorrelation:
        """
        Calculate correlation between two specific tickers.
        
        More efficient than full matrix when only comparing 2 stocks.
        """
        ticker1 = ticker1.upper()
        ticker2 = ticker2.upper()
        period_days = period.value
        
        if ticker1 == ticker2:
            return PairCorrelation(
                ticker1=ticker1,
                ticker2=ticker2,
                correlation=1.0,
                period_days=period_days,
                data_points=0,
                calculated_at=datetime.now(UTC),
            )
        
        # Check cache
        if use_cache and self.redis:
            cached = await self._get_cached_pair(ticker1, ticker2, period_days)
            if cached:
                return cached
        
        # Fetch returns
        returns_df = await self._get_returns_dataframe([ticker1, ticker2], period_days)
        
        if returns_df.empty or len(returns_df) < 10:
            raise ValueError("Insufficient price data")
        
        # Calculate correlation
        correlation = returns_df[ticker1].corr(returns_df[ticker2])
        
        result = PairCorrelation(
            ticker1=ticker1,
            ticker2=ticker2,
            correlation=round(correlation, 4),
            period_days=period_days,
            data_points=len(returns_df),
            calculated_at=datetime.now(UTC),
        )
        
        # Cache
        if self.redis:
            await self._cache_pair(result)
        
        return result
    
    # ================================
    # Statistics
    # ================================
    
    def calculate_statistics(self, matrix: CorrelationMatrix) -> CorrelationStats:
        """Calculate statistics from a correlation matrix."""
        n = len(matrix.tickers)
        correlations = []
        
        # Extract upper triangle (excluding diagonal)
        for i in range(n):
            for j in range(i + 1, n):
                correlations.append(matrix.matrix[i][j])
        
        if not correlations:
            return CorrelationStats(
                avg_correlation=0,
                max_correlation=0,
                min_correlation=0,
                high_correlation_count=0,
                low_correlation_count=0,
            )
        
        return CorrelationStats(
            avg_correlation=round(np.mean(correlations), 4),
            max_correlation=round(max(correlations), 4),
            min_correlation=round(min(correlations), 4),
            high_correlation_count=sum(1 for c in correlations if abs(c) > 0.7),
            low_correlation_count=sum(1 for c in correlations if abs(c) < 0.3),
        )
    
    # ================================
    # Multi-Period Analysis
    # ================================
    
    async def calculate_correlation_across_periods(
        self,
        ticker1: str,
        ticker2: str,
    ) -> dict[str, PairCorrelation]:
        """Calculate correlation for multiple time periods."""
        results = {}
        
        for period in [CorrelationPeriod.DAYS_30, CorrelationPeriod.DAYS_90, CorrelationPeriod.YEAR_1]:
            try:
                corr = await self.calculate_pair_correlation(ticker1, ticker2, period)
                results[f"{period.value}d"] = corr
            except ValueError:
                pass
        
        return results
    
    # ================================
    # Rolling Correlation
    # ================================
    
    async def calculate_rolling_correlation(
        self,
        ticker1: str,
        ticker2: str,
        window: int = 30,
        total_days: int = 252,
    ) -> list[dict]:
        """
        Calculate rolling correlation over time.
        
        Returns a time series of correlation values.
        """
        ticker1 = ticker1.upper()
        ticker2 = ticker2.upper()
        
        # Get returns for longer period
        returns_df = await self._get_returns_dataframe([ticker1, ticker2], total_days + window)
        
        if returns_df.empty:
            return []
        
        # Calculate rolling correlation
        rolling_corr = returns_df[ticker1].rolling(window=window).corr(returns_df[ticker2])
        
        # Convert to list of date/value pairs
        result = []
        for date, value in rolling_corr.dropna().items():
            result.append({
                "date": date.isoformat() if hasattr(date, 'isoformat') else str(date),
                "correlation": round(value, 4),
            })
        
        return result
    
    # ================================
    # Returns Calculation
    # ================================
    
    async def _get_returns_dataframe(
        self,
        tickers: list[str],
        days: int,
    ) -> pd.DataFrame:
        """
        Fetch price data and calculate daily returns.
        
        Returns a DataFrame with ticker columns and daily returns.
        """
        if self.price_fetcher:
            # Use provided price fetcher
            price_data = await self.price_fetcher(tickers, days)
            return self._calculate_returns(price_data)
        
        # Fallback: Generate sample data for demonstration
        # In production, this would fetch from the data service
        return self._generate_sample_returns(tickers, days)
    
    def _calculate_returns(self, price_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Calculate daily returns from price data."""
        returns = {}
        
        for ticker, df in price_data.items():
            if 'close' in df.columns:
                returns[ticker] = df['close'].pct_change().dropna()
            elif 'Close' in df.columns:
                returns[ticker] = df['Close'].pct_change().dropna()
        
        if not returns:
            return pd.DataFrame()
        
        # Combine into single DataFrame
        returns_df = pd.DataFrame(returns)
        
        # Drop any rows with NaN
        returns_df = returns_df.dropna()
        
        return returns_df
    
    def _generate_sample_returns(self, tickers: list[str], days: int) -> pd.DataFrame:
        """
        Generate sample return data for demonstration.
        
        In production, replace with actual price data fetching.
        """
        np.random.seed(42)  # For reproducibility
        
        # Generate correlated returns
        n = len(tickers)
        
        # Create a base correlation structure
        # Technology stocks correlate more, etc.
        base_corr = np.eye(n)
        for i in range(n):
            for j in range(i + 1, n):
                # Random correlation between 0.2 and 0.8
                corr = 0.3 + 0.5 * np.random.random()
                base_corr[i, j] = corr
                base_corr[j, i] = corr
        
        # Generate correlated returns using Cholesky decomposition
        try:
            L = np.linalg.cholesky(base_corr)
        except np.linalg.LinAlgError:
            # If matrix not positive definite, use identity
            L = np.eye(n)
        
        # Generate random returns
        uncorrelated = np.random.randn(days, n) * 0.02  # ~2% daily volatility
        correlated = uncorrelated @ L.T
        
        # Create DataFrame
        dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
        returns_df = pd.DataFrame(correlated, index=dates, columns=tickers)
        
        return returns_df
    
    # ================================
    # Caching
    # ================================
    
    async def _get_cached_matrix(
        self,
        tickers: list[str],
        period: int,
    ) -> CorrelationMatrix | None:
        """Get cached correlation matrix."""
        if not self.redis:
            return None
        
        tickers_hash = hash(tuple(sorted(tickers)))
        key = self.MATRIX_CACHE_KEY.format(tickers_hash=tickers_hash, period=period)
        
        data = await self.redis.get(key)
        if data:
            return CorrelationMatrix.from_dict(json.loads(data))
        
        return None
    
    async def _cache_matrix(self, matrix: CorrelationMatrix) -> None:
        """Cache correlation matrix."""
        if not self.redis:
            return
        
        tickers_hash = hash(tuple(sorted(matrix.tickers)))
        key = self.MATRIX_CACHE_KEY.format(
            tickers_hash=tickers_hash, 
            period=matrix.period_days
        )
        
        await self.redis.setex(key, self.CACHE_TTL, json.dumps(matrix.to_dict()))
    
    async def _get_cached_pair(
        self,
        ticker1: str,
        ticker2: str,
        period: int,
    ) -> PairCorrelation | None:
        """Get cached pair correlation."""
        if not self.redis:
            return None
        
        # Sort tickers for consistent key
        t1, t2 = sorted([ticker1, ticker2])
        key = self.PAIR_CACHE_KEY.format(ticker1=t1, ticker2=t2, period=period)
        
        data = await self.redis.get(key)
        if data:
            d = json.loads(data)
            return PairCorrelation(
                ticker1=d["ticker1"],
                ticker2=d["ticker2"],
                correlation=d["correlation"],
                period_days=d["period_days"],
                data_points=d["data_points"],
                calculated_at=datetime.fromisoformat(d["calculated_at"]),
            )
        
        return None
    
    async def _cache_pair(self, pair: PairCorrelation) -> None:
        """Cache pair correlation."""
        if not self.redis:
            return
        
        t1, t2 = sorted([pair.ticker1, pair.ticker2])
        key = self.PAIR_CACHE_KEY.format(ticker1=t1, ticker2=t2, period=pair.period_days)
        
        await self.redis.setex(key, self.CACHE_TTL, json.dumps(pair.to_dict()))


# ============================================
# Factory Function
# ============================================


def get_correlation_service(
    redis_client: Redis | None = None,
    price_fetcher: Any = None,
) -> CorrelationService:
    """Get CorrelationService instance."""
    return CorrelationService(
        redis_client=redis_client,
        price_fetcher=price_fetcher,
    )

