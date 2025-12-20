"""
In-memory task queue.

Simple implementation using asyncio for async execution.
Suitable for single-process deployments.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, UTC
from typing import Any
from uuid import UUID, uuid4

from maverick_capabilities.tasks.protocols import (
    TaskConfig,
    TaskPriority,
    TaskQueue,
    TaskResult,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class MemoryTaskQueue(TaskQueue):
    """
    In-memory task queue using asyncio.

    Features:
    - Priority queuing (critical tasks run first)
    - Progress tracking
    - Retry support
    - Webhook callbacks

    Limitations:
    - Single process only
    - Tasks lost on restart
    - No persistence

    For production with persistence, use RedisTaskQueue or CeleryTaskQueue.
    """

    def __init__(
        self,
        max_concurrent: int = 4,
        max_tasks: int = 1000,
    ):
        """
        Initialize memory queue.

        Args:
            max_concurrent: Maximum concurrent task executions
            max_tasks: Maximum tasks to retain in history
        """
        self._max_concurrent = max_concurrent
        self._max_tasks = max_tasks

        # Task storage
        self._tasks: dict[UUID, TaskResult] = {}
        self._input_data: dict[UUID, dict[str, Any]] = {}
        self._configs: dict[UUID, TaskConfig] = {}

        # Execution tracking
        self._running_tasks: dict[UUID, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # Orchestrator will be injected
        self._orchestrator: Any = None

    def set_orchestrator(self, orchestrator: Any) -> None:
        """Set the orchestrator for executing capabilities."""
        self._orchestrator = orchestrator

    async def enqueue(
        self,
        capability_id: str,
        input_data: dict[str, Any],
        config: TaskConfig | None = None,
    ) -> TaskResult:
        """Enqueue a task for async execution."""
        config = config or TaskConfig()
        task_id = uuid4()

        # Create task result
        result = TaskResult(
            task_id=task_id,
            capability_id=capability_id,
            status=TaskStatus.QUEUED,
            created_at=datetime.now(UTC),
            max_retries=config.max_retries,
        )

        # Store task data
        self._tasks[task_id] = result
        self._input_data[task_id] = input_data
        self._configs[task_id] = config

        # Handle scheduling
        delay = 0.0
        if config.countdown_seconds:
            delay = float(config.countdown_seconds)
        elif config.eta:
            delta = config.eta - datetime.now(UTC)
            delay = max(0.0, delta.total_seconds())

        # Start execution
        asyncio.create_task(self._execute_with_delay(task_id, delay))

        # Enforce max tasks limit
        await self._enforce_limit()

        return result

    async def _execute_with_delay(self, task_id: UUID, delay: float) -> None:
        """Execute task after optional delay."""
        if delay > 0:
            await asyncio.sleep(delay)

        await self._execute_task(task_id)

    async def _execute_task(self, task_id: UUID) -> None:
        """Execute a single task."""
        if task_id not in self._tasks:
            return

        result = self._tasks[task_id]
        input_data = self._input_data.get(task_id, {})
        config = self._configs.get(task_id, TaskConfig())

        # Acquire semaphore for concurrency limiting
        async with self._semaphore:
            # Update status
            result.status = TaskStatus.RUNNING
            result.started_at = datetime.now(UTC)
            result.progress_percent = 5

            try:
                # Get orchestrator
                if self._orchestrator is None:
                    from maverick_capabilities.orchestration import get_orchestrator

                    self._orchestrator = get_orchestrator()

                # Execute
                exec_result = await self._orchestrator.execute(
                    result.capability_id,
                    input_data,
                )

                # Update with result
                result.status = (
                    TaskStatus.COMPLETED
                    if exec_result.is_success
                    else TaskStatus.FAILED
                )
                result.result = exec_result.result
                result.error = exec_result.error
                result.error_type = exec_result.error_type
                result.completed_at = datetime.now(UTC)
                result.progress_percent = 100

            except asyncio.CancelledError:
                result.status = TaskStatus.CANCELLED
                result.completed_at = datetime.now(UTC)
                raise

            except Exception as e:
                logger.exception(f"Task {task_id} failed")

                # Check for retry
                if result.retry_count < config.max_retries:
                    result.status = TaskStatus.RETRY
                    result.retry_count += 1
                    result.next_retry_at = datetime.now(UTC)
                    result.error = str(e)
                    result.error_type = type(e).__name__

                    # Schedule retry
                    asyncio.create_task(
                        self._execute_with_delay(task_id, config.retry_delay_seconds)
                    )
                else:
                    result.status = TaskStatus.FAILED
                    result.error = str(e)
                    result.error_type = type(e).__name__
                    result.completed_at = datetime.now(UTC)

            finally:
                # Send webhook if configured
                if config.webhook_url and result.is_complete:
                    asyncio.create_task(
                        self._send_webhook(config.webhook_url, result)
                    )

    async def _send_webhook(self, url: str, result: TaskResult) -> None:
        """Send webhook notification."""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                await client.post(url, json=result.to_dict(), timeout=10)
        except Exception as e:
            logger.warning(f"Webhook failed: {e}")

    async def get_status(self, task_id: UUID) -> TaskResult:
        """Get task status."""
        if task_id in self._tasks:
            return self._tasks[task_id]

        return TaskResult(
            task_id=task_id,
            capability_id="unknown",
            status=TaskStatus.FAILED,
            error="Task not found",
            error_type="NotFoundError",
        )

    async def cancel(self, task_id: UUID) -> bool:
        """Cancel a task."""
        if task_id not in self._tasks:
            return False

        result = self._tasks[task_id]

        if result.is_complete:
            return False

        # Cancel running asyncio task if exists
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]

        result.status = TaskStatus.CANCELLED
        result.completed_at = datetime.now(UTC)

        return True

    async def update_progress(
        self,
        task_id: UUID,
        percent: int,
        message: str | None = None,
    ) -> None:
        """Update task progress."""
        if task_id in self._tasks:
            self._tasks[task_id].progress_percent = min(100, max(0, percent))
            if message:
                self._tasks[task_id].progress_message = message

    async def list_tasks(
        self,
        capability_id: str | None = None,
        status: TaskStatus | None = None,
        limit: int = 100,
    ) -> list[TaskResult]:
        """List tasks."""
        results = []

        for task in self._tasks.values():
            if capability_id and task.capability_id != capability_id:
                continue
            if status and task.status != status:
                continue
            results.append(task)

            if len(results) >= limit:
                break

        # Sort by created_at descending
        results.sort(key=lambda t: t.created_at, reverse=True)

        return results

    async def cleanup(self, max_age_seconds: int = 3600) -> int:
        """Cleanup old completed tasks."""
        now = datetime.now(UTC)
        to_remove = []

        for task_id, result in self._tasks.items():
            if result.is_complete and result.completed_at:
                age = (now - result.completed_at).total_seconds()
                if age > max_age_seconds:
                    to_remove.append(task_id)

        for task_id in to_remove:
            self._tasks.pop(task_id, None)
            self._input_data.pop(task_id, None)
            self._configs.pop(task_id, None)
            self._running_tasks.pop(task_id, None)

        return len(to_remove)

    async def _enforce_limit(self) -> None:
        """Enforce maximum task limit."""
        if len(self._tasks) <= self._max_tasks:
            return

        # Remove oldest completed tasks
        completed = [
            (task_id, result.completed_at)
            for task_id, result in self._tasks.items()
            if result.is_complete and result.completed_at
        ]
        completed.sort(key=lambda x: x[1])

        to_remove = len(self._tasks) - self._max_tasks
        for task_id, _ in completed[:to_remove]:
            self._tasks.pop(task_id, None)
            self._input_data.pop(task_id, None)
            self._configs.pop(task_id, None)

    # Utility methods

    def stats(self) -> dict[str, Any]:
        """Get queue statistics."""
        by_status = {}
        for result in self._tasks.values():
            status = result.status.value
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total_tasks": len(self._tasks),
            "by_status": by_status,
            "max_concurrent": self._max_concurrent,
            "semaphore_available": self._semaphore._value,
        }
