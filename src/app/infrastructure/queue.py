import asyncio
import json
import time
from typing import Any

from src.app.application.cancellation_manager import cancellation_manager
from src.app.infrastructure.config import get_settings
from src.app.infrastructure.logging import logger

settings = get_settings()


class AsyncJobQueue:
    """
    Lightweight, async job queue with Redis-backed execution and an in-memory fallback.
    Provides:
    - Retries with exponential backoff
    - Job idempotency (prevents duplicate execution of the same investigation)
    - Integrated cancellation tracking
    - Resilient partial-result completion
    """

    def __init__(self) -> None:
        self._in_memory_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._active_jobs: set[str] = set()
        self._worker_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    async def _ensure_local_worker(self) -> None:
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._local_worker_loop())

    async def _local_worker_loop(self) -> None:
        while True:
            job = await self._in_memory_queue.get()
            investigation_id = job["investigation_id"]
            attempt = job.get("attempt", 0)
            max_retries = job.get("max_retries", 2)
            backoff_base = job.get("backoff_base", 1.0)

            try:
                # Import dynamically to avoid circular dependencies
                from src.app.application.worker_tasks import execute_investigation_async

                await execute_investigation_async(investigation_id)

            except Exception as exc:
                logger.error(
                    "Job execution encountered an error",
                    investigation_id=investigation_id,
                    attempt=attempt,
                    error=str(exc),
                )
                if attempt < max_retries and not cancellation_manager.is_cancelled(investigation_id):
                    delay = backoff_base * (2**attempt)
                    logger.info(
                        "Retrying investigation job with backoff",
                        investigation_id=investigation_id,
                        next_attempt=attempt + 1,
                        delay_seconds=delay,
                    )
                    await asyncio.sleep(delay)
                    await self._in_memory_queue.put({
                        "investigation_id": investigation_id,
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "backoff_base": backoff_base,
                    })
            finally:
                async with self._lock:
                    self._active_jobs.discard(investigation_id)
                self._in_memory_queue.task_done()

    async def enqueue(
        self,
        investigation_id: str,
        max_retries: int = 2,
        backoff_base: float = 1.0,
    ) -> bool:
        """
        Enqueues an investigation job with idempotency guarantee.
        Returns True if enqueued, False if already running.
        """
        async with self._lock:
            if investigation_id in self._active_jobs:
                logger.warn("Job already active/enqueued (idempotency guarded)", investigation_id=investigation_id)
                return False
            self._active_jobs.add(investigation_id)

        # Check if Redis queue is available and configured
        redis_enqueued = False
        if settings.REDIS_URL and settings.ENV != "test":
            try:
                import redis.asyncio as aioredis

                client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                payload = json.dumps({
                    "investigation_id": investigation_id,
                    "attempt": 0,
                    "max_retries": max_retries,
                    "backoff_base": backoff_base,
                    "timestamp": time.time(),
                })
                # LPUSH to Redis jobs list
                await client.lpush("openintel:jobs:queue", payload)
                await client.aclose()
                redis_enqueued = True
                logger.info("Enqueued investigation to Redis job queue", investigation_id=investigation_id)
            except Exception as exc:
                logger.debug("Redis queue unavailable, falling back to local async runner", error=str(exc))

        if not redis_enqueued:
            await self._ensure_local_worker()
            await self._in_memory_queue.put({
                "investigation_id": investigation_id,
                "attempt": 0,
                "max_retries": max_retries,
                "backoff_base": backoff_base,
            })
            logger.info("Enqueued investigation to local in-memory queue", investigation_id=investigation_id)

        return True


_global_queue = AsyncJobQueue()


def get_job_queue() -> AsyncJobQueue:
    return _global_queue
