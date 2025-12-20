"""
Task queue factory.

Provides factory functions for creating and accessing task queues.
"""

from __future__ import annotations

from maverick_capabilities.tasks.protocols import TaskQueue
from maverick_capabilities.tasks.memory_queue import MemoryTaskQueue


# Global task queue instance
_task_queue: TaskQueue | None = None


def get_task_queue() -> TaskQueue:
    """
    Get the global task queue instance.

    Creates a default MemoryTaskQueue if none exists.

    Returns:
        The global task queue instance
    """
    global _task_queue

    if _task_queue is None:
        _task_queue = MemoryTaskQueue()

    return _task_queue


def set_task_queue(queue: TaskQueue) -> None:
    """
    Set the global task queue instance.

    Args:
        queue: The task queue to use
    """
    global _task_queue
    _task_queue = queue


def reset_task_queue() -> None:
    """Reset the global task queue (for testing)."""
    global _task_queue
    _task_queue = None
