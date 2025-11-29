"""
Tests for the circuit breaker and resilience module.
"""

import asyncio
import time

import pytest

from maverick_core.exceptions import CircuitBreakerError, ExternalServiceError
from maverick_core.resilience import (
    CircuitBreakerConfig,
    CircuitBreakerMetrics,
    CircuitState,
    EnhancedCircuitBreaker,
    FailureDetectionStrategy,
    FallbackChain,
    FallbackStrategy,
    circuit_breaker,
    get_all_circuit_breakers,
    get_circuit_breaker,
    get_circuit_breaker_status,
    reset_all_circuit_breakers,
)


class TestCircuitBreakerMetrics:
    """Test circuit breaker metrics collection."""

    def test_metrics_initialization(self):
        metrics = CircuitBreakerMetrics(window_size=10)
        stats = metrics.get_stats()

        assert stats["total_calls"] == 0
        assert stats["success_rate"] == 1.0
        assert stats["failure_rate"] == 0.0
        assert stats["avg_duration"] == 0.0
        assert stats["timeout_rate"] == 0.0

    def test_record_successful_call(self):
        metrics = CircuitBreakerMetrics()

        metrics.record_call(True, 0.5)
        metrics.record_call(True, 1.0)

        stats = metrics.get_stats()
        assert stats["total_calls"] == 2
        assert stats["success_rate"] == 1.0
        assert stats["failure_rate"] == 0.0
        assert stats["avg_duration"] == 0.75

    def test_record_failed_call(self):
        metrics = CircuitBreakerMetrics()

        metrics.record_call(False, 2.0)
        metrics.record_call(True, 1.0)

        stats = metrics.get_stats()
        assert stats["total_calls"] == 2
        assert stats["success_rate"] == 0.5
        assert stats["failure_rate"] == 0.5
        assert stats["avg_duration"] == 1.5

    def test_window_cleanup(self):
        metrics = CircuitBreakerMetrics(window_size=1)  # 1 second window

        metrics.record_call(True, 0.5)
        time.sleep(1.1)  # Wait for window to expire
        metrics.record_call(True, 1.0)

        stats = metrics.get_stats()
        assert stats["total_calls"] == 1  # Old call should be removed


