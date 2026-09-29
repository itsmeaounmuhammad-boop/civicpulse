"""
System routes: /health (liveness), /ready (readiness), /metrics (Prometheus).
"""

from fastapi import APIRouter, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    """
    Liveness probe. Deliberately does NOT touch the database — a slow
    database must never look like a dead process, or Kubernetes will
    restart-loop every pod in the deployment.
    """
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request, response: Response) -> dict[str, str]:
    """
    Readiness probe. 200 only if Postgres AND Redis are both reachable;
    503 naming the failed dependency otherwise.
    """
    engine = request.app.state.db_engine
    redis = request.app.state.redis

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return {"status": "not ready", "failed_dependency": "postgres"}

    try:
        await redis.ping()
    except Exception:
        response.status_code = 503
        return {"status": "not ready", "failed_dependency": "redis"}

    return {"status": "ready"}


@router.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)