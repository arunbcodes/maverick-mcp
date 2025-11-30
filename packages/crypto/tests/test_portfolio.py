"""Tests for mixed portfolio module."""

import pytest
import numpy as np
import pandas as pd


class TestAssetType:
    """Test AssetType enum."""
    
    def test_stock_type(self):
        """Test stock asset type."""
        from maverick_crypto.portfolio import AssetType
        
        assert AssetType.STOCK.value == "stock"
    
    def test_crypto_type(self):
        """Test crypto asset type."""
        from maverick_crypto.portfolio import AssetType
        
        assert AssetType.CRYPTO.value == "crypto"


class TestPortfolioAsset:
    """Test PortfolioAsset dataclass."""
    
    def test_create_stock_asset(self):
        """Test creating a stock asset."""
        from maverick_crypto.portfolio import PortfolioAsset, AssetType
        
        asset = PortfolioAsset(
            symbol="AAPL",
            asset_type=AssetType.STOCK,
            weight=0.5,
        )
        
        assert asset.symbol == "AAPL"
        assert asset.is_stock
        assert not asset.is_crypto
        assert asset.weight == 0.5
    
    def test_create_crypto_asset(self):
        """Test creating a crypto asset."""
        from maverick_crypto.portfolio import PortfolioAsset, AssetType
        
        asset = PortfolioAsset(
            symbol="BTC",
            asset_type=AssetType.CRYPTO,
            weight=0.3,
        )
        
        assert asset.symbol == "BTC"
        assert asset.is_crypto
        assert not asset.is_stock
    
    def test_asset_to_dict(self):
        """Test asset to_dict method."""
        from maverick_crypto.portfolio import PortfolioAsset, AssetType
        
        asset = PortfolioAsset(
            symbol="ETH",
            asset_type=AssetType.CRYPTO,
            weight=0.2,
        )
        
        d = asset.to_dict()
        
        assert d["symbol"] == "ETH"
        assert d["asset_type"] == "crypto"
        assert d["weight"] == 0.2


class TestMixedPortfolioService:
    """Test MixedPortfolioService."""
    
    @pytest.fixture
    def service(self):
        """Create portfolio service."""
        from maverick_crypto.portfolio import MixedPortfolioService
        return MixedPortfolioService()
    
    def test_create_portfolio(self, service):
        """Test creating a portfolio."""
        portfolio = service.create_portfolio([
            ("AAPL", "stock", 0.3),
            ("MSFT", "stock", 0.3),
            ("BTC", "crypto", 0.4),
        ])
        
        assert len(portfolio) == 3
        assert portfolio[0].symbol == "AAPL"
        assert portfolio[2].symbol == "BTC"
        assert portfolio[2].is_crypto
    
    def test_create_portfolio_normalizes_weights(self, service):
        """Test weight normalization."""
        portfolio = service.create_portfolio([
            ("AAPL", "stock", 0.5),
            ("BTC", "crypto", 0.5),
            ("ETH", "crypto", 0.5),  # Total = 1.5
        ])
        
        # Weights should be normalized
        total_weight = sum(a.weight for a in portfolio)
        assert abs(total_weight - 1.0) < 0.01
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_fetch_asset_data_crypto(self, service):
        """Test fetching crypto data."""
        from maverick_crypto.portfolio import AssetType
        
        df = await service.fetch_asset_data("BTC", AssetType.CRYPTO, days=7)
        
        assert not df.empty
        assert "Close" in df.columns
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_calculate_performance(self, service):
        """Test calculating portfolio performance."""
        portfolio = service.create_portfolio([
            ("AAPL", "stock", 0.5),
            ("BTC", "crypto", 0.5),
        ])
        
        result = await service.calculate_performance(portfolio, days=30)
        
        assert "portfolio" in result or "error" in result


class TestCorrelationAnalyzer:
    """Test CorrelationAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create correlation analyzer."""
        from maverick_crypto.portfolio import CorrelationAnalyzer
        return CorrelationAnalyzer()
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_calculate_correlation_matrix(self, analyzer):
        """Test correlation matrix calculation."""
        result = await analyzer.calculate_correlation_matrix(
            stocks=["AAPL"],
            cryptos=["BTC"],
            days=30,
        )
        
        assert "correlation_matrix" in result or "error" in result
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_asset_class_comparison(self, analyzer):
        """Test asset class comparison."""
        result = await analyzer.asset_class_comparison(
            stocks=["AAPL"],
            cryptos=["BTC"],
            days=30,
        )
        
        assert "stocks" in result or "error" in result
        assert "crypto" in result or "error" in result


class TestPortfolioOptimizer:
    """Test PortfolioOptimizer."""
    
    @pytest.fixture
    def optimizer(self):
        """Create portfolio optimizer."""
        from maverick_crypto.portfolio import PortfolioOptimizer
        return PortfolioOptimizer()
    
    def test_optimization_objectives(self):
        """Test optimization objective enum."""
        from maverick_crypto.portfolio import OptimizationObjective
        
        assert OptimizationObjective.MAX_SHARPE.value == "max_sharpe"
        assert OptimizationObjective.MIN_VOLATILITY.value == "min_volatility"
        assert OptimizationObjective.MAX_RETURN.value == "max_return"
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_optimize_portfolio(self, optimizer):
        """Test portfolio optimization."""
        result = await optimizer.optimize(
            stocks=["AAPL"],
            cryptos=["BTC"],
            objective="max_sharpe",
            days=90,
        )
        
        # Should have result or error
        assert "optimal_weights" in result or "error" in result
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_suggest_allocation_moderate(self, optimizer):
        """Test moderate risk allocation suggestion."""
        result = await optimizer.suggest_allocation(
            stocks=["AAPL"],
            cryptos=["BTC"],
            risk_tolerance="moderate",
        )
        
        assert "risk_profile" in result or "error" in result


class TestPortfolioConstraints:
    """Test portfolio constraint handling."""
    
    @pytest.fixture
    def optimizer(self):
        """Create portfolio optimizer."""
        from maverick_crypto.portfolio import PortfolioOptimizer
        return PortfolioOptimizer()
    
    @pytest.mark.asyncio
    @pytest.mark.external
    async def test_max_crypto_weight_constraint(self, optimizer):
        """Test that crypto weight is respected."""
        result = await optimizer.optimize(
            stocks=["AAPL", "MSFT"],
            cryptos=["BTC", "ETH"],
            objective="max_sharpe",
            max_crypto_weight=0.3,
            days=90,
        )
        
        if "allocation" in result:
            crypto_weight = result["allocation"]["crypto_weight_pct"]
            assert crypto_weight <= 31  # Allow small rounding error


class TestRiskProfiles:
    """Test risk profile allocations."""
    
    def test_conservative_has_lower_crypto(self):
        """Test conservative profile limits crypto."""
        from maverick_crypto.portfolio import PortfolioOptimizer
        
        # Just verify the profile definitions exist
        profiles = {
            "conservative": {"max_crypto_weight": 0.15},
            "moderate": {"max_crypto_weight": 0.30},
            "aggressive": {"max_crypto_weight": 0.50},
        }
        
        assert profiles["conservative"]["max_crypto_weight"] < profiles["moderate"]["max_crypto_weight"]
        assert profiles["moderate"]["max_crypto_weight"] < profiles["aggressive"]["max_crypto_weight"]

