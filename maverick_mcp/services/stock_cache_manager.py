"""
Stock Cache Manager Service

Handles caching of stock price data using database persistence.
"""

import logging
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from maverick_mcp.data.models import PriceCache, Stock, SessionLocal, bulk_insert_price_data

logger = logging.getLogger(__name__)


class StockCacheManager:
    """
    Service for managing stock data cache.
    
    Implements ICacheManager interface to provide caching operations
    with database persistence.
    
    Features:
    - Database-backed caching
    - Smart cache retrieval (flexible date ranges)
    - Bulk insert for performance
    - Session management
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize cache manager.
        
        Args:
            db_session: Optional database session for dependency injection
                       If not provided, will create sessions as needed
        """
        self._db_session = db_session
        logger.info("StockCacheManager initialized")
    
    def _get_db_session(self) -> tuple[Session, bool]:
        """
        Get a database session.
        
        Returns:
            Tuple of (session, should_close) where should_close indicates
            whether the caller should close the session.
        """
        # Use injected session if available - should NOT be closed
        if self._db_session:
            return self._db_session, False
        
        # Otherwise, create a new session using session factory - should be closed
        try:
            session = SessionLocal()
            return session, True
        except Exception as e:
            logger.error(f"Failed to get database session: {e}", exc_info=True)
            raise
    
    def get_cached_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve cached stock data with flexible date range.
        
        Returns whatever cached data exists within the requested range,
        even if incomplete.
        
        Args:
            symbol: Stock ticker symbol (will be uppercased)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with available cached data or None if not found
        """
        symbol = symbol.upper()
        session, should_close = self._get_db_session()
        
        try:
            # Get whatever data exists in the range
            df = PriceCache.get_price_data(session, symbol, start_date, end_date)
            
            if df.empty:
                logger.debug(f"No cached data found for {symbol} ({start_date} to {end_date})")
                return None
            
            # Add expected columns for compatibility
            for col in ["Dividends", "Stock Splits"]:
                if col not in df.columns:
                    df[col] = 0.0
            
            # Ensure column names match yfinance format
            column_mapping = {
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            }
            df.rename(columns=column_mapping, inplace=True)
            
            # Ensure proper data types to match yfinance
            # Convert Decimal to float for price columns
            for col in ["Open", "High", "Low", "Close"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
            
            # Convert volume to int
            if "Volume" in df.columns:
                df["Volume"] = (
                    pd.to_numeric(df["Volume"], errors="coerce")
                    .fillna(0)
                    .astype("int64")
                )
            
            # Ensure index is timezone-naive for consistency
            df.index = pd.to_datetime(df.index).tz_localize(None)
            
            logger.debug(f"Retrieved {len(df)} cached records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting cached data for {symbol}: {e}")
            return None
        finally:
            if should_close:
                session.close()
    
    def cache_data(self, symbol: str, data: pd.DataFrame) -> None:
        """
        Store stock data in cache.
        
        Args:
            symbol: Stock ticker symbol
            data: DataFrame with stock data
        """
        if data.empty:
            logger.debug(f"Skipping cache of empty dataframe for {symbol}")
            return
        
        symbol = symbol.upper()
        session, should_close = self._get_db_session()
        
        try:
            # Ensure symbol is uppercase to match database
            symbol = symbol.upper()
            
            # Prepare DataFrame for caching
            cache_df = data.copy()
            
            # Ensure proper column names
            column_mapping = {
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
            cache_df.rename(columns=column_mapping, inplace=True)
            
            # Log DataFrame info for debugging
            logger.debug(f"Caching {len(cache_df)} records for {symbol}")
            
            # Ensure stock exists in database
            self._ensure_stock_exists(session, symbol)
            
            # Insert data
            count = bulk_insert_price_data(session, symbol, cache_df)
            if count == 0:
                logger.debug(
                    f"No new records cached for {symbol} (data may already exist)"
                )
            else:
                logger.info(f"Cached {count} new price records for {symbol}")
                
        except Exception as e:
            logger.error(f"Error caching data for {symbol}: {e}", exc_info=True)
            session.rollback()
        finally:
            if should_close:
                session.close()
    
    def invalidate_cache(self, symbol: Optional[str] = None) -> None:
        """
        Invalidate cache for a symbol or all symbols.
        
        Args:
            symbol: Stock ticker symbol, or None to invalidate all
        """
        session, should_close = self._get_db_session()
        
        try:
            if symbol:
                symbol = symbol.upper()
                # Delete cache entries for this symbol
                deleted = session.query(PriceCache).filter(
                    PriceCache.ticker_symbol == symbol
                ).delete()
                session.commit()
                logger.info(f"Invalidated cache for {symbol} ({deleted} records deleted)")
            else:
                # Delete all cache entries
                deleted = session.query(PriceCache).delete()
                session.commit()
                logger.info(f"Invalidated all cache ({deleted} records deleted)")
                
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}", exc_info=True)
            session.rollback()
        finally:
            if should_close:
                session.close()
    
    def _ensure_stock_exists(self, session: Session, symbol: str) -> Stock:
        """
        Ensure a stock exists in the database.
        
        Args:
            session: Database session
            symbol: Stock ticker symbol
            
        Returns:
            Stock object
        """
        return Stock.get_or_create(session, symbol)


__all__ = ["StockCacheManager"]

