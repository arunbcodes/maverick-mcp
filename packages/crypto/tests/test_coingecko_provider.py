"""Tests for CoinGecko provider."""

import pytest


class TestCoinGeckoAvailability:
    """Test CoinGecko provider availability."""
    
    def test_has_coingecko_flag(self):
        """Test HAS_COINGECKO flag is set correctly."""
        from maverick_crypto.providers import HAS_COINGECKO
        # This should be True if pycoingecko is installed
        assert isinstance(HAS_COINGECKO, bool)
    
    @pytest.mark.skipif(
        not pytest.importorskip("pycoingecko", reason="pycoingecko not installed"),
        reason="pycoingecko not installed"
    )
    def test_coingecko_provider_importable(self):
        """Test CoinGeckoProvider can be imported when pycoingecko is available."""
        from maverick_crypto.providers import CoinGeckoProvider
        assert CoinGeckoProvider is not None


class TestSymbolToIdMapping:
    """Test symbol to CoinGecko ID mapping."""
    
    @pytest.fixture
    def provider(self):
        """Create provider if pycoingecko available."""
        pytest.importorskip("pycoingecko")
        from maverick_crypto.providers import CoinGeckoProvider
        return CoinGeckoProvider()
    
    def test_btc_maps_to_bitcoin(self, provider):
        """Test BTC maps to bitcoin."""
        assert provider.SYMBOL_TO_ID["BTC"] == "bitcoin"
    
    def test_eth_maps_to_ethereum(self, provider):
        """Test ETH maps to ethereum."""
        assert provider.SYMBOL_TO_ID["ETH"] == "ethereum"
    
    def test_sol_maps_to_solana(self, provider):
        """Test SOL maps to solana."""
        assert provider.SYMBOL_TO_ID["SOL"] == "solana"


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter."""
        pytest.importorskip("pycoingecko")
        from maverick_crypto.providers.coingecko_provider import RateLimiter
        return RateLimiter(calls_per_minute=10)
    
    def test_initial_remaining_calls(self, rate_limiter):
        """Test initial remaining calls equals limit."""
        assert rate_limiter.remaining_calls == 10
    
    @pytest.mark.asyncio
    async def test_acquire_reduces_remaining(self, rate_limiter):
        """Test acquiring reduces remaining calls."""
        await rate_limiter.acquire()
        assert rate_limiter.remaining_calls == 9


class TestFearGreedProvider:
    """Test Fear & Greed provider (doesn't need pycoingecko)."""
    
    @pytest.fixture
    def provider(self):
        """Create FearGreedProvider."""
        from maverick_crypto.providers.coingecko_provider import FearGreedProvider
        return FearGreedProvider()
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_fear_greed_index(self, provider):
        """Test fetching fear/greed index."""
        result = await provider.get_fear_greed_index()
        
        # Should have required fields
        assert "value" in result
        assert "classification" in result or "error" in result
        
        if "value" in result:
            # Value should be 0-100
            assert 0 <= result["value"] <= 100


class TestCoinGeckoIntegration:
    """Integration tests for CoinGecko provider."""
    
    @pytest.fixture
    def provider(self):
        """Create provider if pycoingecko available."""
        pytest.importorskip("pycoingecko")
        from maverick_crypto.providers import CoinGeckoProvider
        return CoinGeckoProvider()
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_trending(self, provider):
        """Test fetching trending coins."""
        result = await provider.get_trending()
        
        assert "coins" in result
        assert len(result["coins"]) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_global_data(self, provider):
        """Test fetching global market data."""
        result = await provider.get_global_data()
        
        assert "btc_dominance" in result
        assert "total_market_cap_usd" in result
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_top_coins(self, provider):
        """Test fetching top coins."""
        result = await provider.get_top_coins(limit=10)
        
        assert len(result) == 10
        assert result[0]["symbol"] == "BTC"  # Bitcoin should be #1
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_coin_id_static(self, provider):
        """Test getting coin ID from static mapping."""
        coin_id = await provider.get_coin_id("BTC")
        assert coin_id == "bitcoin"
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_coin_data(self, provider):
        """Test fetching detailed coin data."""
        result = await provider.get_coin_data("bitcoin")
        
        assert result["symbol"] == "BTC"
        assert "current_price" in result
        assert "market_cap" in result

