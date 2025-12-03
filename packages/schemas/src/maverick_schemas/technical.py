"""
Technical analysis models.

Models for RSI, MACD, Bollinger Bands, and other technical indicators.
"""

from decimal import Decimal

from pydantic import Field

from maverick_schemas.base import MaverickBaseModel, TrendDirection


class RSIAnalysis(MaverickBaseModel):
    """RSI (Relative Strength Index) analysis."""
    
    ticker: str = Field(description="Stock ticker symbol")
    current_rsi: Decimal = Field(description="Current RSI value (0-100)")
    period: int = Field(default=14, description="RSI period")
    
    # Interpretation
    signal: str = Field(description="Signal: oversold, neutral, overbought")
    strength: str = Field(description="Signal strength: weak, moderate, strong")
    
    # Historical context
    rsi_high: Decimal | None = Field(default=None, description="Recent RSI high")
    rsi_low: Decimal | None = Field(default=None, description="Recent RSI low")
    days_oversold: int = Field(default=0, description="Days in oversold territory")
    days_overbought: int = Field(default=0, description="Days in overbought territory")
    
    # Thresholds used
    oversold_threshold: Decimal = Field(default=Decimal("30"), description="Oversold threshold")
    overbought_threshold: Decimal = Field(default=Decimal("70"), description="Overbought threshold")


class MACDAnalysis(MaverickBaseModel):
    """MACD (Moving Average Convergence Divergence) analysis."""
    
    ticker: str = Field(description="Stock ticker symbol")
    
    # MACD components
    macd_line: Decimal = Field(description="MACD line value")
    signal_line: Decimal = Field(description="Signal line value")
    histogram: Decimal = Field(description="MACD histogram value")
    
    # Parameters
    fast_period: int = Field(default=12, description="Fast EMA period")
    slow_period: int = Field(default=26, description="Slow EMA period")
    signal_period: int = Field(default=9, description="Signal line period")
    
    # Interpretation
    signal: str = Field(description="Signal: bullish_crossover, bearish_crossover, bullish, bearish")
    trend: TrendDirection = Field(description="Trend direction")
    histogram_direction: str = Field(description="Histogram direction: expanding, contracting")
    
    # Crossover info
    days_since_crossover: int | None = Field(default=None, description="Days since last crossover")
    crossover_type: str | None = Field(default=None, description="Last crossover type")


class BollingerBands(MaverickBaseModel):
    """Bollinger Bands analysis."""
    
    ticker: str = Field(description="Stock ticker symbol")
    
    # Band values
    upper_band: Decimal = Field(description="Upper Bollinger Band")
    middle_band: Decimal = Field(description="Middle Band (SMA)")
    lower_band: Decimal = Field(description="Lower Bollinger Band")
    
    # Current price position
    current_price: Decimal = Field(description="Current stock price")
    percent_b: Decimal = Field(description="%B indicator (0-1, can exceed)")
    bandwidth: Decimal = Field(description="Band width as percentage")
    
    # Parameters
    period: int = Field(default=20, description="SMA period")
    std_dev: Decimal = Field(default=Decimal("2.0"), description="Standard deviations")
    
    # Interpretation
    signal: str = Field(description="Signal: squeeze, breakout_up, breakout_down, mean_reversion")
    position: str = Field(description="Price position: above_upper, upper_half, lower_half, below_lower")


class SupportResistance(MaverickBaseModel):
    """Support and resistance levels."""
    
    ticker: str = Field(description="Stock ticker symbol")
    current_price: Decimal = Field(description="Current stock price")
    
    # Key levels
    support_levels: list[Decimal] = Field(description="Support levels (strongest first)")
    resistance_levels: list[Decimal] = Field(description="Resistance levels (closest first)")
    
    # Pivot points
    pivot_point: Decimal | None = Field(default=None, description="Classic pivot point")
    r1: Decimal | None = Field(default=None, description="Resistance 1")
    r2: Decimal | None = Field(default=None, description="Resistance 2")
    r3: Decimal | None = Field(default=None, description="Resistance 3")
    s1: Decimal | None = Field(default=None, description="Support 1")
    s2: Decimal | None = Field(default=None, description="Support 2")
    s3: Decimal | None = Field(default=None, description="Support 3")
    
    # Analysis period
    lookback_days: int = Field(default=90, description="Lookback period for analysis")


class MovingAverages(MaverickBaseModel):
    """Moving averages analysis."""
    
    ticker: str = Field(description="Stock ticker symbol")
    current_price: Decimal = Field(description="Current stock price")
    
    # Simple Moving Averages
    sma_20: Decimal | None = Field(default=None, description="20-day SMA")
    sma_50: Decimal | None = Field(default=None, description="50-day SMA")
    sma_100: Decimal | None = Field(default=None, description="100-day SMA")
    sma_200: Decimal | None = Field(default=None, description="200-day SMA")
    
    # Exponential Moving Averages
    ema_12: Decimal | None = Field(default=None, description="12-day EMA")
    ema_26: Decimal | None = Field(default=None, description="26-day EMA")
    ema_50: Decimal | None = Field(default=None, description="50-day EMA")
    
    # Position relative to MAs
    above_sma_20: bool = Field(description="Price above 20 SMA")
    above_sma_50: bool = Field(description="Price above 50 SMA")
    above_sma_200: bool = Field(description="Price above 200 SMA")
    
    # Golden/Death cross
    golden_cross: bool = Field(default=False, description="50 SMA above 200 SMA")
    death_cross: bool = Field(default=False, description="50 SMA below 200 SMA")


class TechnicalSummary(MaverickBaseModel):
    """Comprehensive technical analysis summary."""
    
    ticker: str = Field(description="Stock ticker symbol")
    
    # Individual indicators
    rsi: RSIAnalysis | None = Field(default=None)
    macd: MACDAnalysis | None = Field(default=None)
    bollinger: BollingerBands | None = Field(default=None)
    support_resistance: SupportResistance | None = Field(default=None)
    moving_averages: MovingAverages | None = Field(default=None)
    
    # Overall assessment
    trend: TrendDirection = Field(description="Overall trend direction")
    trend_strength: Decimal = Field(description="Trend strength (0-100)")
    
    # Signal summary
    buy_signals: int = Field(default=0, description="Number of buy signals")
    sell_signals: int = Field(default=0, description="Number of sell signals")
    neutral_signals: int = Field(default=0, description="Number of neutral signals")
    
    # Overall recommendation
    recommendation: str = Field(description="Overall recommendation: strong_buy, buy, hold, sell, strong_sell")
    confidence: Decimal = Field(description="Confidence score (0-100)")


__all__ = [
    "RSIAnalysis",
    "MACDAnalysis",
    "BollingerBands",
    "SupportResistance",
    "MovingAverages",
    "TechnicalSummary",
]

