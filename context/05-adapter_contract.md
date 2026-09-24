# OpenIntel — Adapter Contract

## Purpose
Every OSINT engine is wrapped by exactly one adapter that satisfies this contract.
The rest of OpenIntel never knows which engine produced a result.

## Non-negotiables
- Adapters live in `infrastructure/adapters/<engine>/`.
- Adapters implement a port declared in `domain/ports/`.
- Adapters never leak engine-specific types outside their folder.
- Adapters never write to the DB. They yield data; the application persists it.
- Adapters never call other adapters.
- Adapters are async. Blocking engines (most of them) wrap subprocess or thread execution.

## Port shape

```python
# domain/ports/adapter.py
from collections.abc import AsyncIterator
from typing import Protocol
import asyncio

class OsintAdapter(Protocol):
    name: str                    # "sherlock"
    version: str                 # adapter's own version, not the engine's
    supported_targets: tuple[TargetKind, ...]

    def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]: ...


@dataclass(frozen=True, slots=True)
class AdapterInput:
    target: Target
    investigation_id: UUID
    options: AdapterOptions


@dataclass(frozen=True, slots=True)
class AdapterOptions:
    depth: int | None = None
    timeout_ms: int = 30_000
    rate_limit: int | None = None
    max_results: int | None = None
    scope: tuple[str, ...] = ()


AdapterEvent = (
    ProgressEvent | EntityEvent | RelationshipEvent | LogEvent | ErrorEvent
)

@dataclass(frozen=True, slots=True)
class ProgressEvent:
    step: str
    pct: float | None = None

@dataclass(frozen=True, slots=True)
class EntityEvent:
    entity: EntityDraft
    evidence: EvidenceDraft

@dataclass(frozen=True, slots=True)
class RelationshipEvent:
    relationship: RelationshipDraft
    evidence: EvidenceDraft

@dataclass(frozen=True, slots=True)
class LogEvent:
    level: Literal["debug", "info", "warn"]
    message: str

@dataclass(frozen=True, slots=True)
class ErrorEvent:
    error: AdapterError