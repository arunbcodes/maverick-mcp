"""
Comprehensive tests for ScreeningService.

Tests cover:
- Initialization and session management
- Maverick bullish recommendations
- Maverick bearish recommendations
- Supply/demand breakout recommendations
- All-in-one screening
- Reason generation helpers
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from maverick_mcp.services.screening_service import ScreeningService


class TestScreeningServiceInitialization:
    """Test initialization and configuration."""
    
    def test_initializes_without_session(self):
        """Test initialization without provided session."""
        service = ScreeningService()
        assert service._db_session is None
    
    def test_initializes_with_session(self):
        """Test initialization with injected session."""
        mock_session = Mock(spec=Session)
        service = ScreeningService(db_session=mock_session)
        assert service._db_session == mock_session
    
    def test_logs_initialization(self, caplog):
        """Test that initialization is logged."""
        ScreeningService()
        assert "ScreeningService initialized" in caplog.text


class TestSessionManagement:
    """Test database session handling."""
    
    def test_uses_injected_session(self):
        """Test that injected session is used and not closed."""
        mock_session = Mock(spec=Session)
        service = ScreeningService(db_session=mock_session)
        
        session, should_close = service._get_db_session()
        
        assert session == mock_session
        assert should_close is False
    
    @patch('maverick_mcp.services.screening_service.SessionLocal')
    def test_creates_new_session_when_none_provided(self, mock_session_local):
        """Test that new session is created when none provided."""
        mock_new_session = Mock(spec=Session)
        mock_session_local.return_value = mock_new_session
        
        service = ScreeningService()
        session, should_close = service._get_db_session()
        
        assert session == mock_new_session
        assert should_close is True
        mock_session_local.assert_called_once()
    
    @patch('maverick_mcp.services.screening_service.SessionLocal')
    def test_handles_session_creation_failure(self, mock_session_local):
        """Test error handling when session creation fails."""
        mock_session_local.side_effect = Exception("Database connection failed")
        
        service = ScreeningService()
        
        with pytest.raises(Exception, match="Database connection failed"):
            service._get_db_session()


class TestGetMaverickRecommendations:
    """Test Maverick bullish recommendations."""
    
    def test_returns_recommendations_successfully(self):
        """Test successful retrieval of bullish recommendations."""
        mock_stock = Mock()
        mock_stock.to_dict.return_value = {
            "ticker_symbol": "AAPL",
            "combined_score": 95,
            "momentum_score": 90
        }
        mock_stock.combined_score = 95
        mock_stock.momentum_score = 90
        mock_stock.pat = "VCP"
        mock_stock.consolidation = "yes"
        mock_stock.sqz = "high"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_stock]
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        
        service = ScreeningService(db_session=mock_session)
        result = service.get_maverick_recommendations(limit=20)
        
        assert len(result) == 1
        assert result[0]["ticker_symbol"] == "AAPL"
        assert result[0]["recommendation_type"] == "maverick_bullish"
        assert "reason" in result[0]
    
    def test_applies_min_score_filter(self):
        """Test that min_score filter is applied."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        
        service = ScreeningService(db_session=mock_session)
        service.get_maverick_recommendations(limit=10, min_score=80)
        
        # Verify filter was called
        mock_query.filter.assert_called()
    
    def test_respects_limit_parameter(self):
        """Test that limit parameter is respected."""
        mock_query = Mock()
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        
        service = ScreeningService(db_session=mock_session)
        service.get_maverick_recommendations(limit=5)
        
        # Verify limit was called with correct value
        mock_query.limit.assert_called_once_with(5)
    
    def test_handles_errors_gracefully(self):
        """Test error handling during query."""
        mock_session = Mock(spec=Session)
        mock_session.query.side_effect = Exception("Database error")
        
        service = ScreeningService(db_session=mock_session)
        result = service.get_maverick_recommendations()
        
        assert result == []
    
    @patch('maverick_mcp.services.screening_service.SessionLocal')
    def test_closes_session_when_created_locally(self, mock_session_local):
        """Test that locally created sessions are closed."""
        mock_query = Mock()
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        mock_session_local.return_value = mock_session
        
        service = ScreeningService()  # No injected session
        service.get_maverick_recommendations()
        
        mock_session.close.assert_called_once()


