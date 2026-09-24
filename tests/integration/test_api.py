import pytest
from httpx import ASGITransport, AsyncClient

from src.app.api.main import app
from src.app.infrastructure.database import Base, engine


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    from src.app.infrastructure.config import get_settings
    monkeypatch.setattr(get_settings(), "ENV", "test")
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "ok"


@pytest.mark.asyncio
async def test_create_investigation_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "name": "Username Investigation Test",
            "target_kind": "username",
            "target_value": "target_analyst",
            "investigation_type": "quick",
        }
        response = await client.post("/api/v1/investigations", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["target_value"] == "target_analyst"
        assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_investigation_ssrf_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "name": "SSRF Exploit Attempt",
            "target_kind": "ip",
            "target_value": "192.168.1.50",
            "investigation_type": "quick",
        }
        response = await client.post("/api/v1/investigations", json=payload)
        assert response.status_code == 422
        assert "SSRF Protection" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_and_get_investigation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create one
        create_res = await client.post(
            "/api/v1/investigations",
            json={
                "name": "Domain Test",
                "target_kind": "domain",
                "target_value": "example.com",
            },
        )
        inv_id = create_res.json()["id"]

        # List
        list_res = await client.get("/api/v1/investigations")
        assert list_res.status_code == 200
        items = list_res.json()
        assert len(items) >= 1
        assert any(item["id"] == inv_id for item in items)

        # Get detail
        detail_res = await client.get(f"/api/v1/investigations/{inv_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == inv_id
        assert detail["target_value"] == "example.com"
