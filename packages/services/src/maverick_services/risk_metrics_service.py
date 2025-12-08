"""
Risk Metrics Service.

Calculate advanced risk metrics: VaR, CVaR, Beta, Volatility, Stress Testing.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


# ============================================
# Constants
# ============================================


class StressScenario(Enum):
    """Pre-defined stress test scenarios."""
    
    MARKET_DROP_10 = "market_drop_10"
    MARKET_DROP_20 = "market_drop_20"
    MARKET_DROP_30 = "market_drop_30"
    FINANCIAL_CRISIS_2008 = "financial_crisis_2008"
    COVID_CRASH_2020 = "covid_crash_2020"
    TECH_BUBBLE_2000 = "tech_bubble_2000"
    FLASH_CRASH = "flash_crash"


# Historical scenario parameters (approximate market drops)
STRESS_SCENARIOS = {
    StressScenario.MARKET_DROP_10: {
        "name": "10% Market Correction",
        "description": "Standard market correction",
        "market_return": -0.10,
        "volatility_spike": 1.5,
        "duration_days": 20,
    },
    StressScenario.MARKET_DROP_20: {
        "name": "20% Bear Market",
        "description": "Official bear market territory",
        "market_return": -0.20,
        "volatility_spike": 2.0,
        "duration_days": 60,
    },
    StressScenario.MARKET_DROP_30: {
        "name": "30% Severe Crash",
        "description": "Severe market crash",
        "market_return": -0.30,
        "volatility_spike": 3.0,
        "duration_days": 90,
    },
    StressScenario.FINANCIAL_CRISIS_2008: {
        "name": "2008 Financial Crisis",
        "description": "Lehman Brothers collapse, ~57% S&P 500 drop",
        "market_return": -0.57,
        "volatility_spike": 4.0,
        "duration_days": 517,  # Oct 2007 - Mar 2009
    },
    StressScenario.COVID_CRASH_2020: {
        "name": "COVID-19 Crash",
        "description": "March 2020 pandemic crash, ~34% drop",
        "market_return": -0.34,
        "volatility_spike": 5.0,
        "duration_days": 33,  # Feb 19 - Mar 23, 2020
    },
    StressScenario.TECH_BUBBLE_2000: {
        "name": "Dot-Com Bubble",
        "description": "2000-2002 tech crash, ~49% S&P 500 drop",
        "market_return": -0.49,
        "volatility_spike": 2.5,
        "duration_days": 929,  # Mar 2000 - Oct 2002
    },
    StressScenario.FLASH_CRASH: {
        "name": "Flash Crash",
        "description": "May 6, 2010 - rapid intraday crash",
        "market_return": -0.09,
        "volatility_spike": 8.0,
        "duration_days": 1,
    },
}


# ============================================
# Data Classes
# ============================================


@dataclass
class VaRResult:
    """Value at Risk calculation result."""
    
    var_95: float  # 95% confidence VaR
    var_99: float  # 99% confidence VaR
    cvar_95: float  # Conditional VaR (Expected Shortfall) 95%
    cvar_99: float  # Conditional VaR 99%
    method: str  # "historical", "parametric", "monte_carlo"
    period_days: int
    portfolio_value: float
    var_95_amount: float  # Dollar amount
    var_99_amount: float
    cvar_95_amount: float
    cvar_99_amount: float
    
    def to_dict(self) -> dict:
        return {
            "var_95": round(self.var_95, 4),
            "var_99": round(self.var_99, 4),
            "cvar_95": round(self.cvar_95, 4),
            "cvar_99": round(self.cvar_99, 4),
            "method": self.method,
            "period_days": self.period_days,
            "portfolio_value": round(self.portfolio_value, 2),
            "var_95_amount": round(self.var_95_amount, 2),
            "var_99_amount": round(self.var_99_amount, 2),
            "cvar_95_amount": round(self.cvar_95_amount, 2),
            "cvar_99_amount": round(self.cvar_99_amount, 2),
        }


@dataclass
class BetaResult:
    """Portfolio beta calculation result."""
    
    beta: float
    alpha: float  # Jensen's alpha (intercept)
    r_squared: float  # Coefficient of determination
    correlation: float  # Correlation with benchmark
    interpretation: str
    
    def to_dict(self) -> dict:
        return {
            "beta": round(self.beta, 3),
            "alpha": round(self.alpha, 4),
            "r_squared": round(self.r_squared, 3),
            "correlation": round(self.correlation, 3),
            "interpretation": self.interpretation,
        }


@dataclass
class VolatilityResult:
    """Volatility metrics result."""
    
    daily_volatility: float
    annualized_volatility: float
    downside_volatility: float  # Only negative returns
    upside_volatility: float  # Only positive returns
    volatility_skew: float  # Ratio of downside to upside
    max_daily_loss: float
    max_daily_gain: float
    
    def to_dict(self) -> dict:
        return {
            "daily_volatility": round(self.daily_volatility, 4),
            "annualized_volatility": round(self.annualized_volatility, 4),
            "downside_volatility": round(self.downside_volatility, 4),
            "upside_volatility": round(self.upside_volatility, 4),
            "volatility_skew": round(self.volatility_skew, 2),
            "max_daily_loss": round(self.max_daily_loss, 4),
            "max_daily_gain": round(self.max_daily_gain, 4),
        }


@dataclass
class StressTestResult:
    """Single stress test scenario result."""
    
    scenario: str
    scenario_name: str
    description: str
    market_return: float
    estimated_portfolio_loss: float
    estimated_loss_amount: float
    recovery_estimate_days: int | None
    
    def to_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "scenario_name": self.scenario_name,
            "description": self.description,
            "market_return": round(self.market_return, 4),
            "estimated_portfolio_loss": round(self.estimated_portfolio_loss, 4),
            "estimated_loss_amount": round(self.estimated_loss_amount, 2),
            "recovery_estimate_days": self.recovery_estimate_days,
        }


@dataclass
class RiskMetricsSummary:
    """Complete risk metrics summary."""
    
    var: VaRResult
    beta: BetaResult
    volatility: VolatilityResult
    stress_tests: list[StressTestResult]
    risk_score: float  # 0-100, higher = riskier
    risk_level: str  # "low", "moderate", "high", "very_high"
    calculated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def to_dict(self) -> dict:
        return {
            "var": self.var.to_dict(),
            "beta": self.beta.to_dict(),
            "volatility": self.volatility.to_dict(),
            "stress_tests": [s.to_dict() for s in self.stress_tests],
            "risk_score": round(self.risk_score, 1),
            "risk_level": self.risk_level,
            "calculated_at": self.calculated_at.isoformat(),
        }


# ============================================
# Risk Metrics Service
# ============================================


class RiskMetricsService:
    """
    Service for calculating advanced risk metrics.
    
    Features:
    - VaR (Value at Risk) at 95% and 99% confidence
    - CVaR (Conditional VaR / Expected Shortfall)
    - Portfolio Beta vs S&P 500
    - Volatility metrics (annualized, downside, upside)
    - Stress testing with historical scenarios
    - Composite risk score
    """
    
    # Trading days per year
    TRADING_DAYS = 252
    
    def __init__(self, price_fetcher: Any = None):
        self.price_fetcher = price_fetcher
    
    # ================================
    # Value at Risk
    # ================================
    
    def calculate_var(
        self,
        returns: np.ndarray | list,
        portfolio_value: float,
        method: str = "historical",
        period_days: int = 252,
    ) -> VaRResult:
        """
        Calculate Value at Risk using specified method.
        
        Methods:
        - historical: Based on actual return distribution
        - parametric: Assumes normal distribution
        - monte_carlo: Simulation-based (future enhancement)
        """
        returns = np.array(returns)
        returns = returns[~np.isnan(returns)]  # Remove NaN
        
        if len(returns) < 20:
            raise ValueError("Insufficient return data for VaR calculation")
        
        if method == "parametric":
            # Parametric VaR (assumes normal distribution)
            mean = np.mean(returns)
            std = np.std(returns)
            var_95 = stats.norm.ppf(0.05, mean, std)
            var_99 = stats.norm.ppf(0.01, mean, std)
            # CVaR for normal distribution
            cvar_95 = mean - std * stats.norm.pdf(stats.norm.ppf(0.05)) / 0.05
            cvar_99 = mean - std * stats.norm.pdf(stats.norm.ppf(0.01)) / 0.01
        else:
            # Historical VaR (non-parametric)
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
            # CVaR: average of returns below VaR
            cvar_95 = np.mean(returns[returns <= var_95])
            cvar_99 = np.mean(returns[returns <= var_99])
        
        return VaRResult(
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            method=method,
            period_days=period_days,
            portfolio_value=portfolio_value,
            var_95_amount=abs(var_95) * portfolio_value,
            var_99_amount=abs(var_99) * portfolio_value,
            cvar_95_amount=abs(cvar_95) * portfolio_value,
            cvar_99_amount=abs(cvar_99) * portfolio_value,
        )
    
    # ================================
    # Beta Calculation
    # ================================
    
    def calculate_beta(
        self,
        portfolio_returns: np.ndarray | list,
        benchmark_returns: np.ndarray | list,
    ) -> BetaResult:
        """
        Calculate portfolio beta relative to benchmark (e.g., S&P 500).
        
        Beta interpretation:
        - beta = 1: Moves with market
        - beta > 1: More volatile than market
        - beta < 1: Less volatile than market
        - beta < 0: Moves opposite to market
        """
        portfolio_returns = np.array(portfolio_returns)
        benchmark_returns = np.array(benchmark_returns)
        
        # Align lengths
        min_len = min(len(portfolio_returns), len(benchmark_returns))
        portfolio_returns = portfolio_returns[:min_len]
        benchmark_returns = benchmark_returns[:min_len]
        
        # Remove NaN
        mask = ~(np.isnan(portfolio_returns) | np.isnan(benchmark_returns))
        portfolio_returns = portfolio_returns[mask]
        benchmark_returns = benchmark_returns[mask]
        
        if len(portfolio_returns) < 20:
            raise ValueError("Insufficient data for beta calculation")
        
        # Linear regression: portfolio = alpha + beta * benchmark
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            benchmark_returns, portfolio_returns
        )
        
        beta = slope
        alpha = intercept
        r_squared = r_value ** 2
        correlation = r_value
        
        # Interpretation
        if beta >= 1.5:
            interpretation = "Very aggressive - significantly more volatile than market"
        elif beta >= 1.2:
            interpretation = "Aggressive - more volatile than market"
        elif beta >= 0.8:
            interpretation = "Market-like volatility"
        elif beta >= 0.5:
            interpretation = "Defensive - less volatile than market"
        elif beta >= 0:
            interpretation = "Very defensive - much less volatile than market"
        else:
            interpretation = "Inverse relationship with market"
        
        return BetaResult(
            beta=beta,
            alpha=alpha,
            r_squared=r_squared,
            correlation=correlation,
            interpretation=interpretation,
        )
    
    # ================================
    # Volatility
    # ================================
    
    def calculate_volatility(
        self,
        returns: np.ndarray | list,
    ) -> VolatilityResult:
        """Calculate comprehensive volatility metrics."""
        returns = np.array(returns)
        returns = returns[~np.isnan(returns)]
        
        if len(returns) < 20:
            raise ValueError("Insufficient data for volatility calculation")
        
        daily_vol = np.std(returns)
        annualized_vol = daily_vol * np.sqrt(self.TRADING_DAYS)
        
        # Downside and upside volatility
        negative_returns = returns[returns < 0]
        positive_returns = returns[returns > 0]
        
        downside_vol = np.std(negative_returns) if len(negative_returns) > 0 else 0
        upside_vol = np.std(positive_returns) if len(positive_returns) > 0 else 0
        
        # Volatility skew (>1 means more downside risk)
        vol_skew = downside_vol / upside_vol if upside_vol > 0 else 1.0
        
        return VolatilityResult(
            daily_volatility=daily_vol,
            annualized_volatility=annualized_vol,
            downside_volatility=downside_vol,
            upside_volatility=upside_vol,
            volatility_skew=vol_skew,
            max_daily_loss=np.min(returns),
            max_daily_gain=np.max(returns),
        )
    
    # ================================
    # Stress Testing
    # ================================
    
    def run_stress_tests(
        self,
        portfolio_beta: float,
        portfolio_value: float,
        scenarios: list[StressScenario] | None = None,
    ) -> list[StressTestResult]:
        """
        Run stress tests for various scenarios.
        
        Uses portfolio beta to estimate impact:
        estimated_loss = market_loss * beta
        """
        if scenarios is None:
            scenarios = list(StressScenario)
        
        results = []
        for scenario in scenarios:
            params = STRESS_SCENARIOS[scenario]
            
            # Estimate portfolio loss based on beta
            # Higher beta = larger loss in down market
            market_return = params["market_return"]
            estimated_loss = market_return * portfolio_beta
            
            # Add volatility adjustment for high-beta portfolios
            if portfolio_beta > 1:
                volatility_factor = 1 + (portfolio_beta - 1) * 0.2
                estimated_loss *= volatility_factor
            
            loss_amount = abs(estimated_loss) * portfolio_value
            
            # Rough recovery estimate (markets historically recover)
            recovery_days = int(params["duration_days"] * 1.5) if params["duration_days"] > 1 else None
            
            results.append(StressTestResult(
                scenario=scenario.value,
                scenario_name=params["name"],
                description=params["description"],
                market_return=market_return,
                estimated_portfolio_loss=estimated_loss,
                estimated_loss_amount=loss_amount,
                recovery_estimate_days=recovery_days,
            ))
        
        # Sort by severity
        results.sort(key=lambda x: x.estimated_portfolio_loss)
        
        return results
    
    # ================================
    # Custom Stress Test
    # ================================
    
    def custom_stress_test(
        self,
        portfolio_beta: float,
        portfolio_value: float,
        market_drop_percent: float,
        scenario_name: str = "Custom Scenario",
    ) -> StressTestResult:
        """Run a custom stress test with user-specified parameters."""
        market_return = -abs(market_drop_percent) / 100
        estimated_loss = market_return * portfolio_beta
        
        if portfolio_beta > 1:
            volatility_factor = 1 + (portfolio_beta - 1) * 0.2
            estimated_loss *= volatility_factor
        
        loss_amount = abs(estimated_loss) * portfolio_value
        
        return StressTestResult(
            scenario="custom",
            scenario_name=scenario_name,
            description=f"Custom {abs(market_drop_percent):.0f}% market drop scenario",
            market_return=market_return,
            estimated_portfolio_loss=estimated_loss,
            estimated_loss_amount=loss_amount,
            recovery_estimate_days=None,
        )
    
    # ================================
    # Composite Risk Score
    # ================================
    
    def calculate_risk_score(
        self,
        var: VaRResult,
        beta: BetaResult,
        volatility: VolatilityResult,
    ) -> tuple[float, str]:
        """
        Calculate composite risk score (0-100) and risk level.
        
        Components:
        - VaR (30%): Higher VaR = higher risk
        - Beta (30%): Higher beta = higher risk
        - Volatility (40%): Higher vol = higher risk
        """
        # Normalize VaR (typical range: 1-5% daily)
        var_score = min(100, abs(var.var_95) / 0.05 * 100)
        
        # Normalize Beta (typical range: 0.5-2.0)
        if beta.beta < 0:
            beta_score = 100  # Negative beta is unusual, high risk
        else:
            beta_score = min(100, beta.beta / 1.5 * 100)
        
        # Normalize Volatility (typical range: 10-50% annualized)
        vol_score = min(100, volatility.annualized_volatility / 0.50 * 100)
        
        # Weighted average
        risk_score = (
            var_score * 0.30 +
            beta_score * 0.30 +
            vol_score * 0.40
        )
        
        # Risk level
        if risk_score >= 75:
            risk_level = "very_high"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        return risk_score, risk_level
    
    # ================================
    # Complete Analysis
    # ================================
    
    def calculate_full_risk_metrics(
        self,
        portfolio_returns: list[float],
        benchmark_returns: list[float],
        portfolio_value: float,
        var_method: str = "historical",
        stress_scenarios: list[StressScenario] | None = None,
    ) -> RiskMetricsSummary:
        """Calculate all risk metrics in one call."""
        # VaR
        var = self.calculate_var(
            portfolio_returns,
            portfolio_value,
            method=var_method,
        )
        
        # Beta
        beta = self.calculate_beta(portfolio_returns, benchmark_returns)
        
        # Volatility
        volatility = self.calculate_volatility(portfolio_returns)
        
        # Stress tests
        stress_tests = self.run_stress_tests(
            beta.beta,
            portfolio_value,
            stress_scenarios,
        )
        
        # Risk score
        risk_score, risk_level = self.calculate_risk_score(var, beta, volatility)
        
        return RiskMetricsSummary(
            var=var,
            beta=beta,
            volatility=volatility,
            stress_tests=stress_tests,
            risk_score=risk_score,
            risk_level=risk_level,
        )
    
    # ================================
    # Sample Data Generation
    # ================================
    
    def generate_sample_returns(
        self,
        days: int = 252,
        mean: float = 0.0004,  # ~10% annual
        volatility: float = 0.015,  # ~24% annual
    ) -> np.ndarray:
        """Generate sample return data for demonstration."""
        np.random.seed(42)
        return np.random.normal(mean, volatility, days)
    
    def generate_benchmark_returns(
        self,
        days: int = 252,
        mean: float = 0.0003,  # ~8% annual
        volatility: float = 0.012,  # ~19% annual
    ) -> np.ndarray:
        """Generate sample benchmark returns (S&P 500-like)."""
        np.random.seed(123)
        return np.random.normal(mean, volatility, days)


# ============================================
# Factory Function
# ============================================


def get_risk_metrics_service(price_fetcher: Any = None) -> RiskMetricsService:
    """Get RiskMetricsService instance."""
    return RiskMetricsService(price_fetcher=price_fetcher)