class TestGetMaverickBearRecommendations:
    """Test Maverick bearish recommendations."""
    
    def test_returns_bear_recommendations_successfully(self):
        """Test successful retrieval of bear recommendations."""
        mock_stock = Mock()
        mock_stock.to_dict.return_value = {
            "ticker_symbol": "WEAK",
            "score": 92,
            "momentum_score": 25
        }
        mock_stock.score = 92
        mock_stock.momentum_score = 25
        mock_stock.rsi_14 = 28
        mock_stock.atr_contraction = True
        mock_stock.big_down_vol = True
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_stock]
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        
        service = ScreeningService(db_session=mock_session)
        result = service.get_maverick_bear_recommendations(limit=20)
        
        assert len(result) == 1
        assert result[0]["ticker_symbol"] == "WEAK"
        assert result[0]["recommendation_type"] == "maverick_bearish"
        assert "reason" in result[0]
    
    def test_applies_min_score_filter(self):
        """Test that min_score filter is applied for bear stocks."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        
        service = ScreeningService(db_session=mock_session)
        service.get_maverick_bear_recommendations(min_score=85)
        
        # Verify filter was called
        mock_query.filter.assert_called()
    
    def test_handles_errors_gracefully(self):
        """Test error handling during bear query."""
        mock_session = Mock(spec=Session)
        mock_session.query.side_effect = Exception("Database error")
        
        service = ScreeningService(db_session=mock_session)
        result = service.get_maverick_bear_recommendations()
        
        assert result == []


class TestGetSupplyDemandBreakoutRecommendations:
    """Test supply/demand breakout recommendations."""
    
    def test_returns_breakout_recommendations_successfully(self):
        """Test successful retrieval of breakout recommendations."""
        mock_stock = Mock()
        mock_stock.to_dict.return_value = {
            "ticker_symbol": "BREAKOUT",
            "momentum_score": 95
        }
        mock_stock.momentum_score = 95
        mock_stock.pat = "Cup and Handle"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_stock]
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        
        service = ScreeningService(db_session=mock_session)
        result = service.get_supply_demand_breakout_recommendations(limit=20)
        
        assert len(result) == 1
        assert result[0]["ticker_symbol"] == "BREAKOUT"
        assert result[0]["recommendation_type"] == "supply_demand_breakout"
        assert "reason" in result[0]
    
    def test_applies_min_momentum_score_filter(self):
        """Test that min_momentum_score filter is applied."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        
        service = ScreeningService(db_session=mock_session)
        service.get_supply_demand_breakout_recommendations(min_momentum_score=80.0)
        
        # Verify query was built with filters
        assert mock_query.filter.call_count >= 1
    
    def test_handles_errors_gracefully(self):
        """Test error handling during breakout query."""
        mock_session = Mock(spec=Session)
        mock_session.query.side_effect = Exception("Database error")
        
        service = ScreeningService(db_session=mock_session)
        result = service.get_supply_demand_breakout_recommendations()
        
        assert result == []


