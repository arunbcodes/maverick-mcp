"""
Bulk Data Operations.

Provides efficient bulk insert operations for price data and screening results.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import pandas as pd
from sqlalchemy.orm import Session

from maverick_data.models import (
    MaverickBearStocks,
    MaverickStocks,
    PriceCache,
    Stock,
    SupplyDemandBreakoutStocks,
)
from maverick_data.session import SessionLocal

if TYPE_CHECKING:
    pass

logger = logging.getLogger("maverick_data.bulk_operations")


def bulk_insert_price_data(
    session: Session, ticker_symbol: str, df: pd.DataFrame
) -> int:
    """
    Bulk insert price data from a DataFrame.

    Args:
        session: Database session
        ticker_symbol: Stock ticker symbol
        df: DataFrame with OHLCV data (must have date index)

    Returns:
        Number of records inserted (or would be inserted)
    """
    if df.empty:
        return 0

    # Get or create stock
    stock = Stock.get_or_create(session, ticker_symbol)

    # First, check how many records already exist
    existing_dates = set()
    if hasattr(df.index[0], "date"):
        dates_to_check = [d.date() for d in df.index]
    else:
        dates_to_check = list(df.index)

    existing_query = session.query(PriceCache.date).filter(
        PriceCache.stock_id == stock.stock_id, PriceCache.date.in_(dates_to_check)
    )
    existing_dates = {row[0] for row in existing_query.all()}

    # Prepare data for bulk insert
    records = []
    new_count = 0
    for date_idx, row in df.iterrows():
        # Handle different index types - datetime index vs date index
        if hasattr(date_idx, "date") and callable(date_idx.date):
            date_val = date_idx.date()
        elif hasattr(date_idx, "to_pydatetime") and callable(date_idx.to_pydatetime):
            date_val = date_idx.to_pydatetime().date()
        else:
            # Assume it's already a date-like object
            date_val = date_idx

        # Skip if already exists
        if date_val in existing_dates:
            continue

        new_count += 1

        # Handle both lowercase and capitalized column names from yfinance
        open_val = row.get("open", row.get("Open", 0))
        high_val = row.get("high", row.get("High", 0))
        low_val = row.get("low", row.get("Low", 0))
        close_val = row.get("close", row.get("Close", 0))
        volume_val = row.get("volume", row.get("Volume", 0))

        # Handle None values
        if volume_val is None:
            volume_val = 0

        records.append(
            {
                "stock_id": stock.stock_id,
                "date": date_val,
                "open_price": Decimal(str(open_val)),
                "high_price": Decimal(str(high_val)),
                "low_price": Decimal(str(low_val)),
                "close_price": Decimal(str(close_val)),
                "volume": int(volume_val),
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )

    # Only insert if there are new records
    if records:
        # Detect database type from session
        database_url = str(session.get_bind().url)

        if "postgresql" in database_url:
            from sqlalchemy.dialects.postgresql import insert

            stmt = insert(PriceCache).values(records)
            stmt = stmt.on_conflict_do_nothing(index_elements=["stock_id", "date"])
        else:
            # For SQLite, use INSERT OR IGNORE
            from sqlalchemy import insert

            stmt = insert(PriceCache).values(records)
            stmt = stmt.prefix_with("OR IGNORE")

        result = session.execute(stmt)
        session.commit()

        # Log if rowcount differs from expected
        if result.rowcount != new_count:
            logger.warning(
                f"Expected to insert {new_count} records but rowcount was {result.rowcount}"
            )

        return result.rowcount
    else:
        logger.debug(
            f"All {len(df)} records already exist in cache for {ticker_symbol}"
        )
        return 0


def bulk_insert_screening_data(
    session: Session,
    model_class: type,
    screening_data: list[dict[str, Any]],
    date_analyzed: date | None = None,
) -> int:
    """
    Bulk insert screening data for any screening model.

    Args:
        session: Database session
        model_class: The screening model class (MaverickStocks, etc.)
        screening_data: List of screening result dictionaries
        date_analyzed: Date of analysis (default: today)

    Returns:
        Number of records inserted
    """
    if not screening_data:
        return 0

    if date_analyzed is None:
        date_analyzed = datetime.now(UTC).date()

    # Remove existing data for this date
    session.query(model_class).filter(
        model_class.date_analyzed == date_analyzed
    ).delete()

    inserted_count = 0
    for data in screening_data:
        # Get or create stock
        ticker = data.get("ticker") or data.get("symbol")
        if not ticker:
            continue

        stock = Stock.get_or_create(session, ticker)

        # Create screening record
        record_data: dict[str, Any] = {
            "stock_id": stock.stock_id,
            "date_analyzed": date_analyzed,
        }

        # Map common fields
        field_mapping = {
            "open": "open_price",
            "high": "high_price",
            "low": "low_price",
            "close": "close_price",
            "pat": "pattern_type",
            "sqz": "squeeze_status",
            "vcp": "consolidation_status",
            "entry": "entry_signal",
        }

        for key, value in data.items():
            if key in ["ticker", "symbol"]:
                continue
            mapped_key = field_mapping.get(key, key)
            if hasattr(model_class, mapped_key):
                record_data[mapped_key] = value

        record = model_class(**record_data)
        session.add(record)
        inserted_count += 1

    session.commit()
    return inserted_count


def get_latest_maverick_screening(days_back: int = 1) -> dict[str, list[dict]]:
    """Get latest screening results from all maverick tables.

    Args:
        days_back: Number of days to look back for results

    Returns:
        Dictionary with screening results by category
    """
    with SessionLocal() as session:
        results = {
            "maverick_stocks": [
                stock.to_dict()
                for stock in MaverickStocks.get_latest_analysis(
                    session, days_back=days_back
                )
            ],
            "maverick_bear_stocks": [
                stock.to_dict()
                for stock in MaverickBearStocks.get_latest_analysis(
                    session, days_back=days_back
                )
            ],
            "supply_demand_breakouts": [
                stock.to_dict()
                for stock in SupplyDemandBreakoutStocks.get_latest_analysis(
                    session, days_back=days_back
                )
            ],
        }

    return results

