"""Liveness/readiness probes.

The important test here is `test_health_does_not_touch_the_database`. Render's
`healthCheckPath` and the keep-warm ping both hit /health, so the moment it
gains a DB dependency a sleeping Neon compute can fail the first probe after a
deploy and Render marks the deploy failed. That turns the probe into a cause of
outages instead of a report of them, so the invariant is pinned by a test.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_is_ok(client: TestClient):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "prognos-api"}


class _DeadEngine:
    """Stands in for the real AsyncEngine; any connect attempt raises.

    `AsyncEngine.connect` is read-only, so the engine object itself is swapped
    rather than the method patched.
    """

    def __init__(self, exc: Exception):
        self._exc = exc

    def connect(self):
        raise self._exc


def test_health_does_not_touch_the_database(client: TestClient, monkeypatch):
    """/health must answer even with the database completely unreachable."""
    monkeypatch.setattr(
        "app.api.v1.routes.health.engine",
        _DeadEngine(AssertionError("/health must not open a DB connection")),
    )

    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_reports_ok_against_a_live_database(client: TestClient):
    r = client.get("/api/v1/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_ready_reports_503_when_the_database_is_down(client: TestClient, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.routes.health.engine",
        _DeadEngine(OSError("connection refused")),
    )

    r = client.get("/api/v1/ready")
    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "degraded"
    assert body["database"] == "unreachable"
    assert body["error"] == "OSError"
