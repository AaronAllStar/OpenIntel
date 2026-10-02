import base64
import hashlib
import hmac
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from src.app.infrastructure.config import get_settings


@dataclass(frozen=True, slots=True)
class UserPrincipal:
    user_id: str
    role: str  # "admin" | "analyst" | "viewer"
    scopes: list[str] = field(default_factory=list)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(
    user_id: str,
    role: str = "analyst",
    expires_in_seconds: int = 3600,
    secret_key: str | None = None,
) -> str:
    """Create a signed HMAC-SHA256 JWT access token."""
    settings = get_settings()
    key = (secret_key or settings.SECRET_KEY).encode("utf-8")

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in_seconds,
    }

    hdr_b64 = _b64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload).encode("utf-8"))
    signature_base = f"{hdr_b64}.{payload_b64}".encode()
    sig = hmac.new(key, signature_base, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)

    return f"{hdr_b64}.{payload_b64}.{sig_b64}"


def verify_access_token(token: str, secret_key: str | None = None) -> dict[str, Any]:
    """Verify and decode HMAC-SHA256 JWT access token."""
    settings = get_settings()
    key = (secret_key or settings.SECRET_KEY).encode("utf-8")

    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token structure")

    hdr_b64, payload_b64, sig_b64 = parts
    signature_base = f"{hdr_b64}.{payload_b64}".encode()
    expected_sig = hmac.new(key, signature_base, hashlib.sha256).digest()

    try:
        actual_sig = _b64url_decode(sig_b64)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token encoding") from exc

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token signature verification failed")

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload") from exc

    if payload.get("exp", 0) < time.time():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

    return payload


async def get_current_user(request: Request) -> UserPrincipal:
    """Extract authenticated user principal from API-Key or Bearer JWT."""
    settings = get_settings()
    if not getattr(settings, "AUTH_ENABLED", False):
        # Default unauthenticated identity when auth is disabled in dev/local
        return UserPrincipal(user_id="local_analyst", role="admin", scopes=["*"])

    # 1. Check X-API-Key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        if hmac.compare_digest(api_key, settings.ADMIN_API_KEY):
            return UserPrincipal(user_id="admin_service", role="admin", scopes=["*"])
        if hmac.compare_digest(api_key, settings.ANALYST_API_KEY):
            return UserPrincipal(user_id="analyst_service", role="analyst", scopes=["read", "write"])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key provided",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 2. Check Authorization Bearer header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        payload = verify_access_token(token)
        return UserPrincipal(
            user_id=payload.get("sub", "unknown"),
            role=payload.get("role", "analyst"),
            scopes=payload.get("scopes", []),
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer, ApiKey"},
    )


def require_role(*allowed_roles: str) -> Callable[[UserPrincipal], UserPrincipal]:
    """Dependency factory checking that the authenticated user possesses one of allowed roles."""

    async def _role_checker(user: UserPrincipal = Depends(get_current_user)) -> UserPrincipal:
        if user.role not in allowed_roles and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: role '{user.role}' lacks permission for this action (required: {allowed_roles})",
            )
        return user

    return _role_checker

