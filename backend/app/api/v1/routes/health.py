"""Liveness and readiness probes.

Two separate endpoints on purpose:

* ``/health`` must stay dependency-free. It is both Render's
  ``healthCheckPath`` and the target of the keep-warm ping, so it has to answer
  instantly from a cold container. If it touched Postgres, Neon's scale-to-zero
  compute could lose the first probe after a deploy and Render would mark the
  deploy failed — manufacturing an outage rather than reporting one.
* ``/ready`` is for humans and uptime monitors. It actually checks the database
  and returns 503 when the API is up but cannot serve real traffic.
"""

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.database import engine

router = APIRouter()


@router.get("/health")
async def health():
    """Liveness. No I/O — see the module docstring."""
    return {"status": "ok", "service": "prognos-api"}


@router.get("/ready")
async def ready(response: Response):
    """Readiness: can we actually reach the database?"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "degraded",
            "service": "prognos-api",
            "database": "unreachable",
            "error": type(exc).__name__,
        }
    return {"status": "ok", "service": "prognos-api", "database": "ok"}
