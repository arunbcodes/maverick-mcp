"""
DefiLlama API Provider.

DefiLlama is the largest TVL aggregator for DeFi protocols.
All endpoints are free and require no API key.

API Documentation: https://defillama.com/docs/api

Features:
    - Protocol TVL and rankings
    - Chain TVL breakdown
    - Historical TVL data
    - Yields/APY data
    - Stablecoin data
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class DefiLlamaProvider:
    """
    DefiLlama API provider for DeFi TVL and protocol data.
    
    All endpoints are free and require no authentication.
    Rate limits are generous (no documented limit).
    
    Example:
        >>> provider = DefiLlamaProvider()
        >>> tvl = await provider.get_protocol_tvl("uniswap")
        >>> print(f"Uniswap TVL: ${tvl['tvl']:,.0f}")
    """
    
    BASE_URL = "https://api.llama.fi"
    YIELDS_URL = "https://yields.llama.fi"
    COINS_URL = "https://coins.llama.fi"
    STABLECOINS_URL = "https://stablecoins.llama.fi"
    
    def __init__(self, timeout: float = 30.0):
        """
        Initialize DefiLlama provider.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        logger.info("DefiLlamaProvider initialized")
    
    async def _request(self, url: str, params: dict | None = None) -> dict | list | None:
        """Make async HTTP request."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from DefiLlama: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching from DefiLlama: {e}")
            return None
    
    # ==================== TVL Endpoints ====================
    
    async def get_protocols(self) -> list[dict[str, Any]]:
        """
        Get all DeFi protocols with TVL data.
        
        Returns:
            List of protocol data including TVL, chains, category
        """
        logger.info("Fetching all protocols from DefiLlama")
        result = await self._request(f"{self.BASE_URL}/protocols")
        return result if result else []
    
    async def get_protocol(self, protocol_slug: str) -> dict[str, Any] | None:
        """
        Get detailed data for a specific protocol.
        
        Args:
            protocol_slug: Protocol slug (e.g., "uniswap", "aave")
            
        Returns:
            Protocol data including TVL history, chain breakdown
        """
        logger.info(f"Fetching protocol data for {protocol_slug}")
        return await self._request(f"{self.BASE_URL}/protocol/{protocol_slug}")
    
    async def get_tvl_history(self) -> list[dict[str, Any]]:
        """
        Get historical TVL for all DeFi.
        
        Returns:
            List of {date, tvl} entries
        """
        logger.info("Fetching historical TVL")
        result = await self._request(f"{self.BASE_URL}/v2/historicalChainTvl")
        return result if result else []
    
    async def get_chain_tvl(self, chain: str) -> dict[str, Any] | None:
        """
        Get TVL for a specific chain.
        
        Args:
            chain: Chain name (e.g., "Ethereum", "Solana", "Arbitrum")
            
        Returns:
            Chain TVL data with history
        """
        logger.info(f"Fetching TVL for chain: {chain}")
        return await self._request(f"{self.BASE_URL}/v2/historicalChainTvl/{chain}")
    
    async def get_chains(self) -> list[dict[str, Any]]:
        """
        Get TVL for all chains.
        
        Returns:
            List of chains with TVL data
        """
        logger.info("Fetching all chains TVL")
        result = await self._request(f"{self.BASE_URL}/v2/chains")
        return result if result else []
    
    # ==================== Rankings ====================
    
    async def get_top_protocols(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Get top DeFi protocols by TVL.
        
        Args:
            limit: Number of protocols to return
            
        Returns:
            List of top protocols sorted by TVL
        """
        protocols = await self.get_protocols()
        if not protocols:
            return []
        
        # Sort by TVL and take top N
        sorted_protocols = sorted(
            protocols,
            key=lambda x: x.get("tvl", 0) or 0,
            reverse=True,
        )[:limit]
        
        return [
            {
                "rank": i + 1,
                "name": p.get("name"),
                "slug": p.get("slug"),
                "tvl": p.get("tvl"),
                "tvl_change_1d": p.get("change_1d"),
                "tvl_change_7d": p.get("change_7d"),
                "category": p.get("category"),
                "chains": p.get("chains", [])[:5],  # Top 5 chains
                "symbol": p.get("symbol"),
            }
            for i, p in enumerate(sorted_protocols)
        ]
    
    async def get_top_chains(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Get top chains by TVL.
        
        Args:
            limit: Number of chains to return
            
        Returns:
            List of chains sorted by TVL
        """
        chains = await self.get_chains()
        if not chains:
            return []
        
        # Sort by TVL
        sorted_chains = sorted(
            chains,
            key=lambda x: x.get("tvl", 0) or 0,
            reverse=True,
        )[:limit]
        
        return [
            {
                "rank": i + 1,
                "name": c.get("name"),
                "tvl": c.get("tvl"),
                "token_symbol": c.get("tokenSymbol"),
                "gecko_id": c.get("gecko_id"),
            }
            for i, c in enumerate(sorted_chains)
        ]
    
    # ==================== Yields ====================
    
    async def get_yields(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get DeFi yield/APY data for pools.
        
        Args:
            limit: Number of pools to return
            
        Returns:
            List of yield pools sorted by APY
        """
        logger.info("Fetching yield pools from DefiLlama")
        result = await self._request(f"{self.YIELDS_URL}/pools")
        
        if not result or "data" not in result:
            return []
        
        pools = result["data"]
        
        # Sort by APY and take top N
        sorted_pools = sorted(
            pools,
            key=lambda x: x.get("apy", 0) or 0,
            reverse=True,
        )[:limit]
        
        return [
            {
                "pool": p.get("pool"),
                "project": p.get("project"),
                "chain": p.get("chain"),
                "symbol": p.get("symbol"),
                "tvl_usd": p.get("tvlUsd"),
                "apy": p.get("apy"),
                "apy_base": p.get("apyBase"),
                "apy_reward": p.get("apyReward"),
                "reward_tokens": p.get("rewardTokens"),
                "stablecoin": p.get("stablecoin"),
            }
            for p in sorted_pools
        ]
    
    async def get_yield_by_protocol(self, protocol: str) -> list[dict[str, Any]]:
        """
        Get yield pools for a specific protocol.
        
        Args:
            protocol: Protocol name (e.g., "aave", "compound")
            
        Returns:
            List of yield pools for the protocol
        """
        all_yields = await self.get_yields(limit=1000)
        return [
            y for y in all_yields
            if y.get("project", "").lower() == protocol.lower()
        ]
    
    # ==================== Stablecoins ====================
    
    async def get_stablecoins(self) -> list[dict[str, Any]]:
        """
        Get stablecoin market data.
        
        Returns:
            List of stablecoins with market cap and peg data
        """
        logger.info("Fetching stablecoin data")
        result = await self._request(f"{self.STABLECOINS_URL}/stablecoins")
        
        if not result or "peggedAssets" not in result:
            return []
        
        stables = result["peggedAssets"]
        
        return [
            {
                "name": s.get("name"),
                "symbol": s.get("symbol"),
                "gecko_id": s.get("gecko_id"),
                "peg_type": s.get("pegType"),
                "peg_mechanism": s.get("pegMechanism"),
                "circulating": s.get("circulating", {}).get("peggedUSD"),
                "price": s.get("price"),
                "chains": list(s.get("chainCirculating", {}).keys())[:5],
            }
            for s in stables[:50]  # Top 50 stablecoins
        ]
    
    # ==================== Search ====================
    
    async def search_protocol(self, query: str) -> list[dict[str, Any]]:
        """
        Search for protocols by name.
        
        Args:
            query: Search query
            
        Returns:
            Matching protocols
        """
        protocols = await self.get_protocols()
        query_lower = query.lower()
        
        matches = [
            p for p in protocols
            if query_lower in p.get("name", "").lower()
            or query_lower in p.get("symbol", "").lower()
        ]
        
        return [
            {
                "name": p.get("name"),
                "slug": p.get("slug"),
                "tvl": p.get("tvl"),
                "category": p.get("category"),
                "symbol": p.get("symbol"),
            }
            for p in matches[:20]
        ]
    
    # ==================== Summary ====================
    
    async def get_defi_summary(self) -> dict[str, Any]:
        """
        Get summary of DeFi market.
        
        Returns:
            Dictionary with total TVL, top protocols, top chains
        """
        logger.info("Generating DeFi summary")
        
        # Fetch data in parallel
        protocols_task = self.get_top_protocols(10)
        chains_task = self.get_top_chains(10)
        stables_task = self.get_stablecoins()
        
        top_protocols, top_chains, stablecoins = await asyncio.gather(
            protocols_task, chains_task, stables_task
        )
        
        # Calculate totals
        total_tvl = sum(p.get("tvl", 0) or 0 for p in top_protocols)
        total_stablecoin_mcap = sum(s.get("circulating", 0) or 0 for s in stablecoins)
        
        return {
            "total_tvl_sampled": total_tvl,
            "top_protocols": top_protocols,
            "top_chains": top_chains,
            "stablecoin_market_cap": total_stablecoin_mcap,
            "top_stablecoins": stablecoins[:5],
            "timestamp": datetime.now().isoformat(),
        }

