"""
Exchange rate model for storing historical currency exchange rates.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pandas as pd
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Session

from maverick_data.models.base import Base, TimestampMixin


class ExchangeRate(Base, TimestampMixin):
    """
    Model for storing historical exchange rates.

    Stores exchange rates fetched from various providers (Exchange Rate API, Yahoo Finance, etc.)
    for historical tracking and analysis.
    """

    __tablename__ = "mcp_exchange_rates"
    __table_args__ = (
        UniqueConstraint(
            "from_currency", "to_currency", "rate_date", name="mcp_exchange_rate_unique"
        ),
        Index(
            "mcp_exchange_rate_currencies_date_idx",
            "from_currency",
            "to_currency",
            "rate_date",
        ),
        Index("mcp_exchange_rate_date_idx", "rate_date"),
        Index("mcp_exchange_rate_source_idx", "source"),
    )

    rate_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    from_currency = Column(String(3), nullable=False, index=True)
    to_currency = Column(String(3), nullable=False, index=True)
    rate = Column(Numeric(15, 6), nullable=False)
    rate_date = Column(Date, nullable=False, index=True)

    source = Column(String(50))
    provider_timestamp = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<ExchangeRate({self.from_currency}/{self.to_currency}={self.rate} on {self.rate_date}, source={self.source})>"

    @classmethod
    def store_rate(
        cls,
        session: Session,
        from_currency: str,
        to_currency: str,
        rate: float,
        rate_date: date | None = None,
        source: str | None = None,
        provider_timestamp: datetime | None = None,
    ) -> ExchangeRate:
        """Store or update an exchange rate in the database."""
        if rate_date is None:
            rate_date = datetime.now(UTC).date()

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        existing = (
            session.query(cls)
            .filter_by(
                from_currency=from_currency,
                to_currency=to_currency,
                rate_date=rate_date,
            )
            .first()
        )

        if existing:
            existing.rate = rate
            existing.source = source
            existing.provider_timestamp = provider_timestamp
            existing.updated_at = datetime.now(UTC)
            session.commit()
            return existing
        else:
            new_rate = cls(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=rate,
                rate_date=rate_date,
                source=source,
                provider_timestamp=provider_timestamp,
            )
            session.add(new_rate)
            session.commit()
            return new_rate

    @classmethod
    def get_latest_rate(
        cls, session: Session, from_currency: str, to_currency: str
    ) -> ExchangeRate | None:
        """Get the most recent exchange rate for a currency pair."""
        return (
            session.query(cls)
            .filter_by(
                from_currency=from_currency.upper(), to_currency=to_currency.upper()
            )
            .order_by(cls.rate_date.desc())
            .first()
        )

    @classmethod
    def get_rate_on_date(
        cls, session: Session, from_currency: str, to_currency: str, target_date: date
    ) -> ExchangeRate | None:
        """Get exchange rate for a specific date."""
        return (
            session.query(cls)
            .filter_by(
                from_currency=from_currency.upper(),
                to_currency=to_currency.upper(),
                rate_date=target_date,
            )
            .first()
        )

    @classmethod
    def get_historical_rates(
        cls,
        session: Session,
        from_currency: str,
        to_currency: str,
        start_date: date,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """Get historical exchange rates as a pandas DataFrame."""
        if end_date is None:
            end_date = datetime.now(UTC).date()

        query = (
            session.query(cls.rate_date, cls.rate, cls.source)
            .filter(
                cls.from_currency == from_currency.upper(),
                cls.to_currency == to_currency.upper(),
                cls.rate_date >= start_date,
                cls.rate_date <= end_date,
            )
            .order_by(cls.rate_date)
        )

        df = pd.DataFrame(query.all(), columns=["date", "rate", "source"])

        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df["rate"] = df["rate"].astype(float)
            df.set_index("date", inplace=True)

        return df
