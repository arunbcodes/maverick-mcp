"""
Base tool classes for persona-aware tools.

Provides tool abstractions that adapt behavior based on investor personas.
"""

from datetime import datetime
from typing import Any

from langchain_core.tools import BaseTool

from maverick_agents.personas import InvestorPersona

# Default cache TTL in seconds (1 hour)
DEFAULT_CACHE_TTL_SECONDS = 3600


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
