"""
Screening Service.

Handles stock screening and recommendation generation based on
technical analysis and patterns.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from maverick_data.models import (
    MaverickBearStocks,
    MaverickStocks,
    SupplyDemandBreakoutStocks,
)
from maverick_data.services.bulk_operations import get_latest_maverick_screening
from maverick_data.session import SessionLocal

logger = logging.getLogger(__name__)


class ScreeningService:
    """
    Service for stock screening operations.

    Implements IScreeningProvider interface to provide stock recommendations
    based on Maverick technical analysis patterns.

    Features:
    - Maverick bullish recommendations
    - Maverick bearish recommendations
    - Supply/demand breakout patterns
    - All-in-one screening
    """

    def __init__(self, db_session: Session | None = None):
        """
        Initialize screening service.

        Args:
            db_session: Optional database session for dependency injection
        """
        self._db_session = db_session
        logger.info("ScreeningService initialized")

    def _get_db_session(self) -> tuple[Session, bool]:
        """Get database session."""
        if self._db_session:
            return self._db_session, False

        try:
            session = SessionLocal()
            return session, True
        except Exception as e:
            logger.error(f"Failed to get database session: {e}", exc_info=True)
            raise

    def get_maverick_recommendations(
        self,
        limit: int = 20,
        min_score: int | None = None,
    ) -> list[dict]:
        """
        Get Maverick bullish stock recommendations.

        Args:
            limit: Maximum number of recommendations
            min_score: Minimum combined score filter

        Returns:
            List of stock recommendations with details
        """
        session, should_close = self._get_db_session()
        try:
            # Build query with filtering at database level
            query = session.query(MaverickStocks)

            # Apply min_score filter in the query if specified
            if min_score:
                query = query.filter(MaverickStocks.combined_score >= min_score)

            # Order by score and limit results
            stocks = (
                query.order_by(MaverickStocks.combined_score.desc()).limit(limit).all()
            )

            # Process results with list comprehension for better performance
            recommendations = [
                {
                    **stock.to_dict(),
                    "recommendation_type": "maverick_bullish",
                    "reason": self._generate_maverick_reason(stock),
                }
                for stock in stocks
            ]

            logger.info(f"Retrieved {len(recommendations)} Maverick bullish recommendations")
            return recommendations
        except Exception as e:
            logger.error(f"Error getting maverick recommendations: {e}")
            return []
        finally:
            if should_close:
                session.close()

    def get_maverick_bear_recommendations(
        self,
        limit: int = 20,
        min_score: int | None = None,
    ) -> list[dict]:
        """
        Get Maverick bearish stock recommendations.

        Args:
            limit: Maximum number of recommendations
            min_score: Minimum score filter

        Returns:
            List of bear stock recommendations with details
        """
        session, should_close = self._get_db_session()
        try:
            # Build query with filtering at database level
            query = session.query(MaverickBearStocks)

            # Apply min_score filter in the query if specified
            if min_score:
                query = query.filter(MaverickBearStocks.score >= min_score)

            # Order by score and limit results
            stocks = query.order_by(MaverickBearStocks.score.desc()).limit(limit).all()

            # Process results with list comprehension for better performance
            recommendations = [
                {
                    **stock.to_dict(),
                    "recommendation_type": "maverick_bearish",
                    "reason": self._generate_bear_reason(stock),
                }
                for stock in stocks
            ]

            logger.info(f"Retrieved {len(recommendations)} Maverick bear recommendations")
            return recommendations
        except Exception as e:
            logger.error(f"Error getting bear recommendations: {e}")
            return []
        finally:
            if should_close:
                session.close()

    def get_supply_demand_breakout_recommendations(
        self,
        limit: int = 20,
        min_momentum_score: float | None = None,
    ) -> list[dict]:
        """
        Get stocks showing supply/demand breakout patterns.

        Args:
            limit: Maximum number of recommendations
            min_momentum_score: Minimum momentum score filter

        Returns:
            List of supply/demand breakout recommendations
        """
        session, should_close = self._get_db_session()
        try:
            # Build query with all filters at database level
            query = session.query(SupplyDemandBreakoutStocks).filter(
                # Supply/demand breakout criteria
                SupplyDemandBreakoutStocks.close_price > SupplyDemandBreakoutStocks.sma_50,
                SupplyDemandBreakoutStocks.close_price > SupplyDemandBreakoutStocks.sma_150,
                SupplyDemandBreakoutStocks.close_price > SupplyDemandBreakoutStocks.sma_200,
                # Moving average alignment
                SupplyDemandBreakoutStocks.sma_50 > SupplyDemandBreakoutStocks.sma_150,
                SupplyDemandBreakoutStocks.sma_150 > SupplyDemandBreakoutStocks.sma_200,
            )

            # Apply min_momentum_score filter if specified
            if min_momentum_score:
                query = query.filter(
                    SupplyDemandBreakoutStocks.momentum_score >= min_momentum_score
                )

            # Order by momentum score and limit results
            stocks = (
                query.order_by(SupplyDemandBreakoutStocks.momentum_score.desc())
                .limit(limit)
                .all()
            )

            # Process results
            recommendations = [
                {
                    **stock.to_dict(),
                    "recommendation_type": "supply_demand_breakout",
                    "reason": self._generate_supply_demand_reason(stock),
                }
                for stock in stocks
            ]

            logger.info(
                f"Retrieved {len(recommendations)} supply/demand breakout recommendations"
            )
            return recommendations
        except Exception as e:
            logger.error(f"Error getting breakout recommendations: {e}")
            return []
        finally:
            if should_close:
                session.close()

    def get_all_screening_recommendations(self) -> dict[str, list[dict]]:
        """
        Get all screening recommendations in one call.

        Returns:
            Dictionary with all screening types and their recommendations
        """
        try:
            results = get_latest_maverick_screening()

            # Add recommendation reasons
            for stock in results.get("maverick_stocks", []):
                stock["recommendation_type"] = "maverick_bullish"
                stock["reason"] = self._generate_maverick_reason_from_dict(stock)

            for stock in results.get("maverick_bear_stocks", []):
                stock["recommendation_type"] = "maverick_bearish"
                stock["reason"] = self._generate_bear_reason_from_dict(stock)

            for stock in results.get("supply_demand_breakouts", []):
                stock["recommendation_type"] = "supply_demand_breakout"
                stock["reason"] = self._generate_supply_demand_reason_from_dict(stock)

            logger.info(
                f"Retrieved all recommendations: "
                f"{len(results.get('maverick_stocks', []))} bullish, "
                f"{len(results.get('maverick_bear_stocks', []))} bearish, "
                f"{len(results.get('supply_demand_breakouts', []))} breakouts"
            )
            return results
        except Exception as e:
            logger.error(f"Error getting all screening recommendations: {e}")
            return {
                "maverick_stocks": [],
                "maverick_bear_stocks": [],
                "supply_demand_breakouts": [],
            }

    # Reason generation helpers

    def _generate_maverick_reason(self, stock: MaverickStocks) -> str:
        """Generate recommendation reason for Maverick stock."""
        reasons = []

        combined_score = getattr(stock, "combined_score", None)
        if combined_score is not None and combined_score >= 90:
            reasons.append("Exceptional combined score")
        elif combined_score is not None and combined_score >= 80:
            reasons.append("Strong combined score")

        momentum_score = getattr(stock, "momentum_score", None)
        if momentum_score is not None and momentum_score >= 90:
            reasons.append("outstanding relative strength")
        elif momentum_score is not None and momentum_score >= 80:
            reasons.append("strong relative strength")

        pat = getattr(stock, "pat", None)
        if pat is not None and pat != "":
            reasons.append(f"{pat} pattern detected")

        consolidation = getattr(stock, "consolidation", None)
        if consolidation is not None and consolidation == "yes":
            reasons.append("consolidation characteristics")

        sqz = getattr(stock, "sqz", None)
        if sqz is not None and sqz != "":
            reasons.append(f"squeeze indicator: {sqz}")

        return (
            "Bullish setup with " + ", ".join(reasons)
            if reasons
            else "Strong technical setup"
        )

    def _generate_bear_reason(self, stock: MaverickBearStocks) -> str:
        """Generate recommendation reason for bear stock."""
        reasons = []

        score = getattr(stock, "score", None)
        if score is not None and score >= 90:
            reasons.append("Exceptional bear score")
        elif score is not None and score >= 80:
            reasons.append("Strong bear score")

        momentum_score = getattr(stock, "momentum_score", None)
        if momentum_score is not None and momentum_score <= 30:
            reasons.append("weak relative strength")

        rsi_14 = getattr(stock, "rsi_14", None)
        if rsi_14 is not None and rsi_14 <= 30:
            reasons.append("oversold RSI")

        atr_contraction = getattr(stock, "atr_contraction", False)
        if atr_contraction is True:
            reasons.append("ATR contraction")

        big_down_vol = getattr(stock, "big_down_vol", False)
        if big_down_vol is True:
            reasons.append("heavy selling volume")

        return (
            "Bearish setup with " + ", ".join(reasons)
            if reasons
            else "Weak technical setup"
        )

    def _generate_supply_demand_reason(self, stock: SupplyDemandBreakoutStocks) -> str:
        """Generate recommendation reason for supply/demand breakout stock."""
        reasons = ["Supply/demand breakout from accumulation"]

        momentum_score = getattr(stock, "momentum_score", None)
        if momentum_score is not None and momentum_score >= 90:
            reasons.append("exceptional relative strength")
        elif momentum_score is not None and momentum_score >= 80:
            reasons.append("strong relative strength")

        reasons.append("price above all major moving averages")
        reasons.append("moving averages in proper alignment")

        pat = getattr(stock, "pat", None)
        if pat is not None and pat != "":
            reasons.append(f"{pat} pattern")

        return " with ".join(reasons)

    def _generate_maverick_reason_from_dict(self, stock: dict) -> str:
        """Generate recommendation reason for Maverick stock from dict."""
        reasons = []

        score = stock.get("combined_score", 0)
        if score >= 90:
            reasons.append("Exceptional combined score")
        elif score >= 80:
            reasons.append("Strong combined score")

        momentum = stock.get("momentum_score", 0)
        if momentum >= 90:
            reasons.append("outstanding relative strength")
        elif momentum >= 80:
            reasons.append("strong relative strength")

        if stock.get("pattern"):
            reasons.append(f"{stock['pattern']} pattern detected")

        if stock.get("consolidation") == "yes":
            reasons.append("consolidation characteristics")

        if stock.get("squeeze"):
            reasons.append(f"squeeze indicator: {stock['squeeze']}")

        return (
            "Bullish setup with " + ", ".join(reasons)
            if reasons
            else "Strong technical setup"
        )

    def _generate_bear_reason_from_dict(self, stock: dict) -> str:
        """Generate recommendation reason for bear stock from dict."""
        reasons = []

        score = stock.get("score", 0)
        if score >= 90:
            reasons.append("Exceptional bear score")
        elif score >= 80:
            reasons.append("Strong bear score")

        momentum = stock.get("momentum_score", 100)
        if momentum <= 30:
            reasons.append("weak relative strength")

        rsi = stock.get("rsi_14")
        if rsi and rsi <= 30:
            reasons.append("oversold RSI")

        if stock.get("atr_contraction"):
            reasons.append("ATR contraction")

        if stock.get("big_down_vol"):
            reasons.append("heavy selling volume")

        return (
            "Bearish setup with " + ", ".join(reasons)
            if reasons
            else "Weak technical setup"
        )

    def _generate_supply_demand_reason_from_dict(self, stock: dict) -> str:
        """Generate recommendation reason for supply/demand breakout stock from dict."""
        reasons = ["Supply/demand breakout from accumulation"]

        momentum = stock.get("momentum_score", 0)
        if momentum >= 90:
            reasons.append("exceptional relative strength")
        elif momentum >= 80:
            reasons.append("strong relative strength")

        reasons.append("price above all major moving averages")
        reasons.append("moving averages in proper alignment")

        if stock.get("pattern"):
            reasons.append(f"{stock['pattern']} pattern")

        return " with ".join(reasons)


__all__ = ["ScreeningService"]

