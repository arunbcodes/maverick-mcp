"""
Memory stores for agent conversations and user data.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class MemoryStore:
    """Base class for memory storage with TTL support."""

    def __init__(self, ttl_hours: float = 24.0):
        """Initialize memory store.

        Args:
            ttl_hours: Default time-to-live in hours for stored values
        """
        self.ttl_hours = ttl_hours
        self.store: dict[str, dict[str, Any]] = {}

    def set(self, key: str, value: Any, ttl_hours: float | None = None) -> None:
        """Store a value with optional custom TTL.

        Args:
            key: Storage key
            value: Value to store
            ttl_hours: Custom TTL in hours (uses default if not specified)
        """
        ttl = ttl_hours or self.ttl_hours
        expiry = datetime.now() + timedelta(hours=ttl)

        self.store[key] = {
            "value": value,
            "expiry": expiry.isoformat(),
            "created": datetime.now().isoformat(),
        }

    def get(self, key: str) -> Any | None:
        """Get a value if not expired.

        Args:
            key: Storage key

        Returns:
            Stored value or None if not found or expired
        """
        if key not in self.store:
            return None

        entry = self.store[key]
        expiry = datetime.fromisoformat(entry["expiry"])

        if datetime.now() > expiry:
            del self.store[key]
            return None

        return entry["value"]

    def delete(self, key: str) -> None:
        """Delete a value.

        Args:
            key: Storage key to delete
        """
        if key in self.store:
            del self.store[key]

    def clear_expired(self) -> int:
        """Clear all expired entries.

        Returns:
            Number of entries cleared
        """
        now = datetime.now()
        expired_keys = []

        for key, entry in self.store.items():
            if now > datetime.fromisoformat(entry["expiry"]):
                expired_keys.append(key)

        for key in expired_keys:
            del self.store[key]

        return len(expired_keys)

    def clear_all(self) -> int:
        """Clear all entries.

        Returns:
            Number of entries cleared
        """
        count = len(self.store)
        self.store.clear()
        return count

    def keys(self) -> list[str]:
        """Get all non-expired keys.

        Returns:
            List of valid keys
        """
        now = datetime.now()
        valid_keys = []

        for key, entry in self.store.items():
            if now <= datetime.fromisoformat(entry["expiry"]):
                valid_keys.append(key)

        return valid_keys


class ConversationStore(MemoryStore):
    """Store for conversation-specific data."""

    def save_analysis(
        self, session_id: str, symbol: str, analysis_type: str, data: dict[str, Any]
    ) -> None:
        """Save analysis results for a conversation.

        Args:
            session_id: Conversation session ID
            symbol: Stock symbol
            analysis_type: Type of analysis (e.g., 'technical', 'fundamental')
            data: Analysis data to store
        """
        key = f"{session_id}:analysis:{symbol}:{analysis_type}"

        analysis_record = {
            "symbol": symbol,
            "type": analysis_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        self.set(key, analysis_record)

    def get_analysis(
        self, session_id: str, symbol: str, analysis_type: str
    ) -> dict[str, Any] | None:
        """Get cached analysis for a symbol.

        Args:
            session_id: Conversation session ID
            symbol: Stock symbol
            analysis_type: Type of analysis

        Returns:
            Cached analysis data or None
        """
        key = f"{session_id}:analysis:{symbol}:{analysis_type}"
        return self.get(key)

    def save_context(self, session_id: str, context_type: str, data: Any) -> None:
        """Save conversation context.

        Args:
            session_id: Conversation session ID
            context_type: Type of context (e.g., 'current_stock', 'persona')
            data: Context data
        """
        key = f"{session_id}:context:{context_type}"
        self.set(key, data)

    def get_context(self, session_id: str, context_type: str) -> Any | None:
        """Get conversation context.

        Args:
            session_id: Conversation session ID
            context_type: Type of context

        Returns:
            Context data or None
        """
        key = f"{session_id}:context:{context_type}"
        return self.get(key)

    def list_analyses(self, session_id: str) -> list[dict[str, Any]]:
        """List all analyses for a session.

        Args:
            session_id: Conversation session ID

        Returns:
            List of analysis records
        """
        analyses = []
        prefix = f"{session_id}:analysis:"

        for key, entry in self.store.items():
            if key.startswith(prefix):
                # Check if not expired
                if datetime.now() <= datetime.fromisoformat(entry["expiry"]):
                    analyses.append(entry["value"])

        return analyses

    def clear_session(self, session_id: str) -> int:
        """Clear all data for a session.

        Args:
            session_id: Session to clear

        Returns:
            Number of entries cleared
        """
        prefix = f"{session_id}:"
        keys_to_delete = [k for k in self.store.keys() if k.startswith(prefix)]

        for key in keys_to_delete:
            del self.store[key]

        return len(keys_to_delete)


class UserMemoryStore(MemoryStore):
    """Store for user-specific long-term memory."""

    def __init__(self, ttl_hours: float = 168.0):  # 1 week default
        """Initialize user memory store.

        Args:
            ttl_hours: Default TTL in hours (default: 1 week)
        """
        super().__init__(ttl_hours)

    def save_preference(self, user_id: str, preference_type: str, value: Any) -> None:
        """Save user preference.

        Args:
            user_id: User identifier
            preference_type: Type of preference (e.g., 'risk_tolerance', 'sectors')
            value: Preference value
        """
        key = f"user:{user_id}:pref:{preference_type}"
        self.set(key, value, ttl_hours=self.ttl_hours * 4)  # Longer TTL for preferences

    def get_preference(self, user_id: str, preference_type: str) -> Any | None:
        """Get user preference.

        Args:
            user_id: User identifier
            preference_type: Type of preference

        Returns:
            Preference value or None
        """
        key = f"user:{user_id}:pref:{preference_type}"
        return self.get(key)

    def save_trade_history(self, user_id: str, trade: dict[str, Any]) -> None:
        """Save trade to history.

        Args:
            user_id: User identifier
            trade: Trade record to save
        """
        key = f"user:{user_id}:trades"

        trades = self.get(key) or []
        trades.append({**trade, "timestamp": datetime.now().isoformat()})

        # Keep last 100 trades
        trades = trades[-100:]
        self.set(key, trades)

    def get_trade_history(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get user's trade history.

        Args:
            user_id: User identifier
            limit: Maximum number of trades to return

        Returns:
            List of trade records
        """
        key = f"user:{user_id}:trades"
        trades = self.get(key) or []
        return trades[-limit:]

    def save_watchlist(self, user_id: str, symbols: list[str]) -> None:
        """Save user's watchlist.

        Args:
            user_id: User identifier
            symbols: List of stock symbols
        """
        key = f"user:{user_id}:watchlist"
        self.set(key, symbols)

    def get_watchlist(self, user_id: str) -> list[str]:
        """Get user's watchlist.

        Args:
            user_id: User identifier

        Returns:
            List of stock symbols
        """
        key = f"user:{user_id}:watchlist"
        return self.get(key) or []

    def add_to_watchlist(self, user_id: str, symbol: str) -> None:
        """Add symbol to watchlist.

        Args:
            user_id: User identifier
            symbol: Symbol to add
        """
        watchlist = self.get_watchlist(user_id)
        if symbol not in watchlist:
            watchlist.append(symbol)
            self.save_watchlist(user_id, watchlist)

    def remove_from_watchlist(self, user_id: str, symbol: str) -> None:
        """Remove symbol from watchlist.

        Args:
            user_id: User identifier
            symbol: Symbol to remove
        """
        watchlist = self.get_watchlist(user_id)
        if symbol in watchlist:
            watchlist.remove(symbol)
            self.save_watchlist(user_id, watchlist)

    def update_risk_profile(self, user_id: str, profile: dict[str, Any]) -> None:
        """Update user's risk profile.

        Args:
            user_id: User identifier
            profile: Risk profile data
        """
        key = f"user:{user_id}:risk_profile"
        self.set(key, profile, ttl_hours=self.ttl_hours * 4)

    def get_risk_profile(self, user_id: str) -> dict[str, Any] | None:
        """Get user's risk profile.

        Args:
            user_id: User identifier

        Returns:
            Risk profile data or None
        """
        key = f"user:{user_id}:risk_profile"
        return self.get(key)

    def clear_user_data(self, user_id: str) -> int:
        """Clear all data for a user.

        Args:
            user_id: User to clear

        Returns:
            Number of entries cleared
        """
        prefix = f"user:{user_id}:"
        keys_to_delete = [k for k in self.store.keys() if k.startswith(prefix)]

        for key in keys_to_delete:
            del self.store[key]

        return len(keys_to_delete)
