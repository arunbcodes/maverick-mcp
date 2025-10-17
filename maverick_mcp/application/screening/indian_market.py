"""
Indian Market Screening Strategies

Screening strategies adapted for Indian stock markets (NSE/BSE) with:
- 10% circuit breakers (vs 7% in US)
- INR denomination with lakhs/crores formatting
- Nifty sector structure
- Indian market trading hours (9:15 AM - 3:30 PM IST)
- T+1 settlement (vs T+2 in US)
- Lower volume thresholds (500K vs 1M)
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

import pandas as pd
from sqlalchemy import and_, or_

from maverick_mcp.config.markets import Market, get_market_config, MARKET_CONFIGS
from maverick_mcp.data.models import Stock, SessionLocal
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider
from maverick_mcp.core.technical_analysis import calculate_rsi, calculate_sma

logger = logging.getLogger(__name__)


def get_maverick_bullish_india(
    min_volume: int = 500000,
    rsi_low: int = 30,
    rsi_high: int = 70,
    lookback_days: int = 30,
    limit: int = 20
) -> List[Dict]:
    """
    Maverick Bullish strategy adapted for Indian market.
    
    Criteria (adjusted for Indian market):
    - Volume > 500,000 shares (lower than US due to smaller market)
    - RSI between 30-70 (momentum but not overbought)
    - Price above 50-day MA
    - Recent price increase > 2% (adjusted for INR volatility)
    - Market cap > ₹5,000 crores
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
    
    session = SessionLocal()
    provider = IndianMarketDataProvider()
    results = []
    
    try:
        # Get active Indian stocks with minimum market cap
        indian_stocks = session.query(Stock).filter(
            and_(
                or_(Stock.market == "NSE", Stock.market == "BSE"),
                Stock.is_active == True,
                Stock.country == "IN"
            )
        ).limit(100).all()  # Limit initial query for performance
        
        logger.info(f"Found {len(indian_stocks)} Indian stocks to analyze")
        
        for stock in indian_stocks:
            try:
                # Fetch recent data
                df = provider.get_stock_data(
                    stock.ticker_symbol,
                    period=f"{lookback_days}d"
                )
                
                if df.empty or len(df) < 50:
                    continue
                
                # Calculate indicators
                current_price = df['close'].iloc[-1]
                avg_volume = df['volume'].mean()
                
                # Volume check
                if avg_volume < min_volume:
                    continue
                
                # RSI check
                rsi = calculate_rsi(df['close'])
                current_rsi = rsi.iloc[-1]
                if not (rsi_low <= current_rsi <= rsi_high):
                    continue
                
                # Moving average check (50-day)
                ma_50 = calculate_sma(df['close'], period=50)
                if current_price < ma_50.iloc[-1]:
                    continue
                
                # Price momentum check (weekly change > 2%)
                if len(df) >= 5:
                    week_ago_price = df['close'].iloc[-5]
                    price_change_pct = ((current_price - week_ago_price) / week_ago_price) * 100
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
                limits = calculate_circuit_breaker_limits(current_price, Market.INDIA_NSE)
                
                results.append({
                    "symbol": stock.ticker_symbol,
                    "company_name": stock.company_name,
                    "current_price": f"₹{current_price:.2f}",
                    "rsi": round(current_rsi, 2),
                    "price_change_pct": round(price_change_pct, 2),
                    "avg_volume": int(avg_volume),
                    "score": round(score, 2),
                    "circuit_upper": f"₹{limits['upper_limit']:.2f}",
                    "circuit_lower": f"₹{limits['lower_limit']:.2f}",
                    "sector": stock.sector or "Unknown",
                    "market": stock.market
                })
                
            except Exception as e:
                logger.debug(f"Error analyzing {stock.ticker_symbol}: {e}")
                continue
        
        # Sort by score and limit results
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:limit]
        
        logger.info(f"Maverick Bullish India: Found {len(results)} recommendations")
        return results
        
    finally:
        session.close()


