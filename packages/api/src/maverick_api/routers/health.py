"""
Health check endpoints for Kubernetes probes.

- /health - Liveness probe (is process running?)
- /ready - Readiness probe (can we serve traffic?)
- /startup - Startup probe (has app initialized?)
"""

from datetime import datetime, UTC

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from maverick_api.dependencies import get_db, get_redis

router = APIRouter()


class HealthResponse(BaseModel):
    """Basic health check response."""

    status: str


class ReadinessResponse(BaseModel):
    """Readiness check response with component status."""

    status: str
    checks: dict[str, str]
    timestamp: datetime


class StartupResponse(BaseModel):
    """Startup check response."""

    status: str
    migration_version: str | None = None
    message: str | None = None


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Liveness probe - is the process running?

    Kubernetes uses this to determine if the pod should be restarted.
    This should be lightweight and always return 200 if the process is alive.
    """
    return {"status": "ok"}


@router.get("/ready", response_model=ReadinessResponse)
async def ready(
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    """
    Readiness probe - can we serve traffic?

    Kubernetes uses this to determine if the pod should receive traffic.
    Checks all critical dependencies (database, cache).
    """
    checks = {}

    # Check Redis
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    # Check Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    # Determine overall status
    all_ok = all(v == "ok" for v in checks.values())

    return {
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
        "timestamp": datetime.now(UTC),
    }


@router.get("/startup", response_model=StartupResponse)
async def startup(
    db: AsyncSession = Depends(get_db),
):
    """
    Startup probe - has the application finished initializing?

    Used during initial startup to give app time to initialize.
    Checks if database migrations are applied.
    """
    try:
        # First check if alembic_version table exists
        check_table = await db.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'alembic_version'
                )
            """)
        )
        table_exists = check_table.scalar()

        if not table_exists:
            return {
                "status": "initializing",
                "message": "Migrations not yet applied - alembic_version table missing",
            }

        # Table exists, get current version
        result = await db.execute(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        )
        row = result.fetchone()
        version = row[0] if row else None

        return {
            "status": "ok",
            "migration_version": version,
        }
    except Exception as e:
        # Handle any database errors gracefully
        return {
            "status": "initializing",
            "message": f"Database check failed: {type(e).__name__}",
        }


__all__ = ["router"]

