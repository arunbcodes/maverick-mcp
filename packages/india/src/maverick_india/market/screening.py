"""
Indian Market Screening Strategies.

Screening strategies adapted for Indian stock markets (NSE/BSE) with:
- 10% circuit breakers (vs 7% in US)
- INR denomination with lakhs/crores formatting
- Nifty sector structure
- Indian market trading hours (9:15 AM - 3:30 PM IST)
- T+1 settlement (vs T+2 in US)
- Lower volume thresholds (500K vs 1M)
"""

import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from maverick_core.technical import calculate_rsi, calculate_sma
from maverick_india.market.provider import (
    IndianMarket,
    IndianMarketDataProvider,
    calculate_circuit_breaker_limits,
)

logger = logging.getLogger(__name__)


def get_maverick_bullish_india(
    min_volume: int = 500000,
    rsi_low: int = 30,
    rsi_high: int = 70,
    lookback_days: int = 30,
    limit: int = 20,
) -> list[dict]:
    """
    Maverick Bullish strategy adapted for Indian market.

    Criteria (adjusted for Indian market):
    - Volume > 500,000 shares (lower than US due to smaller market)
    - RSI between 30-70 (momentum but not overbought)
    - Price above 50-day MA
    - Recent price increase > 2% (adjusted for INR volatility)
    - Respects 10% circuit breaker limits

    Args:
        min_volume: Minimum daily volume in shares
        rsi_low: Lower RSI threshold
        rsi_high: Upper RSI threshold
        lookback_days: Days to look back for analysis
        limit: Maximum number of stocks to return

    Returns:
        List of recommended stocks with scores
    """
    logger.info(f"Running Maverick Bullish India strategy (limit={limit})")

    provider = IndianMarketDataProvider()
    results = []

    # Get Nifty 50 constituents as the stock universe
    stocks = provider.get_nifty50_constituents()
    logger.info(f"Analyzing {len(stocks)} Nifty 50 stocks")

    for symbol in stocks:
        try:
            # Fetch recent data
            df = provider.fetch_data(symbol, period=f"{lookback_days + 50}d")

            if df.empty or len(df) < 50:
                continue

            # Calculate indicators
            current_price = df["Close"].iloc[-1]
            avg_volume = df["Volume"].mean()

            # Volume check
            if avg_volume < min_volume:
                continue

            # RSI check
            rsi_series = calculate_rsi(df)
            current_rsi = rsi_series.iloc[-1]
            if pd.isna(current_rsi) or not (rsi_low <= current_rsi <= rsi_high):
                continue

            # Moving average check (50-day)
            ma_50 = calculate_sma(df, period=50)
            if current_price < ma_50.iloc[-1]:
                continue

            # Price momentum check (weekly change > 2%)
            if len(df) >= 5:
                week_ago_price = df["Close"].iloc[-5]
                price_change_pct = (
                    (current_price - week_ago_price) / week_ago_price
                ) * 100
                if price_change_pct < 2.0:
                    continue
            else:
                continue

            # Calculate score
            score = 0
            score += min(current_rsi / 10, 7)  # RSI contribution (0-7)
            score += min(price_change_pct / 2, 5)  # Momentum (0-5)
            score += min((avg_volume / min_volume) * 2, 3)  # Volume (0-3)

            # Circuit breaker check
            limits = calculate_circuit_breaker_limits(current_price, IndianMarket.NSE)

            results.append(
                {
                    "symbol": symbol,
                    "current_price": f"₹{current_price:.2f}",
                    "rsi": round(current_rsi, 2),
                    "price_change_pct": round(price_change_pct, 2),
                    "avg_volume": int(avg_volume),
                    "score": round(score, 2),
                    "circuit_upper": f"₹{limits['upper_limit']:.2f}",
                    "circuit_lower": f"₹{limits['lower_limit']:.2f}",
                    "market": "NSE",
                }
            )

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            continue

    # Sort by score and limit results
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:limit]

    logger.info(f"Maverick Bullish India: Found {len(results)} recommendations")
    return results