def get_maverick_bearish_india(
    min_volume: int = 500000,
    rsi_high: int = 70,
    lookback_days: int = 30,
    limit: int = 20
) -> List[Dict]:
    """
    Maverick Bearish strategy for Indian market (short opportunities).
    
    Criteria:
    - Volume > 500,000 shares
    - RSI > 70 (overbought)
    - Price below 50-day MA
    - Recent price decrease
    - High debt-to-equity (if available)
    
    Args:
        min_volume: Minimum daily volume
        rsi_high: Upper RSI threshold for overbought
        lookback_days: Days to look back
        limit: Maximum results
        
    Returns:
        List of potential short candidates
    """
    logger.info(f"Running Maverick Bearish India strategy (limit={limit})")
    
    session = SessionLocal()
    provider = IndianMarketDataProvider()
    results = []
    
    try:
        indian_stocks = session.query(Stock).filter(
            and_(
                or_(Stock.market == "NSE", Stock.market == "BSE"),
                Stock.is_active == True,
                Stock.country == "IN"
            )
        ).limit(100).all()
        
        for stock in indian_stocks:
            try:
                df = provider.get_stock_data(
                    stock.ticker_symbol,
                    period=f"{lookback_days}d"
                )
                
                if df.empty or len(df) < 50:
                    continue
                
                current_price = df['close'].iloc[-1]
                avg_volume = df['volume'].mean()
                
                if avg_volume < min_volume:
                    continue
                
                # RSI overbought check
                rsi = calculate_rsi(df['close'])
                current_rsi = rsi.iloc[-1]
                if current_rsi < rsi_high:
                    continue
                
                # Below MA check
                ma_50 = calculate_sma(df['close'], period=50)
                if current_price > ma_50.iloc[-1]:
                    continue
                
                # Negative momentum
                if len(df) >= 5:
                    week_ago_price = df['close'].iloc[-5]
                    price_change_pct = ((current_price - week_ago_price) / week_ago_price) * 100
                else:
                    price_change_pct = 0
                
                score = 0
                score += min((current_rsi - 70) / 5, 5)  # Overbought degree
                score += abs(min(price_change_pct, 0)) / 2  # Negative momentum
                
                results.append({
                    "symbol": stock.ticker_symbol,
                    "company_name": stock.company_name,
                    "current_price": f"₹{current_price:.2f}",
                    "rsi": round(current_rsi, 2),
                    "price_change_pct": round(price_change_pct, 2),
                    "avg_volume": int(avg_volume),
                    "score": round(score, 2),
                    "sector": stock.sector or "Unknown",
                    "market": stock.market
                })
                
            except Exception as e:
                logger.debug(f"Error analyzing {stock.ticker_symbol}: {e}")
                continue
        
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:limit]
        
        logger.info(f"Maverick Bearish India: Found {len(results)} recommendations")
        return results
        
    finally:
        session.close()


def get_nifty50_momentum(
    min_price_change_pct: float = 2.0,
    rsi_low: int = 50,
    rsi_high: int = 70,
    limit: int = 15
) -> List[Dict]:
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
            df = provider.get_stock_data(symbol, period="3mo")
            
            if df.empty or len(df) < 50:
                continue
            
            current_price = df['close'].iloc[-1]
            avg_volume = df['volume'].mean()
            recent_volume = df['volume'].iloc[-5:].mean()
            
            # Volume increase check
            if recent_volume < avg_volume:
                continue
            
            # RSI check
            rsi = calculate_rsi(df['close'])
            current_rsi = rsi.iloc[-1]
            if not (rsi_low <= current_rsi <= rsi_high):
                continue
            
            # MA check
            ma_50 = calculate_moving_average(df['close'], period=50)
            if current_price < ma_50.iloc[-1]:
                continue
            
            # Weekly momentum
            if len(df) >= 5:
                week_ago_price = df['close'].iloc[-5]
                price_change_pct = ((current_price - week_ago_price) / week_ago_price) * 100
                
                if price_change_pct < min_price_change_pct:
                    continue
            else:
                continue
            
            # Score calculation
            score = 0
            score += min(price_change_pct, 10) / 2  # Momentum
            score += (current_rsi - 50) / 5  # RSI strength
            score += min((recent_volume / avg_volume - 1) * 5, 3)  # Volume spike
            
            results.append({
                "symbol": symbol,
                "current_price": f"₹{current_price:.2f}",
                "rsi": round(current_rsi, 2),
                "price_change_pct": round(price_change_pct, 2),
                "volume_ratio": round(recent_volume / avg_volume, 2),
                "score": round(score, 2)
            })
            
        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            continue
    
    results.sort(key=lambda x: x['score'], reverse=True)
    results = results[:limit]
    
    logger.info(f"Nifty 50 Momentum: Found {len(results)} recommendations")
    return results


