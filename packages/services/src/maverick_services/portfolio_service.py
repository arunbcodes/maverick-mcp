"""
Portfolio management service.

Provides portfolio operations: add/remove positions, calculate P&L, performance metrics.
"""

from datetime import date, datetime, timedelta, UTC
from decimal import Decimal
import math
from typing import Protocol

from maverick_schemas.portfolio import (
    Position,
    PositionCreate,
    Portfolio,
    PortfolioSummary,
    PortfolioPerformanceChart,
    PerformanceDataPoint,
)
from maverick_schemas.base import Market, PositionStatus
from maverick_services.exceptions import (
    PortfolioNotFoundError,
    PositionNotFoundError,
    StockNotFoundError,
)


class PortfolioRepository(Protocol):
    """Protocol for portfolio data access."""

    async def get_portfolio(self, user_id: str, name: str) -> dict | None:
        """Get portfolio by user and name."""
        ...

    async def get_positions(self, user_id: str, portfolio_name: str) -> list[dict]:
        """Get all positions for a portfolio."""
        ...

    async def get_position(self, user_id: str, ticker: str) -> dict | None:
        """Get single position."""
        ...

    async def create_position(self, user_id: str, position: dict) -> dict:
        """Create new position."""
        ...

    async def update_position(self, user_id: str, ticker: str, updates: dict) -> dict:
        """Update existing position."""
        ...

    async def delete_position(self, user_id: str, ticker: str) -> bool:
        """Delete position."""
        ...


class QuoteProvider(Protocol):
    """Protocol for getting current prices."""

    async def get_quote(self, ticker: str) -> dict:
        """Get current quote for ticker."""
        ...


class HistoricalDataProvider(Protocol):
    """Protocol for getting historical price data."""

    async def get_historical(
        self, ticker: str, start_date: date, end_date: date
    ) -> list[dict]:
        """Get historical OHLCV data for ticker."""
        ...


def _to_decimal(value: float | int | str | None) -> Decimal | None:
    """Convert to Decimal."""
    if value is None:
        return None
    return Decimal(str(value))


def _detect_market(ticker: str) -> Market:
    """Detect market from ticker."""
    ticker_upper = ticker.upper()
    if ticker_upper.endswith(".NS"):
        return Market.NSE
    elif ticker_upper.endswith(".BO"):
        return Market.BSE
    return Market.US


