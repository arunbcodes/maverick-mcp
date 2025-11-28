"""
Macroeconomic Data Provider.

Provides macroeconomic indicators using FRED API including:
- GDP growth rate
- Unemployment rate
- Inflation rate (Core CPI)
- S&P 500 and NASDAQ momentum
- VIX
- USD momentum
- Sentiment scoring
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Configuration
FRED_API_KEY = os.getenv("FRED_API_KEY", "")


class MacroDataProvider:
    """
    Provider for macroeconomic data using FRED API.

    Features:
    - GDP growth rate tracking
    - Unemployment rate monitoring
    - Inflation rate (Core CPI Year-over-Year)
    - Market momentum (S&P 500, NASDAQ)
    - VIX volatility index
    - USD index momentum
    - Composite sentiment scoring
    - Historical data bounds normalization
    """

    MAX_WINDOW_DAYS = 365

    def __init__(self, window_days: int = MAX_WINDOW_DAYS):
        """
        Initialize macro data provider.

        Args:
            window_days: Number of days for historical bounds calculation
        """
        self._fred = None
        self._scaler = None
        self.window_days = window_days
        self.historical_data_bounds: dict[str, dict[str, Any]] = {}
        self.lookback_days = 30
        self.previous_sentiment_score: float | None = None

        # Weights for macro sentiment
        self.weights = {
            # Short-term signals (60% total)
            "vix": 0.20,
            "sp500_momentum": 0.20,
            "nasdaq_momentum": 0.15,
            "usd_momentum": 0.05,
            # Macro signals (40% total)
            "inflation_rate": 0.15,
            "gdp_growth_rate": 0.15,
            "unemployment_rate": 0.10,
        }

        # Initialize FRED client
        self._init_fred()

        logger.info("MacroDataProvider initialized")

    def _init_fred(self):
        """Initialize FRED API client."""
        try:
            from fredapi import Fred
            from sklearn.preprocessing import MinMaxScaler

            self._fred = Fred(api_key=FRED_API_KEY)
            self._scaler = MinMaxScaler()
            self.update_historical_bounds()
        except ImportError:
            logger.warning(
                "fredapi or sklearn not installed. Macro data will be limited."
            )
            self._fred = None
            self._scaler = None

    @property
    def fred(self):
        """Get FRED client, initializing if needed."""
        if self._fred is None:
            self._init_fred()
        return self._fred

    def _get_fred_series(
        self, series_id: str, start_date: str, end_date: str
    ) -> pd.Series:
        """
        Get FRED series data.

        Args:
            series_id: FRED series identifier
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Pandas Series with the data
        """
        if self.fred is None:
            return pd.Series(dtype=float)
        return self.fred.get_series(series_id, start_date, end_date)

    def _calculate_weighted_rolling_performance(
        self, series_id: str, lookbacks: list[int], weights: list[float]
    ) -> float:
        """
        Calculate weighted performance over multiple rolling windows.

        Args:
            series_id: FRED series ID
            lookbacks: List of lookback periods in days
            weights: Corresponding weights for each lookback

        Returns:
            Weighted performance value
        """
        if len(lookbacks) != len(weights):
            logger.error("Lookbacks and weights must have the same length.")
            return 0.0

        end_date = datetime.now(UTC)
        total_performance = 0.0

        for days, w in zip(lookbacks, weights, strict=False):
            start_date = end_date - timedelta(days=days)
            series_data = self._get_fred_series(
                series_id,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            )

            if isinstance(series_data, pd.Series):
                df = series_data.dropna()
                if not df.empty:
                    df = df.rolling(window=2).mean().dropna()
                    if not df.empty:
                        start_price = df.iloc[0]
                        end_price = df.iloc[-1]
                        performance = ((end_price - start_price) / start_price) * 100
                        total_performance += performance * w
                else:
                    logger.warning(
                        f"No FRED data for {series_id} over last {days} days."
                    )
            else:
                logger.warning(
                    f"Unexpected data type from FRED API for {series_id}: {type(series_data)}"
                )

        return total_performance

    def get_sp500_performance(self) -> float:
        """
        Calculate multi-timeframe rolling performance for S&P 500.

        Returns:
            Weighted performance percentage
        """
        try:
            lookbacks = [30, 90, 180]
            weights = [0.5, 0.3, 0.2]
            return self._calculate_weighted_rolling_performance(
                "SP500", lookbacks, weights
            )
        except Exception as e:
            logger.error(f"Error fetching S&P 500 rolling performance: {e}")
            return 0.0

    def get_nasdaq_performance(self) -> float:
        """
        Calculate multi-timeframe rolling performance for NASDAQ-100.

        Returns:
            Weighted performance percentage
        """
        try:
            lookbacks = [30, 90, 180]
            weights = [0.5, 0.3, 0.2]
            return self._calculate_weighted_rolling_performance(
                "NASDAQ100", lookbacks, weights
            )
        except Exception as e:
            logger.error(f"Error fetching NASDAQ rolling performance: {e}")
            return 0.0

    def get_gdp_growth_rate(self) -> dict[str, float]:
        """
        Fetch GDP growth rate.

        Returns:
            Dictionary with current and previous GDP growth rates
        """
        try:
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=180)

            data = self._get_fred_series(
                "A191RL1Q225SBEA",
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            )

            if data.empty:
                logger.warning("No GDP data available from FRED")
                return {"current": 0.0, "previous": 0.0}

            last_two = data.tail(2)
            if len(last_two) >= 2:
                return {
                    "current": float(last_two.iloc[-1]),
                    "previous": float(last_two.iloc[-2]),
                }
            return {
                "current": float(last_two.iloc[-1]),
                "previous": float(last_two.iloc[-1]),
            }

        except Exception as e:
            logger.error(f"Error fetching GDP growth rate: {e}")
            return {"current": 0.0, "previous": 0.0}

    def get_unemployment_rate(self) -> dict[str, float | None]:
        """
        Fetch unemployment rate.

        Returns:
            Dictionary with current and previous unemployment rates
        """
        try:
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=90)
            series_data = self._get_fred_series(
                "UNRATE", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )

            if not isinstance(series_data, pd.Series):
                logger.error(
                    f"Expected pandas Series from FRED API, got {type(series_data)}"
                )
                return {"current": 0.0, "previous": 0.0}

            data = series_data.dropna()
            if len(data) >= 2:
                return {
                    "current": float(data.iloc[-1]),
                    "previous": float(data.iloc[-2]),
                }
            return {"current": float(data.iloc[-1]), "previous": float(data.iloc[-1])}

        except Exception as e:
            logger.error(f"Error fetching unemployment rate: {e}")
            return {"current": None, "previous": None}

    def get_inflation_rate(self) -> dict[str, Any]:
        """
        Fetch the annual core inflation rate based on CPI data.

        Uses CPILFESL (Core CPI: All Items Less Food and Energy).

        Returns:
            Dictionary with current, previous inflation rates and bounds
        """
        try:
            if self.fred is None:
                return {"current": None, "previous": None, "bounds": (None, None)}

            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=5 * 365)

            series_data = self.fred.get_series(
                "CPILFESL",
                observation_start=start_date.strftime("%Y-%m-%d"),
                observation_end=end_date.strftime("%Y-%m-%d"),
            )

            if not isinstance(series_data, pd.Series):
                logger.error(
                    f"Expected pandas Series from FRED API, got {type(series_data)}"
                )
                return {"current": None, "previous": None, "bounds": (None, None)}

            data = series_data.dropna().sort_index()
            data = data.asfreq("MS").dropna()

            if data.empty:
                logger.error("No inflation data available from FRED")
                return {"current": None, "previous": None, "bounds": (None, None)}

            # Calculate year-over-year inflation
            latest_idx = data.index[-1]
            latest_value = data.iloc[-1]

            if isinstance(latest_idx, pd.Timestamp):
                year_ago_idx = latest_idx - pd.DateOffset(years=1)
            else:
                year_ago_idx = pd.Timestamp(latest_idx) - pd.DateOffset(years=1)

            year_ago_series = data[data.index <= year_ago_idx]
            if year_ago_series.empty:
                logger.warning(
                    "Not enough data to get year-ago CPI. Using 0 as fallback."
                )
                current_inflation = 0.0
            else:
                year_ago_value = year_ago_series.iloc[-1]
                current_inflation = (
                    (latest_value - year_ago_value) / year_ago_value
                ) * 100

            # Calculate previous month's YoY
            if isinstance(latest_idx, pd.Timestamp):
                prev_month_idx = latest_idx - pd.DateOffset(months=1)
            else:
                prev_month_idx = pd.Timestamp(latest_idx) - pd.DateOffset(months=1)

            prev_month_series = data[data.index <= prev_month_idx]
            if prev_month_series.empty:
                previous_inflation = 0.0
            else:
                prev_month_value = prev_month_series.iloc[-1]
                if isinstance(prev_month_idx, pd.Timestamp):
                    prev_year_ago_idx = prev_month_idx - pd.DateOffset(years=1)
                else:
                    prev_year_ago_idx = pd.Timestamp(prev_month_idx) - pd.DateOffset(
                        years=1
                    )
                prev_year_ago_series = data[data.index <= prev_year_ago_idx]
                if prev_year_ago_series.empty:
                    previous_inflation = 0.0
                else:
                    prev_year_ago_value = prev_year_ago_series.iloc[-1]
                    previous_inflation = (
                        (prev_month_value - prev_year_ago_value) / prev_year_ago_value
                    ) * 100

            current_inflation = round(current_inflation, 2)
            previous_inflation = round(previous_inflation, 2)

            # Calculate bounds
            yoy_changes = data.pct_change(periods=12) * 100
            yoy_changes = yoy_changes.dropna()
            if yoy_changes.empty:
                inflation_min, inflation_max = 0.0, 0.0
            else:
                inflation_min = yoy_changes.min()
                inflation_max = yoy_changes.max()

            bounds = (round(inflation_min, 2), round(inflation_max, 2))

            logger.info(
                f"Core CPI (YoY): current={current_inflation}%, previous={previous_inflation}%"
            )
            return {
                "current": current_inflation,
                "previous": previous_inflation,
                "bounds": bounds,
            }

        except Exception as e:
            logger.error(f"Error fetching core inflation rate: {e}", exc_info=True)
            return {"current": None, "previous": None, "bounds": (None, None)}

    def get_vix(self) -> float | None:
        """
        Get VIX data.

        Returns:
            Current VIX value or None
        """
        try:
            import yfinance as yf

            # Try Yahoo Finance first
            ticker = yf.Ticker("^VIX")
            data = ticker.history(period="1d")
            if not data.empty:
                return float(data["Close"].iloc[-1])

            # Fallback to FRED
            if self.fred is not None:
                end_date = datetime.now(UTC)
                start_date = end_date - timedelta(days=7)
                series_data = self.fred.get_series(
                    "VIXCLS",
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                )
                if isinstance(series_data, pd.Series):
                    df = series_data.dropna()
                    if not df.empty:
                        return float(df.iloc[-1])

            return None

        except Exception as e:
            logger.error(f"Error fetching VIX: {e}")
            return None

    def get_sp500_momentum(self) -> float:
        """
        Calculate short-term momentum of the S&P 500.

        Uses 3-day, 7-day, and 14-day lookbacks with weighted average.

        Returns:
            Momentum value
        """
        try:
            if self.fred is None:
                return 0.0

            end_date = datetime.now(UTC)
            lookbacks = [3, 7, 14]
            momentums = []

            for days in lookbacks:
                start_date = end_date - timedelta(days=days)
                series_data = self.fred.get_series(
                    "SP500",
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                )
                if isinstance(series_data, pd.Series):
                    df = series_data.dropna()
                    df = df.rolling(window=2).mean().dropna()

                    if len(df) >= 2:
                        momentum = ((df.iloc[-1] - df.iloc[0]) / df.iloc[0]) * 100
                        momentums.append(momentum)

            if momentums:
                weighted: float = (
                    0.5 * momentums[0] + 0.3 * momentums[1] + 0.2 * momentums[2]
                    if len(momentums) == 3
                    else sum(momentums) / len(momentums)
                )
                return weighted

            return 0.0

        except Exception as e:
            logger.error(f"Error fetching S&P 500 momentum: {e}")
            return 0.0

    def get_nasdaq_momentum(self) -> float:
        """
        Calculate short-term momentum of the NASDAQ-100.

        Uses 3-day, 7-day, and 14-day lookbacks with weighted average.

        Returns:
            Momentum value
        """
        try:
            if self.fred is None:
                return 0.0

            end_date = datetime.now(UTC)
            lookbacks = [3, 7, 14]
            momentums = []

            for days in lookbacks:
                start_date = end_date - timedelta(days=days + 5)
                series_data = self.fred.get_series(
                    "NASDAQ100",
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                )
                if isinstance(series_data, pd.Series):
                    df = series_data.dropna()
                    df = df.rolling(window=2).mean().dropna()

                    if len(df) >= 2:
                        momentum = ((df.iloc[-1] - df.iloc[0]) / df.iloc[0]) * 100
                        momentums.append(momentum)
                else:
                    logger.warning(f"Insufficient NASDAQ data for {days}-day lookback")
                    momentums.append(0.0)

            if len(momentums) == 3:
                result: float = (
                    0.5 * momentums[0] + 0.3 * momentums[1] + 0.2 * momentums[2]
                )
                return result

            logger.warning("Insufficient data for NASDAQ momentum calculation")
            return sum(momentums) / len(momentums) if momentums else 0.0

        except Exception as e:
            logger.error(f"Error fetching NASDAQ momentum: {e}")
            return 0.0

    def get_usd_momentum(self) -> float:
        """
        Calculate USD momentum using DTWEXBGS (Broad USD Index).

        Returns:
            USD momentum value
        """
        try:
            if self.fred is None:
                return 0.0

            end_date = datetime.now(UTC)
            lookbacks = [3, 7, 14]
            momentums = []

            for days in lookbacks:
                start_date = end_date - timedelta(days=days + 5)
                df = self.fred.get_series(
                    "DTWEXBGS",
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                )
                df = df.dropna()
                df = df.rolling(window=2).mean().dropna()

                if len(df) >= 2:
                    first_valid = df.iloc[0]
                    last_valid = df.iloc[-1]
                    momentum = ((last_valid - first_valid) / first_valid) * 100
                    momentums.append(momentum)
                else:
                    logger.warning(f"Insufficient USD data for {days}-day lookback")
                    momentums.append(0.0)

            if len(momentums) == 3:
                result: float = (
                    0.5 * momentums[0] + 0.3 * momentums[1] + 0.2 * momentums[2]
                )
                return result

            logger.warning("Insufficient data for USD momentum calculation")
            return sum(momentums) / len(momentums) if momentums else 0.0

        except Exception as e:
            logger.error(f"Error fetching USD momentum: {e}")
            return 0.0

    def update_historical_bounds(self):
        """
        Update historical bounds for normalization.

        Fetches min/max values for each indicator over the window period.
        """
        if self.fred is None:
            for key in self.weights.keys():
                self.historical_data_bounds[key] = self.default_bounds(key)
            return

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=self.window_days)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        indicators = {
            "gdp_growth_rate": "A191RL1Q225SBEA",
            "unemployment_rate": "UNRATE",
            "inflation_rate": "CPILFESL",
            "sp500_momentum": "SP500",
            "nasdaq_momentum": "NASDAQCOM",
            "vix": "VIXCLS",
        }

        for key, series_id in indicators.items():
            try:
                if key == "gdp_growth_rate":
                    data = self.fred.get_series(series_id, start_date_str, end_date_str)
                elif key == "inflation_rate":
                    wider_start = (end_date - timedelta(days=5 * 365)).strftime(
                        "%Y-%m-%d"
                    )
                    cpi = self.fred.get_series(series_id, wider_start, end_date_str)
                    cpi = cpi.dropna()

                    if len(cpi) > 13:
                        inflation_rates = []
                        for i in range(12, len(cpi)):
                            yoy_inflation = (
                                (cpi.iloc[i] - cpi.iloc[i - 12]) / cpi.iloc[i - 12]
                            ) * 100
                            inflation_rates.append(yoy_inflation)

                        data = (
                            pd.Series(inflation_rates)
                            if inflation_rates
                            else pd.Series([], dtype=float)
                        )
                    else:
                        data = pd.Series([], dtype=float)
                elif key in ["sp500_momentum", "nasdaq_momentum"]:
                    df = self.fred.get_series(series_id, start_date_str, end_date_str)
                    df = df.dropna()
                    df = df.rolling(window=2).mean().dropna()
                    if not df.empty:
                        start_price = df.iloc[0]
                        end_price = df.iloc[-1]
                        performance = ((end_price - start_price) / start_price) * 100
                        data = pd.Series([performance], index=[df.index[-1]])
                    else:
                        data = pd.Series([], dtype=float)
                else:
                    data = self.fred.get_series(series_id, start_date_str, end_date_str)

                if not data.empty:
                    min_val = data.min()
                    max_val = data.max()
                    self.historical_data_bounds[key] = {"min": min_val, "max": max_val}
                else:
                    self.historical_data_bounds[key] = self.default_bounds(key)
                    logger.warning(f"No data fetched for {key}. Using default bounds.")

            except Exception as e:
                logger.error(f"Error updating historical bounds for {key}: {e}")
                self.historical_data_bounds[key] = self.default_bounds(key)

    def default_bounds(self, key: str) -> dict[str, float]:
        """
        Get default bounds for an indicator.

        Args:
            key: Indicator name

        Returns:
            Dictionary with min and max bounds
        """
        default_bounds = {
            "vix": {"min": 10.0, "max": 50.0},
            "sp500_momentum": {"min": -15.0, "max": 15.0},
            "nasdaq_momentum": {"min": -20.0, "max": 20.0},
            "usd_momentum": {"min": -5.0, "max": 5.0},
            "inflation_rate": {"min": 0.0, "max": 10.0},
            "gdp_growth_rate": {"min": -2.0, "max": 6.0},
            "unemployment_rate": {"min": 2.0, "max": 10.0},
        }
        return default_bounds.get(key, {"min": 0.0, "max": 1.0})

    def normalize_indicators(self, indicators: dict[str, Any]) -> dict[str, float]:
        """
        Normalize indicators to [0,1] scale.

        Risk-off indicators are inverted (lower is better).

        Args:
            indicators: Raw indicator values

        Returns:
            Normalized indicator values
        """
        normalized = {}
        for key, value in indicators.items():
            if value is None:
                normalized[key] = 0.5
                continue

            bounds = self.historical_data_bounds.get(key, self.default_bounds(key))
            min_val = float(bounds["min"])
            max_val = float(bounds["max"])
            denom = max_val - min_val if (max_val != min_val) else 1e-9

            norm_val = (value - min_val) / denom

            # Invert risk-off indicators
            if key in ["vix", "unemployment_rate", "inflation_rate"]:
                norm_val = 1.0 - norm_val

            norm_val = max(0.0, min(1.0, norm_val))
            normalized[key] = norm_val

        return normalized

    def get_historical_data(self) -> dict[str, list]:
        """
        Get historical data for all indicators.

        Returns:
            Dictionary with historical data lists
        """
        if self.fred is None:
            return {
                "sp500_performance": [],
                "nasdaq_performance": [],
                "vix": [],
                "gdp_growth_rate": [],
                "unemployment_rate": [],
                "inflation_rate": [],
            }

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=self.lookback_days)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        try:
            sp500_data = self.fred.get_series("SP500", start_date_str, end_date_str)
            sp500_performance = []
            if not sp500_data.empty:
                first_value = sp500_data.iloc[0]
                sp500_performance = [
                    (x - first_value) / first_value * 100 for x in sp500_data
                ]

            nasdaq_data = self.fred.get_series(
                "NASDAQ100", start_date_str, end_date_str
            )
            nasdaq_performance = []
            if not nasdaq_data.empty:
                first_value = nasdaq_data.iloc[0]
                nasdaq_performance = [
                    (x - first_value) / first_value * 100 for x in nasdaq_data
                ]

            vix_data = self.fred.get_series("VIXCLS", start_date_str, end_date_str)
            vix_values = vix_data.tolist() if not vix_data.empty else []

            gdp_data = self.fred.get_series(
                "A191RL1Q225SBEA", start_date_str, end_date_str
            )
            gdp_values = gdp_data.tolist() if not gdp_data.empty else []

            unemployment_data = self.fred.get_series(
                "UNRATE", start_date_str, end_date_str
            )
            unemployment_values = (
                unemployment_data.tolist() if not unemployment_data.empty else []
            )

            cpi_data = self.fred.get_series("CPILFESL", start_date_str, end_date_str)
            inflation_values = []
            if not cpi_data.empty and len(cpi_data) > 12:
                inflation_values = [
                    ((cpi_data.iloc[i] - cpi_data.iloc[i - 12]) / cpi_data.iloc[i - 12])
                    * 100
                    for i in range(12, len(cpi_data))
                ]

            return {
                "sp500_performance": sp500_performance,
                "nasdaq_performance": nasdaq_performance,
                "vix": vix_values,
                "gdp_growth_rate": gdp_values,
                "unemployment_rate": unemployment_values,
                "inflation_rate": inflation_values,
            }

        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return {
                "sp500_performance": [],
                "nasdaq_performance": [],
                "vix": [],
                "gdp_growth_rate": [],
                "unemployment_rate": [],
                "inflation_rate": [],
            }

    def get_macro_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive macroeconomic statistics.

        Returns:
            Dictionary with all macro indicators and sentiment score
        """
        try:
            self.update_historical_bounds()

            # Get individual indicators
            inflation_data = self.get_inflation_rate()
            gdp_data = self.get_gdp_growth_rate()
            unemployment_data = self.get_unemployment_rate()

            # Pull raw indicator values with safe defaults
            indicators = {
                "gdp_growth_rate": gdp_data["current"] or 0.0,
                "gdp_growth_rate_previous": gdp_data["previous"] or 0.0,
                "unemployment_rate": unemployment_data["current"] or 0.0,
                "unemployment_rate_previous": unemployment_data["previous"] or 0.0,
                "inflation_rate": inflation_data["current"] or 0.0,
                "inflation_rate_previous": inflation_data["previous"] or 0.0,
                "vix": self.get_vix() or 0.0,
                "sp500_momentum": self.get_sp500_momentum() or 0.0,
                "nasdaq_momentum": self.get_nasdaq_momentum() or 0.0,
                "usd_momentum": self.get_usd_momentum() or 0.0,
            }

            # Normalize and calculate sentiment score
            normalized = self.normalize_indicators(indicators)
            sentiment_score = sum(normalized[k] * self.weights[k] for k in self.weights)
            sentiment_score = (sentiment_score / sum(self.weights.values())) * 100
            sentiment_score = max(1, min(100, sentiment_score))

            # Apply smoothing
            if self.previous_sentiment_score is not None:
                smoothing_factor = 0.8
                sentiment_score = (
                    smoothing_factor * self.previous_sentiment_score
                    + (1 - smoothing_factor) * sentiment_score
                )

            self.previous_sentiment_score = sentiment_score

            historical_data = self.get_historical_data()

            return {
                "gdp_growth_rate": float(indicators["gdp_growth_rate"]),
                "gdp_growth_rate_previous": float(
                    indicators["gdp_growth_rate_previous"]
                ),
                "unemployment_rate": float(indicators["unemployment_rate"]),
                "unemployment_rate_previous": float(
                    indicators["unemployment_rate_previous"]
                ),
                "inflation_rate": float(indicators["inflation_rate"]),
                "inflation_rate_previous": float(indicators["inflation_rate_previous"]),
                "sp500_performance": float(self.get_sp500_performance() or 0.0),
                "nasdaq_performance": float(self.get_nasdaq_performance() or 0.0),
                "vix": float(indicators["vix"]),
                "sentiment_score": float(sentiment_score),
                "historical_data": historical_data,
            }

        except Exception as e:
            logger.error(f"Error in get_macro_statistics: {e}")
            return {
                "gdp_growth_rate": 0.0,
                "gdp_growth_rate_previous": 0.0,
                "unemployment_rate": 0.0,
                "unemployment_rate_previous": 0.0,
                "inflation_rate": 0.0,
                "inflation_rate_previous": 0.0,
                "sp500_performance": 0.0,
                "nasdaq_performance": 0.0,
                "vix": 0.0,
                "sentiment_score": 50.0,
                "historical_data": {},
            }


__all__ = ["MacroDataProvider"]
