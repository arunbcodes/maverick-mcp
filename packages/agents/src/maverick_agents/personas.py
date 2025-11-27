"""
Investor persona definitions for persona-aware agents.

Provides risk parameter configurations for different investor profiles,
and base tool classes that adapt behavior based on investor personas.
"""

from datetime import datetime
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

# Default cache TTL in seconds (1 hour)
DEFAULT_CACHE_TTL_SECONDS = 3600


class InvestorPersona(BaseModel):
    """Defines an investor persona with risk parameters."""

    name: str
    risk_tolerance: tuple[int, int] = Field(
        description="Risk tolerance range (min, max) on 0-100 scale"
    )
    position_size_max: float = Field(
        description="Maximum position size as percentage of portfolio"
    )
    stop_loss_multiplier: float = Field(
        description="Multiplier for stop loss calculation"
    )
    preferred_timeframe: str = Field(
        default="swing", description="Preferred trading timeframe: day, swing, position"
    )
    characteristics: list[str] = Field(
        default_factory=list, description="Key behavioral characteristics"
    )


# Default risk parameters for each persona type
# These can be overridden via configuration injection
DEFAULT_PERSONA_PARAMS = {
    "conservative": {
        "risk_tolerance_min": 10,
        "risk_tolerance_max": 30,
        "max_position_size": 0.05,  # 5%
        "stop_loss_multiplier": 0.8,
    },
    "moderate": {
        "risk_tolerance_min": 30,
        "risk_tolerance_max": 60,
        "max_position_size": 0.10,  # 10%
        "stop_loss_multiplier": 1.0,
    },
    "aggressive": {
        "risk_tolerance_min": 60,
        "risk_tolerance_max": 85,
        "max_position_size": 0.15,  # 15%
        "stop_loss_multiplier": 1.2,
    },
    "day_trader": {
        "risk_tolerance_min": 70,
        "risk_tolerance_max": 95,
        "max_position_size": 0.25,  # 25%
        "stop_loss_multiplier": 1.5,
    },
}


def create_default_personas(
    params: dict[str, dict] | None = None,
) -> dict[str, InvestorPersona]:
    """
    Create default investor personas with optional parameter overrides.

    Args:
        params: Optional dictionary to override default parameters.
                Structure: {persona_name: {param_name: value}}

    Returns:
        Dictionary of persona name to InvestorPersona instance
    """
    effective_params = DEFAULT_PERSONA_PARAMS.copy()
    if params:
        for persona_name, overrides in params.items():
            if persona_name in effective_params:
                effective_params[persona_name].update(overrides)

    return {
        "conservative": InvestorPersona(
            name="Conservative",
            risk_tolerance=(
                effective_params["conservative"]["risk_tolerance_min"],
                effective_params["conservative"]["risk_tolerance_max"],
            ),
            position_size_max=effective_params["conservative"]["max_position_size"],
            stop_loss_multiplier=effective_params["conservative"]["stop_loss_multiplier"],
            preferred_timeframe="position",
            characteristics=[
                "Prioritizes capital preservation",
                "Focuses on dividend stocks",
                "Prefers established companies",
                "Long-term oriented",
            ],
        ),
        "moderate": InvestorPersona(
            name="Moderate",
            risk_tolerance=(
                effective_params["moderate"]["risk_tolerance_min"],
                effective_params["moderate"]["risk_tolerance_max"],
            ),
            position_size_max=effective_params["moderate"]["max_position_size"],
            stop_loss_multiplier=effective_params["moderate"]["stop_loss_multiplier"],
            preferred_timeframe="swing",
            characteristics=[
                "Balanced risk/reward approach",
                "Mix of growth and value",
                "Diversified portfolio",
                "Medium-term focus",
            ],
        ),
        "aggressive": InvestorPersona(
            name="Aggressive",
            risk_tolerance=(
                effective_params["aggressive"]["risk_tolerance_min"],
                effective_params["aggressive"]["risk_tolerance_max"],
            ),
            position_size_max=effective_params["aggressive"]["max_position_size"],
            stop_loss_multiplier=effective_params["aggressive"]["stop_loss_multiplier"],
            preferred_timeframe="day",
            characteristics=[
                "High risk tolerance",
                "Growth-focused",
                "Momentum trading",
                "Short-term opportunities",
            ],
        ),
        "day_trader": InvestorPersona(
            name="Day Trader",
            risk_tolerance=(
                effective_params["day_trader"]["risk_tolerance_min"],
                effective_params["day_trader"]["risk_tolerance_max"],
            ),
            position_size_max=effective_params["day_trader"]["max_position_size"],
            stop_loss_multiplier=effective_params["day_trader"]["stop_loss_multiplier"],
            preferred_timeframe="day",
            characteristics=[
                "Intraday positions only",
                "High-frequency trading",
                "Technical analysis focused",
                "Tight risk controls",
            ],
        ),
    }