def get_nifty_sector_rotation(
    lookback_days: int = 90,
    top_n: int = 3
) -> Dict:
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
    
    session = SessionLocal()
    provider = IndianMarketDataProvider()
    
    try:
        # Get all Indian stocks with sectors
        indian_stocks = session.query(Stock).filter(
            and_(
                or_(Stock.market == "NSE", Stock.market == "BSE"),
                Stock.is_active == True,
                Stock.country == "IN",
                Stock.sector.isnot(None)
            )
        ).all()
        
        sector_performance = {}
        
        for stock in indian_stocks:
            try:
                df = provider.get_stock_data(
                    stock.ticker_symbol,
                    period=f"{lookback_days}d"
                )
                
                if df.empty or len(df) < lookback_days:
                    continue
                
                # Calculate returns
                start_price = df['close'].iloc[0]
                end_price = df['close'].iloc[-1]
                returns = ((end_price - start_price) / start_price) * 100
                
                sector = stock.sector
                if sector not in sector_performance:
                    sector_performance[sector] = {
                        "stocks": [],
                        "returns": [],
                        "count": 0
                    }
                
                sector_performance[sector]["stocks"].append({
                    "symbol": stock.ticker_symbol,
                    "returns": round(returns, 2),
                    "current_price": f"₹{end_price:.2f}"
                })
                sector_performance[sector]["returns"].append(returns)
                sector_performance[sector]["count"] += 1
                
            except Exception as e:
                logger.debug(f"Error analyzing {stock.ticker_symbol}: {e}")
                continue
        
        # Calculate average returns per sector
        sector_rankings = []
        for sector, data in sector_performance.items():
            if data["count"] > 0:
                avg_return = sum(data["returns"]) / data["count"]
                
                # Get top 3 stocks in sector
                data["stocks"].sort(key=lambda x: x["returns"], reverse=True)
                top_stocks = data["stocks"][:3]
                
                sector_rankings.append({
                    "sector": sector,
                    "avg_return": round(avg_return, 2),
                    "stock_count": data["count"],
                    "top_stocks": top_stocks
                })
        
        # Sort by performance
        sector_rankings.sort(key=lambda x: x["avg_return"], reverse=True)
        
        return {
            "analysis_period_days": lookback_days,
            "total_sectors": len(sector_rankings),
            "top_sectors": sector_rankings[:top_n],
            "all_sectors": sector_rankings,
            "timestamp": datetime.now().isoformat()
        }
        
    finally:
        session.close()


def get_value_picks_india(
    max_pe_ratio: float = 20,
    min_dividend_yield: float = 2.0,
    max_debt_equity: float = 1.5,
    limit: int = 20
) -> List[Dict]:
    """
    Value investing strategy for Indian market.
    
    Criteria:
    - P/E ratio < 20 (adjusted for Indian market norms)
    - Dividend yield > 2%
    - Debt-to-equity < 1.5 (if available)
    - Market cap > ₹5,000 crores
    - Positive earnings growth
    
    Note: This is a simplified version since we may not have all fundamental data.
    
    Args:
        max_pe_ratio: Maximum P/E ratio
        min_dividend_yield: Minimum dividend yield
        max_debt_equity: Maximum debt-to-equity ratio
        limit: Maximum results
        
    Returns:
        List of value stock picks
    """
    logger.info(f"Running Value Picks India strategy (limit={limit})")
    logger.warning("Limited fundamental data available - using price-based value proxies")
    
    session = SessionLocal()
    provider = IndianMarketDataProvider()
    results = []
    
    try:
        indian_stocks = session.query(Stock).filter(
            and_(
                or_(Stock.market == "NSE", Stock.market == "BSE"),
                Stock.is_active == True,
                Stock.country == "IN"
            )
        ).limit(100).all()
        
        for stock in indian_stocks:
            try:
                df = provider.get_stock_data(stock.ticker_symbol, period="1y")
                
                if df.empty:
                    continue
                
                current_price = df['close'].iloc[-1]
                year_low = df['low'].min()
                year_high = df['high'].max()
                
                # Value proxy: trading near 52-week low
                price_position = ((current_price - year_low) / (year_high - year_low)) * 100
                
                # Look for stocks in lower 30% of range (potential value)
                if price_position > 30:
                    continue
                
                # Stable price action (not crashing)
                recent_volatility = df['close'].iloc[-20:].std() / df['close'].iloc[-20:].mean()
                if recent_volatility > 0.05:  # Too volatile
                    continue
                
                score = 0
                score += (30 - price_position) / 5  # Lower in range = higher score
                score += max(0, (0.05 - recent_volatility) * 50)  # Stability score
                
                results.append({
                    "symbol": stock.ticker_symbol,
                    "company_name": stock.company_name,
                    "current_price": f"₹{current_price:.2f}",
                    "52w_low": f"₹{year_low:.2f}",
                    "52w_high": f"₹{year_high:.2f}",
                    "price_position_pct": round(price_position, 2),
                    "score": round(score, 2),
                    "sector": stock.sector or "Unknown",
                    "market": stock.market
                })
                
            except Exception as e:
                logger.debug(f"Error analyzing {stock.ticker_symbol}: {e}")
                continue
        
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:limit]
        
        logger.info(f"Value Picks India: Found {len(results)} recommendations")
        return results
        
    finally:
        session.close()


