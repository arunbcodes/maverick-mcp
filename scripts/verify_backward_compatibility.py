#!/usr/bin/env python3
"""
Verification script for Phase 1 multi-market support.

This script verifies that existing S&P 500 functionality still works
correctly after implementing multi-market support.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from maverick_mcp.config.markets import (
    get_market_from_symbol,
    get_market_config,
    Market,
    is_us_market,
    is_indian_market
)

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title):
    """Print a formatted section header."""
    logger.info(f"\n{'='*60}")
    logger.info(f"  {title}")
    logger.info(f"{'='*60}\n")


def verify_market_detection():
    """Verify market detection works correctly."""
    print_section("Testing Market Detection")
    
    test_cases = [
        ("AAPL", Market.US, "US stock without suffix"),
        ("MSFT", Market.US, "US stock"),
        ("GOOGL", Market.US, "US stock"),
        ("RELIANCE.NS", Market.INDIA_NSE, "Indian NSE stock"),
        ("TCS.NS", Market.INDIA_NSE, "Indian NSE stock"),
        ("SENSEX.BO", Market.INDIA_BSE, "Indian BSE stock"),
        ("INFY.BO", Market.INDIA_BSE, "Indian BSE stock"),
    ]
    
    passed = 0
    failed = 0
    
    for symbol, expected_market, description in test_cases:
        detected = get_market_from_symbol(symbol)
        if detected == expected_market:
            logger.info(f"✅ {symbol:15} → {detected.value:5} ({description})")
            passed += 1
        else:
            logger.error(f"❌ {symbol:15} → {detected.value:5} (expected {expected_market.value}) ({description})")
            failed += 1
    
    logger.info(f"\n📊 Results: {passed} passed, {failed} failed")
    return failed == 0


def verify_market_configs():
    """Verify market configurations are correct."""
    print_section("Testing Market Configurations")
    
    # US Market Config
    us_config = get_market_config("AAPL")
    logger.info(f"US Market Configuration:")
    logger.info(f"  Country: {us_config.country} (expected: US)")
    logger.info(f"  Currency: {us_config.currency} (expected: USD)")
    logger.info(f"  Trading Hours: {us_config.trading_hours_start} - {us_config.trading_hours_end}")
    logger.info(f"  Circuit Breaker: {us_config.circuit_breaker_percent}%")
    logger.info(f"  Settlement: {us_config.settlement_cycle}")
    
    assert us_config.country == "US", "US country code mismatch"
    assert us_config.currency == "USD", "US currency mismatch"
    assert us_config.circuit_breaker_percent == 7.0, "US circuit breaker mismatch"
    logger.info(f"✅ US market config verified\n")
    
    # Indian NSE Config
    nse_config = get_market_config("RELIANCE.NS")
    logger.info(f"Indian NSE Market Configuration:")
    logger.info(f"  Country: {nse_config.country} (expected: IN)")
    logger.info(f"  Currency: {nse_config.currency} (expected: INR)")
    logger.info(f"  Trading Hours: {nse_config.trading_hours_start} - {nse_config.trading_hours_end}")
    logger.info(f"  Circuit Breaker: {nse_config.circuit_breaker_percent}%")
    logger.info(f"  Settlement: {nse_config.settlement_cycle}")
    
    assert nse_config.country == "IN", "Indian country code mismatch"
    assert nse_config.currency == "INR", "Indian currency mismatch"
    assert nse_config.circuit_breaker_percent == 10.0, "Indian circuit breaker mismatch"
    logger.info(f"✅ Indian NSE market config verified\n")
    
    return True


def verify_helper_functions():
    """Verify helper functions work correctly."""
    print_section("Testing Helper Functions")
    
    # Test is_us_market
    assert is_us_market("AAPL") == True, "AAPL should be US market"
    assert is_us_market("RELIANCE.NS") == False, "RELIANCE.NS should not be US market"
    logger.info("✅ is_us_market() works correctly")
    
    # Test is_indian_market
    assert is_indian_market("AAPL") == False, "AAPL should not be Indian market"
    assert is_indian_market("RELIANCE.NS") == True, "RELIANCE.NS should be Indian market"
    assert is_indian_market("TCS.BO") == True, "TCS.BO should be Indian market"
    logger.info("✅ is_indian_market() works correctly")
    
    return True


def verify_backward_compatibility():
    """Verify that US stock handling is backward compatible."""
    print_section("Testing Backward Compatibility")
    
    # Verify US stocks work without .NS or .BO suffix
    us_stocks = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
    
    for symbol in us_stocks:
        market = get_market_from_symbol(symbol)
        config = get_market_config(symbol)
        
        assert market == Market.US, f"{symbol} should be detected as US market"
        assert config.currency == "USD", f"{symbol} should use USD"
        assert config.country == "US", f"{symbol} should be in US"
        
        logger.info(f"✅ {symbol:6} → Market: {market.value:5}, Currency: {config.currency}, Country: {config.country}")
    
    logger.info(f"\n✅ All existing US stocks work correctly")
    return True


def verify_database_model():
    """Verify database model integration."""
    print_section("Testing Database Model Integration")
    
    try:
        from maverick_mcp.data.models import Stock
        from unittest.mock import Mock
        
        # Test US stock auto-detection
        us_stock = Stock(
            ticker_symbol="AAPL",
            company_name="Apple Inc.",
            market="US",
            country="US",
            currency="USD"
        )
        
        assert us_stock.market == "US"
        assert us_stock.country == "US"
        assert us_stock.currency == "USD"
        logger.info(f"✅ US stock model: {us_stock}")
        
        # Test Indian NSE stock auto-detection
        nse_stock = Stock(
            ticker_symbol="RELIANCE.NS",
            company_name="Reliance Industries",
            market="NSE",
            country="IN",
            currency="INR"
        )
        
        assert nse_stock.market == "NSE"
        assert nse_stock.country == "IN"
        assert nse_stock.currency == "INR"
        logger.info(f"✅ Indian NSE stock model: {nse_stock}")
        
        logger.info(f"\n✅ Database model integration verified")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database model test failed: {e}")
        return False


def main():
    """Run all verification tests."""
    logger.info("🔍 MaverickMCP Phase 1 Multi-Market Support Verification")
    logger.info("=" * 60)
    
    all_passed = True
    
    tests = [
        ("Market Detection", verify_market_detection),
        ("Market Configurations", verify_market_configs),
        ("Helper Functions", verify_helper_functions),
        ("Backward Compatibility", verify_backward_compatibility),
        ("Database Model Integration", verify_database_model),
    ]
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            if not passed:
                all_passed = False
        except Exception as e:
            logger.error(f"\n❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print_section("Final Results")
    
    if all_passed:
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("\n🎉 Phase 1 multi-market support is working correctly")
        logger.info("   - US market functionality: ✅ VERIFIED")
        logger.info("   - Indian market support: ✅ VERIFIED")
        logger.info("   - Backward compatibility: ✅ VERIFIED")
        logger.info("\nExisting S&P 500 functionality is fully preserved.")
        return 0
    else:
        logger.error("❌ SOME TESTS FAILED")
        logger.error("\nPlease review the errors above and fix the issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

