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
from datetime import date, datetime, timedelta
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
    
    # ============================================================
    # CoinGecko-powered tools (optional - requires pycoingecko)
    # ============================================================
    
    @mcp.tool()
    async def crypto_trending() -> dict[str, Any]:
        """
        Get trending cryptocurrencies from CoinGecko.
        
        Returns the top 7 trending coins based on CoinGecko's algorithm,
        which considers search volume, price action, and social metrics.
        
        Returns:
            Dictionary with:
                - coins: List of trending coin data
                - timestamp: When data was fetched
                
        Note:
            Requires pycoingecko: pip install maverick-crypto[coingecko]
            
        Examples:
            - "What cryptos are trending today?"
            - "Show me trending coins"
            - "What's hot in crypto right now?"
        """
        try:
            from maverick_crypto.providers import CoinGeckoProvider, HAS_COINGECKO
        except ImportError:
            return {"error": "CoinGecko provider not available"}
        
        if not HAS_COINGECKO:
            return {
                "error": "pycoingecko not installed",
                "help": "Install with: pip install maverick-crypto[coingecko]",
            }
        
        try:
            provider = CoinGeckoProvider()
            return await provider.get_trending()
        except Exception as e:
            logger.error(f"Error fetching trending cryptos: {e}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def crypto_fear_greed() -> dict[str, Any]:
        """
        Get the Crypto Fear & Greed Index.
        
        The Fear & Greed Index measures market sentiment on a scale of 0-100:
        - 0-24: Extreme Fear (potential buying opportunity)
        - 25-49: Fear
        - 50-74: Greed
        - 75-100: Extreme Greed (potential selling signal)
        
        Returns:
            Dictionary with:
                - value: Current index value (0-100)
                - classification: Text classification
                - interpretation: What the value means
                - timestamp: When data was fetched
                
        Examples:
            - "What's the crypto fear and greed index?"
            - "Is the market fearful or greedy?"
            - "What's the crypto sentiment right now?"
        """
        try:
            from maverick_crypto.providers.coingecko_provider import FearGreedProvider
        except ImportError:
            return {"error": "Fear & Greed provider not available"}
        
        try:
            provider = FearGreedProvider()
            return await provider.get_fear_greed_index()
        except Exception as e:
            logger.error(f"Error fetching fear/greed index: {e}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def crypto_global_data() -> dict[str, Any]:
        """
        Get global cryptocurrency market data.
        
        Returns comprehensive market-wide metrics including total market cap,
        Bitcoin/Ethereum dominance, and market trends.
        
        Returns:
            Dictionary with:
                - total_market_cap_usd: Total crypto market cap
                - btc_dominance: Bitcoin's market share (%)
                - eth_dominance: Ethereum's market share (%)
                - active_cryptocurrencies: Number of tracked coins
                - market_cap_change_24h_pct: 24h market change
                
        Note:
            Requires pycoingecko: pip install maverick-crypto[coingecko]
            
        Examples:
            - "What's Bitcoin's market dominance?"
            - "Show me the total crypto market cap"
            - "What's the global crypto market data?"
        """
        try:
            from maverick_crypto.providers import CoinGeckoProvider, HAS_COINGECKO
        except ImportError:
            return {"error": "CoinGecko provider not available"}
        
        if not HAS_COINGECKO:
            return {
                "error": "pycoingecko not installed",
                "help": "Install with: pip install maverick-crypto[coingecko]",
            }
        
        try:
            provider = CoinGeckoProvider()
            return await provider.get_global_data()
        except Exception as e:
            logger.error(f"Error fetching global data: {e}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def crypto_top_coins(limit: int = 20) -> dict[str, Any]:
        """
        Get top cryptocurrencies by market cap.
        
        Returns the largest cryptocurrencies ranked by market capitalization.
        Similar to S&P 500 for stocks but for crypto.
        
        Args:
            limit: Number of coins to return (default: 20, max: 100)
            
        Returns:
            Dictionary with:
                - coins: List of coin data with price, market cap, etc.
                - count: Number of coins returned
                - timestamp: When data was fetched
                
        Note:
            Requires pycoingecko: pip install maverick-crypto[coingecko]
            
        Examples:
            - "Show me the top 10 cryptos by market cap"
            - "What are the largest cryptocurrencies?"
            - "List top 50 crypto coins"
        """
        try:
            from maverick_crypto.providers import CoinGeckoProvider, HAS_COINGECKO
        except ImportError:
            return {"error": "CoinGecko provider not available"}
        
        if not HAS_COINGECKO:
            return {
                "error": "pycoingecko not installed",
                "help": "Install with: pip install maverick-crypto[coingecko]",
            }
        
        try:
            limit = min(limit, 100)  # Cap at 100
            provider = CoinGeckoProvider()
            coins = await provider.get_top_coins(limit=limit)
            
            return {
                "coins": coins,
                "count": len(coins),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error fetching top coins: {e}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def crypto_search(query: str) -> dict[str, Any]:
        """
        Search for cryptocurrencies by name or symbol.
        
        Finds coins matching a search query - useful for discovering
        coins by partial name or symbol.
        
        Args:
            query: Search term (e.g., "bit", "doge", "solana")
            
        Returns:
            Dictionary with:
                - coins: List of matching coins
                - count: Number of matches
                
        Note:
            Requires pycoingecko: pip install maverick-crypto[coingecko]
            
        Examples:
            - "Search for coins with 'dog' in the name"
            - "Find crypto called pepe"
            - "Search for layer 2 tokens"
        """
        try:
            from maverick_crypto.providers import CoinGeckoProvider, HAS_COINGECKO
        except ImportError:
            return {"error": "CoinGecko provider not available"}
        
        if not HAS_COINGECKO:
            return {
                "error": "pycoingecko not installed",
                "help": "Install with: pip install maverick-crypto[coingecko]",
            }
        
        try:
            provider = CoinGeckoProvider()
            coins = await provider.search_coins(query)
            
            return {
                "query": query,
                "coins": coins,
                "count": len(coins),
            }
        except Exception as e:
            logger.error(f"Error searching coins: {e}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def crypto_detailed_info(symbol: str) -> dict[str, Any]:
        """
        Get detailed information for a specific cryptocurrency.
        
        Returns comprehensive data including description, market data,
        supply information, and all-time high/low prices.
        
        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH", "SOL")
            
        Returns:
            Dictionary with detailed coin information:
                - id, symbol, name, description
                - market_cap_rank, current_price, market_cap
                - circulating_supply, total_supply, max_supply
                - ath (all-time high), atl (all-time low)
                
        Note:
            Requires pycoingecko: pip install maverick-crypto[coingecko]
            
        Examples:
            - "Get detailed info for Bitcoin"
            - "Tell me about Ethereum"
            - "What's the max supply of Solana?"
        """
        try:
            from maverick_crypto.providers import CoinGeckoProvider, HAS_COINGECKO
        except ImportError:
            return {"error": "CoinGecko provider not available"}
        
        if not HAS_COINGECKO:
            return {
                "error": "pycoingecko not installed",
                "help": "Install with: pip install maverick-crypto[coingecko]",
            }
        
        try:
            provider = CoinGeckoProvider()
            
            # Get CoinGecko ID from symbol
            coin_id = await provider.get_coin_id(symbol)
            if not coin_id:
                return {
                    "error": f"Unknown symbol: {symbol}",
                    "help": "Try searching with crypto_search first",
                }
            
            return await provider.get_coin_data(coin_id)
        except Exception as e:
            logger.error(f"Error fetching coin info for {symbol}: {e}")
            return {"error": str(e)}
    
    # ============================================================
    # Backtesting tools (requires vectorbt)
    # ============================================================
    
    @mcp.tool()
    async def crypto_backtest(
        symbol: str,
        strategy: str = "crypto_momentum",
        days: int = 90,
        initial_capital: float = 10000.0,
    ) -> dict[str, Any]:
        """
        Run a backtest on cryptocurrency data.
        
        Tests a trading strategy on historical crypto data and returns
        performance metrics including return, Sharpe ratio, and drawdown.
        
        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH", "SOL")
            strategy: Strategy name. Options:
                - crypto_momentum: SMA crossover momentum
                - crypto_mean_reversion: Bollinger Band mean reversion
                - crypto_breakout: Volatility breakout
                - crypto_rsi: RSI overbought/oversold
                - crypto_macd: MACD crossover
                - crypto_bollinger: Bollinger Band bounce
            days: Number of days of data (default: 90)
            initial_capital: Starting capital (default: $10,000)
            
        Returns:
            Dictionary with:
                - total_return_pct: Total return percentage
                - sharpe_ratio: Risk-adjusted return
                - max_drawdown: Maximum drawdown
                - win_rate: Percentage of winning trades
                - num_trades: Number of trades executed
                - trades: Recent trade history
                
        Examples:
            - "Backtest Bitcoin with momentum strategy"
            - "Test RSI strategy on ETH for 180 days"
            - "Compare crypto_macd vs crypto_rsi on Solana"
        """
        try:
            from maverick_crypto.backtesting import CryptoBacktestEngine
        except ImportError:
            return {
                "error": "Backtesting dependencies not available",
                "help": "Install with: pip install vectorbt",
            }
        
        try:
            engine = CryptoBacktestEngine()
            result = await engine.run_backtest(
                symbol=symbol,
                strategy=strategy,
                days=days,
                initial_capital=initial_capital,
            )
            return result
        except Exception as e:
            logger.error(f"Backtest failed for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol, "strategy": strategy}
    
    @mcp.tool()
    async def crypto_compare_strategies(
        symbol: str,
        days: int = 90,
    ) -> dict[str, Any]:
        """
        Compare all crypto strategies on a single symbol.
        
        Runs all available crypto strategies and ranks them by performance.
        Useful for finding the best strategy for a particular cryptocurrency.
        
        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH")
            days: Number of days for backtesting (default: 90)
            
        Returns:
            Dictionary with:
                - results: Performance for each strategy
                - best_strategy: Name of best performing strategy
                - best_return: Return of best strategy
                - comparison_summary: Side-by-side comparison
                
        Examples:
            - "Which strategy works best for Bitcoin?"
            - "Compare all strategies on ETH over 180 days"
            - "Find the best crypto strategy for Solana"
        """
        try:
            from maverick_crypto.backtesting import CryptoBacktestEngine
        except ImportError:
            return {
                "error": "Backtesting dependencies not available",
                "help": "Install with: pip install vectorbt",
            }
        
        try:
            engine = CryptoBacktestEngine()
            result = await engine.compare_strategies(
                symbol=symbol,
                days=days,
            )
            return result
        except Exception as e:
            logger.error(f"Strategy comparison failed for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}
    
    @mcp.tool()
    async def crypto_list_strategies() -> dict[str, Any]:
        """
        List all available crypto backtesting strategies.
        
        Returns information about each strategy including description
        and default parameters.
        
        Returns:
            Dictionary with:
                - strategies: List of available strategies
                - count: Number of strategies
                
        Examples:
            - "What crypto strategies are available?"
            - "List backtesting strategies for crypto"
            - "Show me crypto trading strategies"
        """
        try:
            from maverick_crypto.backtesting import list_crypto_strategies
            strategies = list_crypto_strategies()
            return {
                "strategies": strategies,
                "count": len(strategies),
                "note": "All strategies are adjusted for crypto volatility",
            }
        except Exception as e:
            logger.error(f"Failed to list strategies: {e}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def crypto_optimize_strategy(
        symbol: str,
        strategy: str = "crypto_momentum",
        days: int = 90,
    ) -> dict[str, Any]:
        """
        Optimize strategy parameters for a cryptocurrency.
        
        Uses grid search to find optimal parameters for a given strategy.
        Tests multiple parameter combinations and returns the best.
        
        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH")
            strategy: Strategy to optimize (default: crypto_momentum)
            days: Number of days for backtesting (default: 90)
            
        Returns:
            Dictionary with:
                - best_parameters: Optimal parameter values
                - best_metric_value: Best Sharpe ratio achieved
                - top_10_results: Top 10 parameter combinations
                
        Examples:
            - "Optimize momentum strategy for Bitcoin"
            - "Find best RSI parameters for ETH"
            - "Optimize crypto_macd for Solana"
        """
        try:
            from maverick_crypto.backtesting import CryptoBacktestEngine
        except ImportError:
            return {
                "error": "Backtesting dependencies not available",
                "help": "Install with: pip install vectorbt",
            }
        
        # Define parameter grids for each strategy
        param_grids = {
            "crypto_momentum": {
                "fast_period": [5, 10, 15, 20],
                "slow_period": [20, 30, 40, 50],
            },
            "crypto_rsi": {
                "period": [7, 14, 21],
                "oversold": [20, 25, 30],
                "overbought": [70, 75, 80],
            },
            "crypto_macd": {
                "fast_period": [6, 8, 12],
                "slow_period": [18, 21, 26],
                "signal_period": [7, 9, 12],
            },
            "crypto_bollinger": {
                "period": [15, 20, 25],
                "std_dev": [2.0, 2.5, 3.0],
            },
            "crypto_mean_reversion": {
                "period": [15, 20, 25],
                "std_dev": [2.0, 2.5, 3.0],
            },
            "crypto_breakout": {
                "lookback": [10, 20, 30],
                "volume_threshold": [1.2, 1.5, 2.0],
            },
        }
        
        if strategy not in param_grids:
            return {
                "error": f"No optimization grid for {strategy}",
                "available": list(param_grids.keys()),
            }
        
        try:
            engine = CryptoBacktestEngine()
            result = await engine.optimize_strategy(
                symbol=symbol,
                strategy=strategy,
                param_grid=param_grids[strategy],
                days=days,
                metric="sharpe_ratio",
            )
            return result
        except Exception as e:
            logger.error(f"Optimization failed for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol, "strategy": strategy}
    
    # ============================================================
    # Mixed Portfolio tools (stocks + crypto)
    # ============================================================
    
    @mcp.tool()
    async def portfolio_mixed_performance(
        stocks: list[str],
        cryptos: list[str],
        stock_weight: float = 0.6,
        days: int = 90,
    ) -> dict[str, Any]:
        """
        Calculate performance of a mixed stock + crypto portfolio.
        
        Creates a portfolio with specified stock and crypto allocations
        and calculates performance metrics.
        
        Args:
            stocks: Stock symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
            cryptos: Crypto symbols (e.g., ["BTC", "ETH"])
            stock_weight: Total weight for stocks (rest goes to crypto). Default: 0.6
            days: Analysis period (default: 90)
            
        Returns:
            Dictionary with:
                - portfolio: Total return, Sharpe ratio, volatility
                - allocation: Stock vs crypto split
                - assets: Individual asset performance
                
        Examples:
            - "How would 60% AAPL+MSFT and 40% BTC+ETH perform?"
            - "Calculate mixed portfolio with tech stocks and crypto"
            - "Compare stocks vs crypto allocation"
        """
        from maverick_crypto.portfolio import MixedPortfolioService, PortfolioAsset, AssetType
        
        try:
            service = MixedPortfolioService()
            
            # Calculate weights
            crypto_weight = 1.0 - stock_weight
            stock_per = stock_weight / len(stocks) if stocks else 0
            crypto_per = crypto_weight / len(cryptos) if cryptos else 0
            
            # Create assets
            assets = [
                PortfolioAsset(symbol=s, asset_type=AssetType.STOCK, weight=stock_per)
                for s in stocks
            ] + [
                PortfolioAsset(symbol=c, asset_type=AssetType.CRYPTO, weight=crypto_per)
                for c in cryptos
            ]
            
            result = await service.calculate_performance(assets, days)
            return result
            
        except Exception as e:
            logger.error(f"Portfolio performance calculation failed: {e}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def portfolio_correlation(
        stocks: list[str],
        cryptos: list[str],
        days: int = 90,
    ) -> dict[str, Any]:
        """
        Calculate correlation between stocks and cryptocurrencies.
        
        Analyzes how different assets move together to help with diversification.
        
        Args:
            stocks: Stock symbols (e.g., ["AAPL", "MSFT", "SPY"])
            cryptos: Crypto symbols (e.g., ["BTC", "ETH"])
            days: Analysis period (default: 90)
            
        Returns:
            Dictionary with:
                - correlation_matrix: Full correlation matrix
                - stock_crypto_correlation: Average stock-crypto correlation
                - diversification_score: Higher = better diversification
                - interpretation: What the correlations mean
                
        Examples:
            - "How correlated are AAPL, MSFT with BTC, ETH?"
            - "Analyze diversification between stocks and crypto"
            - "Calculate correlation matrix for my portfolio"
        """
        from maverick_crypto.portfolio import CorrelationAnalyzer
        
        try:
            analyzer = CorrelationAnalyzer()
            result = await analyzer.calculate_correlation_matrix(stocks, cryptos, days)
            return result
            
        except Exception as e:
            logger.error(f"Correlation analysis failed: {e}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def portfolio_optimize(
        stocks: list[str],
        cryptos: list[str],
        objective: str = "max_sharpe",
        max_crypto_weight: float = 0.4,
        days: int = 365,
    ) -> dict[str, Any]:
        """
        Optimize portfolio allocation across stocks and crypto.
        
        Uses mean-variance optimization to find optimal weights
        that maximize return for a given risk level.
        
        Args:
            stocks: Stock symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
            cryptos: Crypto symbols (e.g., ["BTC", "ETH"])
            objective: Optimization goal:
                - "max_sharpe": Maximize risk-adjusted return (default)
                - "min_volatility": Minimize risk
                - "max_return": Maximize return (higher risk)
            max_crypto_weight: Maximum total crypto allocation (default: 0.4 = 40%)
            days: Historical data period (default: 365)
            
        Returns:
            Dictionary with:
                - optimal_weights: Best allocation for each asset
                - metrics: Expected return, volatility, Sharpe ratio
                - allocation: Total stock vs crypto split
                
        Examples:
            - "Optimize portfolio with AAPL, MSFT, BTC, ETH"
            - "Find best allocation with max 30% crypto"
            - "Minimize volatility for my stock and crypto portfolio"
        """
        from maverick_crypto.portfolio import PortfolioOptimizer
        
        try:
            optimizer = PortfolioOptimizer()
            result = await optimizer.optimize(
                stocks=stocks,
                cryptos=cryptos,
                objective=objective,
                max_crypto_weight=max_crypto_weight,
                days=days,
            )
            return result
            
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def portfolio_suggest(
        stocks: list[str],
        cryptos: list[str],
        risk_tolerance: str = "moderate",
    ) -> dict[str, Any]:
        """
        Get portfolio allocation suggestion based on risk tolerance.
        
        Provides personalized allocation recommendations.
        
        Args:
            stocks: Stock symbols
            cryptos: Crypto symbols
            risk_tolerance: Your risk preference:
                - "conservative": Lower risk, max 15% crypto
                - "moderate": Balanced, max 30% crypto (default)
                - "aggressive": Higher risk, max 50% crypto
                
        Returns:
            Dictionary with:
                - optimal_weights: Suggested allocation
                - risk_profile: Description of selected profile
                - metrics: Expected performance
                
        Examples:
            - "Suggest portfolio for conservative investor"
            - "What allocation for moderate risk with AAPL, BTC?"
            - "Aggressive portfolio suggestion with tech stocks and crypto"
        """
        from maverick_crypto.portfolio import PortfolioOptimizer
        
        try:
            optimizer = PortfolioOptimizer()
            result = await optimizer.suggest_allocation(
                stocks=stocks,
                cryptos=cryptos,
                risk_tolerance=risk_tolerance,
            )
            return result
            
        except Exception as e:
            logger.error(f"Portfolio suggestion failed: {e}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def portfolio_compare_classes(
        stocks: list[str],
        cryptos: list[str],
        days: int = 90,
    ) -> dict[str, Any]:
        """
        Compare stocks vs crypto as asset classes.
        
        Analyzes which asset class performed better and provides
        insights for allocation decisions.
        
        Args:
            stocks: Stock symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
            cryptos: Crypto symbols (e.g., ["BTC", "ETH"])
            days: Analysis period (default: 90)
            
        Returns:
            Dictionary with:
                - stocks: Performance metrics for stocks
                - crypto: Performance metrics for crypto
                - comparison: Which performed better
                - recommendation: Allocation suggestion
                
        Examples:
            - "Compare FAANG stocks vs top cryptos"
            - "Which performed better: stocks or crypto?"
            - "Should I hold more stocks or crypto?"
        """
        from maverick_crypto.portfolio import CorrelationAnalyzer
        
        try:
            analyzer = CorrelationAnalyzer()
            result = await analyzer.asset_class_comparison(stocks, cryptos, days)
            return result
            
        except Exception as e:
            logger.error(f"Asset class comparison failed: {e}")
            return {"error": str(e)}
    
    logger.info("Crypto tools registered successfully")

