"""
Service Orchestrator Implementation.

This orchestrator directly calls service methods without any
intermediate agent framework. It's the simplest implementation
and suitable for most use cases.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from datetime import datetime, UTC
from typing import Any, AsyncIterator
from uuid import UUID

from maverick_capabilities.models import Capability, ExecutionMode
from maverick_capabilities.registry import get_registry
from maverick_capabilities.orchestration.protocols import (
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
    Orchestrator,
)

logger = logging.getLogger(__name__)


class ServiceOrchestrator(Orchestrator):
    """
    Orchestrator that directly calls service methods.

    This is the default orchestrator that executes capabilities
    by calling the configured service method directly.

    Features:
    - Timeout handling
    - Error wrapping
    - Async execution with in-memory tracking
    - Progress updates for streaming
    """

    def __init__(
        self,
        service_factory: dict[str, Any] | None = None,
    ):
        """
        Initialize the service orchestrator.

        Args:
            service_factory: Map of service class names to instances.
                           If not provided, will attempt to instantiate services.
        """
        self._service_factory = service_factory or {}
        self._registry = get_registry()

        # Track async executions (in-memory for simplicity)
        self._executions: dict[UUID, ExecutionResult] = {}
        self._tasks: dict[UUID, asyncio.Task] = {}

    def register_service(self, name: str, instance_or_factory: Any) -> None:
        """
        Register a service instance or factory.
        
        Args:
            name: Service class name
            instance_or_factory: Either a service instance or a callable
                that returns a service instance (for per-request creation)
        """
        self._service_factory[name] = instance_or_factory

    def _get_service(self, capability: Capability) -> Any:
        """Get or create service instance for a capability."""
        service_name = capability.service_class.__name__

        if service_name in self._service_factory:
            instance_or_factory = self._service_factory[service_name]
            # If it's a callable (factory function), call it to get instance
            if callable(instance_or_factory) and not isinstance(instance_or_factory, type):
                # Check if it looks like a factory (not a class or instance)
                if hasattr(instance_or_factory, '__call__') and not hasattr(instance_or_factory, '__self__'):
                    try:
                        return instance_or_factory()
                    except TypeError:
                        # Not a factory, treat as instance
                        return instance_or_factory
            return instance_or_factory

        # Try to instantiate (might fail if service requires dependencies)
        try:
            instance = capability.service_class()
            self._service_factory[service_name] = instance
            return instance
        except Exception as e:
            raise RuntimeError(
                f"Cannot instantiate service {service_name}: {e}. "
                "Register it via register_service() or service_factory."
            ) from e

    async def _cleanup_service(self, service: Any) -> None:
        """
        Cleanup a factory-created service after use.
        
        Closes any database sessions held by the service's repository.
        """
        try:
            # Check if service has a repository with a session to close
            repository = getattr(service, "_repository", None)
            if repository is None:
                repository = getattr(service, "repository", None)
            
            if repository is not None:
                session = getattr(repository, "_session", None)
                if session is not None and hasattr(session, "close"):
                    await session.close()
        except Exception as e:
            logger.warning(f"Error cleaning up service: {e}")

    async def execute(
        self,
        capability_id: str,
        input_data: dict[str, Any],
        context: ExecutionContext | None = None,
    ) -> ExecutionResult:
        """Execute a capability synchronously."""
        context = context or ExecutionContext(capability_id=capability_id)
        context.capability_id = capability_id

        # Get capability
        capability = self._registry.get(capability_id)
        if not capability:
            return ExecutionResult(
                execution_id=context.execution_id,
                capability_id=capability_id,
                status=ExecutionStatus.FAILED,
                error=f"Unknown capability: {capability_id}",
                error_type="NotFoundError",
                started_at=context.started_at,
                completed_at=datetime.now(UTC),
            )

        # Check if deprecated
        if capability.deprecated:
            logger.warning(
                f"Executing deprecated capability: {capability_id}. "
                f"{capability.deprecation_message or ''}"
            )

        started_at = datetime.now(UTC)
        service = None
        is_factory_created = False

        try:
            # Get service instance
            if context.service_instance:
                service = context.service_instance
            else:
                service = self._get_service(capability)
                # Check if this was created by a factory (needs cleanup)
                service_name = capability.service_class.__name__
                if service_name in self._service_factory:
                    instance_or_factory = self._service_factory[service_name]
                    is_factory_created = (
                        callable(instance_or_factory) 
                        and not isinstance(instance_or_factory, type)
                    )

            # Get method
            method = capability.get_method(service)

            # Inject user_id from context if method expects it and not already provided
            if context.user_id and "user_id" not in input_data:
                sig = inspect.signature(method)
                if "user_id" in sig.parameters:
                    input_data = {**input_data, "user_id": context.user_id}

            # Execute with timeout
            timeout = capability.execution.timeout_seconds

            if asyncio.iscoroutinefunction(method):
                result = await asyncio.wait_for(
                    method(**input_data),
                    timeout=timeout,
                )
            else:
                # Run sync method in thread pool
                result = await asyncio.wait_for(
                    asyncio.to_thread(method, **input_data),
                    timeout=timeout,
                )

            completed_at = datetime.now(UTC)

            return ExecutionResult(
                execution_id=context.execution_id,
                capability_id=capability_id,
                status=ExecutionStatus.COMPLETED,
                result=result,
                started_at=started_at,
                completed_at=completed_at,
                progress_percent=100,
            )

        except asyncio.TimeoutError:
            return ExecutionResult(
                execution_id=context.execution_id,
                capability_id=capability_id,
                status=ExecutionStatus.TIMEOUT,
                error=f"Execution timed out after {capability.execution.timeout_seconds}s",
                error_type="TimeoutError",
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )

        except Exception as e:
            logger.exception(f"Error executing capability {capability_id}")
            return ExecutionResult(
                execution_id=context.execution_id,
                capability_id=capability_id,
                status=ExecutionStatus.FAILED,
                error=str(e),
                error_type=type(e).__name__,
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )

        finally:
            # Cleanup factory-created services that may hold resources
            if is_factory_created and service is not None:
                await self._cleanup_service(service)

    async def execute_async(
        self,
        capability_id: str,
        input_data: dict[str, Any],
        context: ExecutionContext | None = None,
    ) -> ExecutionResult:
        """Start async execution."""
        context = context or ExecutionContext(capability_id=capability_id)
        context.capability_id = capability_id

        # Create initial pending result
        result = ExecutionResult(
            execution_id=context.execution_id,
            capability_id=capability_id,
            status=ExecutionStatus.QUEUED,
            started_at=datetime.now(UTC),
            progress_percent=0,
        )
        self._executions[context.execution_id] = result

        # Start background task
        task = asyncio.create_task(
            self._run_async(capability_id, input_data, context)
        )
        self._tasks[context.execution_id] = task

        return result

    async def _run_async(
        self,
        capability_id: str,
        input_data: dict[str, Any],
        context: ExecutionContext,
    ) -> None:
        """Background execution handler."""
        # Update status to running
        self._executions[context.execution_id].status = ExecutionStatus.RUNNING
        self._executions[context.execution_id].progress_percent = 10

        # Execute
        result = await self.execute(capability_id, input_data, context)

        # Update stored result
        self._executions[context.execution_id] = result

        # Call webhook if configured
        if context.webhook_url:
            await self._send_webhook(context.webhook_url, result)

        # Call callback if configured
        if context.callback:
            try:
                context.callback(result)
            except Exception as e:
                logger.warning(f"Callback failed: {e}")

        # Cleanup task reference
        self._tasks.pop(context.execution_id, None)

    async def _send_webhook(self, url: str, result: ExecutionResult) -> None:
        """Send webhook notification."""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                await client.post(
                    url,
                    json=result.to_dict(),
                    timeout=10,
                )
        except Exception as e:
            logger.warning(f"Failed to send webhook: {e}")

    async def get_status(self, execution_id: UUID) -> ExecutionResult:
        """Get status of an async execution."""
        if execution_id in self._executions:
            return self._executions[execution_id]

        return ExecutionResult(
            execution_id=execution_id,
            capability_id="unknown",
            status=ExecutionStatus.FAILED,
            error="Execution not found",
            error_type="NotFoundError",
        )

    async def cancel(self, execution_id: UUID) -> bool:
        """Cancel a running execution."""
        if execution_id not in self._tasks:
            return False

        task = self._tasks[execution_id]

        if task.done():
            return False

        task.cancel()

        # Update status
        if execution_id in self._executions:
            self._executions[execution_id].status = ExecutionStatus.CANCELLED
            self._executions[execution_id].completed_at = datetime.now(UTC)

        # Cleanup
        self._tasks.pop(execution_id, None)

        return True

    async def stream(
        self,
        capability_id: str,
        input_data: dict[str, Any],
        context: ExecutionContext | None = None,
    ) -> AsyncIterator[ExecutionResult]:
        """
        Stream execution results.

        For non-streaming capabilities, this yields a single result.
        For streaming capabilities, this would yield progressive updates.
        """
        context = context or ExecutionContext(capability_id=capability_id)

        capability = self._registry.get(capability_id)

        if not capability or capability.execution.mode != ExecutionMode.STREAMING:
            # Non-streaming: just execute and yield result
            result = await self.execute(capability_id, input_data, context)
            yield result
            return

        # Streaming execution - yield progress updates
        # This is a simplified implementation; real streaming would
        # depend on the service supporting it

        yield ExecutionResult(
            execution_id=context.execution_id,
            capability_id=capability_id,
            status=ExecutionStatus.RUNNING,
            progress_percent=0,
            progress_message="Starting...",
        )

        result = await self.execute(capability_id, input_data, context)

        yield result

    # Utility methods

    def list_running(self) -> list[ExecutionResult]:
        """List currently running executions."""
        return [
            result
            for result in self._executions.values()
            if result.status in (ExecutionStatus.QUEUED, ExecutionStatus.RUNNING)
        ]

    def cleanup_completed(self, max_age_seconds: int = 3600) -> int:
        """
        Cleanup completed executions older than max_age_seconds.

        Returns the number of executions cleaned up.
        """
        now = datetime.now(UTC)
        to_remove = []

        for exec_id, result in self._executions.items():
            if result.is_complete and result.completed_at:
                age = (now - result.completed_at).total_seconds()
                if age > max_age_seconds:
                    to_remove.append(exec_id)

        for exec_id in to_remove:
            self._executions.pop(exec_id, None)
            self._tasks.pop(exec_id, None)

        return len(to_remove)
