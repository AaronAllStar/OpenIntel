import threading

import httpx

_client_lock = threading.Lock()
_shared_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """
    Returns a shared, connection-pooled AsyncClient with keep-alive and SSL context caching.
    Prevents repeated ~350ms SSL verification handshakes across HTTP-based OSINT adapters.
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
                )
    return _shared_client


async def close_http_client() -> None:
    """Closes the shared connection pool during application shutdown."""
    global _shared_client
    with _client_lock:
        if _shared_client is not None and not _shared_client.is_closed:
            await _shared_client.aclose()
            _shared_client = None
