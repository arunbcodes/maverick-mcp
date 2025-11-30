#!/usr/bin/env python3
"""
Seed top cryptocurrencies into the database.

Similar to seed_sp500.py, this script populates the database with
the top cryptocurrencies by market cap, enabling local caching and
faster queries.

Usage:
    # Seed top 100 cryptos (default)
    python scripts/seed_top_cryptos.py

    # Seed top 50 cryptos
    python scripts/seed_top_cryptos.py --limit 50

    # Force refresh all data
    python scripts/seed_top_cryptos.py --force

Requirements:
    - pycoingecko: pip install pycoingecko
    - Or: pip install maverick-crypto[coingecko]
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add packages to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "packages" / "crypto" / "src"))
sys.path.insert(0, str(project_root / "packages" / "data" / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def seed_top_cryptos(
    limit: int = 100,
    force: bool = False,
) -> dict[str, int]:
    """
    Seed top cryptocurrencies into the database.
    
    Args:
        limit: Number of cryptos to seed (default: 100)
        force: Force update existing records
        
    Returns:
        Dictionary with counts: added, updated, skipped, errors
    """
    # Import here to handle missing dependencies gracefully
    try:
        from maverick_crypto.providers import CoinGeckoProvider, HAS_COINGECKO
    except ImportError as e:
        logger.error(f"Failed to import CoinGecko provider: {e}")
        logger.error("Install with: pip install maverick-crypto[coingecko]")
        return {"error": str(e)}
    
    if not HAS_COINGECKO:
        logger.error("CoinGecko not available. Install with: pip install pycoingecko")
        return {"error": "pycoingecko not installed"}
    
    # Try to import database session
    try:
        from maverick_data.session import SessionLocal
        from maverick_crypto.models import Crypto
    except ImportError:
        logger.warning("maverick_data not available, using standalone session")
        # Create standalone session for crypto
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import os
        
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:55432/maverick_mcp"
        )
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(bind=engine)
        
        from maverick_crypto.models import Crypto, CryptoBase
        CryptoBase.metadata.create_all(engine)
    
    # Initialize provider
    provider = CoinGeckoProvider(calls_per_minute=10)
    
    counts = {"added": 0, "updated": 0, "skipped": 0, "errors": 0}
    
    try:
        logger.info(f"Fetching top {limit} cryptocurrencies from CoinGecko...")
        top_coins = await provider.get_top_coins(limit=limit)
        
        logger.info(f"Fetched {len(top_coins)} coins, starting database seed...")
        
        session = SessionLocal()
        try:
            for coin_data in top_coins:
                try:
                    symbol = coin_data.get("symbol", "").upper()
                    coingecko_id = coin_data.get("id")
                    
                    if not symbol or not coingecko_id:
                        logger.warning(f"Skipping coin with missing data: {coin_data}")
                        counts["skipped"] += 1
                        continue
                    
                    # Check if exists
                    existing = session.query(Crypto).filter_by(symbol=symbol).first()
                    
                    if existing:
                        if force:
                            # Update existing
                            existing.name = coin_data.get("name", existing.name)
                            existing.coingecko_id = coingecko_id
                            existing.yfinance_symbol = f"{symbol}-USD"
                            existing.market_cap_rank = coin_data.get("market_cap_rank")
                            existing.market_cap = coin_data.get("market_cap")
                            existing.current_price = coin_data.get("current_price")
                            existing.price_change_24h = coin_data.get("price_change_24h")
                            existing.price_change_percentage_24h = coin_data.get("price_change_percentage_24h")
                            existing.circulating_supply = coin_data.get("circulating_supply")
                            existing.total_supply = coin_data.get("total_supply")
                            existing.total_volume = coin_data.get("total_volume")
                            existing.ath = coin_data.get("ath")
                            existing.ath_date = coin_data.get("ath_date")
                            counts["updated"] += 1
                            logger.debug(f"Updated {symbol}")
                        else:
                            counts["skipped"] += 1
                            logger.debug(f"Skipped existing {symbol}")
                    else:
                        # Create new
                        crypto = Crypto(
                            symbol=symbol,
                            name=coin_data.get("name", symbol),
                            coingecko_id=coingecko_id,
                            yfinance_symbol=f"{symbol}-USD",
                            market_cap_rank=coin_data.get("market_cap_rank"),
                            market_cap=coin_data.get("market_cap"),
                            current_price=coin_data.get("current_price"),
                            price_change_24h=coin_data.get("price_change_24h"),
                            price_change_percentage_24h=coin_data.get("price_change_percentage_24h"),
                            circulating_supply=coin_data.get("circulating_supply"),
                            total_supply=coin_data.get("total_supply"),
                            total_volume=coin_data.get("total_volume"),
                            ath=coin_data.get("ath"),
                            ath_date=coin_data.get("ath_date"),
                            is_active=True,
                        )
                        session.add(crypto)
                        counts["added"] += 1
                        logger.debug(f"Added {symbol}")
                    
                except Exception as e:
                    logger.error(f"Error processing coin {coin_data.get('symbol')}: {e}")
                    counts["errors"] += 1
            
            session.commit()
            logger.info(
                f"Seed complete: {counts['added']} added, "
                f"{counts['updated']} updated, "
                f"{counts['skipped']} skipped, "
                f"{counts['errors']} errors"
            )
            
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            counts["errors"] += 1
            raise
        finally:
            session.close()
    
    except Exception as e:
        logger.error(f"Failed to seed cryptocurrencies: {e}")
        counts["errors"] += 1
    
    return counts


async def verify_seeded_data() -> dict[str, int]:
    """Verify the seeded cryptocurrency data."""
    try:
        from maverick_data.session import SessionLocal
        from maverick_crypto.models import Crypto
    except ImportError:
        logger.warning("Cannot verify - maverick_data not available")
        return {}
    
    session = SessionLocal()
    try:
        total = session.query(Crypto).count()
        active = session.query(Crypto).filter_by(is_active=True).count()
        
        # Get top 5 by market cap
        top_5 = (
            session.query(Crypto)
            .filter(Crypto.market_cap_rank.isnot(None))
            .order_by(Crypto.market_cap_rank)
            .limit(5)
            .all()
        )
        
        logger.info("Verification complete:")
        logger.info(f"  Total cryptocurrencies: {total}")
        logger.info(f"  Active: {active}")
        logger.info("  Top 5 by market cap:")
        for crypto in top_5:
            logger.info(
                f"    #{crypto.market_cap_rank}: {crypto.symbol} ({crypto.name}) "
                f"- ${crypto.current_price:,.2f}"
            )
        
        return {
            "total": total,
            "active": active,
        }
    finally:
        session.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Seed top cryptocurrencies into the database"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of cryptocurrencies to seed (default: 100)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force update existing records",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing data, don't seed",
    )
    
    args = parser.parse_args()
    
    if args.verify_only:
        asyncio.run(verify_seeded_data())
    else:
        asyncio.run(seed_top_cryptos(limit=args.limit, force=args.force))
        asyncio.run(verify_seeded_data())


if __name__ == "__main__":
    main()