def get_high_dividend_india(
    min_market_cap_crores: float = 10000,
    limit: int = 20
) -> List[Dict]:
    """
    Find high dividend-yielding Indian stocks.
    
    Note: Simplified version without direct dividend data access.
    Uses mature, large-cap stocks as proxy.
    
    Args:
        min_market_cap_crores: Minimum market cap in crores
        limit: Maximum results
        
    Returns:
        List of potential high dividend stocks
    """
    logger.info(f"Running High Dividend India strategy (limit={limit})")
    logger.warning("Limited dividend data - focusing on mature large-cap stocks")
    
    session = SessionLocal()
    provider = IndianMarketDataProvider()
    
    # Focus on sectors known for dividends in India
    dividend_sectors = [
        "Banking",
        "Financial Services",
        "Oil & Gas",
        "Power",
        "Utilities",
        "FMCG"
    ]
    
    results = []
    
    try:
        indian_stocks = session.query(Stock).filter(
            and_(
                or_(Stock.market == "NSE", Stock.market == "BSE"),
                Stock.is_active == True,
                Stock.country == "IN",
                Stock.sector.in_(dividend_sectors)
            )
        ).limit(50).all()
        
        for stock in indian_stocks:
            try:
                df = provider.get_stock_data(stock.ticker_symbol, period="1y")
                
                if df.empty:
                    continue
                
                current_price = df['close'].iloc[-1]
                
                # Stable price (good for dividend seekers)
                price_stability = 1 - (df['close'].std() / df['close'].mean())
                
                score = price_stability * 10
                
                results.append({
                    "symbol": stock.ticker_symbol,
                    "company_name": stock.company_name,
                    "current_price": f"₹{current_price:.2f}",
                    "sector": stock.sector,
                    "stability_score": round(price_stability, 3),
                    "score": round(score, 2),
                    "market": stock.market
                })
                
            except Exception as e:
                logger.debug(f"Error analyzing {stock.ticker_symbol}: {e}")
                continue
        
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:limit]
        
        logger.info(f"High Dividend India: Found {len(results)} recommendations")
        return results
        
    finally:
        session.close()


