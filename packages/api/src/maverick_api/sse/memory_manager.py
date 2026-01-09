"""
In-memory SSE manager for single-instance deployments without Redis.

Provides the same interface as SSEManager but uses asyncio.Queue for
pub/sub instead of Redis. Useful for development or single-pod deployments.

Limitations:
- Single process only (no horizontal scaling)
- Messages lost on restart
- Higher memory usage with many subscribers
"""

import asyncio
import json
import logging
import time
from typing import AsyncIterator
from collections import defaultdict

logger = logging.getLogger(__name__)

# Heartbeat interval in seconds (keeps connection alive through proxies)
HEARTBEAT_INTERVAL = 15


class InMemorySSEManager:
    """
    In-memory pub/sub for SSE when Redis is unavailable.

    Architecture:
    - Each channel has a list of subscriber queues
    - Publishers push to all subscriber queues
    - Subscribers read from their own queue

    This is a drop-in replacement for SSEManager with the same interface.
    """

    PRICE_CHANNEL = "prices"
    PORTFOLIO_CHANNEL = "portfolio:{user_id}"
    ALERTS_CHANNEL = "alerts:{user_id}"

    def __init__(self):
        """Initialize in-memory SSE manager."""
        # Map of channel -> list of subscriber queues
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()
        logger.info("InMemorySSEManager initialized (no horizontal scaling)")

    # --- Publishers ---

    async def publish_price(self, ticker: str, data: dict) -> None:
        """
        Publish price update to all subscribers.

        Args:
            ticker: Stock ticker
            data: Price data (price, change, volume, etc.)
        """
        message = {"ticker": ticker, **data}
        await self._publish(self.PRICE_CHANNEL, message)

    async def publish_portfolio_update(self, user_id: str, data: dict) -> None:
        """
        Publish portfolio P&L update.

        Args:
            user_id: User identifier
            data: Portfolio update data
        """
        channel = self.PORTFOLIO_CHANNEL.format(user_id=user_id)
        await self._publish(channel, data)

    async def publish_alert(self, user_id: str, data: dict) -> None:
        """
        Publish price alert.

        Args:
            user_id: User identifier
            data: Alert data
        """
        channel = self.ALERTS_CHANNEL.format(user_id=user_id)
        await self._publish(channel, data)

    async def _publish(self, channel: str, message: dict) -> None:
        """Publish message to all subscribers of a channel."""
        async with self._lock:
            subscribers = self._subscribers.get(channel, [])
            for queue in subscribers:
                try:
                    # Use put_nowait to avoid blocking publisher
                    queue.put_nowait(message)
                except asyncio.QueueFull:
                    logger.warning(f"SSE subscriber queue full for channel {channel}")

    # --- Subscribers ---

    async def subscribe_prices(
        self,
        tickers: set[str],
        timeout: float = 30.0,
    ) -> AsyncIterator[dict]:
        """
        Subscribe to price updates for specific tickers.

        Args:
            tickers: Set of tickers to subscribe to
            timeout: Unused (kept for interface compatibility)

        Yields:
            Price update dictionaries or heartbeat events
        """
        logger.info(f"SSE (memory): Client subscribing to prices for {tickers}")
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        async with self._lock:
            self._subscribers[self.PRICE_CHANNEL].append(queue)

        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        queue.get(),
                        timeout=HEARTBEAT_INTERVAL,
                    )
                    logger.debug(f"SSE (memory): Received price for {message.get('ticker')}")
                    if message.get("ticker") in tickers:
                        yield message
                except asyncio.TimeoutError:
                    logger.debug("SSE (memory): Sending heartbeat")
                    yield {"_heartbeat": True, "timestamp": time.time()}
        except Exception as e:
            logger.error(f"SSE (memory): Error in subscribe_prices: {e}")
            raise
        finally:
            logger.info(f"SSE (memory): Client unsubscribing from prices for {tickers}")
            async with self._lock:
                try:
                    self._subscribers[self.PRICE_CHANNEL].remove(queue)
                except ValueError:
                    pass

    async def subscribe_portfolio(
        self,
        user_id: str,
    ) -> AsyncIterator[dict]:
        """
        Subscribe to portfolio updates for a user.

        Args:
            user_id: User identifier

        Yields:
            Portfolio update dictionaries or heartbeat events
        """
        logger.info(f"SSE (memory): Client subscribing to portfolio for user {user_id}")
        channel = self.PORTFOLIO_CHANNEL.format(user_id=user_id)
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        async with self._lock:
            self._subscribers[channel].append(queue)

        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        queue.get(),
                        timeout=HEARTBEAT_INTERVAL,
                    )
                    logger.debug(f"SSE (memory): Received portfolio update for user {user_id}")
                    yield message
                except asyncio.TimeoutError:
                    logger.debug(f"SSE (memory): Sending portfolio heartbeat for user {user_id}")
                    yield {"_heartbeat": True, "timestamp": time.time()}
        except Exception as e:
            logger.error(f"SSE (memory): Error in subscribe_portfolio for user {user_id}: {e}")
            raise
        finally:
            logger.info(f"SSE (memory): Client unsubscribing from portfolio for user {user_id}")
            async with self._lock:
                try:
                    self._subscribers[channel].remove(queue)
                except ValueError:
                    pass

    async def subscribe_alerts(
        self,
        user_id: str,
    ) -> AsyncIterator[dict]:
        """
        Subscribe to price alerts for a user.

        Args:
            user_id: User identifier

        Yields:
            Alert dictionaries or heartbeat events
        """
        logger.info(f"SSE (memory): Client subscribing to alerts for user {user_id}")
        channel = self.ALERTS_CHANNEL.format(user_id=user_id)
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        async with self._lock:
            self._subscribers[channel].append(queue)

        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        queue.get(),
                        timeout=HEARTBEAT_INTERVAL,
                    )
                    logger.debug(f"SSE (memory): Received alert for user {user_id}")
                    yield message
                except asyncio.TimeoutError:
                    logger.debug(f"SSE (memory): Sending alerts heartbeat for user {user_id}")
                    yield {"_heartbeat": True, "timestamp": time.time()}
        except Exception as e:
            logger.error(f"SSE (memory): Error in subscribe_alerts for user {user_id}: {e}")
            raise
        finally:
            logger.info(f"SSE (memory): Client unsubscribing from alerts for user {user_id}")
            async with self._lock:
                try:
                    self._subscribers[channel].remove(queue)
                except ValueError:
                    pass


__all__ = ["InMemorySSEManager"]
