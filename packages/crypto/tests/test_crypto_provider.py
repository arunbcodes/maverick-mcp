"""Tests for CryptoDataProvider."""

import pytest


class TestSymbolNormalization:
    """Test symbol normalization logic."""
    
    def test_normalize_btc(self, crypto_provider):
        """Test BTC normalizes to BTC-USD."""
        assert crypto_provider.normalize_symbol("BTC") == "BTC-USD"
    
    def test_normalize_lowercase(self, crypto_provider):
        """Test lowercase symbols are uppercased."""
        assert crypto_provider.normalize_symbol("eth") == "ETH-USD"
    
    def test_normalize_already_correct(self, crypto_provider):
        """Test already correct format is unchanged."""
        assert crypto_provider.normalize_symbol("BTC-USD") == "BTC-USD"
    
    def test_normalize_usdt_suffix(self, crypto_provider):
        """Test USDT suffix is removed."""
        assert crypto_provider.normalize_symbol("BTCUSDT") == "BTC-USD"
    
    def test_normalize_stock_suffix_removed(self, crypto_provider):
        """Test stock suffixes are removed."""
        assert crypto_provider.normalize_symbol("BTC.NS") == "BTC-USD"
    
    def test_normalize_with_whitespace(self, crypto_provider):
        """Test whitespace is trimmed."""
        assert crypto_provider.normalize_symbol("  ETH  ") == "ETH-USD"


class TestIsCryptoSymbol:
    """Test crypto symbol detection."""
    
    def test_btc_usd_is_crypto(self, crypto_provider):
        """Test BTC-USD is detected as crypto."""
        assert crypto_provider.is_crypto_symbol("BTC-USD")
    
    def test_btc_is_crypto(self, crypto_provider):
        """Test BTC is detected as crypto."""
        assert crypto_provider.is_crypto_symbol("BTC")
    
    def test_eth_is_crypto(self, crypto_provider):
        """Test ETH is detected as crypto."""
        assert crypto_provider.is_crypto_symbol("ETH")
    
    def test_usdt_suffix_is_crypto(self, crypto_provider):
        """Test USDT suffix is detected as crypto."""
        assert crypto_provider.is_crypto_symbol("BTC-USDT")


class TestCryptoDataFetching:
    """Test actual data fetching (integration tests)."""
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_fetch_btc_data(self, crypto_provider):
        """Test fetching Bitcoin data."""
        df = await crypto_provider.get_crypto_data("BTC", days=7)
        
        assert not df.empty
        assert "Close" in df.columns
        assert "Volume" in df.columns
        assert len(df) >= 5  # At least 5 days of data
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_fetch_eth_data(self, crypto_provider):
        """Test fetching Ethereum data."""
        df = await crypto_provider.get_crypto_data("ETH", days=7)
        
        assert not df.empty
        assert "Close" in df.columns
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_get_realtime_price(self, crypto_provider):
        """Test getting current price."""
        price_data = await crypto_provider.get_realtime_price("BTC")
        
        assert price_data is not None
        assert "price" in price_data
        assert price_data["price"] > 0
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_fetch_multiple_cryptos(self, crypto_provider):
        """Test fetching multiple cryptocurrencies."""
        symbols = ["BTC", "ETH"]
        data = await crypto_provider.get_multiple_cryptos(symbols, days=7)
        
        assert len(data) >= 1
        for symbol, df in data.items():
            assert not df.empty

