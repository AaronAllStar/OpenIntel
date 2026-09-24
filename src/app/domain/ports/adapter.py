import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol
from uuid import UUID

from src.app.domain.enums import ConfidenceLevel, EntityKind, InfoClassification, TargetKind
from src.app.domain.errors import AdapterError
from src.app.domain.value_objects import Target


@dataclass(frozen=True, slots=True)
class EntityDraft:
    kind: EntityKind
    value: str
    confidence: ConfidenceLevel = ConfidenceLevel.OBSERVED
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EvidenceDraft:
    source: str
    tool: str
    raw_observation: str
    confidence: ConfidenceLevel = ConfidenceLevel.OBSERVED
    info_classification: InfoClassification = InfoClassification.PUBLIC_OBSERVATION
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RelationshipDraft:
    source_entity_value: str
    source_entity_kind: EntityKind
    target_entity_value: str
    target_entity_kind: EntityKind
    predicate: str
    confidence: ConfidenceLevel = ConfidenceLevel.SUPPORTED
    reasoning: str = ""


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


AdapterEvent = ProgressEvent | EntityEvent | RelationshipEvent | LogEvent | ErrorEvent


@dataclass(frozen=True, slots=True)
class AdapterOptions:
    depth: int | None = None
    timeout_ms: int = 30_000
    rate_limit: int | None = None
    max_results: int | None = None
    scope: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AdapterInput:
    target: Target
    investigation_id: UUID
    options: AdapterOptions = field(default_factory=AdapterOptions)


class OsintAdapter(Protocol):
    name: str
    version: str
    supported_targets: tuple[TargetKind, ...]

    def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]: ...
