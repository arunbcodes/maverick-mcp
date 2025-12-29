"""
Natural language strategy parser for backtesting.

Parses user descriptions into structured strategy configurations.
"""

import re
from dataclasses import dataclass


@dataclass
class ParsedStrategy:
    """Result of parsing a strategy description."""

    strategy_type: str
    parameters: dict
    confidence: float


class StrategyParser:
    """
    Parse natural language strategy descriptions into structured parameters.

    Supports common trading strategy patterns like:
    - Moving average crossovers
    - RSI overbought/oversold
    - MACD signals
    - Bollinger Band breakouts
    """

    # Pattern matchers for common strategies
    PATTERNS = {
        "sma_cross": [
            r"(\d+)[\s-]*(?:day|period)?\s*(?:and|&)?\s*(\d+)[\s-]*(?:day|period)?\s*(?:moving\s*average|sma|ma)\s*cross",
            r"(?:sma|ma|moving\s*average)\s*cross(?:over)?\s*(?:with\s*)?(\d+)\s*(?:and|&)\s*(\d+)",
            r"(\d+)\s*(?:sma|ma)\s*(?:crosses?|cross(?:ing)?)\s*(\d+)\s*(?:sma|ma)",
        ],
        "rsi": [
            r"rsi\s*(?:below|under|<)\s*(\d+).*(?:above|over|>)\s*(\d+)",
            r"(?:buy|long)\s*(?:when\s*)?rsi\s*(?:is\s*)?(?:below|under|<)\s*(\d+)",
            r"rsi\s*(\d+)\s*(?:period)?",
        ],
        "macd": [
            r"macd\s*(?:signal|cross)",
            r"macd\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)",
        ],
        "bollinger": [
            r"bollinger\s*band",
            r"bb\s*(?:breakout|squeeze)",
        ],
        "momentum": [
            r"momentum\s*(?:strategy)?",
            r"(\d+)[\s-]*(?:day|period)?\s*momentum",
        ],
    }

    def parse(self, description: str) -> ParsedStrategy:
        """
        Parse a natural language strategy description.

        Args:
            description: Natural language description of trading strategy

        Returns:
            ParsedStrategy with type, parameters, and confidence score

        Examples:
            >>> parser = StrategyParser()
            >>> result = parser.parse("Buy when RSI is below 30 and sell when above 70")
            >>> result.strategy_type
            'rsi'
            >>> result.parameters
            {'oversold': 30, 'overbought': 70, 'period': 14}
        """
        description_lower = description.lower()

        # Try each strategy pattern
        for strategy_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, description_lower)
                if match:
                    params, confidence = self._extract_params(
                        strategy_type, match, description_lower
                    )
                    return ParsedStrategy(
                        strategy_type=strategy_type,
                        parameters=params,
                        confidence=confidence,
                    )

        # Default fallback
        return ParsedStrategy(
            strategy_type="sma_cross",
            parameters={"fast_period": 10, "slow_period": 20},
            confidence=0.3,
        )

    def _extract_params(
        self, strategy_type: str, match: re.Match, description: str
    ) -> tuple[dict, float]:
        """Extract parameters from regex match."""
        groups = match.groups()

        if strategy_type == "sma_cross":
            if len(groups) >= 2 and groups[0] and groups[1]:
                fast = min(int(groups[0]), int(groups[1]))
                slow = max(int(groups[0]), int(groups[1]))
                return {"fast_period": fast, "slow_period": slow}, 0.9
            return {"fast_period": 10, "slow_period": 20}, 0.7

        elif strategy_type == "rsi":
            params = {"period": 14}
            if len(groups) >= 2 and groups[0] and groups[1]:
                params["oversold"] = int(groups[0])
                params["overbought"] = int(groups[1])
                return params, 0.9
            elif len(groups) >= 1 and groups[0]:
                val = int(groups[0])
                if val <= 50:
                    params["oversold"] = val
                    params["overbought"] = 100 - val
                else:
                    params["period"] = val
                return params, 0.7
            params["oversold"] = 30
            params["overbought"] = 70
            return params, 0.6

        elif strategy_type == "macd":
            if len(groups) >= 3 and all(groups[:3]):
                return {
                    "fast_period": int(groups[0]),
                    "slow_period": int(groups[1]),
                    "signal_period": int(groups[2]),
                }, 0.9
            return {"fast_period": 12, "slow_period": 26, "signal_period": 9}, 0.7

        elif strategy_type == "bollinger":
            # Extract period and std_dev if mentioned
            period_match = re.search(r"(\d+)[\s-]*(?:day|period)", description)
            std_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:std|standard)", description)
            return {
                "period": int(period_match.group(1)) if period_match else 20,
                "std_dev": float(std_match.group(1)) if std_match else 2.0,
            }, 0.8

        elif strategy_type == "momentum":
            if len(groups) >= 1 and groups[0]:
                return {"period": int(groups[0])}, 0.8
            return {"period": 14}, 0.6

        return {}, 0.5


__all__ = ["StrategyParser", "ParsedStrategy"]
