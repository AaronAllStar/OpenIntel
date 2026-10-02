import asyncio
import json
import time
from collections.abc import AsyncIterator
from typing import Any

import redis
import redis.asyncio as aioredis

from src.app.infrastructure.config import get_settings
from src.app.infrastructure.logging import logger

settings = get_settings()

# In-memory pub/sub fallback for local testing when Redis server is offline
_in_memory_channels: dict[str, list[asyncio.Queue[str]]] = {}
_redis_offline_until: float = 0.0


def get_channel_name(investigation_id: str) -> str:
    return f"investigation:{investigation_id}:events"


def publish_event_sync(investigation_id: str, event_data: dict[str, Any]) -> None:
    """Synchronous publish called by Celery workers or local executors."""
    global _redis_offline_until
    payload = json.dumps(event_data)
    channel = get_channel_name(investigation_id)

    if settings.ENV != "test" and time.monotonic() > _redis_offline_until:
        try:
            client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.2,
                socket_timeout=0.5,
            )
            client.publish(channel, payload)
            client.close()
            return
        except Exception as exc:
            _redis_offline_until = time.monotonic() + 10.0
            logger.debug("Redis sync publish failed, using in-memory fallback", error=str(exc))

    # Push to in-memory queues if any
    if channel in _in_memory_channels:
        for q in _in_memory_channels[channel]:
            q.put_nowait(payload)


async def subscribe_events_async(investigation_id: str) -> AsyncIterator[dict[str, Any]]:
    """Asynchronous subscription stream for FastAPI SSE."""
    global _redis_offline_until
    channel = get_channel_name(investigation_id)

    if settings.ENV != "test" and time.monotonic() > _redis_offline_until:
        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.2,
                socket_timeout=0.5,
            )
            pubsub = client.pubsub()
            await pubsub.subscribe(channel)
            logger.info("Subscribed to Redis SSE channel", channel=channel)

            try:
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message.get("type") == "message":
                        raw_data = message.get("data", "{}")
                        yield json.loads(raw_data)
                    await asyncio.sleep(0.05)
            finally:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
                await client.aclose()
            return
        except Exception as exc:
            _redis_offline_until = time.monotonic() + 10.0
            logger.debug("Redis async connection failed, falling back to memory queue", error=str(exc))

    # In-memory queue fallback
    q: asyncio.Queue[str] = asyncio.Queue()
    if channel not in _in_memory_channels:
        _in_memory_channels[channel] = []
    _in_memory_channels[channel].append(q)

    try:
        while True:
            payload = await q.get()
            yield json.loads(payload)
    finally:
        if channel in _in_memory_channels and q in _in_memory_channels[channel]:
            _in_memory_channels[channel].remove(q)
