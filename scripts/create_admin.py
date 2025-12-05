#!/usr/bin/env python3
"""
Create an admin user.

This script creates an admin user with elevated privileges.
Admin users can:
- View all users (future admin panel)
- Manage demo data
- Access admin-only features

Usage:
    python scripts/create_admin.py --email admin@example.com --password secure123

Security:
    - This script should only be run from CLI, never exposed via API
    - Admin users should use strong passwords
    - Consider using environment variables for credentials in production
"""

import asyncio
import argparse
import os
import sys
import getpass

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "data", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "services", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "core", "src"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4


async def create_admin(email: str, password: str, name: str | None = None):
    """Create an admin user."""
    from maverick_data.models import User
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
        # Check if email already exists
        result = await session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            if existing_user.is_admin:
                print(f"Admin user already exists: {email}")
            else:
                # Promote to admin
                existing_user.is_admin = True
                await session.commit()
                print(f"Promoted existing user to admin: {email}")
            await engine.dispose()
            return
        
        # Hash password
        password_hash = password_hasher.hash(password)
        
        # Create admin user
        admin_user = User(
            id=uuid4(),
            email=email.lower().strip(),
            password_hash=password_hash,
            name=name or "Admin",
            tier="enterprise",  # Admin gets enterprise tier
            email_verified=True,
            is_active=True,
            is_admin=True,
            onboarding_completed=True,
        )
        
        session.add(admin_user)
        await session.commit()
        
        print(f"\n✅ Admin user created successfully!")
        print(f"   Email: {email}")
        print(f"   Name: {name or 'Admin'}")
        print(f"   Tier: enterprise")
        print(f"\n⚠️  Keep these credentials secure!")
    
    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(
        description="Create an admin user for Maverick MCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Interactive mode (prompts for password)
    python scripts/create_admin.py --email admin@example.com
    
    # With password (not recommended for production)
    python scripts/create_admin.py --email admin@example.com --password secure123
    
    # With name
    python scripts/create_admin.py --email admin@example.com --name "System Admin"
"""
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Admin email address"
    )
    parser.add_argument(
        "--password",
        help="Admin password (will prompt if not provided)"
    )
    parser.add_argument(
        "--name",
        help="Admin display name (default: Admin)"
    )
    
    args = parser.parse_args()
    
    # Validate email
    if "@" not in args.email:
        print("ERROR: Invalid email address")
        sys.exit(1)
    
    # Get password securely if not provided
    password = args.password
    if not password:
        password = getpass.getpass("Enter admin password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("ERROR: Passwords do not match")
            sys.exit(1)
    
    # Validate password
    if len(password) < 8:
        print("ERROR: Password must be at least 8 characters")
        sys.exit(1)
    
    # Create admin
    asyncio.run(create_admin(args.email, password, args.name))


if __name__ == "__main__":
    main()

