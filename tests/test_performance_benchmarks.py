import time

import pytest
from httpx import ASGITransport, AsyncClient

from src.app.api.main import app
from src.app.infrastructure.database import Base, engine
from src.app.infrastructure.http_client import get_http_client
from src.app.infrastructure.metrics import metrics
from src.app.infrastructure.warmup import warmup_subsystems


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from src.app.infrastructure import database
    from src.app.infrastructure.config import get_settings

    test_engine = create_engine("sqlite:///:memory:", echo=False)
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=test_engine))
    monkeypatch.setattr(get_settings(), "ENV", "test")
    monkeypatch.setattr(get_settings(), "RATE_LIMIT_ENABLED", False)

    database.Base.metadata.create_all(bind=test_engine)
    yield
    database.Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_warmup_subsystems_performance():
    """Verify that warmup runs cleanly and subsequent carrier lookups take < 50ms."""
    res = warmup_subsystems()
    assert "warmup_duration_ms" in res
    assert res["warmup_duration_ms"] >= 0.0

    # Post-warmup phone carrier resolution
    import phonenumbers
    from phonenumbers import carrier

    start = time.monotonic()
    parsed = phonenumbers.parse("+12025550143", "US")
    name = carrier.name_for_number(parsed, "en")
    elapsed_ms = (time.monotonic() - start) * 1000.0

    # Post-warmup resolution must be fast (< 50ms)
    assert elapsed_ms < 50.0, f"Carrier resolution took too long: {elapsed_ms}ms"
    assert name is not None


def test_http_client_connection_pooling():
    """Verify that get_http_client returns a shared singleton instance with connection limits."""
    client1 = get_http_client()
    client2 = get_http_client()
    assert client1 is client2
    assert not client1.is_closed


@pytest.mark.asyncio
async def test_health_ready_and_metrics_endpoints():
    """Verify health readiness probe and Prometheus metrics text exposition."""
    # Emit test metrics
    metrics.inc_investigation(status="completed", target_kind="domain")
    metrics.inc_adapter_run(engine="amass", status="ok", duration_s=0.25)
    metrics.set_circuit_breaker(engine="holehe", state=0)
    metrics.set_active_connections(3)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Health check
        res_health = await client.get("/api/v1/health")
        assert res_health.status_code == 200
        data_health = res_health.json()
        assert data_health["status"] == "healthy"
        assert "uptime_seconds" in data_health

        # 2. Readiness check
        res_ready = await client.get("/api/v1/health/ready")
        assert res_ready.status_code == 200
        assert res_ready.json()["status"] == "ready"

        # 3. Prometheus metrics endpoint
        res_metrics = await client.get("/api/v1/metrics")
        assert res_metrics.status_code == 200
        assert "text/plain" in res_metrics.headers["content-type"]
        text_body = res_metrics.text
        assert "openintel_uptime_seconds" in text_body
        assert 'openintel_investigations_total{status="completed",target_kind="domain"} 1' in text_body
        assert 'openintel_adapter_runs_total{engine="amass",status="ok"} 1' in text_body
        assert 'openintel_circuit_breaker_state{engine="holehe"} 0' in text_body
        assert "openintel_active_sse_connections 3" in text_body