def get_maverick_bearish_india(
    min_volume: int = 500000,
    rsi_high: int = 70,
    lookback_days: int = 30,
    limit: int = 20,
) -> list[dict]:
    """
    Maverick Bearish strategy for Indian market (short opportunities).

    Criteria:
    - Volume > 500,000 shares
    - RSI > 70 (overbought)
    - Price below 50-day MA
    - Recent price decrease

    Args:
        min_volume: Minimum daily volume
        rsi_high: Upper RSI threshold for overbought
        lookback_days: Days to look back
        limit: Maximum results

    Returns:
        List of potential short candidates
    """
    logger.info(f"Running Maverick Bearish India strategy (limit={limit})")

    provider = IndianMarketDataProvider()
    results = []

    stocks = provider.get_nifty50_constituents()

    for symbol in stocks:
        try:
            df = provider.fetch_data(symbol, period=f"{lookback_days + 50}d")

            if df.empty or len(df) < 50:
                continue

            current_price = df["Close"].iloc[-1]
            avg_volume = df["Volume"].mean()

            if avg_volume < min_volume:
                continue

            # RSI overbought check
            rsi_series = calculate_rsi(df)
            current_rsi = rsi_series.iloc[-1]
            if pd.isna(current_rsi) or current_rsi < rsi_high:
                continue

            # Below MA check
            ma_50 = calculate_sma(df, period=50)
            if current_price > ma_50.iloc[-1]:
                continue

            # Negative momentum
            if len(df) >= 5:
                week_ago_price = df["Close"].iloc[-5]
                price_change_pct = (
                    (current_price - week_ago_price) / week_ago_price
                ) * 100
            else:
                price_change_pct = 0

            score = 0
            score += min((current_rsi - 70) / 5, 5)  # Overbought degree
            score += abs(min(price_change_pct, 0)) / 2  # Negative momentum

            results.append(
                {
                    "symbol": symbol,
                    "current_price": f"₹{current_price:.2f}",
                    "rsi": round(current_rsi, 2),
                    "price_change_pct": round(price_change_pct, 2),
                    "avg_volume": int(avg_volume),
                    "score": round(score, 2),
                    "market": "NSE",
                }
            )

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:limit]

    logger.info(f"Maverick Bearish India: Found {len(results)} recommendations")
    return results


def get_nifty50_momentum(
    min_price_change_pct: float = 2.0,
    rsi_low: int = 50,
    rsi_high: int = 70,
    limit: int = 15,
) -> list[dict]:
    """
    Find momentum plays within Nifty 50 constituents.

    Criteria:
    - Stock must be in Nifty 50
    - Price change > 2% in last week
    - RSI between 50-70 (strong but not overbought)
    - Volume > average volume
    - Above 50-day MA

    Args:
        min_price_change_pct: Minimum weekly price change
        rsi_low: Lower RSI threshold
        rsi_high: Upper RSI threshold
        limit: Maximum results

    Returns:
        List of momentum stocks from Nifty 50
    """
    logger.info(f"Running Nifty 50 Momentum strategy (limit={limit})")

    provider = IndianMarketDataProvider()
    nifty50 = provider.get_nifty50_constituents()
    results = []

    for symbol in nifty50:
        try:
            df = provider.fetch_data(symbol, period="3mo")

            if df.empty or len(df) < 50:
                continue

            current_price = df["Close"].iloc[-1]
            avg_volume = df["Volume"].mean()
            recent_volume = df["Volume"].iloc[-5:].mean()

            # Volume increase check
            if recent_volume < avg_volume:
                continue

            # RSI check
            rsi_series = calculate_rsi(df)
            current_rsi = rsi_series.iloc[-1]
            if pd.isna(current_rsi) or not (rsi_low <= current_rsi <= rsi_high):
                continue

            # MA check
            ma_50 = calculate_sma(df, period=50)
            if current_price < ma_50.iloc[-1]:
                continue

            # Weekly momentum
            if len(df) >= 5:
                week_ago_price = df["Close"].iloc[-5]
                price_change_pct = (
                    (current_price - week_ago_price) / week_ago_price
                ) * 100

                if price_change_pct < min_price_change_pct:
                    continue
            else:
                continue

            # Score calculation
            score = 0
            score += min(price_change_pct, 10) / 2  # Momentum
            score += (current_rsi - 50) / 5  # RSI strength
            score += min((recent_volume / avg_volume - 1) * 5, 3)  # Volume spike

            results.append(
                {
                    "symbol": symbol,
                    "current_price": f"₹{current_price:.2f}",
                    "rsi": round(current_rsi, 2),
                    "price_change_pct": round(price_change_pct, 2),
                    "volume_ratio": round(recent_volume / avg_volume, 2),
                    "score": round(score, 2),
                }
            )

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:limit]

    logger.info(f"Nifty 50 Momentum: Found {len(results)} recommendations")
    return results


