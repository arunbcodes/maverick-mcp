"""
Investor persona definitions for persona-aware agents.

Provides risk parameter configurations for different investor profiles.
"""

from pydantic import BaseModel, Field


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
