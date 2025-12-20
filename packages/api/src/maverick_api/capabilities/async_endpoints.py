"""
Async endpoint generation for long-running operations.

Creates endpoints that use the Redis task queue for capabilities
with ExecutionMode.ASYNC, returning task IDs for status polling.
"""

from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from maverick_api.dependencies import get_current_user, get_request_id
from maverick_schemas.auth import AuthenticatedUser
from maverick_schemas.responses import APIResponse, ResponseMeta

logger = logging.getLogger(__name__)


class AsyncTaskResponse(BaseModel):
    """Response for async task submission."""

    task_id: str = Field(description="Unique task identifier")
    status: str = Field(description="Task status: queued, running, completed, failed")
    status_url: str = Field(description="URL to check task status")
    message: str = Field(default="Task submitted successfully")


class TaskStatusResponse(BaseModel):
    """Response for task status check."""

    task_id: str
    capability_id: str
    status: str
    progress_percent: int = Field(ge=0, le=100)
    progress_message: str | None = None
    result: Any | None = None
    error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


# Global task queue instance (set during app startup)
_task_queue = None


def set_task_queue(queue: Any) -> None:
    """Set the global task queue instance."""
    global _task_queue
    _task_queue = queue


def get_task_queue() -> Any:
    """Get the global task queue instance."""
    if _task_queue is None:
        raise RuntimeError("Task queue not initialized. Call set_task_queue() first.")
    return _task_queue


