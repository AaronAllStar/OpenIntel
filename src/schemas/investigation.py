from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.app.domain.enums import InvestigationType, TargetKind


class CreateInvestigationRequest(BaseModel):
    name: str | None = None
    target_kind: TargetKind
    target_value: str = Field(min_length=1, max_length=512)
    investigation_type: InvestigationType = InvestigationType.QUICK
    settings: dict[str, Any] = Field(default_factory=dict)


class InvestigationListItemResponse(BaseModel):
    id: UUID
    name: str
    target_kind: str
    target_value: str
    type: str
    status: str
    created_at: str | None
    started_at: str | None
    finished_at: str | None
    entities_count: int
    evidence_count: int
    relationships_count: int


class EntityResponse(BaseModel):
    id: str
    kind: str
    value: str
    confidence: str
    attributes: dict[str, Any]
    first_seen: str | None


class EvidenceResponse(BaseModel):
    id: str
    entity_id: str | None
    source: str
    tool: str
    timestamp: str | None
    raw_observation: str
    confidence: str
    info_classification: str = "PUBLIC_OBSERVATION"
    metadata: dict[str, Any]


class RelationshipResponse(BaseModel):
    id: str
    source_entity_id: str
    target_entity_id: str
    predicate: str
    confidence: str
    reasoning: str
    created_at: str | None


class InvestigationDetailResponse(BaseModel):
    id: UUID
    name: str
    target_kind: str
    target_value: str
    type: str
    status: str
    created_at: str | None
    started_at: str | None
    finished_at: str | None
    settings: dict[str, Any]
    error_message: str | None
    entities: list[EntityResponse]
    evidence: list[EvidenceResponse]
    relationships: list[RelationshipResponse]