def get_smallcap_breakouts_india(
    min_volume_spike_pct: float = 150,
    limit: int = 15
) -> List[Dict]:
    """
    Identify small-cap breakout opportunities.
    
    Criteria:
    - Volume spike > 150%
    - Price breaking out
    - Strong recent momentum
    - Above key moving averages
    
    Args:
        min_volume_spike_pct: Minimum volume increase %
        limit: Maximum results
        
    Returns:
        List of small-cap breakout candidates
    """
    logger.info(f"Running Small-Cap Breakouts India strategy (limit={limit})")
    
    session = SessionLocal()
    provider = IndianMarketDataProvider()
    results = []
    
    try:
        # Get Indian stocks (focusing on smaller ones by limiting query)
        indian_stocks = session.query(Stock).filter(
            and_(
                or_(Stock.market == "NSE", Stock.market == "BSE"),
                Stock.is_active == True,
                Stock.country == "IN"
            )
        ).limit(100).all()
        
        for stock in indian_stocks:
            try:
                df = provider.get_stock_data(stock.ticker_symbol, period="3mo")
                
                if df.empty or len(df) < 50:
                    continue
                
                current_price = df['close'].iloc[-1]
                avg_volume_30d = df['volume'].iloc[:-5].mean()
                recent_volume = df['volume'].iloc[-5:].mean()
                
                # Volume spike check
                volume_spike_pct = ((recent_volume - avg_volume_30d) / avg_volume_30d) * 100
                if volume_spike_pct < min_volume_spike_pct:
                    continue
                
                # Price momentum
                week_ago_price = df['close'].iloc[-5]
                price_change_pct = ((current_price - week_ago_price) / week_ago_price) * 100
                
                if price_change_pct < 3.0:  # Need strong momentum
                    continue
                
                # Above moving averages
                ma_20 = calculate_sma(df['close'], period=20)
                ma_50 = calculate_sma(df['close'], period=50)
                
                if current_price < ma_20.iloc[-1] or current_price < ma_50.iloc[-1]:
                    continue
                
                score = 0
                score += min(volume_spike_pct / 50, 5)  # Volume contribution
                score += min(price_change_pct, 10) / 2  # Price momentum
                
                results.append({
                    "symbol": stock.ticker_symbol,
                    "company_name": stock.company_name,
                    "current_price": f"₹{current_price:.2f}",
                    "volume_spike_pct": round(volume_spike_pct, 2),
                    "price_change_pct": round(price_change_pct, 2),
                    "score": round(score, 2),
                    "sector": stock.sector or "Unknown",
                    "market": stock.market
                })
                
            except Exception as e:
                logger.debug(f"Error analyzing {stock.ticker_symbol}: {e}")
                continue
        
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:limit]
        
        logger.info(f"Small-Cap Breakouts India: Found {len(results)} recommendations")
        return results
        
    finally:
        session.close()


# Utility functions

def calculate_circuit_breaker_limits(
    current_price: float,
    market: Market = Market.INDIA_NSE
) -> Dict[str, float]:
    """
    Calculate circuit breaker limits for Indian stocks.
    
    Indian market has 10% circuit breakers (vs 7% in US).
    
    Args:
        current_price: Current stock price
        market: Market (NSE or BSE)
        
    Returns:
        Dict with upper_limit, lower_limit, and circuit_breaker_pct
    """
    config = MARKET_CONFIGS.get(market)
    if not config:
        # Default to NSE config
        config = MARKET_CONFIGS[Market.INDIA_NSE]
    
    breaker_pct = config.circuit_breaker_percent / 100
    
    return {
        "upper_limit": current_price * (1 + breaker_pct),
        "lower_limit": current_price * (1 - breaker_pct),
        "circuit_breaker_pct": config.circuit_breaker_percent
    }


def get_nifty_sectors() -> List[str]:
    """
    Get list of Nifty sectors.
    
    Returns:
        List of sector names used in Nifty indices
    """
    return [
        "Banking & Financial Services",
        "Information Technology",
        "Oil & Gas",
        "Fast Moving Consumer Goods",
        "Automobile",
        "Pharmaceuticals",
        "Metals & Mining",
        "Infrastructure",
        "Telecom",
        "Power",
        "Consumer Durables",
        "Cement",
        "Real Estate",
        "Media & Entertainment"
    ]


def format_indian_currency(amount: float) -> str:
    """
    Format amount in Indian numbering system (lakhs and crores).
    
    Args:
        amount: Amount in rupees
        
    Returns:
        Formatted string (e.g., "₹1.5 Cr", "₹50 L")
    """
    if amount >= 10000000:  # 1 crore = 10 million
        crores = amount / 10000000
        return f"₹{crores:.2f} Cr"
    elif amount >= 100000:  # 1 lakh = 100 thousand
        lakhs = amount / 100000
        return f"₹{lakhs:.2f} L"
    else:
        return f"₹{amount:,.2f}"


__all__ = [
    "get_maverick_bullish_india",
    "get_maverick_bearish_india",
    "get_nifty50_momentum",
    "get_nifty_sector_rotation",
    "get_value_picks_india",
    "get_high_dividend_india",
    "get_smallcap_breakouts_india",
    "calculate_circuit_breaker_limits",
    "get_nifty_sectors",
    "format_indian_currency",
]

