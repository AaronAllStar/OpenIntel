import asyncio
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.app.api.main import app
from src.app.infrastructure.database import Base, engine
from src.app.infrastructure.redis_bus import (
    _bus_lock,
    _in_memory_buffers,
    _in_memory_channels,
    _in_memory_sequences,
    get_channel_name,
    publish_event_sync,
    subscribe_events_async,
)


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    from src.app.infrastructure.config import get_settings

    monkeypatch.setattr(get_settings(), "ENV", "test")
    monkeypatch.setattr(get_settings(), "RATE_LIMIT_ENABLED", False)
    with _bus_lock:
        _in_memory_channels.clear()
        _in_memory_buffers.clear()
        _in_memory_sequences.clear()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    with _bus_lock:
        _in_memory_channels.clear()
        _in_memory_buffers.clear()
        _in_memory_sequences.clear()



@pytest.mark.asyncio
async def test_replay_buffer_and_cursor_order():
    """Verify that subscribe_events_async accurately replays missed events with monotonic sequence IDs."""
    inv_id = str(uuid4())

    # Publish 5 events prior to subscription
    for i in range(1, 6):
        publish_event_sync(inv_id, {"type": "progress", "index": i, "step": f"Step {i}"})

    # Client connects asking for events since seq 2
    received = []
    async for event in subscribe_events_async(inv_id, since_seq=2):
        received.append(event)
        if event.get("index") == 5:
            break

    # Must receive events 3, 4, 5
    assert len(received) == 3
    assert [e["index"] for e in received] == [3, 4, 5]
    assert [e["seq"] for e in received] == [3, 4, 5]


@pytest.mark.asyncio
async def test_50_concurrent_streaming_clients_no_dropped_events():
    """
    Stress test: 50 concurrent subscribers reading events from a single investigation channel.
    Verifies zero dropped events, zero deadlocks, and total cleanup of queues on exit.
    """
    inv_id = str(uuid4())
    total_subscribers = 50
    events_to_publish = 30

    async def subscriber_task(sub_id: int) -> list[int]:
        collected = []
        async for event in subscribe_events_async(inv_id, since_seq=0):
            collected.append(event.get("index", 0))
            if len(collected) == events_to_publish:
                break
        return collected

    # Launch 50 concurrent subscriber tasks
    tasks = [asyncio.create_task(subscriber_task(i)) for i in range(total_subscribers)]

    # Give all tasks time to subscribe
    await asyncio.sleep(0.05)

    # Publish events sequentially
    for i in range(1, events_to_publish + 1):
        publish_event_sync(inv_id, {"type": "metric", "index": i})
        await asyncio.sleep(0.001)

    # Await all subscribers with a safety timeout to catch any deadlocks
    results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=10.0)

    assert len(results) == total_subscribers
    for idx, collected_seq in enumerate(results):
        assert len(collected_seq) == events_to_publish, f"Subscriber {idx} dropped events!"
        assert collected_seq == list(range(1, events_to_publish + 1))

    # Verify channel deregistration and zero memory leak
    channel = get_channel_name(inv_id)
    with _bus_lock:
        active_queues = len(_in_memory_channels.get(channel, []))
    assert active_queues == 0, f"Lingering active queues detected: {active_queues}"


@pytest.mark.asyncio
async def test_sse_endpoint_reconnection_with_last_event_id():
    """Test standard SSE reconnect using Last-Event-ID header and since_seq query param."""
    inv_id = str(uuid4())

    # Pre-publish 3 events
    publish_event_sync(inv_id, {"type": "entity", "name": "e1"})
    publish_event_sync(inv_id, {"type": "entity", "name": "e2"})
    publish_event_sync(inv_id, {"type": "completed", "name": "e3"})

    # Connect with Last-Event-ID: 1
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Last-Event-ID": "1"}
        response = await client.get(f"/api/v1/investigations/{inv_id}/events", headers=headers)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        body_text = response.text
        # Should contain connected event with cursor 1
        assert '"cursor": 1' in body_text
        # Should contain replayed events 2 and 3
        assert '"id": 2' in body_text or "id: 2" in body_text
        assert '"id": 3' in body_text or "id: 3" in body_text
        # Should not replay event 1
        assert '"name": "e1"' not in body_text
