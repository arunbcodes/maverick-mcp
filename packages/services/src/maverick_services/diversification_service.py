"""
Diversification Service.

Calculate portfolio diversification metrics and provide recommendations.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


# ============================================
# Constants
# ============================================


# GICS Sectors
GICS_SECTORS = [
    "Technology",
    "Healthcare",
    "Financials",
    "Consumer Discretionary",
    "Communication Services",
    "Industrials",
    "Consumer Staples",
    "Energy",
    "Utilities",
    "Real Estate",
    "Materials",
]

# S&P 500 sector weights (approximate)
SP500_SECTOR_WEIGHTS = {
    "Technology": 28.5,
    "Healthcare": 13.2,
    "Financials": 12.8,
    "Consumer Discretionary": 10.5,
    "Communication Services": 8.8,
    "Industrials": 8.5,
    "Consumer Staples": 6.5,
    "Energy": 4.2,
    "Utilities": 2.5,
    "Real Estate": 2.5,
    "Materials": 2.0,
}


# ============================================
# Enums and Data Classes
# ============================================


class DiversificationLevel(Enum):
    """Diversification level classification."""
    
    EXCELLENT = "excellent"  # 80-100
    GOOD = "good"           # 60-79
    MODERATE = "moderate"   # 40-59
    POOR = "poor"           # 20-39
    VERY_POOR = "very_poor" # 0-19


@dataclass
class PositionConcentration:
    """Concentration data for a single position."""
    
    ticker: str
    weight: float  # Percentage of portfolio
    is_overconcentrated: bool
    max_recommended: float = 20.0  # Default 20% max


@dataclass
class SectorConcentration:
    """Concentration data for a sector."""
    
    sector: str
    weight: float
    benchmark_weight: float  # S&P 500 weight
    deviation: float  # Difference from benchmark
    is_overweight: bool
    is_underweight: bool


@dataclass
class DiversificationBreakdown:
    """Breakdown of diversification score components."""
    
    # Component scores (0-100 each)
    position_score: float  # Based on HHI
    sector_score: float    # Based on sector distribution
    correlation_score: float  # Based on avg correlation
    concentration_score: float  # Based on largest position
    
    # Weights (must sum to 1.0)
    position_weight: float = 0.3
    sector_weight: float = 0.3
    correlation_weight: float = 0.2
    concentration_weight: float = 0.2
    
    def to_dict(self) -> dict:
        return {
            "position_score": round(self.position_score, 1),
            "sector_score": round(self.sector_score, 1),
            "correlation_score": round(self.correlation_score, 1),
            "concentration_score": round(self.concentration_score, 1),
            "weights": {
                "position": self.position_weight,
                "sector": self.sector_weight,
                "correlation": self.correlation_weight,
                "concentration": self.concentration_weight,
            },
        }


@dataclass
class DiversificationScore:
    """Complete diversification analysis result."""
    
    # Overall score (0-100)
    score: float
    level: DiversificationLevel
    
    # HHI metrics
    hhi: float  # Herfindahl-Hirschman Index (0-10000)
    hhi_normalized: float  # Normalized to 0-100 scale
    effective_positions: float  # 1/HHI normalized
    
    # Position analysis
    position_count: int
    largest_position: PositionConcentration | None
    overconcentrated_positions: list[PositionConcentration]
    
    # Sector analysis
    sector_breakdown: list[SectorConcentration]
    sector_count: int
    
    # Average correlation (if available)
    avg_correlation: float | None
    
    # Score breakdown
    breakdown: DiversificationBreakdown
    
    # Recommendations
    recommendations: list[str]
    
    # Metadata
    calculated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 1),
            "level": self.level.value,
            "hhi": round(self.hhi, 2),
            "hhi_normalized": round(self.hhi_normalized, 1),
            "effective_positions": round(self.effective_positions, 1),
            "position_count": self.position_count,
            "largest_position": {
                "ticker": self.largest_position.ticker,
                "weight": round(self.largest_position.weight, 2),
                "is_overconcentrated": self.largest_position.is_overconcentrated,
            } if self.largest_position else None,
            "overconcentrated_count": len(self.overconcentrated_positions),
            "sector_count": self.sector_count,
            "avg_correlation": round(self.avg_correlation, 3) if self.avg_correlation else None,
            "breakdown": self.breakdown.to_dict(),
            "recommendations": self.recommendations,
            "calculated_at": self.calculated_at.isoformat(),
        }


# ============================================
# Diversification Service
# ============================================


class DiversificationService:
    """
    Service for calculating portfolio diversification metrics.
    
    Features:
    - Diversification score (0-100)
    - HHI concentration index
    - Effective number of positions
    - Position limit checks
    - Sector balance analysis
    - Correlation penalty
    - Actionable recommendations
    """
    
    # Thresholds
    MAX_POSITION_WEIGHT = 20.0  # Flag if > 20%
    HIGH_CONCENTRATION_THRESHOLD = 25.0  # Warning if > 25%
    SECTOR_OVERWEIGHT_THRESHOLD = 10.0  # Flag if > 10% above benchmark
    
    def __init__(self):
        pass
    
    # ================================
    # Main Score Calculation
    # ================================
    
    def calculate_diversification_score(
        self,
        positions: list[dict],
        sector_map: dict[str, str] | None = None,
        avg_correlation: float | None = None,
    ) -> DiversificationScore:
        """
        Calculate comprehensive diversification score.
        
        Args:
            positions: List of position dicts with 'ticker', 'market_value'
            sector_map: Optional mapping of ticker -> sector
            avg_correlation: Optional average portfolio correlation
        
        Returns:
            DiversificationScore with all metrics and recommendations
        """
        if not positions:
            return self._empty_score()
        
        # Calculate weights
        total_value = sum(p.get("market_value", 0) or p.get("cost_basis", 0) for p in positions)
        if total_value <= 0:
            return self._empty_score()
        
        weights = []
        position_concentrations = []
        
        for p in positions:
            value = p.get("market_value", 0) or p.get("cost_basis", 0)
            weight = (value / total_value) * 100
            weights.append(weight)
            
            pc = PositionConcentration(
                ticker=p.get("ticker", ""),
                weight=weight,
                is_overconcentrated=weight > self.MAX_POSITION_WEIGHT,
            )
            position_concentrations.append(pc)
        
        # Sort by weight descending
        position_concentrations.sort(key=lambda x: x.weight, reverse=True)
        
        # Calculate HHI
        hhi = sum(w ** 2 for w in weights)
        hhi_normalized = min(100, (10000 - hhi) / 100)  # Higher = more diversified
        
        # Effective positions (1/HHI normalized to nice scale)
        effective_positions = 10000 / hhi if hhi > 0 else 0
        
        # Overconcentrated positions
        overconcentrated = [pc for pc in position_concentrations if pc.is_overconcentrated]
        
        # Sector analysis
        sector_breakdown = self._calculate_sector_breakdown(positions, sector_map, total_value)
        
        # Calculate component scores
        position_score = self._calculate_position_score(hhi)
        sector_score = self._calculate_sector_score(sector_breakdown)
        correlation_score = self._calculate_correlation_score(avg_correlation)
        concentration_score = self._calculate_concentration_score(
            position_concentrations[0].weight if position_concentrations else 0
        )
        
        breakdown = DiversificationBreakdown(
            position_score=position_score,
            sector_score=sector_score,
            correlation_score=correlation_score,
            concentration_score=concentration_score,
        )
        
        # Calculate overall score
        overall_score = (
            breakdown.position_score * breakdown.position_weight +
            breakdown.sector_score * breakdown.sector_weight +
            breakdown.correlation_score * breakdown.correlation_weight +
            breakdown.concentration_score * breakdown.concentration_weight
        )
        
        # Determine level
        level = self._score_to_level(overall_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            position_concentrations,
            sector_breakdown,
            avg_correlation,
            overall_score,
        )
        
        return DiversificationScore(
            score=overall_score,
            level=level,
            hhi=hhi,
            hhi_normalized=hhi_normalized,
            effective_positions=effective_positions,
            position_count=len(positions),
            largest_position=position_concentrations[0] if position_concentrations else None,
            overconcentrated_positions=overconcentrated,
            sector_breakdown=sector_breakdown,
            sector_count=len(set(s.sector for s in sector_breakdown if s.weight > 0)),
            avg_correlation=avg_correlation,
            breakdown=breakdown,
            recommendations=recommendations,
        )
    
    # ================================
    # Component Score Calculations
    # ================================
    
    def _calculate_position_score(self, hhi: float) -> float:
        """
        Convert HHI to a 0-100 score.
        
        HHI ranges from 0 (infinite positions) to 10000 (single position).
        - HHI < 1000: Well diversified (score 80-100)
        - HHI 1000-2500: Moderate (score 50-80)
        - HHI 2500-5000: Concentrated (score 20-50)
        - HHI > 5000: Highly concentrated (score 0-20)
        """
        if hhi <= 500:
            return 100
        elif hhi <= 1000:
            return 100 - (hhi - 500) / 500 * 20  # 80-100
        elif hhi <= 2500:
            return 80 - (hhi - 1000) / 1500 * 30  # 50-80
        elif hhi <= 5000:
            return 50 - (hhi - 2500) / 2500 * 30  # 20-50
        else:
            return max(0, 20 - (hhi - 5000) / 5000 * 20)  # 0-20
    
    def _calculate_sector_score(self, sectors: list[SectorConcentration]) -> float:
        """Calculate sector diversification score based on coverage and balance."""
        if not sectors:
            return 0
        
        # Count sectors with meaningful allocation (>2%)
        active_sectors = sum(1 for s in sectors if s.weight > 2)
        
        # Score based on sector count (max 11 GICS sectors)
        count_score = min(100, active_sectors * 12)  # ~8 sectors = 96
        
        # Penalty for extreme over/underweights
        deviation_penalty = 0
        for s in sectors:
            if abs(s.deviation) > 15:
                deviation_penalty += 5
            elif abs(s.deviation) > 10:
                deviation_penalty += 2
        
        return max(0, count_score - deviation_penalty)
    
    def _calculate_correlation_score(self, avg_corr: float | None) -> float:
        """
        Convert average correlation to a 0-100 score.
        
        Lower correlation = better diversification.
        """
        if avg_corr is None:
            return 50  # Neutral if unknown
        
        # Correlation typically ranges 0.2-0.8 for diversified portfolios
        if avg_corr <= 0.2:
            return 100
        elif avg_corr <= 0.4:
            return 100 - (avg_corr - 0.2) / 0.2 * 20  # 80-100
        elif avg_corr <= 0.6:
            return 80 - (avg_corr - 0.4) / 0.2 * 30  # 50-80
        elif avg_corr <= 0.8:
            return 50 - (avg_corr - 0.6) / 0.2 * 30  # 20-50
        else:
            return max(0, 20 - (avg_corr - 0.8) / 0.2 * 20)  # 0-20
    
    def _calculate_concentration_score(self, largest_weight: float) -> float:
        """
        Score based on largest position weight.
        
        Ideal: No position > 10%
        Acceptable: No position > 20%
        Concerning: Any position > 30%
        """
        if largest_weight <= 5:
            return 100
        elif largest_weight <= 10:
            return 100 - (largest_weight - 5) / 5 * 15  # 85-100
        elif largest_weight <= 20:
            return 85 - (largest_weight - 10) / 10 * 35  # 50-85
        elif largest_weight <= 30:
            return 50 - (largest_weight - 20) / 10 * 30  # 20-50
        else:
            return max(0, 20 - (largest_weight - 30) / 20 * 20)  # 0-20
    
    # ================================
    # Sector Analysis
    # ================================
    
    def _calculate_sector_breakdown(
        self,
        positions: list[dict],
        sector_map: dict[str, str] | None,
        total_value: float,
    ) -> list[SectorConcentration]:
        """Calculate sector weights and compare to benchmark."""
        sector_values = {}
        
        for p in positions:
            ticker = p.get("ticker", "")
            value = p.get("market_value", 0) or p.get("cost_basis", 0)
            
            # Get sector from map or position data
            if sector_map and ticker in sector_map:
                sector = sector_map[ticker]
            else:
                sector = p.get("sector", "Unknown")
            
            sector_values[sector] = sector_values.get(sector, 0) + value
        
        # Create concentration objects
        breakdown = []
        for sector in GICS_SECTORS:
            value = sector_values.get(sector, 0)
            weight = (value / total_value * 100) if total_value > 0 else 0
            benchmark = SP500_SECTOR_WEIGHTS.get(sector, 0)
            deviation = weight - benchmark
            
            breakdown.append(SectorConcentration(
                sector=sector,
                weight=weight,
                benchmark_weight=benchmark,
                deviation=deviation,
                is_overweight=deviation > self.SECTOR_OVERWEIGHT_THRESHOLD,
                is_underweight=weight < 1 and benchmark > 5,
            ))
        
        # Add unknown sector if present
        unknown_value = sector_values.get("Unknown", 0)
        if unknown_value > 0:
            breakdown.append(SectorConcentration(
                sector="Unknown",
                weight=unknown_value / total_value * 100,
                benchmark_weight=0,
                deviation=unknown_value / total_value * 100,
                is_overweight=False,
                is_underweight=False,
            ))
        
        # Sort by weight descending
        breakdown.sort(key=lambda x: x.weight, reverse=True)
        
        return breakdown
    
    # ================================
    # Recommendations
    # ================================
    
    def _generate_recommendations(
        self,
        positions: list[PositionConcentration],
        sectors: list[SectorConcentration],
        avg_correlation: float | None,
        score: float,
    ) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Position concentration
        for pos in positions[:3]:  # Top 3 positions
            if pos.weight > self.HIGH_CONCENTRATION_THRESHOLD:
                recommendations.append(
                    f"Consider reducing {pos.ticker} ({pos.weight:.1f}%) to improve diversification"
                )
            elif pos.weight > self.MAX_POSITION_WEIGHT:
                recommendations.append(
                    f"{pos.ticker} is {pos.weight:.1f}% of portfolio - consider trimming to <20%"
                )
        
        # Sector balance
        overweight_sectors = [s for s in sectors if s.is_overweight]
        underweight_sectors = [s for s in sectors if s.is_underweight]
        
        if overweight_sectors:
            top_overweight = overweight_sectors[0]
            recommendations.append(
                f"{top_overweight.sector} is {top_overweight.weight:.1f}% vs {top_overweight.benchmark_weight:.1f}% benchmark - consider rebalancing"
            )
        
        if len(underweight_sectors) >= 3:
            recommendations.append(
                "Portfolio lacks exposure to multiple sectors - consider adding diversification"
            )
        
        # Correlation
        if avg_correlation and avg_correlation > 0.7:
            recommendations.append(
                "High average correlation ({:.2f}) - holdings move together, consider uncorrelated assets".format(avg_correlation)
            )
        
        # General advice based on score
        if score < 40:
            if not recommendations:
                recommendations.append(
                    "Portfolio is highly concentrated - consider adding more positions across sectors"
                )
        elif score < 60:
            if not recommendations:
                recommendations.append(
                    "Moderate diversification - a few more positions or sectors would help"
                )
        
        # Position count
        if len(positions) < 5:
            recommendations.append(
                f"Only {len(positions)} positions - consider adding more for better diversification"
            )
        
        return recommendations[:5]  # Max 5 recommendations
    
    # ================================
    # Helpers
    # ================================
    
    def _score_to_level(self, score: float) -> DiversificationLevel:
        """Convert numeric score to level."""
        if score >= 80:
            return DiversificationLevel.EXCELLENT
        elif score >= 60:
            return DiversificationLevel.GOOD
        elif score >= 40:
            return DiversificationLevel.MODERATE
        elif score >= 20:
            return DiversificationLevel.POOR
        else:
            return DiversificationLevel.VERY_POOR
    
    def _empty_score(self) -> DiversificationScore:
        """Return empty score for portfolios with no positions."""
        return DiversificationScore(
            score=0,
            level=DiversificationLevel.VERY_POOR,
            hhi=10000,
            hhi_normalized=0,
            effective_positions=0,
            position_count=0,
            largest_position=None,
            overconcentrated_positions=[],
            sector_breakdown=[],
            sector_count=0,
            avg_correlation=None,
            breakdown=DiversificationBreakdown(
                position_score=0,
                sector_score=0,
                correlation_score=50,
                concentration_score=0,
            ),
            recommendations=["Add positions to start building a diversified portfolio"],
        )


# ============================================
# Factory Function
# ============================================


def get_diversification_service() -> DiversificationService:
    """Get DiversificationService instance."""
    return DiversificationService()