class TestGetAllScreeningRecommendations:
    """Test all-in-one screening."""
    
    @patch('maverick_mcp.services.screening_service.get_latest_maverick_screening')
    def test_returns_all_recommendations_successfully(self, mock_get_latest):
        """Test successful retrieval of all recommendations."""
        mock_get_latest.return_value = {
            "maverick_stocks": [
                {"ticker_symbol": "AAPL", "combined_score": 95, "momentum_score": 90}
            ],
            "maverick_bear_stocks": [
                {"ticker_symbol": "WEAK", "score": 90, "momentum_score": 25}
            ],
            "supply_demand_breakouts": [
                {"ticker_symbol": "BREAKOUT", "momentum_score": 92}
            ]
        }
        
        service = ScreeningService()
        result = service.get_all_screening_recommendations()
        
        assert "maverick_stocks" in result
        assert "maverick_bear_stocks" in result
        assert "supply_demand_breakouts" in result
        assert len(result["maverick_stocks"]) == 1
        assert len(result["maverick_bear_stocks"]) == 1
        assert len(result["supply_demand_breakouts"]) == 1
        
        # Check that reasons and types were added
        assert result["maverick_stocks"][0]["recommendation_type"] == "maverick_bullish"
        assert "reason" in result["maverick_stocks"][0]
    
    @patch('maverick_mcp.services.screening_service.get_latest_maverick_screening')
    def test_handles_errors_gracefully(self, mock_get_latest):
        """Test error handling in all screening."""
        mock_get_latest.side_effect = Exception("Database error")
        
        service = ScreeningService()
        result = service.get_all_screening_recommendations()
        
        assert result == {
            "maverick_stocks": [],
            "maverick_bear_stocks": [],
            "supply_demand_breakouts": []
        }


class TestGenerateMaverickReason:
    """Test Maverick bullish reason generation."""
    
    def test_generates_reason_with_high_scores(self):
        """Test reason generation with exceptional scores."""
        mock_stock = Mock()
        mock_stock.combined_score = 95
        mock_stock.momentum_score = 92
        mock_stock.pat = "VCP"
        mock_stock.consolidation = "yes"
        mock_stock.sqz = "high"
        
        service = ScreeningService()
        reason = service._generate_maverick_reason(mock_stock)
        
        assert "Exceptional combined score" in reason
        assert "outstanding relative strength" in reason
        assert "VCP pattern detected" in reason
        assert "consolidation characteristics" in reason
        assert "squeeze indicator: high" in reason
    
    def test_generates_reason_with_moderate_scores(self):
        """Test reason generation with strong scores."""
        mock_stock = Mock()
        mock_stock.combined_score = 85
        mock_stock.momentum_score = 82
        mock_stock.pat = ""
        mock_stock.consolidation = "no"
        mock_stock.sqz = ""
        
        service = ScreeningService()
        reason = service._generate_maverick_reason(mock_stock)
        
        assert "Strong combined score" in reason
        assert "strong relative strength" in reason
    
    def test_generates_fallback_reason(self):
        """Test fallback reason when no specific criteria met."""
        mock_stock = Mock()
        mock_stock.combined_score = 70
        mock_stock.momentum_score = 65
        mock_stock.pat = ""
        mock_stock.consolidation = "no"
        mock_stock.sqz = ""
        
        service = ScreeningService()
        reason = service._generate_maverick_reason(mock_stock)
        
        assert reason == "Strong technical setup"


class TestGenerateBearReason:
    """Test Maverick bearish reason generation."""
    
    def test_generates_reason_with_strong_signals(self):
        """Test reason generation with strong bearish signals."""
        mock_stock = Mock()
        mock_stock.score = 92
        mock_stock.momentum_score = 25
        mock_stock.rsi_14 = 28
        mock_stock.atr_contraction = True
        mock_stock.big_down_vol = True
        
        service = ScreeningService()
        reason = service._generate_bear_reason(mock_stock)
        
        assert "Exceptional bear score" in reason
        assert "weak relative strength" in reason
        assert "oversold RSI" in reason
        assert "ATR contraction" in reason
        assert "heavy selling volume" in reason
    
    def test_generates_fallback_reason(self):
        """Test fallback reason for bear stocks."""
        mock_stock = Mock()
        mock_stock.score = 70
        mock_stock.momentum_score = 50
        mock_stock.rsi_14 = 45
        mock_stock.atr_contraction = False
        mock_stock.big_down_vol = False
        
        service = ScreeningService()
        reason = service._generate_bear_reason(mock_stock)
        
        assert reason == "Weak technical setup"


