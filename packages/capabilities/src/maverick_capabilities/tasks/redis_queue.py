"""
Redis-backed task queue.

Provides persistent async task execution with Redis as the backing store.
Supports task persistence, progress tracking, and webhooks.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, UTC, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from maverick_capabilities.tasks.protocols import (
    TaskConfig,
    TaskPriority,
    TaskResult,
    TaskStatus,
    TaskQueue,
)

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisTaskQueue(TaskQueue):
    """
    Redis-backed async task queue.

    Uses Redis for:
    - Task persistence and state management
    - Priority queues for task scheduling
    - Progress tracking with pub/sub
    - Webhook delivery

    Usage:
        >>> from redis.asyncio import Redis
        >>> redis = Redis.from_url("redis://localhost:6379")
        >>> queue = RedisTaskQueue(redis)
        >>> result = await queue.enqueue("analyze_stock", {"ticker": "AAPL"})
        >>> status = await queue.get_status(result.task_id)
    """

    # Redis key prefixes
    TASK_KEY_PREFIX = "maverick:task:"
    QUEUE_KEY_PREFIX = "maverick:queue:"
    PROGRESS_CHANNEL_PREFIX = "maverick:progress:"

    def __init__(
        self,
        redis: Redis,
        orchestrator: Any | None = None,
        default_queue: str = "default",
        worker_enabled: bool = True,
        max_concurrent: int = 5,
    ):
        """
        Initialize Redis task queue.

        Args:
            redis: Redis async client
            orchestrator: Orchestrator for executing capabilities
            default_queue: Default queue name
            worker_enabled: Whether to process tasks (False for read-only)
            max_concurrent: Maximum concurrent task executions
        """
        self._redis = redis
        self._orchestrator = orchestrator
        self._default_queue = default_queue
        self._worker_enabled = worker_enabled
        self._max_concurrent = max_concurrent
        self._running_tasks: dict[UUID, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._worker_task: asyncio.Task | None = None

    async def start_worker(self) -> None:
        """Start the background worker to process tasks."""
        if not self._worker_enabled:
            return

        if self._worker_task is not None:
            return

        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Redis task queue worker started")

    async def stop_worker(self) -> None:
        """Stop the background worker."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

        # Cancel running tasks
        for task in self._running_tasks.values():
            task.cancel()
        self._running_tasks.clear()

        logger.info("Redis task queue worker stopped")

    async def _worker_loop(self) -> None:
        """Main worker loop - polls queues and executes tasks."""
        queues = [
            f"{self.QUEUE_KEY_PREFIX}{self._default_queue}:critical",
            f"{self.QUEUE_KEY_PREFIX}{self._default_queue}:high",
            f"{self.QUEUE_KEY_PREFIX}{self._default_queue}:normal",
            f"{self.QUEUE_KEY_PREFIX}{self._default_queue}:low",
        ]

        while True:
            try:
                # Try to get a task from queues (priority order)
                result = await self._redis.blpop(queues, timeout=1)
                if result is None:
                    continue

                _, task_id_bytes = result
                task_id = UUID(task_id_bytes.decode("utf-8"))

                # Execute task with semaphore
                async with self._semaphore:
                    await self._execute_task(task_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)

    async def _execute_task(self, task_id: UUID) -> None:
        """Execute a single task."""
        task_result = await self.get_status(task_id)
        if task_result.status != TaskStatus.QUEUED:
            return

        # Update status to running
        task_result.status = TaskStatus.RUNNING
        task_result.started_at = datetime.now(UTC)
        await self._save_task(task_result)

        try:
            # Get task data
            task_data = await self._get_task_data(task_id)
            if not task_data:
                raise ValueError("Task data not found")

            # Execute via orchestrator
            if self._orchestrator is None:
                raise RuntimeError("No orchestrator configured")

            exec_result = await self._orchestrator.execute(
                task_result.capability_id,
                task_data.get("input_data", {}),
            )

            # Update with result
            task_result.status = TaskStatus.COMPLETED
            task_result.result = exec_result.result
            task_result.completed_at = datetime.now(UTC)
            task_result.progress_percent = 100

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            task_result.status = TaskStatus.FAILED
            task_result.error = str(e)
            task_result.error_type = type(e).__name__
            task_result.completed_at = datetime.now(UTC)

            # Check for retry
            task_data = await self._get_task_data(task_id)
            if task_data:
                config = task_data.get("config", {})
                max_retries = config.get("max_retries", 3)
                if task_result.retry_count < max_retries:
                    task_result.status = TaskStatus.RETRY
                    task_result.retry_count += 1
                    delay = config.get("retry_delay_seconds", 60)
                    task_result.next_retry_at = datetime.now(UTC) + timedelta(
                        seconds=delay
                    )
                    # Re-queue with delay
                    await self._schedule_retry(task_id, delay)

        await self._save_task(task_result)

        # Trigger webhook if configured
        task_data = await self._get_task_data(task_id)
        if task_data:
            webhook_url = task_data.get("config", {}).get("webhook_url")
            if webhook_url:
                asyncio.create_task(self._call_webhook(webhook_url, task_result))

    async def _schedule_retry(self, task_id: UUID, delay_seconds: float) -> None:
        """Schedule a task retry after delay."""
        await asyncio.sleep(delay_seconds)
        task_result = await self.get_status(task_id)
        if task_result.status == TaskStatus.RETRY:
            # Re-queue the task
            task_data = await self._get_task_data(task_id)
            if task_data:
                priority = task_data.get("config", {}).get("priority", "normal")
                queue_key = f"{self.QUEUE_KEY_PREFIX}{self._default_queue}:{priority}"
                await self._redis.rpush(queue_key, str(task_id))
                task_result.status = TaskStatus.QUEUED
                await self._save_task(task_result)

    async def _call_webhook(self, url: str, result: TaskResult) -> None:
        """Call webhook with task result."""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                await client.post(
                    url,
                    json=result.to_dict(),
                    timeout=30,
                )
        except Exception as e:
            logger.error(f"Webhook call failed: {e}")

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

        # Save task data
        task_data = {
            "capability_id": capability_id,
            "input_data": input_data,
            "config": {
                "queue": config.queue,
                "priority": config.priority.value,
                "timeout_seconds": config.timeout_seconds,
                "max_retries": config.max_retries,
                "retry_delay_seconds": config.retry_delay_seconds,
                "webhook_url": config.webhook_url,
            },
        }
        await self._save_task_data(task_id, task_data)
        await self._save_task(result)

        # Add to appropriate priority queue
        queue_key = f"{self.QUEUE_KEY_PREFIX}{config.queue}:{config.priority.value}"

        if config.countdown_seconds:
            # Delayed execution
            execute_at = datetime.now(UTC) + timedelta(seconds=config.countdown_seconds)
            await self._redis.zadd(
                f"{self.QUEUE_KEY_PREFIX}delayed",
                {str(task_id): execute_at.timestamp()},
            )
        elif config.eta:
            # Scheduled execution
            await self._redis.zadd(
                f"{self.QUEUE_KEY_PREFIX}delayed",
                {str(task_id): config.eta.timestamp()},
            )
        else:
            # Immediate execution
            await self._redis.rpush(queue_key, str(task_id))

        logger.debug(f"Task {task_id} queued for {capability_id}")
        return result

    async def get_status(self, task_id: UUID) -> TaskResult:
        """Get task status."""
        key = f"{self.TASK_KEY_PREFIX}{task_id}"
        data = await self._redis.hgetall(key)

        if not data:
            return TaskResult(
                task_id=task_id,
                capability_id="unknown",
                status=TaskStatus.FAILED,
                error="Task not found",
            )

        return self._deserialize_task_result(task_id, data)

    async def cancel(self, task_id: UUID) -> bool:
        """Cancel a pending or running task."""
        result = await self.get_status(task_id)

        if result.is_complete:
            return False

        # Cancel if running
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]

        # Update status
        result.status = TaskStatus.CANCELLED
        result.completed_at = datetime.now(UTC)
        await self._save_task(result)

        return True

    async def update_progress(
        self,
        task_id: UUID,
        percent: int,
        message: str | None = None,
    ) -> None:
        """Update task progress."""
        result = await self.get_status(task_id)
        result.progress_percent = min(100, max(0, percent))
        result.progress_message = message
        await self._save_task(result)

        # Publish progress update
        channel = f"{self.PROGRESS_CHANNEL_PREFIX}{task_id}"
        await self._redis.publish(
            channel,
            json.dumps({"percent": percent, "message": message}),
        )

    async def list_tasks(
        self,
        capability_id: str | None = None,
        status: TaskStatus | None = None,
        limit: int = 100,
    ) -> list[TaskResult]:
        """List tasks."""
        # Get all task keys
        pattern = f"{self.TASK_KEY_PREFIX}*"
        keys = []
        async for key in self._redis.scan_iter(pattern):
            keys.append(key)
            if len(keys) >= limit * 2:  # Get more to account for filtering
                break

        results = []
        for key in keys:
            if len(results) >= limit:
                break

            data = await self._redis.hgetall(key)
            if not data:
                continue

            # Extract task_id from key
            task_id_str = key.decode("utf-8").replace(self.TASK_KEY_PREFIX, "")
            try:
                task_id = UUID(task_id_str)
            except ValueError:
                continue

            result = self._deserialize_task_result(task_id, data)

            # Apply filters
            if capability_id and result.capability_id != capability_id:
                continue
            if status and result.status != status:
                continue

            results.append(result)

        return results

    async def cleanup(self, max_age_seconds: int = 3600) -> int:
        """Cleanup old completed tasks."""
        cutoff = datetime.now(UTC) - timedelta(seconds=max_age_seconds)
        removed = 0

        pattern = f"{self.TASK_KEY_PREFIX}*"
        async for key in self._redis.scan_iter(pattern):
            data = await self._redis.hgetall(key)
            if not data:
                continue

            status = data.get(b"status", b"").decode("utf-8")
            if status not in ("completed", "failed", "cancelled"):
                continue

            completed_at_str = data.get(b"completed_at", b"").decode("utf-8")
            if completed_at_str:
                try:
                    completed_at = datetime.fromisoformat(completed_at_str)
                    if completed_at < cutoff:
                        await self._redis.delete(key)
                        # Also delete task data
                        task_id_str = key.decode("utf-8").replace(
                            self.TASK_KEY_PREFIX, ""
                        )
                        await self._redis.delete(f"{self.TASK_KEY_PREFIX}data:{task_id_str}")
                        removed += 1
                except ValueError:
                    pass

        return removed

    # Helper methods

    async def _save_task(self, result: TaskResult) -> None:
        """Save task result to Redis."""
        key = f"{self.TASK_KEY_PREFIX}{result.task_id}"
        data = {
            "capability_id": result.capability_id,
            "status": result.status.value,
            "result": json.dumps(result.result) if result.result else "",
            "error": result.error or "",
            "error_type": result.error_type or "",
            "created_at": result.created_at.isoformat() if result.created_at else "",
            "started_at": result.started_at.isoformat() if result.started_at else "",
            "completed_at": result.completed_at.isoformat()
            if result.completed_at
            else "",
            "progress_percent": str(result.progress_percent),
            "progress_message": result.progress_message or "",
            "retry_count": str(result.retry_count),
            "max_retries": str(result.max_retries),
        }
        await self._redis.hset(key, mapping=data)
        # Set TTL for completed tasks (24 hours)
        if result.is_complete:
            await self._redis.expire(key, 86400)

    async def _save_task_data(self, task_id: UUID, data: dict) -> None:
        """Save task input data to Redis."""
        key = f"{self.TASK_KEY_PREFIX}data:{task_id}"
        await self._redis.set(key, json.dumps(data))
        await self._redis.expire(key, 86400)

    async def _get_task_data(self, task_id: UUID) -> dict | None:
        """Get task input data from Redis."""
        key = f"{self.TASK_KEY_PREFIX}data:{task_id}"
        data = await self._redis.get(key)
        if data:
            return json.loads(data)
        return None

    def _deserialize_task_result(
        self, task_id: UUID, data: dict[bytes, bytes]
    ) -> TaskResult:
        """Deserialize task result from Redis hash."""
        result_json = data.get(b"result", b"").decode("utf-8")
        created_at_str = data.get(b"created_at", b"").decode("utf-8")
        started_at_str = data.get(b"started_at", b"").decode("utf-8")
        completed_at_str = data.get(b"completed_at", b"").decode("utf-8")

        return TaskResult(
            task_id=task_id,
            capability_id=data.get(b"capability_id", b"").decode("utf-8"),
            status=TaskStatus(data.get(b"status", b"pending").decode("utf-8")),
            result=json.loads(result_json) if result_json else None,
            error=data.get(b"error", b"").decode("utf-8") or None,
            error_type=data.get(b"error_type", b"").decode("utf-8") or None,
            created_at=datetime.fromisoformat(created_at_str)
            if created_at_str
            else datetime.now(UTC),
            started_at=datetime.fromisoformat(started_at_str)
            if started_at_str
            else None,
            completed_at=datetime.fromisoformat(completed_at_str)
            if completed_at_str
            else None,
            progress_percent=int(data.get(b"progress_percent", b"0").decode("utf-8")),
            progress_message=data.get(b"progress_message", b"").decode("utf-8") or None,
            retry_count=int(data.get(b"retry_count", b"0").decode("utf-8")),
            max_retries=int(data.get(b"max_retries", b"3").decode("utf-8")),
        )
