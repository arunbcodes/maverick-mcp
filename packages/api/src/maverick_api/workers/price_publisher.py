"""
Background worker to publish live price updates.

This runs as a background task and publishes price updates
to Redis pub/sub channels that SSE clients subscribe to.
"""

import asyncio
import logging
from typing import Set

from redis.asyncio import Redis

from maverick_api.sse.manager import SSEManager
from maverick_data.providers.yfinance_provider import YFinanceProvider

logger = logging.getLogger(__name__)

# Default tickers to track (commonly watched stocks)
DEFAULT_TICKERS = {"AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "SPY", "QQQ"}

# Update interval in seconds
UPDATE_INTERVAL = 5.0


class PricePublisher:
    """
    Background service that fetches prices and publishes to SSE.

    This worker periodically fetches real-time quotes for tracked tickers
    and publishes them to Redis pub/sub, which SSE clients subscribe to.
    """

    def __init__(
        self,
        redis: Redis,
        tickers: Set[str] | None = None,
        interval: float = UPDATE_INTERVAL,
    ):
        """
        Initialize the price publisher.

        Args:
            redis: Redis client for pub/sub
            tickers: Set of tickers to track (defaults to popular tickers)
            interval: Update interval in seconds
        """
        self.sse_manager = SSEManager(redis)
        self.provider = YFinanceProvider()
        self.tickers = tickers.copy() if tickers else DEFAULT_TICKERS.copy()
        self.interval = interval
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the price publisher background task."""
        if self._running:
            logger.warning("Price publisher already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Price publisher started for {len(self.tickers)} tickers")

    async def stop(self) -> None:
        """Stop the price publisher."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Price publisher stopped")

    async def _run(self) -> None:
        """Main loop that fetches and publishes prices."""
        while self._running:
            try:
                await self._publish_all_prices()
            except Exception as e:
                logger.error(f"Error publishing prices: {e}")

            await asyncio.sleep(self.interval)

    async def _publish_all_prices(self) -> None:
        """Fetch and publish prices for all tracked tickers."""
        for ticker in self.tickers:
            try:
                quote = await self.provider.get_realtime_quote(ticker)
                if quote:
                    await self.sse_manager.publish_price(
                        ticker,
                        {
                            "price": quote.get("price"),
                            "change": quote.get("change"),
                            "change_percent": quote.get("change_percent"),
                            "volume": quote.get("volume"),
                            "timestamp": quote.get("timestamp"),
                        },
                    )
                    logger.debug(f"Published price for {ticker}: {quote.get('price')}")
            except Exception as e:
                logger.warning(f"Failed to fetch/publish price for {ticker}: {e}")

    def add_ticker(self, ticker: str) -> None:
        """Add a ticker to track."""
        self.tickers.add(ticker.upper())
        logger.debug(f"Added ticker {ticker.upper()} to price publisher")

    def remove_ticker(self, ticker: str) -> None:
        """Remove a ticker from tracking."""
        self.tickers.discard(ticker.upper())
        logger.debug(f"Removed ticker {ticker.upper()} from price publisher")

    @property
    def is_running(self) -> bool:
        """Check if the publisher is running."""
        return self._running


__all__ = ["PricePublisher"]
