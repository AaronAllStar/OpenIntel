import asyncio
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest

from src.adapters.circuit_breaker import CircuitBreaker
from src.adapters.osint_executor import execute_adapters
from src.app.application.investigation_service import InvestigationService
from src.app.application.worker_tasks import execute_investigation_async
from src.app.domain.enums import ConfidenceLevel, EntityKind, TargetKind
from src.app.domain.ports.adapter import (
    AdapterEvent,
    AdapterInput,
    AdapterOptions,
    EngineStatusEvent,
    EntityDraft,
    EntityEvent,
    EvidenceDraft,
    OsintAdapter,
    RelationshipDraft,
    RelationshipEvent,
)
from src.app.domain.value_objects import Target
from src.app.infrastructure.config import get_settings
from src.app.infrastructure.database import Base, SessionLocal, engine
from src.app.infrastructure.models import InvestigationModel


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setattr(get_settings(), "ENV", "test")
    Base.metadata.create_all(bind=engine)
    yield


class HealthyAdapter:
    name = "healthy_adapter"
    version = "1.0.0"
    supported_targets = (TargetKind.USERNAME,)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        entity = EntityDraft(
            kind=EntityKind.PROFILE,
            value="https://example.com/healthy",
            confidence=ConfidenceLevel.OBSERVED,
            attributes={"platform": "HealthyPlatform"},
        )
        evidence = EvidenceDraft(
            source="HealthyPlatform",
            tool=self.name,
            raw_observation="Found healthy profile",
            confidence=ConfidenceLevel.OBSERVED,
        )
        yield EntityEvent(entity=entity, evidence=evidence)

        rel = RelationshipDraft(
            source_entity_value=input.target.value,
            source_entity_kind=EntityKind.PROFILE,
            target_entity_value="https://example.com/healthy",
            target_entity_kind=EntityKind.PROFILE,
            predicate="has_account_on",
            confidence=ConfidenceLevel.SUPPORTED,
        )
        yield RelationshipEvent(relationship=rel, evidence=evidence)


class HungAdapter:
    name = "hung_adapter"
    version = "1.0.0"
    supported_targets = (TargetKind.USERNAME,)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        # Sleep for a long time simulating an unresponsive engine/network hang
        await asyncio.sleep(10.0)
        # Should not reach here because timeout is small
        yield EntityEvent(
            entity=EntityDraft(kind=EntityKind.PROFILE, value="https://example.com/never"),
            evidence=EvidenceDraft(source="Hang", tool=self.name, raw_observation="never"),
        )


class CrashingAdapter:
    name = "crashing_adapter"
    version = "1.0.0"
    supported_targets = (TargetKind.USERNAME,)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        # Async generator raising an unexpected crash
        if False:
            yield  # Ensures Python compiles this as an async generator
        raise RuntimeError("Engine segmentation fault / unhandled crash")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_hung_and_crashing_engines_return_partial_results():
    """
    Acceptance Criteria:
    A test simulating a hung engine and another that raises;
    the investigation finishes with a partial result and correct statuses.
    """
    target = Target(kind=TargetKind.USERNAME, value="resilience_user")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(timeout_ms=200),  # 200ms timeout
    )
    cancel_event = asyncio.Event()

    adapters: list[OsintAdapter] = [
        HealthyAdapter(),
        HungAdapter(),
        CrashingAdapter(),
    ]

    events: list[AdapterEvent] = []
    async for event in execute_adapters(adapters, adapter_input, cancel_event, max_concurrency=3):
        events.append(event)

    # 1. Verify all three engine statuses are captured
    status_events = [e for e in events if isinstance(e, EngineStatusEvent)]
    status_map = {s.engine: s.status for s in status_events}

    assert status_map.get("healthy_adapter") == "ok"
    assert status_map.get("hung_adapter") == "timeout"
    assert status_map.get("crashing_adapter") == "error"

    # 2. Verify partial results from healthy adapter were preserved
    entity_events = [e for e in events if isinstance(e, EntityEvent)]
    assert len(entity_events) == 1
    assert entity_events[0].entity.value == "https://example.com/healthy"

    rel_events = [e for e in events if isinstance(e, RelationshipEvent)]
    assert len(rel_events) == 1
    assert rel_events[0].relationship.predicate == "has_account_on"


@pytest.mark.asyncio
async def test_end_to_end_investigation_with_partial_results_in_db():
    """
    Verifies that worker_tasks properly updates database with partial results
    and per-engine statuses when some engines fail or time out.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        inv = InvestigationService.create_investigation(
            db=db,
            name="Resilience E2E Test",
            target_kind=TargetKind.USERNAME,
            target_value="test_analyst",
            settings={"timeout_ms": 5000, "selected_engines": ["sherlock"]},
        )
        inv_id_str = str(inv.id)

        # Execute investigation
        await execute_investigation_async(inv_id_str)

        # Reload investigation detail from DB
        db.expire_all()
        detail = InvestigationService.get_investigation_detail(db, inv.id)

        assert detail["status"] == "review"
        assert "engine_statuses" in detail
        assert isinstance(detail["engine_statuses"], dict)
        assert detail["engine_statuses"].get("sherlock") == "ok"
        assert len(detail["entities"]) > 0
        assert len(detail["evidence"]) > 0
        assert len(detail["relationships"]) > 0

    finally:
        db.close()


@pytest.mark.asyncio
async def test_in_flight_cancellation():
    """
    Verifies clean cancellation: when cancel signal is triggered,
    in-flight engines stop promptly and investigation finishes in CANCELLED status.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        inv = InvestigationService.create_investigation(
            db=db,
            name="Cancellation Test",
            target_kind=TargetKind.USERNAME,
            target_value="cancel_user",
            settings={"timeout_ms": 10000, "selected_engines": ["sherlock"]},
        )
        inv_id_str = str(inv.id)

        # Launch worker in background
        task = asyncio.create_task(execute_investigation_async(inv_id_str))

        # Yield control to let worker start
        await asyncio.sleep(0.02)

        # Trigger cancellation via manager
        success = InvestigationService.cancel_investigation(db, inv.id)
        assert success is True

        # Wait for worker task to finalize
        await task

        # Verify investigation status is cancelled
        db.expire_all()
        refreshed = db.query(InvestigationModel).filter_by(id=inv.id).first()
        assert refreshed is not None
        assert refreshed.status == "cancelled"
        assert refreshed.finished_at is not None

    finally:
        db.close()


def test_circuit_breaker_tripping():
    """
    Verifies that after consecutive failures, circuit breaker enters OPEN state
    and skips further execution attempts.
    """
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=10.0)
    engine_name = "test_engine"

    assert cb.can_execute(engine_name) is True
    assert cb.get_state(engine_name) == "closed"

    # Record 2 failures (threshold not reached)
    cb.record_failure(engine_name, "error 1")
    cb.record_failure(engine_name, "error 2")
    assert cb.can_execute(engine_name) is True

    # 3rd failure trips the circuit breaker
    cb.record_failure(engine_name, "error 3")
    assert cb.get_state(engine_name) == "open"
    assert cb.can_execute(engine_name) is False

    # Success after reset returns to closed
    cb.reset(engine_name)
    assert cb.can_execute(engine_name) is True
    assert cb.get_state(engine_name) == "closed"