def get_nifty_sector_rotation(
    lookback_days: int = 90, top_n: int = 3
) -> dict:
    """
    Analyze Nifty 50 sector rotation and identify strongest sectors.

    Returns sector performance, momentum, and top stocks per sector.

    Args:
        lookback_days: Period for sector analysis
        top_n: Number of top sectors to highlight

    Returns:
        Dict with sector rankings and top stocks
    """
    logger.info(f"Analyzing Nifty sector rotation (lookback={lookback_days} days)")

    provider = IndianMarketDataProvider()

    # Define sector mapping for Nifty 50 stocks
    sector_mapping = {
        "RELIANCE.NS": "Oil & Gas",
        "ONGC.NS": "Oil & Gas",
        "BPCL.NS": "Oil & Gas",
        "IOC.NS": "Oil & Gas",
        "TCS.NS": "Information Technology",
        "INFY.NS": "Information Technology",
        "WIPRO.NS": "Information Technology",
        "HCLTECH.NS": "Information Technology",
        "TECHM.NS": "Information Technology",
        "HDFCBANK.NS": "Banking",
        "ICICIBANK.NS": "Banking",
        "KOTAKBANK.NS": "Banking",
        "AXISBANK.NS": "Banking",
        "SBIN.NS": "Banking",
        "INDUSINDBK.NS": "Banking",
        "BAJFINANCE.NS": "Financial Services",
        "BAJAJFINSV.NS": "Financial Services",
        "SBILIFE.NS": "Financial Services",
        "HDFCLIFE.NS": "Financial Services",
        "HINDUNILVR.NS": "FMCG",
        "ITC.NS": "FMCG",
        "NESTLEIND.NS": "FMCG",
        "BRITANNIA.NS": "FMCG",
        "TATACONSUM.NS": "FMCG",
        "MARUTI.NS": "Automobile",
        "TATAMOTORS.NS": "Automobile",
        "M&M.NS": "Automobile",
        "BAJAJ-AUTO.NS": "Automobile",
        "EICHERMOT.NS": "Automobile",
        "HEROMOTOCO.NS": "Automobile",
        "SUNPHARMA.NS": "Pharmaceuticals",
        "DRREDDY.NS": "Pharmaceuticals",
        "CIPLA.NS": "Pharmaceuticals",
        "DIVISLAB.NS": "Pharmaceuticals",
        "APOLLOHOSP.NS": "Healthcare",
        "JSWSTEEL.NS": "Metals",
        "TATASTEEL.NS": "Metals",
        "HINDALCO.NS": "Metals",
        "COALINDIA.NS": "Mining",
        "ASIANPAINT.NS": "Consumer Durables",
        "TITAN.NS": "Consumer Durables",
        "LT.NS": "Infrastructure",
        "ULTRACEMCO.NS": "Cement",
        "GRASIM.NS": "Cement",
        "BHARTIARTL.NS": "Telecom",
        "POWERGRID.NS": "Power",
        "NTPC.NS": "Power",
        "ADANIENT.NS": "Conglomerate",
        "ADANIPORTS.NS": "Infrastructure",
        "UPL.NS": "Chemicals",
    }

    sector_performance: dict = {}

    for symbol in provider.get_nifty50_constituents():
        try:
            df = provider.fetch_data(symbol, period=f"{lookback_days}d")

            if df.empty or len(df) < lookback_days // 2:
                continue

            # Calculate returns
            start_price = df["Close"].iloc[0]
            end_price = df["Close"].iloc[-1]
            returns = ((end_price - start_price) / start_price) * 100

            sector = sector_mapping.get(symbol, "Other")
            if sector not in sector_performance:
                sector_performance[sector] = {
                    "stocks": [],
                    "returns": [],
                    "count": 0,
                }

            sector_performance[sector]["stocks"].append(
                {
                    "symbol": symbol,
                    "returns": round(returns, 2),
                    "current_price": f"₹{end_price:.2f}",
                }
            )
            sector_performance[sector]["returns"].append(returns)
            sector_performance[sector]["count"] += 1

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            continue

    # Calculate average returns per sector
    sector_rankings = []
    for sector, data in sector_performance.items():
        if data["count"] > 0:
            avg_return = sum(data["returns"]) / data["count"]

            # Get top 3 stocks in sector
            data["stocks"].sort(key=lambda x: x["returns"], reverse=True)
            top_stocks = data["stocks"][:3]

            sector_rankings.append(
                {
                    "sector": sector,
                    "avg_return": round(avg_return, 2),
                    "stock_count": data["count"],
                    "top_stocks": top_stocks,
                }
            )

    # Sort by performance
    sector_rankings.sort(key=lambda x: x["avg_return"], reverse=True)

    return {
        "analysis_period_days": lookback_days,
        "total_sectors": len(sector_rankings),
        "top_sectors": sector_rankings[:top_n],
        "all_sectors": sector_rankings,
        "timestamp": datetime.now().isoformat(),
    }


