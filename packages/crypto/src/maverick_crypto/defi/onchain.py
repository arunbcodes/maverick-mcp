"""
On-Chain Data Provider using CoinGecko's GeckoTerminal API.

GeckoTerminal provides on-chain DEX data including:
- Trending pools
- Token prices from DEXs
- Pool liquidity and volume
- New token/pool listings

API Documentation: https://docs.coingecko.com/docs/common-use-cases
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OnChainProvider:
    """
    On-chain data provider using CoinGecko GeckoTerminal API.
    
    Provides access to DEX trading data, trending pools, and
    token security information.
    
    Note:
        - Demo API (free): https://api.coingecko.com/api/v3/
        - Pro API: https://pro-api.coingecko.com/api/v3/
        
    Example:
        >>> provider = OnChainProvider()
        >>> trending = await provider.get_trending_pools()
    """
    
    # GeckoTerminal endpoints are available through CoinGecko API
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Supported networks
    NETWORKS = {
        "ethereum": "eth",
        "solana": "solana",
        "arbitrum": "arbitrum",
        "polygon": "polygon_pos",
        "base": "base",
        "avalanche": "avax",
        "bsc": "bsc",
        "optimism": "optimism",
    }
    
    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ):
        """
        Initialize OnChain provider.

        Args:
            api_key: Optional CoinGecko API key for higher rate limits
            timeout: Request timeout in seconds
            http_client: Optional shared HTTP client (recommended for connection reuse)
        """
        self.api_key = api_key
        self.timeout = timeout
        self._http_client = http_client
        self._owns_client = http_client is None

        # Use Pro API if key provided
        if api_key:
            self.base_url = "https://pro-api.coingecko.com/api/v3"
        else:
            self.base_url = self.BASE_URL

        logger.info(f"OnChainProvider initialized (API key: {'yes' if api_key else 'no'})")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client if owned by this instance."""
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with API key if available."""
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key
        return headers

    async def _request(self, endpoint: str, params: dict | None = None) -> dict | list | None:
        """Make async HTTP request using shared client."""
        url = f"{self.base_url}{endpoint}"

        # Add API key to params for demo API
        if self.api_key and "pro-api" not in self.base_url:
            params = params or {}
            params["x_cg_demo_api_key"] = self.api_key

        try:
            client = await self._get_client()
            response = await client.get(
                url,
                params=params,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None
    
    # ==================== Trending ====================
    
    async def get_trending_pools(self, network: str | None = None) -> list[dict[str, Any]]:
        """
        Get trending DEX pools.
        
        Args:
            network: Optional network filter (e.g., "ethereum", "solana")
            
        Returns:
            List of trending pools with volume and price data
        """
        logger.info(f"Fetching trending pools (network: {network or 'all'})")
        
        if network:
            network_id = self.NETWORKS.get(network.lower(), network)
            endpoint = f"/onchain/networks/{network_id}/trending_pools"
        else:
            endpoint = "/onchain/trending_pools"
        
        result = await self._request(endpoint)
        
        if not result or "data" not in result:
            return []
        
        pools = []
        for pool in result["data"][:20]:
            attrs = pool.get("attributes", {})
            pools.append({
                "name": attrs.get("name"),
                "address": attrs.get("address"),
                "network": pool.get("relationships", {}).get("network", {}).get("data", {}).get("id"),
                "dex": pool.get("relationships", {}).get("dex", {}).get("data", {}).get("id"),
                "base_token": attrs.get("base_token_price_usd"),
                "quote_token": attrs.get("quote_token_price_usd"),
                "price_usd": attrs.get("base_token_price_usd"),
                "price_change_24h": attrs.get("price_change_percentage", {}).get("h24"),
                "volume_24h": attrs.get("volume_usd", {}).get("h24"),
                "reserve_usd": attrs.get("reserve_in_usd"),
                "fdv_usd": attrs.get("fdv_usd"),
            })
        
        return pools
    
    async def search_pools(self, query: str) -> list[dict[str, Any]]:
        """
        Search for DEX pools by token name or symbol.
        
        Args:
            query: Search query
            
        Returns:
            List of matching pools
        """
        logger.info(f"Searching pools for: {query}")
        
        result = await self._request("/onchain/search/pools", {"query": query})
        
        if not result or "data" not in result:
            return []
        
        pools = []
        for pool in result["data"][:20]:
            attrs = pool.get("attributes", {})
            pools.append({
                "name": attrs.get("name"),
                "address": attrs.get("address"),
                "network": attrs.get("network", {}).get("identifier"),
                "price_usd": attrs.get("base_token_price_usd"),
                "volume_24h": attrs.get("volume_usd", {}).get("h24"),
                "reserve_usd": attrs.get("reserve_in_usd"),
            })
        
        return pools
    
    # ==================== Token Prices ====================
    
    async def get_token_price(
        self,
        network: str,
        token_address: str,
    ) -> dict[str, Any] | None:
        """
        Get token price from DEX data.
        
        Args:
            network: Network name (e.g., "ethereum", "solana")
            token_address: Token contract address
            
        Returns:
            Token price data
        """
        network_id = self.NETWORKS.get(network.lower(), network)
        endpoint = f"/onchain/simple/networks/{network_id}/token_price/{token_address}"
        
        result = await self._request(endpoint)
        
        if not result or "data" not in result:
            return None
        
        data = result["data"]
        attrs = data.get("attributes", {})
        
        return {
            "address": token_address,
            "network": network,
            "price_usd": attrs.get("token_prices", {}).get(token_address.lower()),
        }
    
    # ==================== Networks & DEXs ====================
    
    async def get_networks(self) -> list[dict[str, Any]]:
        """
        Get list of supported blockchain networks.
        
        Returns:
            List of networks with identifiers
        """
        result = await self._request("/onchain/networks")
        
        if not result or "data" not in result:
            return []
        
        return [
            {
                "id": n.get("id"),
                "name": n.get("attributes", {}).get("name"),
                "coingecko_asset_platform_id": n.get("attributes", {}).get("coingecko_asset_platform_id"),
            }
            for n in result["data"][:50]
        ]
    
    async def get_dexes(self, network: str) -> list[dict[str, Any]]:
        """
        Get DEXs available on a network.
        
        Args:
            network: Network name
            
        Returns:
            List of DEXs on the network
        """
        network_id = self.NETWORKS.get(network.lower(), network)
        result = await self._request(f"/onchain/networks/{network_id}/dexes")
        
        if not result or "data" not in result:
            return []
        
        return [
            {
                "id": d.get("id"),
                "name": d.get("attributes", {}).get("name"),
            }
            for d in result["data"]
        ]
    
    # ==================== Pool Details ====================
    
    async def get_pool_details(
        self,
        network: str,
        pool_address: str,
    ) -> dict[str, Any] | None:
        """
        Get detailed data for a specific pool.
        
        Args:
            network: Network name
            pool_address: Pool contract address
            
        Returns:
            Pool details including liquidity, volume, trades
        """
        network_id = self.NETWORKS.get(network.lower(), network)
        endpoint = f"/onchain/networks/{network_id}/pools/{pool_address}"
        
        result = await self._request(endpoint)
        
        if not result or "data" not in result:
            return None
        
        data = result["data"]
        attrs = data.get("attributes", {})
        
        return {
            "name": attrs.get("name"),
            "address": attrs.get("address"),
            "base_token": attrs.get("base_token_price_usd"),
            "quote_token": attrs.get("quote_token_price_usd"),
            "reserve_usd": attrs.get("reserve_in_usd"),
            "volume_24h": attrs.get("volume_usd", {}).get("h24"),
            "price_change_24h": attrs.get("price_change_percentage", {}).get("h24"),
            "transactions_24h": attrs.get("transactions", {}).get("h24"),
            "pool_created_at": attrs.get("pool_created_at"),
        }
    
    # ==================== New Pools ====================
    
    async def get_new_pools(self, network: str | None = None) -> list[dict[str, Any]]:
        """
        Get recently created pools.
        
        Args:
            network: Optional network filter
            
        Returns:
            List of new pools sorted by creation time
        """
        logger.info(f"Fetching new pools (network: {network or 'all'})")
        
        if network:
            network_id = self.NETWORKS.get(network.lower(), network)
            endpoint = f"/onchain/networks/{network_id}/new_pools"
        else:
            endpoint = "/onchain/new_pools"
        
        result = await self._request(endpoint)
        
        if not result or "data" not in result:
            return []
        
        pools = []
        for pool in result["data"][:20]:
            attrs = pool.get("attributes", {})
            pools.append({
                "name": attrs.get("name"),
                "address": attrs.get("address"),
                "network": pool.get("relationships", {}).get("network", {}).get("data", {}).get("id"),
                "dex": pool.get("relationships", {}).get("dex", {}).get("data", {}).get("id"),
                "created_at": attrs.get("pool_created_at"),
                "reserve_usd": attrs.get("reserve_in_usd"),
                "volume_24h": attrs.get("volume_usd", {}).get("h24"),
            })
        
        return pools
    
    # ==================== Summary ====================
    
    async def get_onchain_summary(self) -> dict[str, Any]:
        """
        Get summary of on-chain DEX activity.
        
        Returns:
            Summary with trending pools, networks, top DEXs
        """
        logger.info("Generating on-chain summary")
        
        trending_task = self.get_trending_pools()
        networks_task = self.get_networks()
        
        trending, networks = await asyncio.gather(trending_task, networks_task)
        
        return {
            "trending_pools": trending[:10],
            "supported_networks": len(networks),
            "top_networks": networks[:10],
            "timestamp": datetime.now().isoformat(),
        }