# Default personas instance for convenience
INVESTOR_PERSONAS = create_default_personas()


def get_persona(name: str) -> InvestorPersona:
    """
    Get an investor persona by name.

    Args:
        name: Persona name (conservative, moderate, aggressive, day_trader)

    Returns:
        InvestorPersona instance

    Raises:
        KeyError: If persona name is not found
    """
    if name not in INVESTOR_PERSONAS:
        raise KeyError(
            f"Unknown persona: {name}. "
            f"Available: {list(INVESTOR_PERSONAS.keys())}"
        )
    return INVESTOR_PERSONAS[name]


class PersonaAwareTool(BaseTool):
    """Base class for tools that adapt to investor personas."""

    persona: InvestorPersona | None = None
    # State tracking
    last_analysis_time: dict[str, datetime] = {}
    analyzed_stocks: dict[str, dict] = {}
    key_price_levels: dict[str, dict] = {}
    # Cache settings - can be overridden via constructor
    cache_ttl: int = DEFAULT_CACHE_TTL_SECONDS

    def set_persona(self, persona: InvestorPersona) -> None:
        """Set the active investor persona."""
        self.persona = persona

    def adjust_for_risk(self, value: float, parameter_type: str) -> float:
        """Adjust a value based on the persona's risk profile."""
        if not self.persona:
            return value

        # Get average risk tolerance
        risk_avg = sum(self.persona.risk_tolerance) / 2
        risk_factor = risk_avg / 50  # Normalize to 1.0 at moderate risk

        # Adjust based on parameter type
        if parameter_type == "position_size":
            # Kelly Criterion-inspired sizing
            kelly_fraction = self._calculate_kelly_fraction(risk_factor)
            adjusted = value * kelly_fraction
            return min(adjusted, self.persona.position_size_max)
        elif parameter_type == "stop_loss":
            # ATR-based dynamic stops
            return value * self.persona.stop_loss_multiplier
        elif parameter_type == "profit_target":
            # Risk-adjusted targets
            return value * (2 - risk_factor)  # Conservative = lower targets
        elif parameter_type == "volatility_filter":
            # Volatility tolerance
            return value * (2 - risk_factor)  # Conservative = lower vol tolerance
        elif parameter_type == "time_horizon":
            # Holding period in days
            if self.persona.preferred_timeframe == "day":
                return 1
            elif self.persona.preferred_timeframe == "swing":
                return 5 * risk_factor  # 2.5-7.5 days
            else:  # position
                return 20 * risk_factor  # 10-30 days
        else:
            return value

    def _calculate_kelly_fraction(self, risk_factor: float) -> float:
        """Calculate position size using Kelly Criterion."""
        # Simplified Kelly: f = (p*b - q) / b
        # where p = win probability, b = win/loss ratio, q = loss probability
        # Using risk factor to adjust expected win rate
        win_probability = 0.45 + (0.1 * risk_factor)  # 45-55% base win rate
        win_loss_ratio = 2.0  # 2:1 reward/risk
        loss_probability = 1 - win_probability

        kelly = (win_probability * win_loss_ratio - loss_probability) / win_loss_ratio

        # Apply safety factor (never use full Kelly)
        safety_factor = 0.25  # Use 25% of Kelly
        return max(0, kelly * safety_factor)

    def update_analysis_data(self, symbol: str, analysis_data: dict[str, Any]):
        """Update stored analysis data for a symbol."""
        symbol = symbol.upper()
        self.analyzed_stocks[symbol] = analysis_data
        self.last_analysis_time[symbol] = datetime.now()
        if "price_levels" in analysis_data:
            self.key_price_levels[symbol] = analysis_data["price_levels"]

    def get_stock_context(self, symbol: str) -> dict[str, Any]:
        """Get stored context for a symbol."""
        symbol = symbol.upper()
        return {
            "analysis": self.analyzed_stocks.get(symbol, {}),
            "last_analysis": self.last_analysis_time.get(symbol),
            "price_levels": self.key_price_levels.get(symbol, {}),
            "cache_expired": self._is_cache_expired(symbol),
        }

    def _is_cache_expired(self, symbol: str) -> bool:
        """Check if cached data has expired."""
        last_time = self.last_analysis_time.get(symbol.upper())
        if not last_time:
            return True

        age_seconds = (datetime.now() - last_time).total_seconds()
        return age_seconds > self.cache_ttl

    def _adjust_risk_parameters(self, params: dict) -> dict:
        """Adjust parameters based on risk profile."""
        if not self.persona:
            return params

        risk_factor = sum(self.persona.risk_tolerance) / 100  # 0.1-0.9 scale

        # Apply risk adjustments based on parameter names
        adjusted = {}
        for key, value in params.items():
            if isinstance(value, int | float):
                key_lower = key.lower()
                if any(term in key_lower for term in ["stop", "support", "risk"]):
                    # Wider stops/support for conservative, tighter for aggressive
                    adjusted[key] = value * (2 - risk_factor)
                elif any(
                    term in key_lower for term in ["resistance", "target", "profit"]
                ):
                    # Lower targets for conservative, higher for aggressive
                    adjusted[key] = value * risk_factor
                elif any(term in key_lower for term in ["size", "amount", "shares"]):
                    # Smaller positions for conservative, larger for aggressive
                    adjusted[key] = self.adjust_for_risk(value, "position_size")
                elif any(term in key_lower for term in ["volume", "liquidity"]):
                    # Higher liquidity requirements for conservative
                    adjusted[key] = value * (2 - risk_factor)
                elif any(term in key_lower for term in ["volatility", "atr", "std"]):
                    # Lower volatility tolerance for conservative
                    adjusted[key] = self.adjust_for_risk(value, "volatility_filter")
                else:
                    adjusted[key] = value
            else:
                adjusted[key] = value

        return adjusted

    def _validate_risk_levels(self, data: dict) -> bool:
        """Validate if the data meets the persona's risk criteria."""
        if not self.persona:
            return True

        min_risk, max_risk = self.persona.risk_tolerance

        # Extract risk metrics
        volatility = data.get("volatility", 0)
        beta = data.get("beta", 1.0)

        # Convert to risk score (0-100)
        volatility_score = min(100, volatility * 2)  # Assume 50% vol = 100 risk
        beta_score = abs(beta - 1) * 100  # Distance from market

        # Combined risk score
        risk_score = (volatility_score + beta_score) / 2

        if risk_score < min_risk or risk_score > max_risk:
            return False

        # Persona-specific validations
        if self.persona.name == "Conservative":
            # Additional checks for conservative investors
            if data.get("debt_to_equity", 0) > 1.5:
                return False
            if data.get("current_ratio", 0) < 1.5:
                return False
            if data.get("dividend_yield", 0) < 0.02:  # Prefer dividend stocks
                return False
        elif self.persona.name == "Day Trader":
            # Day traders need high liquidity
            if data.get("average_volume", 0) < 1_000_000:
                return False
            if data.get("spread_percentage", 0) > 0.1:  # Tight spreads only
                return False

        return True

    def format_for_persona(self, data: dict) -> dict:
        """Format output data based on persona preferences."""
        if not self.persona:
            return data

        formatted = data.copy()

        # Add persona-specific insights
        formatted["persona_insights"] = {
            "suitable_for_profile": self._validate_risk_levels(data),
            "risk_adjusted_parameters": self._adjust_risk_parameters(
                data.get("parameters", {})
            ),
            "recommended_timeframe": self.persona.preferred_timeframe,
            "max_position_size": self.persona.position_size_max,
        }

        # Add risk warnings if needed
        warnings = []
        if not self._validate_risk_levels(data):
            warnings.append(f"Risk profile outside {self.persona.name} parameters")

        if data.get("volatility", 0) > 50:
            warnings.append("High volatility - consider smaller position size")

        if warnings:
            formatted["risk_warnings"] = warnings

        return formatted
