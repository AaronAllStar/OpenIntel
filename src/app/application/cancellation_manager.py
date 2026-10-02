import asyncio

from src.app.infrastructure.logging import logger


class CancellationManager:
    """
    Centralized registry for active investigation cancellation tokens.
    Coordinates immediate in-flight cancellation across async adapters,
    worker tasks, and API control endpoints.
    """

    def __init__(self) -> None:
        self._events: dict[str, asyncio.Event] = {}
        self._lock = asyncio.Lock()

    def get_or_create(self, investigation_id: str) -> asyncio.Event:
        if investigation_id not in self._events:
            self._events[investigation_id] = asyncio.Event()
        return self._events[investigation_id]

    def cancel(self, investigation_id: str) -> bool:
        """Signals cancellation to all workers running this investigation."""
        event = self._events.get(investigation_id)
        if event is not None:
            event.set()
            logger.info("Cancellation token triggered", investigation_id=investigation_id)

        # Broadcast cancellation signal via Redis bus if configured
        try:
            from src.app.infrastructure.redis_bus import publish_event_sync
            publish_event_sync(investigation_id, {
                "type": "cancelled",
                "action": "cancel",
                "status": "cancelled",
                "message": "Investigation cancelled by user request",
            })
        except Exception as exc:
            logger.debug("Failed to publish cancellation event to Redis", error=str(exc))

        return True

    def is_cancelled(self, investigation_id: str) -> bool:
        event = self._events.get(investigation_id)
        return event.is_set() if event is not None else False

    def remove(self, investigation_id: str) -> None:
        self._events.pop(investigation_id, None)


cancellation_manager = CancellationManager()