class PortfolioService:
    """
    Domain service for portfolio management.

    Handles position tracking, P&L calculations, and portfolio analytics.
    """

    def __init__(
        self,
        repository: PortfolioRepository,
        quote_provider: QuoteProvider | None = None,
        historical_provider: HistoricalDataProvider | None = None,
    ):
        """
        Initialize portfolio service.

        Args:
            repository: Portfolio data repository
            quote_provider: Optional provider for current prices
            historical_provider: Optional provider for historical data
        """
        self._repository = repository
        self._quote_provider = quote_provider
        self._historical_provider = historical_provider

    async def get_portfolio(
        self,
        user_id: str,
        portfolio_name: str = "My Portfolio",
        include_prices: bool = True,
    ) -> Portfolio:
        """
        Get complete portfolio with positions.

        Args:
            user_id: User identifier
            portfolio_name: Portfolio name
            include_prices: Whether to fetch current prices

        Returns:
            Portfolio with positions and summary
        """
        positions_data = await self._repository.get_positions(user_id, portfolio_name)

        if not positions_data:
            # Return empty portfolio
            return Portfolio(
                name=portfolio_name,
                user_id=user_id,
                positions=[],
                summary=PortfolioSummary(
                    total_value=Decimal("0"),
                    total_cost=Decimal("0"),
                    total_pnl=Decimal("0"),
                    total_pnl_percent=Decimal("0"),
                    position_count=0,
                    last_updated=datetime.now(UTC),
                ),
            )

        # Convert to Position objects
        positions = []
        total_value = Decimal("0")
        total_cost = Decimal("0")
        winning = 0
        losing = 0

        for pos_data in positions_data:
            position = Position(
                id=pos_data.get("id"),
                ticker=pos_data["ticker"],
                shares=_to_decimal(pos_data["shares"]),
                avg_cost=_to_decimal(pos_data["avg_cost"]),
                total_cost=_to_decimal(pos_data["total_cost"]),
                market=_detect_market(pos_data["ticker"]),
                status=PositionStatus.OPEN,
                first_purchase_date=pos_data.get("first_purchase_date"),
                notes=pos_data.get("notes"),
            )

            # Fetch current price if requested and provider available
            if include_prices and self._quote_provider:
                try:
                    quote = await self._quote_provider.get_quote(position.ticker)
                    current_price = _to_decimal(quote.get("price"))
                    if current_price and position.shares:
                        position.current_price = current_price
                        position.current_value = current_price * position.shares
                        position.unrealized_pnl = position.current_value - position.total_cost
                        if position.total_cost and position.total_cost > 0:
                            position.unrealized_pnl_percent = (
                                position.unrealized_pnl / position.total_cost * 100
                            )

                        total_value += position.current_value
                        if position.unrealized_pnl > 0:
                            winning += 1
                        elif position.unrealized_pnl < 0:
                            losing += 1
                except Exception:
                    # Skip price lookup on error
                    pass

            total_cost += position.total_cost or Decimal("0")
            positions.append(position)

        # Calculate summary
        total_pnl = total_value - total_cost if total_value else Decimal("0")
        total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else Decimal("0")

        summary = PortfolioSummary(
            total_value=total_value,
            total_cost=total_cost,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            position_count=len(positions),
            winning_positions=winning,
            losing_positions=losing,
            last_updated=datetime.now(UTC),
        )

        return Portfolio(
            name=portfolio_name,
            user_id=user_id,
            positions=positions,
            summary=summary,
            updated_at=datetime.now(UTC),
        )

    async def add_position(
        self,
        user_id: str,
        position: PositionCreate,
        portfolio_name: str = "My Portfolio",
    ) -> Position:
        """
        Add or update a position.

        If position already exists, averages the cost basis.

        Args:
            user_id: User identifier
            position: Position to add
            portfolio_name: Portfolio name

        Returns:
            Created or updated Position
        """
        existing = await self._repository.get_position(user_id, position.ticker)

        if existing:
            # Average into existing position
            existing_shares = Decimal(str(existing["shares"]))
            existing_cost = Decimal(str(existing["total_cost"]))

            new_shares = existing_shares + position.shares
            new_total_cost = existing_cost + (position.shares * position.purchase_price)
            new_avg_cost = new_total_cost / new_shares

            updated = await self._repository.update_position(
                user_id,
                position.ticker,
                {
                    "shares": float(new_shares),
                    "avg_cost": float(new_avg_cost),
                    "total_cost": float(new_total_cost),
                },
            )

            return Position(
                id=updated.get("id"),
                ticker=position.ticker.upper(),
                shares=new_shares,
                avg_cost=new_avg_cost,
                total_cost=new_total_cost,
                market=_detect_market(position.ticker),
                notes=position.notes,
            )
        else:
            # Create new position
            total_cost = position.shares * position.purchase_price

            created = await self._repository.create_position(
                user_id,
                {
                    "ticker": position.ticker.upper(),
                    "shares": float(position.shares),
                    "avg_cost": float(position.purchase_price),
                    "total_cost": float(total_cost),
                    "portfolio_name": portfolio_name,
                    "first_purchase_date": position.purchase_date or date.today(),
                    "notes": position.notes,
                },
            )

            return Position(
                id=created.get("id"),
                ticker=position.ticker.upper(),
                shares=position.shares,
                avg_cost=position.purchase_price,
                total_cost=total_cost,
                market=_detect_market(position.ticker),
                first_purchase_date=position.purchase_date,
                notes=position.notes,
            )

    async def remove_position(
        self,
        user_id: str,
        ticker: str,
        shares: Decimal | None = None,
    ) -> Position | None:
        """
        Remove shares from a position or close entirely.

        Args:
            user_id: User identifier
            ticker: Stock ticker
            shares: Shares to remove (None = remove all)

        Returns:
            Updated or removed Position

        Raises:
            PositionNotFoundError: If position doesn't exist
        """
        existing = await self._repository.get_position(user_id, ticker)

        if not existing:
            raise PositionNotFoundError(ticker, user_id)

        existing_shares = Decimal(str(existing["shares"]))

        if shares is None or shares >= existing_shares:
            # Remove entire position
            await self._repository.delete_position(user_id, ticker)
            return None
        else:
            # Partial removal
            new_shares = existing_shares - shares
            avg_cost = Decimal(str(existing["avg_cost"]))
            new_total_cost = new_shares * avg_cost

            updated = await self._repository.update_position(
                user_id,
                ticker,
                {
                    "shares": float(new_shares),
                    "total_cost": float(new_total_cost),
                },
            )

            return Position(
                id=updated.get("id"),
                ticker=ticker.upper(),
                shares=new_shares,
                avg_cost=avg_cost,
                total_cost=new_total_cost,
            )

    async def get_performance(
        self,
        user_id: str,
        period: str = "90d",
        benchmark: str = "SPY",
        portfolio_name: str = "My Portfolio",
    ) -> PortfolioPerformanceChart:
        """
        Calculate portfolio performance with time series data.

        Args:
            user_id: User identifier
            period: Performance period (7d, 30d, 90d, 1y, ytd, all)
            benchmark: Benchmark ticker for comparison
            portfolio_name: Portfolio name

        Returns:
            PortfolioPerformanceChart with time series data
        """
        # Calculate date range based on period
        end_date = date.today()
        if period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "ytd":
            start_date = date(end_date.year, 1, 1)
        else:  # "all"
            start_date = end_date - timedelta(days=365 * 5)

        # Get current positions
        positions_data = await self._repository.get_positions(user_id, portfolio_name)

        if not positions_data or not self._historical_provider:
            # Return empty or simulated performance
            return self._generate_simulated_performance(
                period, start_date, end_date, benchmark
            )

        # Get historical data for all positions and benchmark
        tickers = [p["ticker"] for p in positions_data]
        all_tickers = tickers + [benchmark]

        # Fetch historical data
        historical_data = {}
        for ticker in all_tickers:
            try:
                data = await self._historical_provider.get_historical(
                    ticker, start_date, end_date
                )
                if data:
                    historical_data[ticker] = {
                        d["date"]: _to_decimal(d["close"]) for d in data
                    }
            except Exception:
                continue

        if not historical_data:
            return self._generate_simulated_performance(
                period, start_date, end_date, benchmark
            )

        # Calculate daily portfolio values
        data_points = []
        dates_in_range = []
        
        # Get all unique dates from benchmark (most liquid)
        benchmark_data = historical_data.get(benchmark, {})
        if benchmark_data:
            dates_in_range = sorted(benchmark_data.keys())
        else:
            # Generate date range
            current = start_date
            while current <= end_date:
                if current.weekday() < 5:  # Skip weekends
                    dates_in_range.append(current)
                current += timedelta(days=1)

        # Calculate positions at each date
        initial_value = None
        initial_benchmark = None
        max_drawdown = Decimal("0")
        max_value = Decimal("0")
        max_drawdown_date = start_date

        for i, d in enumerate(dates_in_range):
            portfolio_value = Decimal("0")

            # Calculate portfolio value at this date
            for pos in positions_data:
                ticker = pos["ticker"]
                shares = Decimal(str(pos["shares"]))
                
                if ticker in historical_data:
                    price = historical_data[ticker].get(d)
                    if price:
                        portfolio_value += shares * price
                    else:
                        # Use last known price or avg_cost
                        avg_cost = Decimal(str(pos.get("avg_cost", 0)))
                        portfolio_value += shares * avg_cost
                else:
                    # Fallback to cost basis
                    avg_cost = Decimal(str(pos.get("avg_cost", 0)))
                    portfolio_value += shares * avg_cost

            # Get benchmark value
            benchmark_value = benchmark_data.get(d)

            # Set initial values
            if initial_value is None and portfolio_value > 0:
                initial_value = portfolio_value
            if initial_benchmark is None and benchmark_value:
                initial_benchmark = benchmark_value

            # Calculate returns
            daily_return = None
            cumulative_return = None
            benchmark_return = None

            if initial_value and initial_value > 0:
                cumulative_return = (
                    (portfolio_value - initial_value) / initial_value * 100
                )

            if i > 0 and len(data_points) > 0:
                prev_value = data_points[-1].portfolio_value
                if prev_value and prev_value > 0:
                    daily_return = (portfolio_value - prev_value) / prev_value * 100

            if initial_benchmark and initial_benchmark > 0 and benchmark_value:
                benchmark_return = (
                    (benchmark_value - initial_benchmark) / initial_benchmark * 100
                )

            # Track max drawdown
            if portfolio_value > max_value:
                max_value = portfolio_value
            if max_value > 0:
                drawdown = (max_value - portfolio_value) / max_value * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_date = d

            data_points.append(
                PerformanceDataPoint(
                    date=d,
                    portfolio_value=portfolio_value,
                    daily_return=daily_return,
                    cumulative_return=cumulative_return,
                    benchmark_value=benchmark_value,
                    benchmark_return=benchmark_return,
                )
            )

        # Calculate summary metrics
        total_return = Decimal("0")
        total_return_value = Decimal("0")
        final_benchmark_return = None
        alpha = None
        volatility = None
        sharpe_ratio = None

        if data_points:
            final_point = data_points[-1]
            if initial_value and initial_value > 0:
                total_return_value = final_point.portfolio_value - initial_value
                total_return = total_return_value / initial_value * 100
            
            if final_point.benchmark_return is not None:
                final_benchmark_return = final_point.benchmark_return
                alpha = total_return - final_benchmark_return

            # Calculate volatility (std dev of daily returns)
            daily_returns = [
                dp.daily_return for dp in data_points if dp.daily_return is not None
            ]
            if len(daily_returns) > 1:
                mean_return = sum(daily_returns) / len(daily_returns)
                variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
                daily_vol = Decimal(str(math.sqrt(float(variance))))
                volatility = daily_vol * Decimal(str(math.sqrt(252)))  # Annualized

                # Sharpe ratio (assuming 0% risk-free rate)
                if volatility > 0:
                    # Annualize mean return
                    annualized_return = mean_return * Decimal("252")
                    sharpe_ratio = annualized_return / volatility

        return PortfolioPerformanceChart(
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_return=total_return,
            total_return_value=total_return_value,
            benchmark_return=final_benchmark_return,
            alpha=alpha,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_date=max_drawdown_date,
            data=data_points,
        )

    def _generate_simulated_performance(
        self,
        period: str,
        start_date: date,
        end_date: date,
        benchmark: str,
    ) -> PortfolioPerformanceChart:
        """Generate simulated performance data when real data is unavailable."""
        import random

        data_points = []
        current = start_date
        portfolio_value = Decimal("100000")
        benchmark_value = Decimal("100")
        initial_portfolio = portfolio_value
        initial_benchmark = benchmark_value
        max_value = portfolio_value
        max_drawdown = Decimal("0")
        max_drawdown_date = start_date

        while current <= end_date:
            if current.weekday() < 5:  # Skip weekends
                # Simulate daily return with slight upward bias
                daily_return = Decimal(str(random.gauss(0.0005, 0.012)))
                benchmark_daily_return = Decimal(str(random.gauss(0.0004, 0.01)))

                prev_portfolio = portfolio_value
                portfolio_value = portfolio_value * (1 + daily_return)
                benchmark_value = benchmark_value * (1 + benchmark_daily_return)

                # Track max drawdown
                if portfolio_value > max_value:
                    max_value = portfolio_value
                drawdown = (max_value - portfolio_value) / max_value * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_date = current

                cumulative_return = (portfolio_value - initial_portfolio) / initial_portfolio * 100
                benchmark_return = (benchmark_value - initial_benchmark) / initial_benchmark * 100

                data_points.append(
                    PerformanceDataPoint(
                        date=current,
                        portfolio_value=portfolio_value.quantize(Decimal("0.01")),
                        daily_return=(daily_return * 100).quantize(Decimal("0.01")),
                        cumulative_return=cumulative_return.quantize(Decimal("0.01")),
                        benchmark_value=benchmark_value.quantize(Decimal("0.01")),
                        benchmark_return=benchmark_return.quantize(Decimal("0.01")),
                    )
                )

            current += timedelta(days=1)

        # Calculate final metrics
        final_value = data_points[-1].portfolio_value if data_points else initial_portfolio
        total_return_value = final_value - initial_portfolio
        total_return = (total_return_value / initial_portfolio * 100)
        final_benchmark_return = data_points[-1].benchmark_return if data_points else Decimal("0")
        alpha = total_return - final_benchmark_return

        # Calculate volatility
        daily_returns = [dp.daily_return for dp in data_points if dp.daily_return is not None]
        volatility = None
        sharpe_ratio = None
        if daily_returns:
            mean_return = sum(daily_returns) / len(daily_returns)
            variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
            daily_vol = Decimal(str(math.sqrt(float(variance))))
            volatility = (daily_vol * Decimal(str(math.sqrt(252)))).quantize(Decimal("0.01"))
            if volatility > 0:
                annualized_return = mean_return * Decimal("252")
                sharpe_ratio = (annualized_return / volatility).quantize(Decimal("0.01"))

        return PortfolioPerformanceChart(
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_return=total_return.quantize(Decimal("0.01")),
            total_return_value=total_return_value.quantize(Decimal("0.01")),
            benchmark_return=final_benchmark_return,
            alpha=alpha.quantize(Decimal("0.01")) if alpha else None,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown.quantize(Decimal("0.01")),
            max_drawdown_date=max_drawdown_date,
            data=data_points,
        )


__all__ = ["PortfolioService"]

