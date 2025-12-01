"""
Error Handling Decorators.

Provides consistent error handling patterns across the codebase.
Replaces broad `except Exception` patterns with proper exception handling.
"""

import asyncio
import functools
import logging
from typing import Any, Callable, ParamSpec, Type, TypeVar

from maverick_core.exceptions import (
    AgentError,
    CacheError,
    DataProviderError,
    DatabaseError,
    MaverickError,
    StockDataError,
)

P = ParamSpec("P")
T = TypeVar("T")

logger = logging.getLogger(__name__)


def handle_errors(
    *catch_exceptions: Type[Exception],
    reraise_as: Type[MaverickError] | None = None,
    default_return: Any = None,
    log_level: int = logging.ERROR,
    include_traceback: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for consistent error handling in synchronous functions.

    Args:
        catch_exceptions: Exception types to catch. Defaults to (Exception,).
        reraise_as: MaverickError subclass to re-raise as. If None, returns default_return.
        default_return: Value to return on error if reraise_as is None.
        log_level: Logging level for errors.
        include_traceback: Whether to include traceback in logs.

    Usage:
        @handle_errors(ValueError, TypeError, reraise_as=ValidationError)
        def validate_input(data):
            ...

        @handle_errors(default_return=[])
        def get_items():
            ...
    """
    if not catch_exceptions:
        catch_exceptions = (Exception,)

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except MaverickError:
                # Don't wrap MaverickErrors - let them propagate
                raise
            except catch_exceptions as e:
                _log_error(func, e, log_level, include_traceback)
                if reraise_as:
                    raise reraise_as(
                        message=f"Error in {func.__name__}: {e}",
                        details={"original_error": str(e), "error_type": type(e).__name__},
                    ) from e
                return default_return

        return wrapper

    return decorator


def handle_async_errors(
    *catch_exceptions: Type[Exception],
    reraise_as: Type[MaverickError] | None = None,
    default_return: Any = None,
    log_level: int = logging.ERROR,
    include_traceback: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for consistent error handling in async functions.

    Args:
        catch_exceptions: Exception types to catch. Defaults to (Exception,).
        reraise_as: MaverickError subclass to re-raise as. If None, returns default_return.
        default_return: Value to return on error if reraise_as is None.
        log_level: Logging level for errors.
        include_traceback: Whether to include traceback in logs.

    Usage:
        @handle_async_errors(aiohttp.ClientError, reraise_as=DataProviderError)
        async def fetch_data():
            ...
    """
    if not catch_exceptions:
        catch_exceptions = (Exception,)

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except MaverickError:
                # Don't wrap MaverickErrors - let them propagate
                raise
            except catch_exceptions as e:
                _log_error(func, e, log_level, include_traceback)
                if reraise_as:
                    raise reraise_as(
                        message=f"Error in {func.__name__}: {e}",
                        details={"original_error": str(e), "error_type": type(e).__name__},
                    ) from e
                return default_return

        return wrapper

    return decorator


def handle_provider_errors(
    provider_name: str | None = None,
    reraise: bool = True,
    default_return: Any = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Specialized decorator for data provider error handling.

    Catches common provider errors (network, timeout, parsing) and converts
    them to DataProviderError.

    Args:
        provider_name: Name of the provider (e.g., "yfinance", "tiingo").
        reraise: Whether to re-raise as DataProviderError. If False, returns default.
        default_return: Value to return if reraise is False.

    Usage:
        @handle_provider_errors("yfinance")
        async def fetch_stock_data(symbol: str):
            ...
    """
    import aiohttp
    import httpx
    from requests.exceptions import RequestException

    provider_exceptions = (
        RequestException,
        aiohttp.ClientError,
        httpx.HTTPError,
        TimeoutError,
        asyncio.TimeoutError,
        ConnectionError,
        ValueError,  # Often raised for invalid data parsing
    )

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        name = provider_name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except MaverickError:
                raise
            except provider_exceptions as e:
                logger.error(f"Provider error in {name}: {e}", exc_info=True)
                if reraise:
                    raise DataProviderError(
                        provider=name,
                        message=f"Failed to fetch data from {name}: {e}",
                        details={"original_error": str(e)},
                    ) from e
                return default_return

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except MaverickError:
                raise
            except provider_exceptions as e:
                logger.error(f"Provider error in {name}: {e}", exc_info=True)
                if reraise:
                    raise DataProviderError(
                        provider=name,
                        message=f"Failed to fetch data from {name}: {e}",
                        details={"original_error": str(e)},
                    ) from e
                return default_return

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def handle_repository_errors(
    operation: str | None = None,
    reraise: bool = True,
    default_return: Any = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Specialized decorator for repository/database error handling.

    Args:
        operation: Operation name (e.g., "get", "create", "update").
        reraise: Whether to re-raise as DatabaseError.
        default_return: Value to return if reraise is False.

    Usage:
        @handle_repository_errors("get")
        async def get_stock(self, symbol: str):
            ...
    """
    from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

    db_exceptions = (
        SQLAlchemyError,
        IntegrityError,
        OperationalError,
        ConnectionError,
    )

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        op_name = operation or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except MaverickError:
                raise
            except db_exceptions as e:
                logger.error(f"Database error in {op_name}: {e}", exc_info=True)
                if reraise:
                    raise DatabaseError(
                        operation=op_name,
                        message=f"Database operation '{op_name}' failed: {e}",
                        details={"original_error": str(e)},
                    ) from e
                return default_return

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except MaverickError:
                raise
            except db_exceptions as e:
                logger.error(f"Database error in {op_name}: {e}", exc_info=True)
                if reraise:
                    raise DatabaseError(
                        operation=op_name,
                        message=f"Database operation '{op_name}' failed: {e}",
                        details={"original_error": str(e)},
                    ) from e
                return default_return

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def handle_service_errors(
    service_name: str | None = None,
    reraise_as: Type[MaverickError] = StockDataError,
    default_return: Any = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Specialized decorator for service layer error handling.

    Args:
        service_name: Name of the service for logging.
        reraise_as: Exception type to re-raise as.
        default_return: Value to return if not re-raising.

    Usage:
        @handle_service_errors("ScreeningService")
        async def get_recommendations(self):
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        name = service_name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except MaverickError:
                raise
            except Exception as e:
                logger.error(f"Service error in {name}: {e}", exc_info=True)
                raise reraise_as(
                    message=f"Service '{name}' error: {e}",
                    details={"original_error": str(e), "service": name},
                ) from e

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except MaverickError:
                raise
            except Exception as e:
                logger.error(f"Service error in {name}: {e}", exc_info=True)
                raise reraise_as(
                    message=f"Service '{name}' error: {e}",
                    details={"original_error": str(e), "service": name},
                ) from e

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def safe_execute(
    default: T = None,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    log_errors: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Execute a function safely, returning a default value on error.

    Use this for non-critical operations where failure is acceptable.

    Args:
        default: Value to return on error.
        exceptions: Exception types to catch.
        log_errors: Whether to log errors.

    Usage:
        @safe_execute(default={})
        def get_optional_metadata():
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_errors:
                    logger.warning(f"Safe execute caught error in {func.__name__}: {e}")
                return default

        return wrapper

    return decorator


def safe_execute_async(
    default: T = None,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    log_errors: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Execute an async function safely, returning a default value on error.

    Use this for non-critical async operations where failure is acceptable.

    Args:
        default: Value to return on error.
        exceptions: Exception types to catch.
        log_errors: Whether to log errors.

    Usage:
        @safe_execute_async(default=[])
        async def get_optional_data():
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                if log_errors:
                    logger.warning(f"Safe execute caught error in {func.__name__}: {e}")
                return default

        return wrapper

    return decorator


def _log_error(
    func: Callable,
    error: Exception,
    level: int,
    include_traceback: bool,
) -> None:
    """Log an error with consistent formatting."""
    msg = f"Error in {func.__module__}.{func.__name__}: {error}"
    logger.log(level, msg, exc_info=include_traceback)