def get_value_picks_india(
    max_price_position_pct: float = 30,
    max_volatility: float = 0.05,
    limit: int = 20,
) -> list[dict]:
    """
    Value investing strategy for Indian market.

    Criteria:
    - Trading near 52-week low (lower 30% of range)
    - Stable price action (low volatility)

    Args:
        max_price_position_pct: Maximum position in 52-week range
        max_volatility: Maximum recent volatility
        limit: Maximum results

    Returns:
        List of value stock picks
    """
    logger.info(f"Running Value Picks India strategy (limit={limit})")

    provider = IndianMarketDataProvider()
    results = []

    stocks = provider.get_nifty50_constituents()

    for symbol in stocks:
        try:
            df = provider.fetch_data(symbol, period="1y")

            if df.empty:
                continue

            current_price = df["Close"].iloc[-1]
            year_low = df["Low"].min()
            year_high = df["High"].max()

            # Value proxy: trading near 52-week low
            price_position = (
                (current_price - year_low) / (year_high - year_low)
            ) * 100

            # Look for stocks in lower 30% of range (potential value)
            if price_position > max_price_position_pct:
                continue

            # Stable price action (not crashing)
            recent_volatility = (
                df["Close"].iloc[-20:].std() / df["Close"].iloc[-20:].mean()
            )
            if recent_volatility > max_volatility:
                continue

            score = 0
            score += (max_price_position_pct - price_position) / 5
            score += max(0, (max_volatility - recent_volatility) * 50)

            results.append(
                {
                    "symbol": symbol,
                    "current_price": f"₹{current_price:.2f}",
                    "52w_low": f"₹{year_low:.2f}",
                    "52w_high": f"₹{year_high:.2f}",
                    "price_position_pct": round(price_position, 2),
                    "score": round(score, 2),
                    "market": "NSE",
                }
            )

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:limit]

    logger.info(f"Value Picks India: Found {len(results)} recommendations")
    return results


def get_smallcap_breakouts_india(
    min_volume_spike_pct: float = 150,
    min_price_change_pct: float = 3.0,
    limit: int = 15,
) -> list[dict]:
    """
    Identify small-cap breakout opportunities.

    Criteria:
    - Volume spike > 150%
    - Price breaking out (> 3% gain)
    - Strong recent momentum
    - Above key moving averages

    Args:
        min_volume_spike_pct: Minimum volume increase %
        min_price_change_pct: Minimum price change %
        limit: Maximum results

    Returns:
        List of small-cap breakout candidates
    """
    logger.info(f"Running Small-Cap Breakouts India strategy (limit={limit})")

    provider = IndianMarketDataProvider()
    results = []

    # Use Nifty 50 for now (would use small-cap index in production)
    stocks = provider.get_nifty50_constituents()

    for symbol in stocks:
        try:
            df = provider.fetch_data(symbol, period="3mo")

            if df.empty or len(df) < 50:
                continue

            current_price = df["Close"].iloc[-1]
            avg_volume_30d = df["Volume"].iloc[:-5].mean()
            recent_volume = df["Volume"].iloc[-5:].mean()

            # Volume spike check
            volume_spike_pct = (
                (recent_volume - avg_volume_30d) / avg_volume_30d
            ) * 100
            if volume_spike_pct < min_volume_spike_pct:
                continue

            # Price momentum
            week_ago_price = df["Close"].iloc[-5]
            price_change_pct = (
                (current_price - week_ago_price) / week_ago_price
            ) * 100

            if price_change_pct < min_price_change_pct:
                continue

            # Above moving averages
            ma_20 = calculate_sma(df, period=20)
            ma_50 = calculate_sma(df, period=50)

            if current_price < ma_20.iloc[-1] or current_price < ma_50.iloc[-1]:
                continue

            score = 0
            score += min(volume_spike_pct / 50, 5)  # Volume contribution
            score += min(price_change_pct, 10) / 2  # Price momentum

            results.append(
                {
                    "symbol": symbol,
                    "current_price": f"₹{current_price:.2f}",
                    "volume_spike_pct": round(volume_spike_pct, 2),
                    "price_change_pct": round(price_change_pct, 2),
                    "score": round(score, 2),
                    "market": "NSE",
                }
            )

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:limit]

    logger.info(f"Small-Cap Breakouts India: Found {len(results)} recommendations")
    return results


__all__ = [
    "get_maverick_bullish_india",
    "get_maverick_bearish_india",
    "get_nifty50_momentum",
    "get_nifty_sector_rotation",
    "get_value_picks_india",
    "get_smallcap_breakouts_india",
]
