from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.app.domain.enums import (
    ConfidenceLevel,
    EntityKind,
    InvestigationStatus,
    InvestigationType,
)
from src.app.domain.errors import InvalidStateTransitionError
from src.app.domain.value_objects import InvestigationSettings, Target, UserId


@dataclass(slots=True)
class Evidence:
    id: UUID = field(default_factory=uuid4)
    investigation_id: UUID = field(default_factory=uuid4)
    source: str = ""
    tool: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    raw_observation: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.OBSERVED
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Entity:
    id: UUID = field(default_factory=uuid4)
    investigation_id: UUID = field(default_factory=uuid4)
    kind: EntityKind = EntityKind.PROFILE
    value: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.OBSERVED
    attributes: dict[str, Any] = field(default_factory=dict)
    first_seen: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class Relationship:
    id: UUID = field(default_factory=uuid4)
    investigation_id: UUID = field(default_factory=uuid4)
    source_entity_id: UUID = field(default_factory=uuid4)
    target_entity_id: UUID = field(default_factory=uuid4)
    predicate: str = "associated_with"  # human-readable association
    confidence: ConfidenceLevel = ConfidenceLevel.SUPPORTED
    reasoning: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class Investigation:
    id: UUID
    name: str
    target: Target
    type: InvestigationType
    status: InvestigationStatus
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    created_by: UserId
    settings: InvestigationSettings
    entities_count: int = 0
    relationships_count: int = 0
    evidence_count: int = 0

    def transition_to(self, new_status: InvestigationStatus) -> None:
        valid_transitions = {
            InvestigationStatus.PENDING: {
                InvestigationStatus.RUNNING,
                InvestigationStatus.CANCELLED,
                InvestigationStatus.ERROR,
            },
            InvestigationStatus.RUNNING: {
                InvestigationStatus.WORKING,
                InvestigationStatus.CANCELLED,
                InvestigationStatus.ERROR,
            },
            InvestigationStatus.WORKING: {
                InvestigationStatus.WORKING,
                InvestigationStatus.REVIEW,
                InvestigationStatus.CANCELLED,
                InvestigationStatus.ERROR,
            },
            InvestigationStatus.REVIEW: {
                InvestigationStatus.REVIEW,
                InvestigationStatus.FINAL,
                InvestigationStatus.CANCELLED,
            },
            InvestigationStatus.FINAL: set(),
            InvestigationStatus.CANCELLED: set(),
            InvestigationStatus.ERROR: set(),
        }

        allowed = valid_transitions.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                f"Cannot transition investigation {self.id} from {self.status} to {new_status}"
            )

        self.status = new_status
        now = datetime.now(UTC)
        if new_status == InvestigationStatus.RUNNING and not self.started_at:
            self.started_at = now
        elif new_status in (
            InvestigationStatus.REVIEW,
            InvestigationStatus.FINAL,
            InvestigationStatus.CANCELLED,
            InvestigationStatus.ERROR,
        ):
            if not self.finished_at:
                self.finished_at = now
