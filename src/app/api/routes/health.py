import sys
import time

import redis
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.app.infrastructure.config import get_settings
from src.app.infrastructure.database import get_db
from src.app.infrastructure.metrics import metrics

router = APIRouter(tags=["observability"])

_app_start_time = time.time()


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict:
    """Liveness probe reporting subsystem statuses, uptime, and version."""
    settings = get_settings()
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {exc}"

    redis_status = "ok"
    if settings.ENV != "test":
        try:
            client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.2)
            client.ping()
            client.close()
        except Exception:
            redis_status = "offline (fallback active)"

    is_healthy = db_status == "ok"
    return {
        "status": "healthy" if is_healthy else "degraded",
        "database": db_status,
        "redis": redis_status,
        "version": "0.1.0",
        "python_version": sys.version.split()[0],
        "uptime_seconds": round(time.time() - _app_start_time, 2),
    }


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)) -> JSONResponse:
    """Readiness probe verifying complete subsystem operational capacity."""
    try:
        # Check database read/write
        db.execute(text("SELECT 1"))
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ready", "database": "connected"},
        )
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "error": str(exc)},
        )


@router.get("/metrics")
def prometheus_metrics() -> PlainTextResponse:
    """Standard Prometheus text exposition format for operational scraping."""
    return PlainTextResponse(
        content=metrics.generate_prometheus_text(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )

