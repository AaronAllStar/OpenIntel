import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.infrastructure.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class InvestigationModel(Base):
    __tablename__ = "investigations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    target_value: Mapped[str] = mapped_column(String(512), nullable=False)
    investigation_type: Mapped[str] = mapped_column(String(50), nullable=False, default="quick")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    entities: Mapped[list["EntityModel"]] = relationship(
        "EntityModel", back_populates="investigation", cascade="all, delete-orphan"
    )
    evidence: Mapped[list["EvidenceModel"]] = relationship(
        "EvidenceModel", back_populates="investigation", cascade="all, delete-orphan"
    )
    relationships: Mapped[list["RelationshipModel"]] = relationship(
        "RelationshipModel", back_populates="investigation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_investigations_status", "status"),
        Index("ix_investigations_created_at", "created_at"),
    )


class EntityModel(Base):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(String(512), nullable=False)
    confidence: Mapped[str] = mapped_column(String(50), nullable=False, default="observed")
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="entities"
    )
    evidence: Mapped[list["EvidenceModel"]] = relationship(
        "EvidenceModel",
        back_populates="entity",
        cascade="all, delete-orphan",
        foreign_keys="EvidenceModel.entity_id",
    )

    __table_args__ = (
        Index("ix_entities_inv_kind_val", "investigation_id", "kind", "value"),
        Index("ix_entities_inv_id", "investigation_id", "id"),
    )


class EvidenceModel(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("entities.id", ondelete="SET NULL"), nullable=True
    )
    relationship_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("relationships.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    tool: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    raw_observation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence: Mapped[str] = mapped_column(String(50), nullable=False, default="observed")
    info_classification: Mapped[str] = mapped_column(String(50), nullable=False, default="PUBLIC_OBSERVATION")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="evidence"
    )
    entity: Mapped["EntityModel | None"] = relationship(
        "EntityModel", back_populates="evidence", foreign_keys=[entity_id]
    )
    relationship: Mapped["RelationshipModel | None"] = relationship(
        "RelationshipModel", back_populates="evidence", foreign_keys=[relationship_id]
    )

    __table_args__ = (
        Index("ix_evidence_inv_tool", "investigation_id", "tool"),
        Index("ix_evidence_inv_entity", "investigation_id", "entity_id"),
        Index("ix_evidence_inv_rel", "investigation_id", "relationship_id"),
        Index("ix_evidence_entity_id", "entity_id"),
        Index("ix_evidence_relationship_id", "relationship_id"),
    )


class RelationshipModel(Base):
    __tablename__ = "relationships"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False
    )
    source_entity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    target_entity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    predicate: Mapped[str] = mapped_column(String(100), nullable=False, default="associated_with")
    confidence: Mapped[str] = mapped_column(String(50), nullable=False, default="supported")
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="relationships"
    )
    evidence: Mapped[list["EvidenceModel"]] = relationship(
        "EvidenceModel",
        back_populates="relationship",
        cascade="all, delete-orphan",
        foreign_keys="EvidenceModel.relationship_id",
    )

    __table_args__ = (
        Index("ix_relationships_inv_entities", "investigation_id", "source_entity_id", "target_entity_id"),
        Index("ix_relationships_source", "source_entity_id"),
        Index("ix_relationships_target", "target_entity_id"),
    )


class AuditLogModel(Base):
    """Immutable audit trail of all security-sensitive actions and investigations."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, default="anonymous")
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="analyst")
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="SUCCESS")
    details_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    __table_args__ = (
        Index("ix_audit_logs_timestamp", "timestamp"),
        Index("ix_audit_logs_user", "user_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )

