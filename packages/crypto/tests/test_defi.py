"""Tests for DeFi module."""

import pytest


class TestDefiLlamaProvider:
    """Test DefiLlama provider."""
    
    @pytest.fixture
    def provider(self):
        """Create DefiLlama provider."""
        from maverick_crypto.defi import DefiLlamaProvider
        return DefiLlamaProvider()
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_top_protocols(self, provider):
        """Test fetching top protocols."""
        protocols = await provider.get_top_protocols(10)
        
        assert len(protocols) <= 10
        if protocols:
            assert "name" in protocols[0]
            assert "tvl" in protocols[0]
            assert "rank" in protocols[0]
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_top_chains(self, provider):
        """Test fetching top chains."""
        chains = await provider.get_top_chains(10)
        
        assert len(chains) <= 10
        if chains:
            assert "name" in chains[0]
            assert "tvl" in chains[0]
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_protocol(self, provider):
        """Test fetching specific protocol."""
        data = await provider.get_protocol("uniswap")

        # API may return None if service is unavailable or rate-limited
        if data is not None:
            assert "tvl" in data or "chainTvls" in data
        else:
            pytest.skip("DefiLlama API returned no data (service may be unavailable)")
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_yields(self, provider):
        """Test fetching yield pools."""
        yields = await provider.get_yields(10)
        
        assert len(yields) <= 10
        if yields:
            assert "apy" in yields[0]
            assert "project" in yields[0]
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_stablecoins(self, provider):
        """Test fetching stablecoins."""
        stables = await provider.get_stablecoins()
        
        assert len(stables) > 0
        assert "name" in stables[0]
        assert "symbol" in stables[0]
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_search_protocol(self, provider):
        """Test protocol search."""
        results = await provider.search_protocol("uni")
        
        assert len(results) > 0
        # Should find Uniswap
        names = [r["name"].lower() for r in results]
        assert any("uni" in name for name in names)


class TestOnChainProvider:
    """Test OnChain/GeckoTerminal provider."""
    
    @pytest.fixture
    def provider(self):
        """Create OnChain provider."""
        from maverick_crypto.defi import OnChainProvider
        return OnChainProvider()
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_trending_pools(self, provider):
        """Test fetching trending pools."""
        pools = await provider.get_trending_pools()
        
        # May return empty if API unavailable
        assert isinstance(pools, list)
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_networks(self, provider):
        """Test fetching networks."""
        networks = await provider.get_networks()
        
        assert isinstance(networks, list)
    
    def test_network_mapping(self, provider):
        """Test network name mapping."""
        assert provider.NETWORKS["ethereum"] == "eth"
        assert provider.NETWORKS["solana"] == "solana"
        assert provider.NETWORKS["arbitrum"] == "arbitrum"


class TestDefiModuleImports:
    """Test DeFi module imports."""
    
    def test_import_defillama(self):
        """Test DefiLlama import."""
        from maverick_crypto.defi import DefiLlamaProvider
        assert DefiLlamaProvider is not None
    
    def test_import_onchain(self):
        """Test OnChain import."""
        from maverick_crypto.defi import OnChainProvider
        assert OnChainProvider is not None
    
    def test_provider_initialization(self):
        """Test providers can be instantiated."""
        from maverick_crypto.defi import DefiLlamaProvider, OnChainProvider
        
        defi = DefiLlamaProvider()
        onchain = OnChainProvider()
        
        assert defi is not None
        assert onchain is not None

