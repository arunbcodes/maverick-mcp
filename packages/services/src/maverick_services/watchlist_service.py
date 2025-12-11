"""
Watchlist Service.

Manages user watchlists with real-time price tracking and alert integration.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from collections.abc import AsyncIterator, Callable
from uuid import uuid4

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


# ============================================
# Data Classes
# ============================================


@dataclass
class WatchlistItem:
    """A stock in a watchlist."""
    
    ticker: str
    added_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    notes: str | None = None
    alert_enabled: bool = False
    target_price: float | None = None
    stop_price: float | None = None
    position: int = 0  # For ordering
    
    # Populated at runtime
    current_price: float | None = None
    price_change: float | None = None
    price_change_pct: float | None = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "added_at": self.added_at.isoformat(),
            "notes": self.notes,
            "alert_enabled": self.alert_enabled,
            "target_price": self.target_price,
            "stop_price": self.stop_price,
            "position": self.position,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "WatchlistItem":
        """Create from dictionary."""
        return cls(
            ticker=data["ticker"],
            added_at=datetime.fromisoformat(data["added_at"]) if data.get("added_at") else datetime.now(UTC),
            notes=data.get("notes"),
            alert_enabled=data.get("alert_enabled", False),
            target_price=data.get("target_price"),
            stop_price=data.get("stop_price"),
            position=data.get("position", 0),
        )


@dataclass
class Watchlist:
    """A user's watchlist."""
    
    watchlist_id: str
    user_id: str
    name: str
    description: str | None = None
    is_default: bool = False
    items: list[WatchlistItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "watchlist_id": self.watchlist_id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "is_default": self.is_default,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Watchlist":
        """Create from dictionary."""
        return cls(
            watchlist_id=data["watchlist_id"],
            user_id=data["user_id"],
            name=data["name"],
            description=data.get("description"),
            is_default=data.get("is_default", False),
            items=[WatchlistItem.from_dict(item) for item in data.get("items", [])],
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(UTC),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ============================================
# Watchlist Service
# ============================================


class WatchlistService:
    """
    Service for managing user watchlists.
    
    Features:
    - Multiple named watchlists per user
    - Add/remove stocks with notes
    - Target price and stop loss tracking
    - Real-time price population
    - Drag & drop reordering
    - Alert integration
    """
    
    # Redis keys
    WATCHLISTS_KEY = "watchlists:{user_id}"
    WATCHLIST_KEY = "watchlist:{watchlist_id}"
    
    # Limits
    MAX_WATCHLISTS_PER_USER = 10
    MAX_ITEMS_PER_WATCHLIST = 50
    
    def __init__(
        self,
        redis_client: Redis | None = None,
    ):
        self.redis = redis_client
    
    # ================================
    # Watchlist CRUD
    # ================================
    
    async def create_watchlist(
        self,
        user_id: str,
        name: str,
        description: str | None = None,
        is_default: bool = False,
    ) -> Watchlist:
        """Create a new watchlist."""
        if not self.redis:
            raise RuntimeError("Redis not available")
        
        # Check limit
        existing = await self.get_watchlists(user_id)
        if len(existing) >= self.MAX_WATCHLISTS_PER_USER:
            raise ValueError(f"Maximum {self.MAX_WATCHLISTS_PER_USER} watchlists allowed")
        
        # If setting as default, unset others
        if is_default:
            for wl in existing:
                if wl.is_default:
                    wl.is_default = False
                    await self._save_watchlist(wl)
        
        # Create if this is the first, make it default
        if len(existing) == 0:
            is_default = True
        
        watchlist = Watchlist(
            watchlist_id=str(uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            is_default=is_default,
        )
        
        # Save to Redis
        await self._save_watchlist(watchlist)
        
        # Add to user's watchlist index
        watchlists_key = self.WATCHLISTS_KEY.format(user_id=user_id)
        await self.redis.sadd(watchlists_key, watchlist.watchlist_id)
        
        logger.info(f"Created watchlist {watchlist.watchlist_id} for user {user_id}")
        return watchlist
    
    async def get_watchlists(self, user_id: str) -> list[Watchlist]:
        """Get all watchlists for a user."""
        if not self.redis:
            return []
        
        watchlists_key = self.WATCHLISTS_KEY.format(user_id=user_id)
        watchlist_ids = await self.redis.smembers(watchlists_key)
        
        watchlists = []
        for wl_id in watchlist_ids:
            watchlist = await self.get_watchlist(user_id, wl_id)
            if watchlist:
                watchlists.append(watchlist)
        
        # Sort by name, default first
        watchlists.sort(key=lambda w: (not w.is_default, w.name.lower()))
        return watchlists
    
    async def get_watchlist(self, user_id: str, watchlist_id: str) -> Watchlist | None:
        """Get a specific watchlist."""
        if not self.redis:
            return None
        
        watchlist_key = self.WATCHLIST_KEY.format(watchlist_id=watchlist_id)
        data = await self.redis.get(watchlist_key)
        
        if not data:
            return None
        
        watchlist = Watchlist.from_dict(json.loads(data))
        
        # Verify ownership
        if watchlist.user_id != user_id:
            return None
        
        return watchlist
    
    async def get_default_watchlist(self, user_id: str) -> Watchlist | None:
        """Get user's default watchlist."""
        watchlists = await self.get_watchlists(user_id)
        for wl in watchlists:
            if wl.is_default:
                return wl
        
        # Return first if no default
        return watchlists[0] if watchlists else None
    
    async def update_watchlist(
        self,
        user_id: str,
        watchlist_id: str,
        name: str | None = None,
        description: str | None = None,
        is_default: bool | None = None,
    ) -> Watchlist | None:
        """Update watchlist details."""
        watchlist = await self.get_watchlist(user_id, watchlist_id)
        if not watchlist:
            return None
        
        if name is not None:
            watchlist.name = name
        if description is not None:
            watchlist.description = description
        if is_default is not None:
            if is_default:
                # Unset other defaults
                all_watchlists = await self.get_watchlists(user_id)
                for wl in all_watchlists:
                    if wl.is_default and wl.watchlist_id != watchlist_id:
                        wl.is_default = False
                        await self._save_watchlist(wl)
            watchlist.is_default = is_default
        
        watchlist.updated_at = datetime.now(UTC)
        await self._save_watchlist(watchlist)
        return watchlist
    
    async def delete_watchlist(self, user_id: str, watchlist_id: str) -> bool:
        """Delete a watchlist."""
        if not self.redis:
            return False
        
        watchlist = await self.get_watchlist(user_id, watchlist_id)
        if not watchlist:
            return False
        
        # Don't allow deleting default if it's the only one
        all_watchlists = await self.get_watchlists(user_id)
        if len(all_watchlists) == 1:
            raise ValueError("Cannot delete the only watchlist")
        
        # Delete from Redis
        watchlist_key = self.WATCHLIST_KEY.format(watchlist_id=watchlist_id)
        await self.redis.delete(watchlist_key)
        
        # Remove from user's index
        watchlists_key = self.WATCHLISTS_KEY.format(user_id=user_id)
        await self.redis.srem(watchlists_key, watchlist_id)
        
        # If was default, set another as default
        if watchlist.is_default:
            remaining = await self.get_watchlists(user_id)
            if remaining:
                remaining[0].is_default = True
                await self._save_watchlist(remaining[0])
        
        logger.info(f"Deleted watchlist {watchlist_id}")
        return True
    
    # ================================
    # Item Management
    # ================================
    
    async def add_item(
        self,
        user_id: str,
        watchlist_id: str,
        ticker: str,
        notes: str | None = None,
        target_price: float | None = None,
        stop_price: float | None = None,
    ) -> WatchlistItem:
        """Add a stock to a watchlist."""
        watchlist = await self.get_watchlist(user_id, watchlist_id)
        if not watchlist:
            raise ValueError("Watchlist not found")
        
        # Check limit
        if len(watchlist.items) >= self.MAX_ITEMS_PER_WATCHLIST:
            raise ValueError(f"Maximum {self.MAX_ITEMS_PER_WATCHLIST} items per watchlist")
        
        # Check if already exists
        ticker = ticker.upper()
        existing = next((item for item in watchlist.items if item.ticker == ticker), None)
        if existing:
            raise ValueError(f"{ticker} is already in this watchlist")
        
        # Add item
        item = WatchlistItem(
            ticker=ticker,
            notes=notes,
            target_price=target_price,
            stop_price=stop_price,
            position=len(watchlist.items),
        )
        
        watchlist.items.append(item)
        watchlist.updated_at = datetime.now(UTC)
        await self._save_watchlist(watchlist)
        
        logger.info(f"Added {ticker} to watchlist {watchlist_id}")
        return item
    
    async def add_items_batch(
        self,
        user_id: str,
        watchlist_id: str,
        tickers: list[str],
    ) -> list[WatchlistItem]:
        """Add multiple stocks to a watchlist."""
        watchlist = await self.get_watchlist(user_id, watchlist_id)
        if not watchlist:
            raise ValueError("Watchlist not found")
        
        existing_tickers = {item.ticker for item in watchlist.items}
        added = []
        
        for ticker in tickers:
            ticker = ticker.upper()
            if ticker in existing_tickers:
                continue
            if len(watchlist.items) >= self.MAX_ITEMS_PER_WATCHLIST:
                break
            
            item = WatchlistItem(
                ticker=ticker,
                position=len(watchlist.items),
            )
            watchlist.items.append(item)
            existing_tickers.add(ticker)
            added.append(item)
        
        if added:
            watchlist.updated_at = datetime.now(UTC)
            await self._save_watchlist(watchlist)
        
        return added
    
    async def update_item(
        self,
        user_id: str,
        watchlist_id: str,
        ticker: str,
        notes: str | None = None,
        alert_enabled: bool | None = None,
        target_price: float | None = None,
        stop_price: float | None = None,
    ) -> WatchlistItem | None:
        """Update a watchlist item."""
        watchlist = await self.get_watchlist(user_id, watchlist_id)
        if not watchlist:
            return None
        
        ticker = ticker.upper()
        item = next((i for i in watchlist.items if i.ticker == ticker), None)
        if not item:
            return None
        
        if notes is not None:
            item.notes = notes
        if alert_enabled is not None:
            item.alert_enabled = alert_enabled
        if target_price is not None:
            item.target_price = target_price
        if stop_price is not None:
            item.stop_price = stop_price
        
        watchlist.updated_at = datetime.now(UTC)
        await self._save_watchlist(watchlist)
        return item
    
    async def remove_item(
        self,
        user_id: str,
        watchlist_id: str,
        ticker: str,
    ) -> bool:
        """Remove a stock from a watchlist."""
        watchlist = await self.get_watchlist(user_id, watchlist_id)
        if not watchlist:
            return False
        
        ticker = ticker.upper()
        original_len = len(watchlist.items)
        watchlist.items = [item for item in watchlist.items if item.ticker != ticker]
        
        if len(watchlist.items) == original_len:
            return False
        
        # Re-index positions
        for i, item in enumerate(watchlist.items):
            item.position = i
        
        watchlist.updated_at = datetime.now(UTC)
        await self._save_watchlist(watchlist)
        
        logger.info(f"Removed {ticker} from watchlist {watchlist_id}")
        return True
    
    async def reorder_items(
        self,
        user_id: str,
        watchlist_id: str,
        tickers: list[str],
    ) -> bool:
        """Reorder items in a watchlist by providing tickers in desired order."""
        watchlist = await self.get_watchlist(user_id, watchlist_id)
        if not watchlist:
            return False
        
        # Create ticker -> item mapping
        item_map = {item.ticker: item for item in watchlist.items}
        
        # Reorder based on provided ticker list
        reordered = []
        for i, ticker in enumerate(tickers):
            ticker = ticker.upper()
            if ticker in item_map:
                item = item_map.pop(ticker)
                item.position = i
                reordered.append(item)
        
        # Add any remaining items at the end
        for ticker, item in item_map.items():
            item.position = len(reordered)
            reordered.append(item)
        
        watchlist.items = reordered
        watchlist.updated_at = datetime.now(UTC)
        await self._save_watchlist(watchlist)
        
        return True
    
    # ================================
    # Quick Add (from screener)
    # ================================
    
    async def quick_add(
        self,
        user_id: str,
        ticker: str,
        watchlist_id: str | None = None,
    ) -> tuple[WatchlistItem, Watchlist]:
        """
        Quickly add a stock to a watchlist.
        
        If no watchlist_id provided, adds to default watchlist.
        """
        # Get or create default watchlist
        if watchlist_id:
            watchlist = await self.get_watchlist(user_id, watchlist_id)
            if not watchlist:
                raise ValueError("Watchlist not found")
        else:
            watchlist = await self.get_default_watchlist(user_id)
            if not watchlist:
                # Create default watchlist
                watchlist = await self.create_watchlist(
                    user_id=user_id,
                    name="My Watchlist",
                    is_default=True,
                )
        
        # Add item
        item = await self.add_item(user_id, watchlist.watchlist_id, ticker)
        return item, watchlist
    
    # ================================
    # Check if watching
    # ================================
    
    async def is_watching(self, user_id: str, ticker: str) -> dict | None:
        """
        Check if a ticker is in any watchlist.
        
        Returns watchlist info if found, None otherwise.
        """
        ticker = ticker.upper()
        watchlists = await self.get_watchlists(user_id)
        
        for watchlist in watchlists:
            for item in watchlist.items:
                if item.ticker == ticker:
                    return {
                        "watchlist_id": watchlist.watchlist_id,
                        "watchlist_name": watchlist.name,
                        "notes": item.notes,
                        "target_price": item.target_price,
                        "stop_price": item.stop_price,
                    }
        
        return None
    
    # ================================
    # Price Population
    # ================================
    
    async def populate_prices(
        self,
        watchlist: Watchlist,
        price_fetcher: Callable | None = None,
    ) -> Watchlist:
        """
        Populate current prices for watchlist items.
        
        price_fetcher should be an async function that takes a list of tickers
        and returns a dict of ticker -> price data.
        """
        if not watchlist.items or not price_fetcher:
            return watchlist
        
        tickers = [item.ticker for item in watchlist.items]
        
        try:
            prices = await price_fetcher(tickers)
            
            for item in watchlist.items:
                if item.ticker in prices:
                    price_data = prices[item.ticker]
                    item.current_price = price_data.get("price")
                    item.price_change = price_data.get("change")
                    item.price_change_pct = price_data.get("change_pct")
        except Exception as e:
            logger.warning(f"Failed to fetch prices for watchlist: {e}")
        
        return watchlist
    
    # ================================
    # Helpers
    # ================================
    
    async def _save_watchlist(self, watchlist: Watchlist) -> None:
        """Save watchlist to Redis."""
        if not self.redis:
            raise RuntimeError("Redis not available")
        
        watchlist_key = self.WATCHLIST_KEY.format(watchlist_id=watchlist.watchlist_id)
        await self.redis.set(watchlist_key, json.dumps(watchlist.to_dict()))


# ============================================
# Factory Function
# ============================================


def get_watchlist_service(
    redis_client: Redis | None = None,
) -> WatchlistService:
    """Get WatchlistService instance."""
    return WatchlistService(redis_client=redis_client)

