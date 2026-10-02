import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal, Protocol
from uuid import UUID

from src.app.domain.enums import ConfidenceLevel, EntityKind, InfoClassification, TargetKind
from src.app.domain.errors import AdapterError
from src.app.domain.value_objects import Target


@dataclass(frozen=True, slots=True)
class LegalityMetadata:
    """Metadata describing the legal classification and operational profile of an adapter."""

    default_classification: InfoClassification = InfoClassification.PUBLIC_OBSERVATION
    requires_auth: bool = False
    requires_network: bool = True
    requires_binary: bool = False
    description: str = ""


@dataclass(frozen=True, slots=True)
class HealthStatus:
    """Represents the runtime health and readiness of an OSINT adapter."""

    is_healthy: bool
    status: Literal["ready", "degraded", "unavailable"]
    message: str
    details: dict[str, Any] = field(default_factory=dict)


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
class Observation:
    """
    Unified, versioned output schema representing a normalized observation
    with mandatory provenance and legal classification.
    """

    source: str
    tool: str
    raw_observation: str
    confidence: ConfidenceLevel
    info_classification: InfoClassification
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    entity: EntityDraft | None = None
    relationship: RelationshipDraft | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


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


@dataclass(frozen=True, slots=True)
class EngineStatusEvent:
    engine: str
    status: Literal["ok", "timeout", "error", "skipped", "cancelled"]
    duration_ms: float
    error: str | None = None


AdapterEvent = (
    ProgressEvent
    | EntityEvent
    | RelationshipEvent
    | LogEvent
    | ErrorEvent
    | EngineStatusEvent
)


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
    capabilities: tuple[str, ...]
    supported_targets: tuple[TargetKind, ...]
    legality_metadata: LegalityMetadata

    def health_check(self) -> HealthStatus: ...

    def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]: ...


class BaseAdapter(ABC):
    """
    Abstract base class providing standard defaults for OpenIntel adapters.
    Subclasses only need to define name, supported_targets, capabilities, and implement run().
    """

    name: str
    version: str = "1.0.0"
    capabilities: tuple[str, ...] = ()
    supported_targets: tuple[TargetKind, ...] = ()
    legality_metadata: LegalityMetadata = LegalityMetadata()

    def health_check(self) -> HealthStatus:
        """Default health check: ready unless external requirements are declared."""
        return HealthStatus(
            is_healthy=True,
            status="ready",
            message=f"Adapter {self.name} v{self.version} is ready",
            details={"version": self.version, "capabilities": list(self.capabilities)},
        )

    @abstractmethod
    def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]: ...
