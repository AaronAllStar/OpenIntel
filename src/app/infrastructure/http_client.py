import ipaddress
import socket
import threading
import httpx

from src.app.infrastructure.config import get_settings

_client_lock = threading.Lock()
_shared_client: httpx.AsyncClient | None = None

BLOCKED_HOSTS = frozenset({
    "localhost",
    "127.0.0.1",
    "::1",
    "metadata.google.internal",
    "instance-data",
    "metadata",
    "169.254.169.254",
})


def _is_private_or_restricted(host: str) -> bool:
    host_clean = host.strip("[]").lower()
    if host_clean in BLOCKED_HOSTS:
        return True

    # Check IP addresses
    try:
        ip = ipaddress.ip_address(host_clean)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_unspecified
            or ip.is_multicast
        )
    except ValueError:
        pass

    # Resolve domain to verify target IP is not private
    try:
        addrinfo = socket.getaddrinfo(host_clean, None)
        for _, _, _, _, sockaddr in addrinfo:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_unspecified
                or ip.is_multicast
            ):
                return True
    except Exception:
        # If DNS resolution fails, let httpx handle it
        pass

    return False


async def _ssrf_filter_hook(request: httpx.Request) -> None:
    settings = get_settings()
    if not settings.ALLOW_PRIVATE_TARGETS:
        host = request.url.host
        if _is_private_or_restricted(host):
            raise httpx.RequestError(
                f"SSRF Protection: Outbound HTTP request to private/restricted host '{host}' blocked.",
                request=request,
            )


def get_http_client() -> httpx.AsyncClient:
    """
    Returns a shared, connection-pooled AsyncClient with SSRF guardrails and keep-alive.
    Prevents repeated SSL handshakes and blocks SSRF pivot attempts.
    """
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        with _client_lock:
            if _shared_client is None or _shared_client.is_closed:
                _shared_client = httpx.AsyncClient(
                    timeout=httpx.Timeout(15.0, connect=5.0),
                    limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
                    follow_redirects=True,
                    headers={"User-Agent": "OpenIntel-OSINT/1.0 (+https://github.com/AaronAllStar/OpenIntel)"},
                    event_hooks={"request": [_ssrf_filter_hook]},
                )
    return _shared_client


async def close_http_client() -> None:
    """Closes the shared connection pool during application shutdown."""
    global _shared_client
    with _client_lock:
        if _shared_client is not None and not _shared_client.is_closed:
            await _shared_client.aclose()
            _shared_client = None
