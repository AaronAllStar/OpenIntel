import pytest
from httpx import ASGITransport, AsyncClient

from src.app.api.main import app
from src.app.api.middleware.auth import create_access_token
from src.app.api.routes.investigations import create_rate_limiter, export_rate_limiter
from src.app.infrastructure.database import Base, engine
from src.app.infrastructure.logging import mask_pii_string, redact_sensitive_keys


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    from src.app.infrastructure.config import get_settings

    monkeypatch.setattr(get_settings(), "ENV", "test")
    monkeypatch.setattr(get_settings(), "RATE_LIMIT_ENABLED", False)
    monkeypatch.setattr(get_settings(), "AUTH_ENABLED", False)
    create_rate_limiter.reset()
    export_rate_limiter.reset()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    create_rate_limiter.reset()
    export_rate_limiter.reset()


@pytest.mark.asyncio
async def test_ethical_guardrail_rejection():
    """Verify that omitting legal acknowledgment blocks investigation creation with 403 Forbidden."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "name": "Unauthorized Scan Attempt",
            "target_kind": "username",
            "target_value": "target_analyst",
            "legal_acknowledged": False,
        }
        res = await client.post("/api/v1/investigations", json=payload)
        assert res.status_code == 403
        assert "Ethical & Legal Guardrail" in res.json()["detail"]


@pytest.mark.asyncio
async def test_legal_notice_endpoint():
    """Verify that ethical and authorized use charter is accessible."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/legal/notice")
        assert res.status_code == 200
        data = res.json()
        assert "Ethical & Authorized Use Charter" in data["title"]
        assert data["compliance"]["cfaa_compliant"] is True


@pytest.mark.asyncio
async def test_authentication_and_rbac(monkeypatch):
    """Verify JWT and API-key authentication with analyst and admin role enforcement."""
    from src.app.infrastructure.config import get_settings

    monkeypatch.setattr(get_settings(), "AUTH_ENABLED", True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Unauthenticated request to /investigations fails
        res_no_auth = await client.get("/api/v1/investigations")
        assert res_no_auth.status_code == 401

        # 2. Invalid API key fails
        res_bad_key = await client.get("/api/v1/investigations", headers={"X-API-Key": "invalid-key"})
        assert res_bad_key.status_code == 401

        # 3. Valid Analyst API key can list investigations
        analyst_key = get_settings().ANALYST_API_KEY
        res_analyst = await client.get("/api/v1/investigations", headers={"X-API-Key": analyst_key})
        assert res_analyst.status_code == 200

        # 4. Analyst role cannot access Admin-only /audit endpoint (403 Forbidden)
        analyst_token = create_access_token(user_id="test_analyst", role="analyst")
        res_audit_forbidden = await client.get(
            "/api/v1/audit",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert res_audit_forbidden.status_code == 403

        # 5. Admin role can access /audit endpoint
        admin_token = create_access_token(user_id="test_admin", role="admin")
        res_audit_ok = await client.get(
            "/api/v1/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_audit_ok.status_code == 200
        assert isinstance(res_audit_ok.json(), list)


@pytest.mark.asyncio
async def test_immutable_audit_logging_lifecycle():
    """Verify that investigation creation, cancellation, and export write immutable audit entries."""
    admin_token = create_access_token(user_id="auditor_admin", role="admin")
    auth_headers = {"Authorization": f"Bearer {admin_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create investigation
        create_payload = {
            "name": "Audit Test Inv",
            "target_kind": "username",
            "target_value": "audited_user",
            "legal_acknowledged": True,
        }
        res_create = await client.post("/api/v1/investigations", json=create_payload, headers=auth_headers)
        assert res_create.status_code == 201
        inv_id = res_create.json()["id"]

        # Cancel investigation
        res_cancel = await client.post(f"/api/v1/investigations/{inv_id}/cancel", headers=auth_headers)
        assert res_cancel.status_code == 200

        # Export investigation
        res_export = await client.get(f"/api/v1/investigations/{inv_id}/export?format=json", headers=auth_headers)
        assert res_export.status_code == 200

        # Query audit trail
        res_audit = await client.get("/api/v1/audit", headers=auth_headers)
        assert res_audit.status_code == 200
        logs = res_audit.json()

        actions = [log["action"] for log in logs]
        assert "INVESTIGATION_CREATE" in actions
        assert "INVESTIGATION_CANCEL" in actions
        assert "INVESTIGATION_EXPORT" in actions

        # Verify resource ID linkage
        inv_logs = [log for log in logs if log["resource_id"] == inv_id]
        assert len(inv_logs) >= 2


def test_log_masking_and_pii_redaction():
    """Verify that email addresses, phone numbers, and sensitive keys are masked."""
    # Test PII string masking
    email_text = "Contact analyst at carlos.navarro@example.org for intelligence."
    masked_email = mask_pii_string(email_text)
    assert "c***@example.org" in masked_email
    assert "carlos.navarro@" not in masked_email

    phone_text = "Target identified with phone +1 202-555-0143 in registry."
    masked_phone = mask_pii_string(phone_text)
    assert "+1 202-***-0143" in masked_phone
    assert "555" not in masked_phone

    # Test dictionary key redaction
    log_event = {
        "event": "Authentication attempt",
        "api_key": "super-secret-key-value",
        "password": "my-password",
        "user_email": "target@domain.com",
    }
    redacted = redact_sensitive_keys(None, "", log_event)
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["password"] == "[REDACTED]"
    assert "t***@domain.com" in redacted["user_email"]