def create_async_endpoints(
    capability_ids: list[str] | None = None,
    groups: list[str] | None = None,
    prefix: str = "/tasks",
    tags: list[str] | None = None,
) -> APIRouter:
    """
    Create async endpoints for long-running capabilities.

    For each async capability, creates:
    - POST /tasks/{capability_id} - Submit task
    - GET /tasks/{task_id}/status - Check status
    - DELETE /tasks/{task_id} - Cancel task

    Args:
        capability_ids: Specific capability IDs to register
        groups: Capability groups to register
        prefix: URL prefix for task endpoints
        tags: OpenAPI tags

    Returns:
        FastAPI router with async task endpoints

    Example:
        >>> router = create_async_endpoints(
        ...     capability_ids=["comprehensive_research", "run_backtest"],
        ...     prefix="/tasks",
        ...     tags=["Async Tasks"],
        ... )
    """
    from maverick_capabilities import get_registry
    from maverick_capabilities.models import ExecutionMode

    router = APIRouter(prefix=prefix, tags=tags or ["Async Tasks"])
    registry = get_registry()

    # Collect capabilities to process
    caps_to_process = []

    if capability_ids:
        for cap_id in capability_ids:
            cap = registry.get(cap_id)
            if cap:
                caps_to_process.append(cap)

    if groups:
        all_caps = registry.list_all()
        for cap in all_caps:
            if cap.group.value in groups and cap not in caps_to_process:
                caps_to_process.append(cap)

    # Filter to only async capabilities (or all if none specified)
    async_caps = [
        cap for cap in caps_to_process if cap.execution.mode == ExecutionMode.ASYNC
    ]

    # If no specific caps requested, use all that are marked async
    if not async_caps and not capability_ids and not groups:
        async_caps = [
            cap
            for cap in registry.list_all()
            if cap.execution.mode == ExecutionMode.ASYNC
        ]

    # Generate submit endpoints for each async capability
    for cap in async_caps:
        _add_submit_endpoint(router, cap)

    # Add generic status and cancel endpoints
    @router.get(
        "/{task_id}/status",
        response_model=APIResponse[TaskStatusResponse],
        summary="Get Task Status",
        description="Check the status of an async task.",
    )
    async def get_task_status(
        task_id: str,
        request_id: str = Depends(get_request_id),
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> APIResponse[TaskStatusResponse]:
        """Get the status of an async task."""
        try:
            queue = get_task_queue()
            task_uuid = UUID(task_id)
            result = await queue.get_status(task_uuid)

            return APIResponse(
                data=TaskStatusResponse(
                    task_id=task_id,
                    capability_id=result.capability_id,
                    status=result.status.value,
                    progress_percent=result.progress_percent,
                    progress_message=result.progress_message,
                    result=result.result if result.is_complete else None,
                    error=result.error,
                    created_at=result.created_at or datetime.now(UTC),
                    started_at=result.started_at,
                    completed_at=result.completed_at,
                ),
                meta=ResponseMeta(
                    request_id=request_id,
                    timestamp=datetime.now(UTC),
                ),
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid task ID format")
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete(
        "/{task_id}",
        response_model=APIResponse[dict],
        summary="Cancel Task",
        description="Cancel a pending or running task.",
    )
    async def cancel_task(
        task_id: str,
        request_id: str = Depends(get_request_id),
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> APIResponse[dict]:
        """Cancel an async task."""
        try:
            queue = get_task_queue()
            task_uuid = UUID(task_id)
            cancelled = await queue.cancel(task_uuid)

            if cancelled:
                return APIResponse(
                    data={"task_id": task_id, "cancelled": True},
                    meta=ResponseMeta(
                        request_id=request_id,
                        timestamp=datetime.now(UTC),
                    ),
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Task cannot be cancelled (already completed or not found)",
                )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid task ID format")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error cancelling task: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get(
        "",
        response_model=APIResponse[list[TaskStatusResponse]],
        summary="List Tasks",
        description="List recent tasks with optional filtering.",
    )
    async def list_tasks(
        capability_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
        request_id: str = Depends(get_request_id),
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> APIResponse[list[TaskStatusResponse]]:
        """List recent tasks."""
        try:
            from maverick_capabilities.tasks.protocols import TaskStatus

            queue = get_task_queue()
            status_enum = TaskStatus(status) if status else None

            results = await queue.list_tasks(
                capability_id=capability_id,
                status=status_enum,
                limit=limit,
            )

            return APIResponse(
                data=[
                    TaskStatusResponse(
                        task_id=str(r.task_id),
                        capability_id=r.capability_id,
                        status=r.status.value,
                        progress_percent=r.progress_percent,
                        progress_message=r.progress_message,
                        result=r.result if r.is_complete else None,
                        error=r.error,
                        created_at=r.created_at or datetime.now(UTC),
                        started_at=r.started_at,
                        completed_at=r.completed_at,
                    )
                    for r in results
                ],
                meta=ResponseMeta(
                    request_id=request_id,
                    timestamp=datetime.now(UTC),
                ),
            )
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    logger.info(f"Created async endpoints for {len(async_caps)} capabilities")
    return router


def _add_submit_endpoint(router: APIRouter, capability: Any) -> None:
    """Add a submit endpoint for an async capability."""
    from maverick_capabilities.tasks.protocols import TaskConfig, TaskPriority

    cap_id = capability.id

    @router.post(
        f"/{cap_id}",
        response_model=APIResponse[AsyncTaskResponse],
        summary=f"Submit: {capability.title}",
        description=capability.description,
    )
    async def submit_task(
        request_id: str = Depends(get_request_id),
        user: AuthenticatedUser = Depends(get_current_user),
        **kwargs: Any,
    ) -> APIResponse[AsyncTaskResponse]:
        """Submit an async task."""
        try:
            queue = get_task_queue()

            # Create task config from capability settings
            config = TaskConfig(
                queue=capability.execution.queue,
                priority=TaskPriority.NORMAL,
                timeout_seconds=capability.execution.timeout_seconds,
                max_retries=capability.execution.max_retries,
            )

            # Enqueue the task
            result = await queue.enqueue(
                capability_id=cap_id,
                input_data=kwargs,
                config=config,
            )

            return APIResponse(
                data=AsyncTaskResponse(
                    task_id=str(result.task_id),
                    status=result.status.value,
                    status_url=f"/api/v1/tasks/{result.task_id}/status",
                    message=f"Task submitted for {capability.title}",
                ),
                meta=ResponseMeta(
                    request_id=request_id,
                    timestamp=datetime.now(UTC),
                ),
            )
        except Exception as e:
            logger.error(f"Error submitting task for {cap_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Override function name for OpenAPI
    submit_task.__name__ = f"submit_{cap_id}"


# Convenience function to mark capabilities for async execution
def mark_async_capabilities() -> list[str]:
    """
    Return list of capability IDs that should use async execution.

    These are long-running operations that benefit from task queue:
    - Research operations (web search, LLM analysis)
    - Backtesting (historical simulation)
    - Bulk data fetching
    """
    return [
        # Research
        "comprehensive_research",
        "company_comprehensive",
        "analyze_market_sentiment",
        "deep_research_financial",
        # Backtesting
        "run_backtest",
        "optimize_strategy",
        "walk_forward_analysis",
        "monte_carlo_simulation",
        "backtest_portfolio",
        # Bulk operations
        "fetch_stock_data_batch",
        # Agent-based
        "orchestrated_analysis",
        "compare_multi_agent_analysis",
    ]
