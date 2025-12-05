#!/usr/bin/env python3
"""
Seed demo user and portfolio data.

This script creates:
- A demo user account with pre-set credentials
- A sample portfolio with diverse positions
- Historical transactions for performance charts

Usage:
    python scripts/seed_demo_data.py

Environment:
    Requires DATABASE_URL or MAVERICK_DATABASE_URL to be set.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, UTC
from uuid import uuid4

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "data", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "services", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "core", "src"))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Demo user credentials
DEMO_USER_EMAIL = "demo@maverick.example"
DEMO_USER_PASSWORD = "demo123456"  # Will be hashed
DEMO_USER_NAME = "Demo Investor"

# Sample portfolio positions
DEMO_POSITIONS = [
    # Tech giants
    {"ticker": "AAPL", "shares": 25, "purchase_price": 175.50, "days_ago": 180, "notes": "Long-term hold - Apple ecosystem"},
    {"ticker": "MSFT", "shares": 15, "purchase_price": 380.25, "days_ago": 120, "notes": "Cloud growth play"},
    {"ticker": "GOOGL", "shares": 10, "purchase_price": 140.00, "days_ago": 90, "notes": "AI and search dominance"},
    # Financial
    {"ticker": "JPM", "shares": 20, "purchase_price": 165.00, "days_ago": 150, "notes": "Banking sector leader"},
    {"ticker": "BAC", "shares": 50, "purchase_price": 32.50, "days_ago": 200, "notes": "Value play in financials"},
    # Healthcare
    {"ticker": "JNJ", "shares": 15, "purchase_price": 155.00, "days_ago": 100, "notes": "Dividend aristocrat"},
    {"ticker": "PFE", "shares": 40, "purchase_price": 28.00, "days_ago": 60, "notes": "Pharma diversification"},
    # Energy
    {"ticker": "XOM", "shares": 30, "purchase_price": 105.00, "days_ago": 45, "notes": "Energy sector exposure"},
    # Consumer
    {"ticker": "AMZN", "shares": 8, "purchase_price": 178.00, "days_ago": 75, "notes": "E-commerce and AWS"},
    {"ticker": "NVDA", "shares": 12, "purchase_price": 480.00, "days_ago": 30, "notes": "AI chip leader"},
]


async def seed_demo_data():
    """Main seeding function."""
    from maverick_data.models import User, UserPortfolio, PortfolioPosition
    from maverick_services.auth.password import password_hasher
    
    # Get database URL
    database_url = os.environ.get("MAVERICK_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL or MAVERICK_DATABASE_URL not set")
        sys.exit(1)
    
    # Convert to async URL if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    print(f"Connecting to database...")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if demo user already exists
        result = await session.execute(
            select(User).where(User.email == DEMO_USER_EMAIL)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"Demo user already exists: {DEMO_USER_EMAIL}")
            demo_user = existing_user
            
            # Update to ensure it's marked as demo
            demo_user.is_demo_user = True
            demo_user.name = DEMO_USER_NAME
            await session.commit()
        else:
            # Create demo user
            print(f"Creating demo user: {DEMO_USER_EMAIL}")
            password_hash = password_hasher.hash(DEMO_USER_PASSWORD)
            
            demo_user = User(
                id=uuid4(),
                email=DEMO_USER_EMAIL,
                password_hash=password_hash,
                name=DEMO_USER_NAME,
                tier="pro",  # Give demo user pro features
                email_verified=True,
                is_active=True,
                is_demo_user=True,
                onboarding_completed=True,
            )
            session.add(demo_user)
            await session.commit()
            print(f"Created demo user with ID: {demo_user.id}")
        
        # Check if demo portfolio exists
        result = await session.execute(
            select(UserPortfolio).where(UserPortfolio.owner_id == demo_user.id)
        )
        existing_portfolio = result.scalar_one_or_none()
        
        if existing_portfolio:
            print(f"Demo portfolio already exists: {existing_portfolio.name}")
            portfolio = existing_portfolio
            
            # Clear existing positions for fresh seed
            await session.execute(
                text(f"DELETE FROM mcp_portfolio_positions WHERE portfolio_id = '{portfolio.id}'")
            )
            await session.commit()
            print("Cleared existing positions for re-seeding")
        else:
            # Create demo portfolio
            print("Creating demo portfolio...")
            portfolio = UserPortfolio(
                id=uuid4(),
                owner_id=demo_user.id,
                user_id="demo",
                name="Demo Portfolio",
            )
            session.add(portfolio)
            await session.commit()
            print(f"Created demo portfolio with ID: {portfolio.id}")
        
        # Add sample positions
        print("Adding sample positions...")
        for pos_data in DEMO_POSITIONS:
            purchase_date = datetime.now(UTC) - timedelta(days=pos_data["days_ago"])
            
            position = PortfolioPosition(
                id=uuid4(),
                portfolio_id=portfolio.id,
                ticker=pos_data["ticker"],
                shares=pos_data["shares"],
                purchase_price=pos_data["purchase_price"],
                purchase_date=purchase_date,
                notes=pos_data["notes"],
            )
            session.add(position)
            print(f"  Added {pos_data['shares']} shares of {pos_data['ticker']} @ ${pos_data['purchase_price']}")
        
        await session.commit()
        print(f"\n✅ Demo data seeded successfully!")
        print(f"\nDemo credentials:")
        print(f"  Email: {DEMO_USER_EMAIL}")
        print(f"  Password: {DEMO_USER_PASSWORD}")
        print(f"\nPortfolio contains {len(DEMO_POSITIONS)} positions")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_demo_data())

