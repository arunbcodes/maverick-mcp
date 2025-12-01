"""
CoinGecko Data Provider with Rate Limiting.

Optional provider for broader cryptocurrency coverage (6000+ coins).
Implements rate limiting to respect CoinGecko free tier limits.

Features:
    - 6000+ cryptocurrency support
    - Rate limiting (10 calls/minute for free tier)
    - Circuit breaker integration
    - Trending coins, market data, dominance metrics
    - Fear & Greed index integration

Note:
    Requires pycoingecko: pip install pycoingecko
    Or: pip install maverick-crypto[coingecko]
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Check if pycoingecko is available
try:
    from pycoingecko import CoinGeckoAPI
    HAS_COINGECKO = True
except ImportError:
    HAS_COINGECKO = False
    CoinGeckoAPI = None


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    
    Implements a sliding window rate limiter to ensure
    we don't exceed CoinGecko's free tier limits.
    """
    
    def __init__(self, calls_per_minute: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_minute: Maximum API calls per minute (default: 10 for free tier)
        """
        self.calls_per_minute = calls_per_minute
        self.window_seconds = 60
        self.call_times: list[datetime] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """
        Acquire permission to make an API call.
        
        Blocks if rate limit would be exceeded.
        """
        async with self._lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window_seconds)
            
            # Remove old calls outside window
            self.call_times = [t for t in self.call_times if t > window_start]
            
            # Check if we need to wait
            if len(self.call_times) >= self.calls_per_minute:
                # Calculate wait time
                oldest_call = self.call_times[0]
                wait_until = oldest_call + timedelta(seconds=self.window_seconds)
                wait_seconds = (wait_until - now).total_seconds()
                
                if wait_seconds > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_seconds:.1f}s")
                    await asyncio.sleep(wait_seconds)
                    
                    # Clean up after waiting
                    now = datetime.now()
                    window_start = now - timedelta(seconds=self.window_seconds)
                    self.call_times = [t for t in self.call_times if t > window_start]
            
            # Record this call
            self.call_times.append(datetime.now())
    
    @property
    def remaining_calls(self) -> int:
        """Get remaining calls in current window."""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        recent_calls = len([t for t in self.call_times if t > window_start])
        return max(0, self.calls_per_minute - recent_calls)


class CoinGeckoProvider:
    """
    CoinGecko API provider with rate limiting.
    
    Provides access to 6000+ cryptocurrencies with intelligent
    rate limiting to respect free tier API limits.
    
    Free Tier Limits:
        - 10-30 calls/minute (we use 10 to be safe)
        - No API key required
        - Historical data up to 365 days
    
    Features:
        - Market data for 6000+ coins
        - Trending coins (top 7)
        - Global market data (dominance, etc.)
        - Historical OHLC data
        - Coin search and lookup
    
    Example:
        >>> provider = CoinGeckoProvider()
        >>> trending = await provider.get_trending()
        >>> print(trending)
    
    Note:
        Install with: pip install maverick-crypto[coingecko]
    """
    
    # CoinGecko ID mappings for common symbols
    SYMBOL_TO_ID = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binancecoin",
        "SOL": "solana",
        "XRP": "ripple",
        "DOGE": "dogecoin",
        "ADA": "cardano",
        "AVAX": "avalanche-2",
        "DOT": "polkadot",
        "MATIC": "matic-network",
        "LINK": "chainlink",
        "UNI": "uniswap",
        "ATOM": "cosmos",
        "LTC": "litecoin",
        "ETC": "ethereum-classic",
        "XLM": "stellar",
        "ALGO": "algorand",
        "NEAR": "near",
        "FTM": "fantom",
        "AAVE": "aave",
    }
    
    def __init__(self, calls_per_minute: int = 10):
        """
        Initialize CoinGecko provider.
        
        Args:
            calls_per_minute: Rate limit (default: 10 for free tier)
            
        Raises:
            ImportError: If pycoingecko is not installed
        """
        if not HAS_COINGECKO:
            raise ImportError(
                "pycoingecko is required for CoinGeckoProvider. "
                "Install with: pip install maverick-crypto[coingecko]"
            )
        
        self.cg = CoinGeckoAPI()
        self.rate_limiter = RateLimiter(calls_per_minute)
        self._coin_list_cache: dict[str, str] | None = None
        self._cache_time: datetime | None = None
        self._cache_ttl = timedelta(hours=24)
        
        logger.info(f"CoinGeckoProvider initialized (rate limit: {calls_per_minute}/min)")
    
    async def _rate_limited_call(self, func, *args, **kwargs) -> Any:
        """
        Make a rate-limited API call.
        
        Args:
            func: CoinGecko API function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            API response
        """
        await self.rate_limiter.acquire()
        
        # Run sync function in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    
    async def get_coin_id(self, symbol: str) -> str | None:
        """
        Get CoinGecko coin ID from symbol.
        
        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH")
            
        Returns:
            CoinGecko ID (e.g., "bitcoin") or None if not found
        """
        symbol = symbol.upper().strip()
        
        # Check static mapping first
        if symbol in self.SYMBOL_TO_ID:
            return self.SYMBOL_TO_ID[symbol]
        
        # Load and cache coin list
        await self._ensure_coin_list_cached()
        
        return self._coin_list_cache.get(symbol)
    
    async def _ensure_coin_list_cached(self) -> None:
        """Ensure coin list is cached and fresh."""
        now = datetime.now()
        
        if (self._coin_list_cache is None or 
            self._cache_time is None or 
            now - self._cache_time > self._cache_ttl):
            
            logger.info("Refreshing CoinGecko coin list cache")
            coin_list = await self._rate_limited_call(self.cg.get_coins_list)
            
            self._coin_list_cache = {
                coin["symbol"].upper(): coin["id"]
                for coin in coin_list
            }
            self._cache_time = now
            logger.info(f"Cached {len(self._coin_list_cache)} coins")
    
    async def get_trending(self) -> dict[str, Any]:
        """
        Get trending cryptocurrencies (top 7).
        
        Returns:
            Dictionary with trending coins data:
                - coins: List of trending coin data
                - nfts: List of trending NFT data (if available)
        """
        logger.info("Fetching trending coins from CoinGecko")
        result = await self._rate_limited_call(self.cg.get_search_trending)
        
        # Format response
        trending_coins = []
        for item in result.get("coins", []):
            coin = item.get("item", {})
            trending_coins.append({
                "rank": coin.get("market_cap_rank"),
                "name": coin.get("name"),
                "symbol": coin.get("symbol"),
                "coingecko_id": coin.get("id"),
                "price_btc": coin.get("price_btc"),
                "score": coin.get("score"),
            })
        
        return {
            "coins": trending_coins,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def get_global_data(self) -> dict[str, Any]:
        """
        Get global cryptocurrency market data.
        
        Returns:
            Dictionary with global market metrics:
                - total_market_cap: Total market cap by currency
                - btc_dominance: Bitcoin dominance percentage
                - eth_dominance: Ethereum dominance percentage
                - active_cryptocurrencies: Number of active coins
                - markets: Number of exchanges
                - market_cap_change_24h: 24h market cap change %
        """
        logger.info("Fetching global market data from CoinGecko")
        result = await self._rate_limited_call(self.cg.get_global)
        
        # CoinGecko free API returns data at top level, not wrapped
        # Check both formats for compatibility
        if "data" in result:
            data = result["data"]
        else:
            data = result
        
        return {
            "total_market_cap_usd": data.get("total_market_cap", {}).get("usd"),
            "total_volume_24h_usd": data.get("total_volume", {}).get("usd"),
            "btc_dominance": data.get("market_cap_percentage", {}).get("btc"),
            "eth_dominance": data.get("market_cap_percentage", {}).get("eth"),
            "active_cryptocurrencies": data.get("active_cryptocurrencies"),
            "markets": data.get("markets"),
            "market_cap_change_24h_pct": data.get("market_cap_change_percentage_24h_usd"),
            "timestamp": datetime.now().isoformat(),
        }
    
    async def get_coin_data(self, coin_id: str) -> dict[str, Any]:
        """
        Get detailed data for a specific coin.
        
        Args:
            coin_id: CoinGecko coin ID (e.g., "bitcoin")
            
        Returns:
            Detailed coin data including price, market cap, etc.
        """
        logger.info(f"Fetching coin data for {coin_id}")
        result = await self._rate_limited_call(
            self.cg.get_coin_by_id,
            id=coin_id,
            localization=False,
            tickers=False,
            market_data=True,
            community_data=False,
            developer_data=False,
        )
        
        market_data = result.get("market_data", {})
        
        return {
            "id": result.get("id"),
            "symbol": result.get("symbol", "").upper(),
            "name": result.get("name"),
            "description": result.get("description", {}).get("en", "")[:500],
            "market_cap_rank": result.get("market_cap_rank"),
            "current_price": market_data.get("current_price", {}).get("usd"),
            "market_cap": market_data.get("market_cap", {}).get("usd"),
            "total_volume": market_data.get("total_volume", {}).get("usd"),
            "price_change_24h": market_data.get("price_change_24h"),
            "price_change_percentage_24h": market_data.get("price_change_percentage_24h"),
            "circulating_supply": market_data.get("circulating_supply"),
            "total_supply": market_data.get("total_supply"),
            "max_supply": market_data.get("max_supply"),
            "ath": market_data.get("ath", {}).get("usd"),
            "ath_date": market_data.get("ath_date", {}).get("usd"),
            "atl": market_data.get("atl", {}).get("usd"),
            "atl_date": market_data.get("atl_date", {}).get("usd"),
            "timestamp": datetime.now().isoformat(),
        }
    
    async def get_coin_ohlc(
        self,
        coin_id: str,
        days: int = 90,
        vs_currency: str = "usd",
    ) -> pd.DataFrame:
        """
        Get OHLC data for a coin.
        
        Args:
            coin_id: CoinGecko coin ID
            days: Number of days (1, 7, 14, 30, 90, 180, 365, max)
            vs_currency: Quote currency (default: usd)
            
        Returns:
            DataFrame with OHLC data
            
        Note:
            CoinGecko free tier limits: 1-2 days (30min), 3-30 days (4hr), 31+ days (daily)
        """
        logger.info(f"Fetching OHLC for {coin_id} ({days} days)")
        
        # CoinGecko only supports specific day values
        valid_days = [1, 7, 14, 30, 90, 180, 365]
        days = min(valid_days, key=lambda x: abs(x - days))
        
        result = await self._rate_limited_call(
            self.cg.get_coin_ohlc_by_id,
            id=coin_id,
            vs_currency=vs_currency,
            days=days,
        )
        
        if not result:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(result, columns=["timestamp", "Open", "High", "Low", "Close"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df["Volume"] = 0  # CoinGecko OHLC doesn't include volume
        
        return df
    
    async def get_top_coins(
        self,
        limit: int = 100,
        vs_currency: str = "usd",
    ) -> list[dict[str, Any]]:
        """
        Get top coins by market cap.
        
        Args:
            limit: Number of coins to fetch (max 250 per page)
            vs_currency: Quote currency
            
        Returns:
            List of coin market data
        """
        logger.info(f"Fetching top {limit} coins by market cap")
        
        # CoinGecko paginates at 250
        per_page = min(limit, 250)
        
        result = await self._rate_limited_call(
            self.cg.get_coins_markets,
            vs_currency=vs_currency,
            per_page=per_page,
            order="market_cap_desc",
        )
        
        coins = []
        for coin in result[:limit]:
            coins.append({
                "id": coin.get("id"),
                "symbol": coin.get("symbol", "").upper(),
                "name": coin.get("name"),
                "current_price": coin.get("current_price"),
                "market_cap": coin.get("market_cap"),
                "market_cap_rank": coin.get("market_cap_rank"),
                "total_volume": coin.get("total_volume"),
                "price_change_24h": coin.get("price_change_24h"),
                "price_change_percentage_24h": coin.get("price_change_percentage_24h"),
                "circulating_supply": coin.get("circulating_supply"),
                "total_supply": coin.get("total_supply"),
                "ath": coin.get("ath"),
                "ath_date": coin.get("ath_date"),
            })
        
        return coins
    
    async def search_coins(self, query: str) -> list[dict[str, Any]]:
        """
        Search for coins by name or symbol.
        
        Args:
            query: Search query
            
        Returns:
            List of matching coins
        """
        logger.info(f"Searching coins for: {query}")
        
        result = await self._rate_limited_call(self.cg.search, query=query)
        
        coins = []
        for coin in result.get("coins", [])[:20]:
            coins.append({
                "id": coin.get("id"),
                "symbol": coin.get("symbol"),
                "name": coin.get("name"),
                "market_cap_rank": coin.get("market_cap_rank"),
            })
        
        return coins
    
    @property
    def remaining_calls(self) -> int:
        """Get remaining API calls in current window."""
        return self.rate_limiter.remaining_calls


# Fear & Greed Index provider (Alternative.me API - free, no auth)
class FearGreedProvider:
    """
    Crypto Fear & Greed Index provider.

    Uses Alternative.me API which is free and requires no authentication.
    The index ranges from 0 (Extreme Fear) to 100 (Extreme Greed).

    Index Interpretation:
        - 0-24: Extreme Fear (buying opportunity?)
        - 25-49: Fear
        - 50-74: Greed
        - 75-100: Extreme Greed (selling opportunity?)
    """

    API_URL = "https://api.alternative.me/fng/"

    def __init__(self, http_client: httpx.AsyncClient | None = None):
        """Initialize Fear & Greed provider."""
        self.rate_limiter = RateLimiter(calls_per_minute=30)
        self._http_client = http_client
        self._owns_client = http_client is None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client if owned by this instance."""
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def get_fear_greed_index(self, limit: int = 1) -> dict[str, Any]:
        """
        Get current Fear & Greed Index.

        Args:
            limit: Number of days of history (default: 1 for current)

        Returns:
            Dictionary with fear/greed data
        """
        import httpx

        await self.rate_limiter.acquire()

        client = await self._get_client()
        response = await client.get(
            self.API_URL,
            params={"limit": limit, "format": "json"},
        )
        response.raise_for_status()
        data = response.json()
        
        if not data.get("data"):
            return {"error": "No data available"}
        
        current = data["data"][0]
        
        # Interpret the value
        value = int(current.get("value", 50))
        if value <= 24:
            interpretation = "Extreme Fear"
        elif value <= 49:
            interpretation = "Fear"
        elif value <= 74:
            interpretation = "Greed"
        else:
            interpretation = "Extreme Greed"
        
        result = {
            "value": value,
            "classification": current.get("value_classification"),
            "interpretation": interpretation,
            "timestamp": current.get("timestamp"),
            "time_until_update": current.get("time_until_update"),
        }
        
        # Add historical data if requested
        if limit > 1:
            result["history"] = [
                {
                    "value": int(d.get("value", 0)),
                    "classification": d.get("value_classification"),
                    "timestamp": d.get("timestamp"),
                }
                for d in data["data"]
            ]
        
        return result

