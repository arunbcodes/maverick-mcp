"""
Alembic environment configuration for Maverick-MCP.

This file configures Alembic to work with the Maverick-MCP database,
managing tables across all packages.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Add project root and package paths to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages" / "core" / "src"))
sys.path.insert(0, str(project_root / "packages" / "data" / "src"))

# Import models from new package structure
from maverick_data.models import Base

# Use data models metadata
target_metadata = Base.metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.getenv("POSTGRES_URL", "postgresql://localhost/local_production_snapshot"),
)

# Override sqlalchemy.url in alembic.ini
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# target_metadata is set above from maverick_data.models.Base

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_object(object, name, type_, reflected, compare_to):
    """
    Include tables managed by Maverick-MCP.

    Includes:
    - Auth tables: users, api_keys
    - MCP-prefixed tables: mcp_*
    - Stock tables: stocks_*
    - Screening tables: maverick_stocks, etc.
    """
    # Define all managed table prefixes and names
    MANAGED_PREFIXES = ("mcp_", "stocks_", "users", "api_keys")
    MANAGED_TABLES = {
        "users",
        "api_keys", 
        "maverick_stocks",
        "maverick_bear_stocks",
        "supply_demand_breakouts",
    }

    if type_ == "table":
        return (
            any(name.startswith(prefix) for prefix in MANAGED_PREFIXES)
            or name in MANAGED_TABLES
        )
    elif type_ in [
        "index",
        "unique_constraint",
        "foreign_key_constraint",
        "check_constraint",
    ]:
        # Include indexes and constraints for our tables
        if hasattr(object, "table") and object.table is not None:
            table_name = object.table.name
            return (
                any(table_name.startswith(prefix) for prefix in MANAGED_PREFIXES)
                or table_name in MANAGED_TABLES
            )
        # For reflected objects, check common prefixes
        managed_index_prefixes = [
            "idx_mcp_", "uq_mcp_", "fk_mcp_", "ck_mcp_",
            "idx_stocks_", "uq_stocks_", "fk_stocks_", "ck_stocks_",
            "idx_user_", "idx_api_key_", "uq_user_", "uq_api_key_",
            "ck_pricecache_", "ck_maverick_", "ck_supply_demand_",
        ]
        return any(name.startswith(prefix) for prefix in managed_index_prefixes)
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
