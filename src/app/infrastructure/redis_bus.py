import asyncio
import json
import threading
import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from typing import Any

import redis
import redis.asyncio as aioredis

from src.app.infrastructure.config import get_settings
from src.app.infrastructure.logging import logger

settings = get_settings()

# In-memory pub/sub fallback and replay buffer
MAX_BUFFER_SIZE = 1000
_in_memory_channels: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
_in_memory_sequences: dict[str, int] = defaultdict(int)
_in_memory_buffers: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=MAX_BUFFER_SIZE))
_bus_lock = threading.Lock()
_redis_offline_until: float = 0.0


def get_channel_name(investigation_id: str) -> str:
    return f"investigation:{investigation_id}:events"


def get_buffer_key(investigation_id: str) -> str:
    return f"investigation:{investigation_id}:buffer"


def get_seq_key(investigation_id: str) -> str:
    return f"investigation:{investigation_id}:seq"


def publish_event_sync(investigation_id: str, event_data: dict[str, Any]) -> dict[str, Any]:
    """
    Synchronous publish called by Celery workers or local executors.
    Attaches a monotonic sequence ID (`seq`), saves to replay buffer, and publishes to subscribers.
    """
    global _redis_offline_until

    # Assign monotonic sequence ID
    with _bus_lock:
        if "seq" not in event_data:
            _in_memory_sequences[investigation_id] += 1
            event_data["seq"] = _in_memory_sequences[investigation_id]
        current_seq = event_data["seq"]
        _in_memory_buffers[investigation_id].append(dict(event_data))

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
            pipe = client.pipeline()
            # Store in sorted set with seq as score for replay
            buf_key = get_buffer_key(investigation_id)
            pipe.zadd(buf_key, {payload: float(current_seq)})
            pipe.zremrangebyrank(buf_key, 0, -(MAX_BUFFER_SIZE + 1))
            pipe.expire(buf_key, 86400)
            pipe.publish(channel, payload)
            pipe.execute()
            client.close()
            return event_data
        except Exception as exc:
            _redis_offline_until = time.monotonic() + 10.0
            logger.debug("Redis sync publish failed, using in-memory fallback", error=str(exc))

    # Push to in-memory queues if any active subscribers exist
    with _bus_lock:
        if channel in _in_memory_channels:
            for q in list(_in_memory_channels[channel]):
                try:
                    q.put_nowait(dict(event_data))
                except Exception:
                    pass

    return event_data


def get_replayed_events_sync(investigation_id: str, since_seq: int = 0) -> list[dict[str, Any]]:
    """Retrieve buffered events with seq > since_seq from Redis or in-memory fallback."""
    global _redis_offline_until

    if settings.ENV != "test" and time.monotonic() > _redis_offline_until:
        try:
            client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.2,
                socket_timeout=0.5,
            )
            buf_key = get_buffer_key(investigation_id)
            # Fetch events strictly greater than since_seq
            raw_items = client.zrangebyscore(buf_key, min=f"({since_seq}", max="+inf")
            client.close()
            return [json.loads(item) for item in raw_items]
        except Exception as exc:
            _redis_offline_until = time.monotonic() + 10.0
            logger.debug("Redis replay read failed, using in-memory fallback", error=str(exc))

    with _bus_lock:
        buffer = _in_memory_buffers.get(investigation_id, deque())
        return [dict(ev) for ev in buffer if ev.get("seq", 0) > since_seq]


async def subscribe_events_async(
    investigation_id: str,
    since_seq: int = 0,
) -> AsyncIterator[dict[str, Any]]:
    """
    Asynchronous subscription stream for FastAPI SSE with replay buffer support.
    Guarantees no dropped events between replay and live subscription.
    """
    global _redis_offline_until
    channel = get_channel_name(investigation_id)
    last_seq = since_seq

    if settings.ENV != "test" and time.monotonic() > _redis_offline_until:
        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.2,
                socket_timeout=0.5,
            )
            pubsub = client.pubsub()
            # 1. Subscribe to pubsub channel first to avoid missing concurrent publishes
            await pubsub.subscribe(channel)
            logger.info("Subscribed to Redis SSE channel", channel=channel)

            # 2. Replay buffered events since_seq
            replayed = get_replayed_events_sync(investigation_id, since_seq=since_seq)
            for event in replayed:
                ev_seq = event.get("seq", 0)
                if ev_seq > last_seq:
                    last_seq = ev_seq
                    yield event

            # 3. Stream live events, deduplicating any overlap
            try:
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message.get("type") == "message":
                        raw_data = message.get("data", "{}")
                        event = json.loads(raw_data)
                        ev_seq = event.get("seq", 0)
                        if ev_seq > last_seq:
                            last_seq = ev_seq
                            yield event
                    await asyncio.sleep(0.01)
            finally:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
                await client.aclose()
            return
        except Exception as exc:
            _redis_offline_until = time.monotonic() + 10.0
            logger.debug("Redis async connection failed, falling back to memory queue", error=str(exc))

    # In-memory queue fallback with race-free replay
    q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    with _bus_lock:
        if channel not in _in_memory_channels:
            _in_memory_channels[channel] = []
        _in_memory_channels[channel].append(q)

        # Snapshot replayed events while under lock
        replayed = [
            dict(ev)
            for ev in _in_memory_buffers.get(investigation_id, deque())
            if ev.get("seq", 0) > since_seq
        ]

    try:
        # Emit replayed events
        for event in replayed:
            ev_seq = event.get("seq", 0)
            if ev_seq > last_seq:
                last_seq = ev_seq
                yield event

        # Stream live queue events, ignoring duplicates already replayed
        while True:
            event = await q.get()
            ev_seq = event.get("seq", 0)
            if ev_seq > last_seq:
                last_seq = ev_seq
                yield event
    finally:
        with _bus_lock:
            if channel in _in_memory_channels and q in _in_memory_channels[channel]:
                _in_memory_channels[channel].remove(q)
                if not _in_memory_channels[channel]:
                    del _in_memory_channels[channel]

