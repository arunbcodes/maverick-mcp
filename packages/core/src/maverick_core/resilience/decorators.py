"""
Decorators for easy circuit breaker integration.
Provides convenient decorators for common external service patterns.
"""

import asyncio
import functools
import logging
from collections.abc import Callable
from typing import TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_http_circuit_breaker(
    timeout: float | None = None, use_session: bool = False
) -> Callable:
    """
    Decorator for general HTTP requests.

    Args:
        timeout: Override default timeout
        use_session: Whether the function uses a requests Session

    Example:
        @with_http_circuit_breaker(timeout=10.0)
        def fetch_api_data(url: str) -> dict:
            response = requests.get(url)
            return response.json()
    """
    from maverick_core.resilience.circuit_breaker import get_circuit_breaker

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Override timeout if specified
                if timeout is not None:
                    kwargs["timeout"] = timeout

                http_breaker = get_circuit_breaker("http_general")
                if http_breaker:
                    return await http_breaker.call_async(func, *args, **kwargs)
                return await func(*args, **kwargs)

            return cast(Callable[..., T], async_wrapper)
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Override timeout if specified
                if timeout is not None:
                    kwargs["timeout"] = timeout

                http_breaker = get_circuit_breaker("http_general")
                if http_breaker:
                    return http_breaker.call_sync(func, *args, **kwargs)
                return func(*args, **kwargs)

            return cast(Callable[..., T], sync_wrapper)

    return decorator


def circuit_breaker_method(
    service: str = "http", use_fallback: bool = True, **breaker_kwargs
) -> Callable:
    """
    Generic circuit breaker decorator for class methods.

    Args:
        service: Service type (yfinance, finviz, fred, news, http)
        use_fallback: Whether to use fallback strategies
        **breaker_kwargs: Additional arguments for the circuit breaker

    Example:
        class DataProvider:
            @circuit_breaker_method(service="yfinance")
            def get_stock_data(self, symbol: str) -> pd.DataFrame:
                return yf.download(symbol)
    """
    from maverick_core.resilience.circuit_breaker import (
        get_circuit_breaker,
        with_async_circuit_breaker,
        with_circuit_breaker,
    )

    # Map service names to circuit breaker names
    service_to_breaker = {
        "yfinance": "yfinance",
        "stock": "yfinance",
        "finviz": "finviz",
        "external_api": "external_api",
        "market": "finviz",
        "fred": "fred_api",
        "economic": "fred_api",
        "news": "news_api",
        "sentiment": "news_api",
        "http": "http_general",
        "openrouter": "openrouter",
        "tiingo": "tiingo",
        "exa": "exa",
    }

    breaker_name = service_to_breaker.get(service, "http_general")

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                breaker = get_circuit_breaker(breaker_name)
                if breaker:
                    return await breaker.call_async(func, *args, **kwargs)
                return await func(*args, **kwargs)

            return cast(Callable[..., T], async_wrapper)
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                breaker = get_circuit_breaker(breaker_name)
                if breaker:
                    return breaker.call_sync(func, *args, **kwargs)
                return func(*args, **kwargs)

            return cast(Callable[..., T], sync_wrapper)

    return decorator

