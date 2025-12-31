#!/usr/bin/env python3
"""
Seed script to populate database with Indian market stocks (Nifty 50 and Sensex).

This script:
1. Loads Nifty 50 and Sensex constituent stocks
2. Fetches basic information for each stock
3. Stores them in the database with proper market metadata
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yfinance as yf
from sqlalchemy.orm import Session

from maverick_data import Stock, SessionLocal
from maverick_india.market import INDIAN_MARKET_CONFIG


# Compatibility shim for Market enum
class Market:
    INDIA_NSE = "NSE"
    INDIA_BSE = "BSE"


def get_market_config(symbol: str):
    """Get market config for symbol."""
    market = "NSE" if symbol.endswith('.NS') else "BSE"
    config = INDIAN_MARKET_CONFIG.get(market, INDIAN_MARKET_CONFIG["NSE"])

    class Config:
        name = market
        country = config["country"]
        currency = config["currency"]

    return Config()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Extended list of major Indian stocks with company names
INDIAN_STOCKS = {
    # Nifty 50 Major Companies
    "RELIANCE.NS": "Reliance Industries Ltd.",
    "TCS.NS": "Tata Consultancy Services Ltd.",
    "HDFCBANK.NS": "HDFC Bank Ltd.",
    "INFY.NS": "Infosys Ltd.",
    "ICICIBANK.NS": "ICICI Bank Ltd.",
    "HINDUNILVR.NS": "Hindustan Unilever Ltd.",
    "ITC.NS": "ITC Ltd.",
    "SBIN.NS": "State Bank of India",
    "BHARTIARTL.NS": "Bharti Airtel Ltd.",
    "BAJFINANCE.NS": "Bajaj Finance Ltd.",
    "KOTAKBANK.NS": "Kotak Mahindra Bank Ltd.",
    "LT.NS": "Larsen & Toubro Ltd.",
    "HCLTECH.NS": "HCL Technologies Ltd.",
    "ASIANPAINT.NS": "Asian Paints Ltd.",
    "AXISBANK.NS": "Axis Bank Ltd.",
    "MARUTI.NS": "Maruti Suzuki India Ltd.",
    "SUNPHARMA.NS": "Sun Pharmaceutical Industries Ltd.",
    "TITAN.NS": "Titan Company Ltd.",
    "ULTRACEMCO.NS": "UltraTech Cement Ltd.",
    "NESTLEIND.NS": "Nestle India Ltd.",
    "WIPRO.NS": "Wipro Ltd.",
    "BAJAJFINSV.NS": "Bajaj Finserv Ltd.",
    "TECHM.NS": "Tech Mahindra Ltd.",
    "POWERGRID.NS": "Power Grid Corporation of India Ltd.",
    "NTPC.NS": "NTPC Ltd.",
    "M&M.NS": "Mahindra & Mahindra Ltd.",
    "ONGC.NS": "Oil and Natural Gas Corporation Ltd.",
    "TATAMOTORS.NS": "Tata Motors Ltd.",
    "JSWSTEEL.NS": "JSW Steel Ltd.",
    "INDUSINDBK.NS": "IndusInd Bank Ltd.",
    "ADANIENT.NS": "Adani Enterprises Ltd.",
    "ADANIPORTS.NS": "Adani Ports and Special Economic Zone Ltd.",
    "TATASTEEL.NS": "Tata Steel Ltd.",
    "COALINDIA.NS": "Coal India Ltd.",
    "HINDALCO.NS": "Hindalco Industries Ltd.",
    "GRASIM.NS": "Grasim Industries Ltd.",
    "DIVISLAB.NS": "Divi's Laboratories Ltd.",
    "DRREDDY.NS": "Dr. Reddy's Laboratories Ltd.",
    "CIPLA.NS": "Cipla Ltd.",
    "APOLLOHOSP.NS": "Apollo Hospitals Enterprise Ltd.",
    "EICHERMOT.NS": "Eicher Motors Ltd.",
    "BRITANNIA.NS": "Britannia Industries Ltd.",
    "BPCL.NS": "Bharat Petroleum Corporation Ltd.",
    "HEROMOTOCO.NS": "Hero MotoCorp Ltd.",
    "TATACONSUM.NS": "Tata Consumer Products Ltd.",
    "SBILIFE.NS": "SBI Life Insurance Company Ltd.",
    "BAJAJ-AUTO.NS": "Bajaj Auto Ltd.",
    "HDFCLIFE.NS": "HDFC Life Insurance Company Ltd.",
    "IOC.NS": "Indian Oil Corporation Ltd.",
    "UPL.NS": "UPL Ltd.",
}


def fetch_stock_info(symbol: str) -> dict:
    """
    Fetch basic stock information from yfinance.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dictionary with stock info
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info
    except Exception as e:
        logger.warning(f"Could not fetch info for {symbol}: {e}")
        return {}


def seed_indian_stock(session: Session, symbol: str, company_name: str) -> Stock:
    """
    Add or update an Indian stock in the database.
    
    Args:
        session: Database session
        symbol: Stock ticker symbol
        company_name: Company name
        
    Returns:
        Stock object
    """
    # Get market configuration
    config = get_market_config(symbol)
    market = Market.INDIA_NSE if symbol.endswith('.NS') else Market.INDIA_BSE
    
    # Fetch additional info from yfinance
    info = fetch_stock_info(symbol)
    
    # Extract relevant fields
    sector = info.get('sector', 'Unknown')
    industry = info.get('industry', 'Unknown')
    market_cap = info.get('marketCap')
    
    # Get or create stock
    stock = Stock.get_or_create(
        session,
        ticker_symbol=symbol,
        company_name=company_name,
        market=market.value,
        exchange=config.name,
        country=config.country,
        currency=config.currency,
        sector=sector,
        industry=industry,
        is_active=True
    )
    
    logger.info(f"✅ Seeded: {symbol} - {company_name} ({market.value})")
    return stock


def main():
    """Main function to seed Indian stocks."""
    logger.info("=" * 80)
    logger.info("🇮🇳 Starting Indian Stock Market Database Seeding")
    logger.info("=" * 80)
    
    # Create database session
    session = SessionLocal()
    
    try:
        total_stocks = len(INDIAN_STOCKS)
        successful = 0
        failed = 0
        
        logger.info(f"\n📊 Seeding {total_stocks} Indian stocks...")
        logger.info("")
        
        for symbol, company_name in INDIAN_STOCKS.items():
            try:
                seed_indian_stock(session, symbol, company_name)
                successful += 1
            except Exception as e:
                logger.error(f"❌ Failed to seed {symbol}: {e}")
                failed += 1
        
        # Commit all changes
        session.commit()
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("📈 Seeding Summary")
        logger.info("=" * 80)
        logger.info(f"✅ Successfully seeded: {successful} stocks")
        if failed > 0:
            logger.info(f"❌ Failed: {failed} stocks")
        logger.info(f"📊 Total: {total_stocks} stocks")
        logger.info("")
        
        # Query and display stats
        nse_count = session.query(Stock).filter(Stock.market == "NSE").count()
        bse_count = session.query(Stock).filter(Stock.market == "BSE").count()
        
        logger.info("💾 Database Statistics:")
        logger.info(f"   NSE stocks: {nse_count}")
        logger.info(f"   BSE stocks: {bse_count}")
        logger.info("")
        logger.info("🎉 Indian stock seeding completed successfully!")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Seeding failed with error: {e}")
        session.rollback()
        return False
        
    finally:
        session.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

