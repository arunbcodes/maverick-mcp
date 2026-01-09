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
            logger.warning("PricePublisher: already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(
            f"PricePublisher: started - tracking {len(self.tickers)} tickers "
            f"({', '.join(sorted(self.tickers))}), interval={self.interval}s"
        )

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
        cycle_count = 0
        while self._running:
            try:
                cycle_count += 1
                await self._publish_all_prices()
                # Log status every 12 cycles (~1 minute at 5s interval)
                if cycle_count % 12 == 0:
                    logger.info(
                        f"PricePublisher: completed {cycle_count} cycles, "
                        f"tracking {len(self.tickers)} tickers"
                    )
            except Exception as e:
                logger.error(f"PricePublisher: error in publish cycle: {e}", exc_info=True)

            await asyncio.sleep(self.interval)

    async def _publish_all_prices(self) -> None:
        """Fetch and publish prices for all tracked tickers in parallel."""
        logger.debug(f"PricePublisher: fetching prices for {len(self.tickers)} tickers")
        tasks = [self._fetch_and_publish(ticker) for ticker in self.tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes and failures
        success_count = sum(1 for r in results if r is None)  # None means no exception
        failure_count = len(results) - success_count
        if failure_count > 0:
            logger.warning(
                f"PricePublisher: {success_count}/{len(self.tickers)} prices published, "
                f"{failure_count} failures"
            )

    async def _fetch_and_publish(self, ticker: str) -> None:
        """Fetch and publish price for a single ticker."""
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
                logger.debug(f"PricePublisher: published {ticker} @ ${quote.get('price')}")
            else:
                logger.warning(f"PricePublisher: no quote data returned for {ticker}")
        except Exception as e:
            logger.error(
                f"PricePublisher: failed to fetch/publish {ticker}: {e}",
                exc_info=True,
            )
            raise  # Re-raise so gather() can track it

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
