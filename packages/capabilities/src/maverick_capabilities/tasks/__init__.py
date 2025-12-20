"""
Async task queue module.

Provides async execution for long-running capabilities.
Supports in-memory (default) and Redis/Celery backends.
"""

from maverick_capabilities.tasks.protocols import (
    TaskQueue,
    TaskConfig,
    TaskResult,
    TaskStatus,
    TaskPriority,
)
from maverick_capabilities.tasks.memory_queue import MemoryTaskQueue
from maverick_capabilities.tasks.redis_queue import RedisTaskQueue
from maverick_capabilities.tasks.factory import (
    get_task_queue,
    set_task_queue,
    reset_task_queue,
)

__all__ = [
    # Protocols
    "TaskQueue",
    "TaskConfig",
    "TaskResult",
    "TaskStatus",
    "TaskPriority",
    # Implementations
    "MemoryTaskQueue",
    "RedisTaskQueue",
    # Factory
    "get_task_queue",
    "set_task_queue",
    "reset_task_queue",
]