class TestGenerateSupplyDemandReason:
    """Test supply/demand breakout reason generation."""
    
    def test_generates_reason_with_high_momentum(self):
        """Test reason generation with exceptional momentum."""
        mock_stock = Mock()
        mock_stock.momentum_score = 95
        mock_stock.pat = "Cup and Handle"
        
        service = ScreeningService()
        reason = service._generate_supply_demand_reason(mock_stock)
        
        assert "Supply/demand breakout from accumulation" in reason
        assert "exceptional relative strength" in reason
        assert "Cup and Handle pattern" in reason
        assert "price above all major moving averages" in reason
        assert "moving averages in proper alignment" in reason
    
    def test_generates_reason_without_pattern(self):
        """Test reason generation without pattern."""
        mock_stock = Mock()
        mock_stock.momentum_score = 82
        mock_stock.pat = ""
        
        service = ScreeningService()
        reason = service._generate_supply_demand_reason(mock_stock)
        
        assert "Supply/demand breakout from accumulation" in reason
        assert "strong relative strength" in reason


class TestGenerateReasonsFromDict:
    """Test reason generation from dictionary."""
    
    def test_generates_maverick_reason_from_dict(self):
        """Test Maverick reason generation from dict."""
        stock_dict = {
            "combined_score": 95,
            "momentum_score": 90,
            "pattern": "VCP",
            "consolidation": "yes",
            "squeeze": "high"
        }
        
        service = ScreeningService()
        reason = service._generate_maverick_reason_from_dict(stock_dict)
        
        assert "Exceptional combined score" in reason
        assert "outstanding relative strength" in reason
        assert "VCP pattern detected" in reason
    
    def test_generates_bear_reason_from_dict(self):
        """Test bear reason generation from dict."""
        stock_dict = {
            "score": 92,
            "momentum_score": 25,
            "rsi_14": 28,
            "atr_contraction": True,
            "big_down_vol": True
        }
        
        service = ScreeningService()
        reason = service._generate_bear_reason_from_dict(stock_dict)
        
        assert "Exceptional bear score" in reason
        assert "weak relative strength" in reason
        assert "oversold RSI" in reason
    
    def test_generates_supply_demand_reason_from_dict(self):
        """Test supply/demand reason generation from dict."""
        stock_dict = {
            "momentum_score": 95,
            "pattern": "Flat Base"
        }
        
        service = ScreeningService()
        reason = service._generate_supply_demand_reason_from_dict(stock_dict)
        
        assert "Supply/demand breakout from accumulation" in reason
        assert "exceptional relative strength" in reason
        assert "Flat Base pattern" in reason


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_handles_empty_results(self):
        """Test handling of empty query results."""
        mock_query = Mock()
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        
        service = ScreeningService(db_session=mock_session)
        result = service.get_maverick_recommendations()
        
        assert result == []
    
    def test_handles_none_attributes_in_reason_generation(self):
        """Test reason generation with None attributes."""
        mock_stock = Mock()
        mock_stock.combined_score = None
        mock_stock.momentum_score = None
        mock_stock.pat = None
        mock_stock.consolidation = None
        mock_stock.sqz = None
        
        service = ScreeningService()
        reason = service._generate_maverick_reason(mock_stock)
        
        # Should not crash and return fallback
        assert isinstance(reason, str)
    
    @patch('maverick_mcp.services.screening_service.get_latest_maverick_screening')
    def test_handles_missing_keys_in_all_screening(self, mock_get_latest):
        """Test handling of missing keys in all screening results."""
        mock_get_latest.return_value = {}  # Missing all keys
        
        service = ScreeningService()
        result = service.get_all_screening_recommendations()
        
        # Should not crash and return the dict (may be empty or have empty lists)
        assert isinstance(result, dict)


# Note: These are unit tests with mocked database dependencies

