import math
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from src.app.infrastructure.config import get_settings


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding window rate limiter per client IP / key.
    Provides standard Retry-After and X-RateLimit-* headers when limit is exceeded.
    """

    def __init__(self, times: int, seconds: int, key_prefix: str = "") -> None:
        self.times = times
        self.seconds = seconds
        self.key_prefix = key_prefix
        self._history: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _get_client_key(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "127.0.0.1"
        return f"{self.key_prefix}:{client_ip}"

    def reset(self) -> None:
        """Clear limiter history (useful in tests)."""
        with self._lock:
            self._history.clear()

    async def __call__(self, request: Request) -> None:
        settings = get_settings()
        if not getattr(settings, "RATE_LIMIT_ENABLED", True):
            return

        key = self._get_client_key(request)
        now = time.monotonic()
        window_start = now - self.seconds

        with self._lock:
            queue = self._history[key]
            # Prune timestamps outside sliding window
            while queue and queue[0] <= window_start:
                queue.popleft()

            if len(queue) >= self.times:
                oldest = queue[0]
                retry_after = max(1, math.ceil(oldest + self.seconds - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {self.times} requests per {self.seconds} seconds. Try again in {retry_after}s.",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(self.times),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(retry_after),
                    },
                )

            queue.append(now)


RateLimiter = SlidingWindowRateLimiter

