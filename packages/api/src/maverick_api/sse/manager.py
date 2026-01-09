"""
SSE Manager with Redis pub/sub for horizontal scaling.

Allows multiple API workers to publish and subscribe to real-time events.
"""

import asyncio
import json
import logging
import time
from typing import AsyncIterator

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# Heartbeat interval in seconds (keeps connection alive through proxies)
HEARTBEAT_INTERVAL = 15


class SSEManager:
    """
    Manages SSE connections with Redis pub/sub.

    Architecture:
    - Background workers publish updates to Redis channels
    - Each API worker subscribes and forwards to connected clients
    - Works across multiple workers/pods

    Channels:
    - sse:prices - Price updates for all tickers
    - sse:portfolio:{user_id} - Portfolio updates for specific user
    - sse:alerts:{user_id} - Price alerts for specific user
    """

    PRICE_CHANNEL = "sse:prices"
    PORTFOLIO_CHANNEL = "sse:portfolio:{user_id}"
    ALERTS_CHANNEL = "sse:alerts:{user_id}"

    def __init__(self, redis: Redis):
        """
        Initialize SSE manager.

        Args:
            redis: Redis client for pub/sub
        """
        self.redis = redis

    # --- Publishers ---

    async def publish_price(self, ticker: str, data: dict) -> None:
        """
        Publish price update.

        Args:
            ticker: Stock ticker
            data: Price data (price, change, volume, etc.)
        """
        message = json.dumps({"ticker": ticker, **data})
        await self.redis.publish(self.PRICE_CHANNEL, message)

    async def publish_portfolio_update(self, user_id: str, data: dict) -> None:
        """
        Publish portfolio P&L update.

        Args:
            user_id: User identifier
            data: Portfolio update data
        """
        channel = self.PORTFOLIO_CHANNEL.format(user_id=user_id)
        await self.redis.publish(channel, json.dumps(data))

    async def publish_alert(self, user_id: str, data: dict) -> None:
        """
        Publish price alert.

        Args:
            user_id: User identifier
            data: Alert data (ticker, condition, triggered, etc.)
        """
        channel = self.ALERTS_CHANNEL.format(user_id=user_id)
        await self.redis.publish(channel, json.dumps(data))

    # --- Subscribers ---

    async def subscribe_prices(
        self,
        tickers: set[str],
        timeout: float = 30.0,
    ) -> AsyncIterator[dict]:
        """
        Subscribe to price updates for specific tickers.

        Includes heartbeat support for mobile clients and proxies.

        Args:
            tickers: Set of tickers to subscribe to
            timeout: Timeout in seconds for waiting on messages (triggers heartbeat)

        Yields:
            Price update dictionaries for matching tickers, or heartbeat events
        """
        logger.info(f"SSE: Client subscribing to prices for {tickers}")
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.PRICE_CHANNEL)
        last_event_time = time.time()

        try:
            while True:
                try:
                    # Use timeout to allow periodic heartbeats
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                        timeout=HEARTBEAT_INTERVAL,
                    )

                    if message is None:
                        # No message, check if we need heartbeat
                        if time.time() - last_event_time >= HEARTBEAT_INTERVAL:
                            logger.debug("SSE: Sending heartbeat (no message)")
                            yield {"_heartbeat": True, "timestamp": time.time()}
                            last_event_time = time.time()
                        continue

                    if message["type"] != "message":
                        continue

                    try:
                        data = json.loads(message["data"])
                        logger.debug(f"SSE: Received price message for {data.get('ticker')}")
                        if data.get("ticker") in tickers:
                            yield data
                            last_event_time = time.time()
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in price message: {message['data']}")
                        continue

                except asyncio.TimeoutError:
                    # Timeout - send heartbeat
                    logger.debug("SSE: Sending heartbeat (timeout)")
                    yield {"_heartbeat": True, "timestamp": time.time()}
                    last_event_time = time.time()
        except Exception as e:
            logger.error(f"SSE: Error in subscribe_prices: {e}")
            raise
        finally:
            logger.info(f"SSE: Client unsubscribing from prices for {tickers}")
            await pubsub.unsubscribe(self.PRICE_CHANNEL)

    async def subscribe_portfolio(
        self,
        user_id: str,
    ) -> AsyncIterator[dict]:
        """
        Subscribe to portfolio updates for a user.

        Includes heartbeat support for mobile clients and proxies.

        Args:
            user_id: User identifier

        Yields:
            Portfolio update dictionaries, or heartbeat events
        """
        logger.info(f"SSE: Client subscribing to portfolio updates for user {user_id}")
        channel = self.PORTFOLIO_CHANNEL.format(user_id=user_id)
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        last_event_time = time.time()

        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                        timeout=HEARTBEAT_INTERVAL,
                    )

                    if message is None:
                        if time.time() - last_event_time >= HEARTBEAT_INTERVAL:
                            logger.debug(f"SSE: Sending portfolio heartbeat for user {user_id}")
                            yield {"_heartbeat": True, "timestamp": time.time()}
                            last_event_time = time.time()
                        continue

                    if message["type"] != "message":
                        continue

                    try:
                        logger.debug(f"SSE: Received portfolio update for user {user_id}")
                        yield json.loads(message["data"])
                        last_event_time = time.time()
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in portfolio message: {message['data']}")
                        continue

                except asyncio.TimeoutError:
                    logger.debug(f"SSE: Sending portfolio heartbeat (timeout) for user {user_id}")
                    yield {"_heartbeat": True, "timestamp": time.time()}
                    last_event_time = time.time()
        except Exception as e:
            logger.error(f"SSE: Error in subscribe_portfolio for user {user_id}: {e}")
            raise
        finally:
            logger.info(f"SSE: Client unsubscribing from portfolio for user {user_id}")
            await pubsub.unsubscribe(channel)

    async def subscribe_alerts(
        self,
        user_id: str,
    ) -> AsyncIterator[dict]:
        """
        Subscribe to price alerts for a user.

        Includes heartbeat support for mobile clients and proxies.

        Args:
            user_id: User identifier

        Yields:
            Alert dictionaries, or heartbeat events
        """
        logger.info(f"SSE: Client subscribing to alerts for user {user_id}")
        channel = self.ALERTS_CHANNEL.format(user_id=user_id)
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        last_event_time = time.time()

        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                        timeout=HEARTBEAT_INTERVAL,
                    )

                    if message is None:
                        if time.time() - last_event_time >= HEARTBEAT_INTERVAL:
                            logger.debug(f"SSE: Sending alerts heartbeat for user {user_id}")
                            yield {"_heartbeat": True, "timestamp": time.time()}
                            last_event_time = time.time()
                        continue

                    if message["type"] != "message":
                        continue

                    try:
                        logger.debug(f"SSE: Received alert for user {user_id}")
                        yield json.loads(message["data"])
                        last_event_time = time.time()
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in alert message: {message['data']}")
                        continue

                except asyncio.TimeoutError:
                    logger.debug(f"SSE: Sending alerts heartbeat (timeout) for user {user_id}")
                    yield {"_heartbeat": True, "timestamp": time.time()}
                    last_event_time = time.time()
        except Exception as e:
            logger.error(f"SSE: Error in subscribe_alerts for user {user_id}: {e}")
            raise
        finally:
            logger.info(f"SSE: Client unsubscribing from alerts for user {user_id}")
            await pubsub.unsubscribe(channel)


__all__ = ["SSEManager"]

