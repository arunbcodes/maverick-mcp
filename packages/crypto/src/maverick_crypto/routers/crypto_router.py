"""
Cryptocurrency MCP Router.

Defines MCP tools for cryptocurrency data fetching and analysis.
These tools integrate with Claude Desktop for natural language queries.

Tools:
    - crypto_fetch_data: Fetch historical OHLCV data
    - crypto_get_price: Get current price
    - crypto_technical_analysis: Get RSI, MACD, Bollinger Bands
    - crypto_compare: Compare multiple cryptocurrencies
    - crypto_market_status: Get 24/7 market info
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def register_crypto_tools(mcp: Any) -> None:
    """
    Register cryptocurrency tools with the MCP server.
    
    Args:
        mcp: FastMCP server instance
    """
    
    @mcp.tool()
    async def crypto_fetch_data(
        symbol: str,
        days: int = 90,
        interval: str = "1d",
    ) -> dict[str, Any]:
        """
        Fetch historical cryptocurrency OHLCV data.
        
        Retrieves Open, High, Low, Close, Volume data for any cryptocurrency.
        Supports major coins like BTC, ETH, SOL, and many more.
        
        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH", "SOL", "DOGE")
            days: Number of days of history (default: 90)
            interval: Data interval - "1d" (daily), "1h" (hourly), "1wk" (weekly)
            
        Returns:
            Dictionary with:
                - symbol: Normalized symbol
                - data: OHLCV data as records
                - rows: Number of data points
                - start_date: First date in data
                - end_date: Last date in data
                
        Examples:
            - "Get Bitcoin price history for last 30 days"
            - "Fetch ETH data for 90 days with daily interval"
            - "Show me Solana OHLCV data"
        """
        from maverick_crypto.providers import CryptoDataProvider
        
        provider = CryptoDataProvider()
        
        try:
            df = await provider.get_crypto_data(symbol, days=days, interval=interval)
            
            return {
                "symbol": provider.normalize_symbol(symbol),
                "original_symbol": symbol,
                "data": df.reset_index().to_dict(orient="records"),
                "rows": len(df),
                "start_date": df.index[0].isoformat() if len(df) > 0 else None,
                "end_date": df.index[-1].isoformat() if len(df) > 0 else None,
                "interval": interval,
                "columns": list(df.columns),
            }
        except Exception as e:
            logger.error(f"Error fetching crypto data for {symbol}: {e}")
            return {
                "error": str(e),
                "symbol": symbol,
                "message": f"Failed to fetch data for {symbol}. Ensure it's a valid crypto symbol.",
            }
    
    @mcp.tool()
    async def crypto_get_price(symbol: str) -> dict[str, Any]:
        """
        Get current cryptocurrency price and market data.
        
        Fetches real-time price, 24h change, volume, and market cap.
        
        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH")
            
        Returns:
            Dictionary with current price data:
                - symbol: Trading symbol
                - price: Current price in USD
                - change: 24h price change
                - change_percent: 24h percentage change
                - volume: 24h trading volume
                - market_cap: Total market capitalization
                
        Examples:
            - "What's the current Bitcoin price?"
            - "Get ETH price and market cap"
            - "Show me Solana's current trading data"
        """
        from maverick_crypto.providers import CryptoDataProvider
        
        provider = CryptoDataProvider()
        
        try:
            price_data = await provider.get_realtime_price(symbol)
            
            if price_data is None:
                return {
                    "error": "Unable to fetch price",
                    "symbol": symbol,
                    "message": f"No price data available for {symbol}",
                }
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return {
                "error": str(e),
                "symbol": symbol,
            }
    
    @mcp.tool()
    async def crypto_technical_analysis(
        symbol: str,
        days: int = 90,
    ) -> dict[str, Any]:
        """
        Get technical analysis indicators for a cryptocurrency.
        
        Calculates RSI, MACD, Bollinger Bands, and moving averages.
        Adjusted for crypto's higher volatility (wider thresholds).
        
        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH")
            days: Number of days for analysis (default: 90)
            
        Returns:
            Dictionary with technical indicators:
                - rsi: Relative Strength Index (14-period)
                - macd: MACD line, signal, and histogram
                - bollinger: Upper, middle, lower bands
                - sma: Simple moving averages (20, 50, 200)
                - interpretation: Analysis summary
                
        Note:
            Crypto uses adjusted thresholds:
            - RSI overbought: 75 (vs 70 for stocks)
            - RSI oversold: 25 (vs 30 for stocks)
            - Bollinger Bands: 2.5 std (vs 2.0 for stocks)
            
        Examples:
            - "Analyze Bitcoin technicals"
            - "Get RSI and MACD for Ethereum"
            - "Technical analysis for SOL"
        """
        from maverick_crypto.providers import CryptoDataProvider
        from maverick_crypto.calendar import CryptoCalendarService
        
        provider = CryptoDataProvider()
        calendar = CryptoCalendarService()
        
        try:
            df = await provider.get_crypto_data(symbol, days=days)
            
            if df.empty:
                return {"error": "No data available", "symbol": symbol}
            
            # Import pandas_ta for technical indicators
            import pandas_ta as ta
            
            # Calculate indicators
            close = df["Close"]
            
            # RSI
            rsi = ta.rsi(close, length=14)
            current_rsi = rsi.iloc[-1] if rsi is not None and len(rsi) > 0 else None
            
            # MACD
            macd_result = ta.macd(close, fast=12, slow=26, signal=9)
            if macd_result is not None and len(macd_result.columns) >= 3:
                macd_line = macd_result.iloc[-1, 0]
                macd_signal = macd_result.iloc[-1, 1]
                macd_hist = macd_result.iloc[-1, 2]
            else:
                macd_line = macd_signal = macd_hist = None
            
            # Bollinger Bands (wider for crypto: 2.5 std)
            bbands = ta.bbands(close, length=20, std=2.5)
            if bbands is not None and len(bbands.columns) >= 3:
                bb_lower = bbands.iloc[-1, 0]
                bb_mid = bbands.iloc[-1, 1]
                bb_upper = bbands.iloc[-1, 2]
            else:
                bb_lower = bb_mid = bb_upper = None
            
            # SMAs
            sma_20 = ta.sma(close, length=20)
            sma_50 = ta.sma(close, length=50)
            sma_200 = ta.sma(close, length=200) if len(close) >= 200 else None
            
            current_price = close.iloc[-1]
            
            # Get crypto-specific parameters
            vol_params = calendar.get_volatility_parameters()
            
            # Interpretation
            interpretation = []
            
            if current_rsi is not None:
                if current_rsi > vol_params["rsi_overbought"]:
                    interpretation.append(f"RSI ({current_rsi:.1f}) indicates OVERBOUGHT conditions")
                elif current_rsi < vol_params["rsi_oversold"]:
                    interpretation.append(f"RSI ({current_rsi:.1f}) indicates OVERSOLD conditions")
                else:
                    interpretation.append(f"RSI ({current_rsi:.1f}) is in neutral territory")
            
            if macd_line is not None and macd_signal is not None:
                if macd_line > macd_signal:
                    interpretation.append("MACD is BULLISH (above signal line)")
                else:
                    interpretation.append("MACD is BEARISH (below signal line)")
            
            if sma_50 is not None and len(sma_50) > 0:
                sma_50_val = sma_50.iloc[-1]
                if current_price > sma_50_val:
                    interpretation.append(f"Price is ABOVE 50-day SMA (${sma_50_val:.2f})")
                else:
                    interpretation.append(f"Price is BELOW 50-day SMA (${sma_50_val:.2f})")
            
            return {
                "symbol": provider.normalize_symbol(symbol),
                "current_price": current_price,
                "indicators": {
                    "rsi": {
                        "value": round(current_rsi, 2) if current_rsi else None,
                        "overbought_threshold": vol_params["rsi_overbought"],
                        "oversold_threshold": vol_params["rsi_oversold"],
                    },
                    "macd": {
                        "line": round(macd_line, 4) if macd_line else None,
                        "signal": round(macd_signal, 4) if macd_signal else None,
                        "histogram": round(macd_hist, 4) if macd_hist else None,
                    },
                    "bollinger_bands": {
                        "upper": round(bb_upper, 2) if bb_upper else None,
                        "middle": round(bb_mid, 2) if bb_mid else None,
                        "lower": round(bb_lower, 2) if bb_lower else None,
                        "std_dev": 2.5,  # Crypto uses wider bands
                    },
                    "sma": {
                        "sma_20": round(sma_20.iloc[-1], 2) if sma_20 is not None and len(sma_20) > 0 else None,
                        "sma_50": round(sma_50.iloc[-1], 2) if sma_50 is not None and len(sma_50) > 0 else None,
                        "sma_200": round(sma_200.iloc[-1], 2) if sma_200 is not None and len(sma_200) > 0 else None,
                    },
                },
                "interpretation": interpretation,
                "analysis_period_days": days,
                "note": "Thresholds adjusted for crypto volatility",
            }
            
        except Exception as e:
            logger.error(f"Error in technical analysis for {symbol}: {e}")
            return {
                "error": str(e),
                "symbol": symbol,
            }
    
    @mcp.tool()
    async def crypto_compare(
        symbols: list[str],
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Compare multiple cryptocurrencies.
        
        Compares price performance, volatility, and returns.
        
        Args:
            symbols: List of crypto symbols to compare (e.g., ["BTC", "ETH", "SOL"])
            days: Number of days for comparison (default: 30)
            
        Returns:
            Dictionary with comparison data:
                - symbols: List of compared symbols
                - performance: Return percentage for each
                - volatility: Standard deviation of returns
                - correlation: Correlation matrix
                - winner: Best performer
                
        Examples:
            - "Compare BTC, ETH, and SOL performance"
            - "Which performed better: Bitcoin or Ethereum?"
            - "Compare top 5 cryptos over 90 days"
        """
        from maverick_crypto.providers import CryptoDataProvider
        import numpy as np
        
        provider = CryptoDataProvider()
        
        try:
            # Fetch data for all symbols
            data = await provider.get_multiple_cryptos(symbols, days=days)
            
            if not data:
                return {
                    "error": "No data available",
                    "symbols": symbols,
                }
            
            # Calculate metrics for each
            results = {}
            returns_data = {}
            
            for symbol, df in data.items():
                if len(df) < 2:
                    continue
                
                close = df["Close"]
                returns = close.pct_change().dropna()
                
                total_return = (close.iloc[-1] / close.iloc[0] - 1) * 100
                volatility = returns.std() * np.sqrt(365) * 100  # Annualized
                
                results[symbol] = {
                    "start_price": round(close.iloc[0], 2),
                    "end_price": round(close.iloc[-1], 2),
                    "return_pct": round(total_return, 2),
                    "volatility_pct": round(volatility, 2),
                    "high": round(close.max(), 2),
                    "low": round(close.min(), 2),
                }
                returns_data[symbol] = returns
            
            # Find best performer
            if results:
                winner = max(results.keys(), key=lambda x: results[x]["return_pct"])
            else:
                winner = None
            
            # Calculate correlation if multiple symbols
            correlation = None
            if len(returns_data) >= 2:
                import pandas as pd
                returns_df = pd.DataFrame(returns_data)
                correlation = returns_df.corr().to_dict()
            
            return {
                "symbols": list(results.keys()),
                "period_days": days,
                "performance": results,
                "correlation": correlation,
                "best_performer": winner,
                "best_return": results[winner]["return_pct"] if winner else None,
            }
            
        except Exception as e:
            logger.error(f"Error comparing cryptos: {e}")
            return {
                "error": str(e),
                "symbols": symbols,
            }
    
    @mcp.tool()
    async def crypto_market_status() -> dict[str, Any]:
        """
        Get cryptocurrency market status.
        
        Unlike stocks, crypto markets operate 24/7/365.
        Returns market status and crypto-specific parameters.
        
        Returns:
            Dictionary with:
                - is_open: Always True for crypto
                - message: Market status description
                - volatility_params: Crypto-specific risk parameters
                - note: 24/7 trading information
                
        Examples:
            - "Is the crypto market open?"
            - "Get crypto market status"
            - "What are crypto trading parameters?"
        """
        from maverick_crypto.calendar import CryptoCalendarService
        
        calendar = CryptoCalendarService()
        
        status = calendar.get_market_status()
        status["volatility_parameters"] = calendar.get_volatility_parameters()
        status["market_hours"] = calendar.get_market_hours()
        
        return status
    
    logger.info("Crypto tools registered successfully")

