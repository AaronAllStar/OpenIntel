import asyncio
import time
from typing import Any, Literal

CircuitState = Literal["closed", "open", "half_open"]


class CircuitBreaker:
    """
    Per-engine circuit breaker to prevent cascading failures.
    - CLOSED: Normal operation. Requests proceed.
    - OPEN: Consecutive failures exceeded threshold. Requests immediately skipped.
    - HALF_OPEN: Cooldown period elapsed. A single trial request is permitted.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        cooldown_seconds: float = 30.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._failures: dict[str, int] = {}
        self._last_failure: dict[str, float] = {}
        self._states: dict[str, CircuitState] = {}
        self._lock = asyncio.Lock()

    def get_state(self, engine_name: str) -> CircuitState:
        state = self._states.get(engine_name, "closed")
        if state == "open":
            last_fail = self._last_failure.get(engine_name, 0.0)
            if (time.monotonic() - last_fail) >= self.cooldown_seconds:
                return "half_open"
        return state

    def can_execute(self, engine_name: str) -> bool:
        state = self.get_state(engine_name)
        return state in ("closed", "half_open")

    def record_success(self, engine_name: str) -> None:
        self._failures[engine_name] = 0
        self._states[engine_name] = "closed"

    def record_failure(self, engine_name: str, error: Any = None) -> None:
        now = time.monotonic()
        failures = self._failures.get(engine_name, 0) + 1
        self._failures[engine_name] = failures
        self._last_failure[engine_name] = now

        if failures >= self.failure_threshold:
            self._states[engine_name] = "open"

    def reset(self, engine_name: str | None = None) -> None:
        if engine_name:
            self._failures.pop(engine_name, None)
            self._last_failure.pop(engine_name, None)
            self._states.pop(engine_name, None)
        else:
            self._failures.clear()
            self._last_failure.clear()
            self._states.clear()


class TokenBucketRateLimiter:
    """
    Asynchronous token bucket rate limiter to prevent hammering external targets or services.
    """

    def __init__(self) -> None:
        self._tokens: dict[str, float] = {}
        self._last_update: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def acquire(
        self,
        service: str,
        rate: float = 5.0,
        burst: float = 10.0,
        max_wait_seconds: float = 2.0,
    ) -> bool:
        async with self._lock:
            now = time.monotonic()
            last = self._last_update.get(service, now)
            current_tokens = self._tokens.get(service, burst)

            # Replenish tokens based on elapsed time
            elapsed = now - last
            current_tokens = min(burst, current_tokens + elapsed * rate)
            self._last_update[service] = now

            if current_tokens >= 1.0:
                self._tokens[service] = current_tokens - 1.0
                return True

            # Calculate required wait time
            deficit = 1.0 - current_tokens
            wait_time = deficit / rate
            if wait_time > max_wait_seconds:
                return False

            self._tokens[service] = 0.0

        await asyncio.sleep(wait_time)
        return True


_global_circuit_breaker = CircuitBreaker()
_global_rate_limiter = TokenBucketRateLimiter()


def get_circuit_breaker() -> CircuitBreaker:
    return _global_circuit_breaker


def get_rate_limiter() -> TokenBucketRateLimiter:
    return _global_rate_limiter