class TestEnhancedCircuitBreaker:
    """Test enhanced circuit breaker functionality."""

    def test_circuit_breaker_initialization(self):
        config = CircuitBreakerConfig(
            name="test_init",
            failure_threshold=3,
            recovery_timeout=5,
        )
        breaker = EnhancedCircuitBreaker(config)

        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed
        assert not breaker.is_open

    def test_consecutive_failures_opens_circuit(self):
        config = CircuitBreakerConfig(
            name="test_consecutive",
            failure_threshold=3,
            detection_strategy=FailureDetectionStrategy.CONSECUTIVE_FAILURES,
        )
        breaker = EnhancedCircuitBreaker(config)

        # Fail 3 times
        for _ in range(3):
            try:
                breaker.call_sync(lambda: 1 / 0)
            except ZeroDivisionError:
                pass

        assert breaker.state == CircuitState.OPEN
        assert breaker.is_open

    def test_circuit_breaker_blocks_calls_when_open(self):
        config = CircuitBreakerConfig(
            name="test_blocking",
            failure_threshold=1,
            recovery_timeout=60,
        )
        breaker = EnhancedCircuitBreaker(config)

        # Open the circuit
        try:
            breaker.call_sync(lambda: 1 / 0)
        except ZeroDivisionError:
            pass

        # Next call should be blocked
        with pytest.raises(CircuitBreakerError) as exc_info:
            breaker.call_sync(lambda: "success")

        assert "Circuit breaker open" in str(exc_info.value)

    def test_circuit_breaker_recovery(self):
        config = CircuitBreakerConfig(
            name="test_recovery",
            failure_threshold=1,
            recovery_timeout=1,  # 1 second
            success_threshold=2,
        )
        breaker = EnhancedCircuitBreaker(config)

        # Open the circuit
        try:
            breaker.call_sync(lambda: 1 / 0)
        except ZeroDivisionError:
            pass

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # First successful call should move to half-open
        result = breaker.call_sync(lambda: "success1")
        assert result == "success1"
        assert breaker.state == CircuitState.HALF_OPEN

        # Second successful call should close the circuit
        result = breaker.call_sync(lambda: "success2")
        assert result == "success2"
        assert breaker.state == CircuitState.CLOSED

    def test_manual_reset(self):
        config = CircuitBreakerConfig(
            name="test_reset",
            failure_threshold=1,
        )
        breaker = EnhancedCircuitBreaker(config)

        # Open the circuit
        try:
            breaker.call_sync(lambda: 1 / 0)
        except ZeroDivisionError:
            pass

        assert breaker.state == CircuitState.OPEN

        # Manual reset
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker._consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_async_circuit_breaker(self):
        config = CircuitBreakerConfig(
            name="test_async_cb",
            failure_threshold=2,
        )
        breaker = EnhancedCircuitBreaker(config)

        async def failing_func():
            raise ValueError("Async failure")

        async def success_func():
            return "async success"

        # Test failures
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call_async(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Test blocking
        with pytest.raises(CircuitBreakerError):
            await breaker.call_async(success_func)


class TestCircuitBreakerDecorator:
    """Test circuit breaker decorator functionality."""

    def test_sync_decorator(self):
        call_count = 0

        @circuit_breaker(name="test_sync_dec", failure_threshold=2)
        def test_func(should_fail=False):
            nonlocal call_count
            call_count += 1
            if should_fail:
                raise ValueError("Test failure")
            return "success"

        # Successful calls
        assert test_func() == "success"
        assert test_func() == "success"

        # Failures
        for _ in range(2):
            with pytest.raises(ValueError):
                test_func(should_fail=True)

        # Circuit should be open
        with pytest.raises(CircuitBreakerError):
            test_func()

    @pytest.mark.asyncio
    async def test_async_decorator(self):
        @circuit_breaker(name="test_async_dec", failure_threshold=1)
        async def async_test_func(should_fail=False):
            if should_fail:
                raise ValueError("Async test failure")
            return "async success"

        # Success
        result = await async_test_func()
        assert result == "async success"

        # Failure
        with pytest.raises(ValueError):
            await async_test_func(should_fail=True)

        # Circuit open
        with pytest.raises(CircuitBreakerError):
            await async_test_func()


class TestCircuitBreakerRegistry:
    """Test global circuit breaker registry."""

    def test_get_circuit_breaker(self):
        @circuit_breaker(name="registry_test_get")
        def test_func():
            return "test"

        # Call to initialize
        test_func()

        # Get from registry
        breaker = get_circuit_breaker("registry_test_get")
        assert breaker is not None
        assert breaker.config.name == "registry_test_get"

    def test_circuit_breaker_status(self):
        @circuit_breaker(name="status_test_cb")
        def test_func():
            return "test"

        test_func()

        status = get_circuit_breaker_status()
        assert "status_test_cb" in status
        assert status["status_test_cb"]["state"] == "closed"


class TestFallbackStrategy:
    """Test fallback strategy functionality."""

    def test_fallback_chain_execution(self):
        class MockFallback(FallbackStrategy):
            def __init__(self, return_value, should_fail=False):
                self._return_value = return_value
                self._should_fail = should_fail

            def execute(self, context):
                if self._should_fail:
                    raise Exception("Fallback failed")
                return self._return_value

            def can_execute(self, context):
                return True

        # Create chain with multiple fallbacks
        chain = FallbackChain([
            MockFallback("first", should_fail=True),
            MockFallback("second", should_fail=False),
            MockFallback("third", should_fail=False),
        ])

        result = chain.execute_sync({"key": "value"})
        assert result == "second"  # First fails, second succeeds

    def test_fallback_chain_all_fail(self):
        class FailingFallback(FallbackStrategy):
            def execute(self, context):
                raise Exception("Failed")

            def can_execute(self, context):
                return True

        chain = FallbackChain([
            FailingFallback(),
            FailingFallback(),
        ])

        with pytest.raises(Exception) as exc_info:
            chain.execute_sync({})

        assert "All fallbacks failed" in str(exc_info.value)

    def test_fallback_can_execute_filtering(self):
        class ConditionalFallback(FallbackStrategy):
            def __init__(self, required_key):
                self._required_key = required_key

            def execute(self, context):
                return f"executed_{self._required_key}"

            def can_execute(self, context):
                return self._required_key in context

        chain = FallbackChain([
            ConditionalFallback("missing"),
            ConditionalFallback("present"),
        ])

        result = chain.execute_sync({"present": True})
        assert result == "executed_present"

