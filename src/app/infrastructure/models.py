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

    __table_args__ = (
        Index("ix_entities_inv_kind_val", "investigation_id", "kind", "value"),
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

    __table_args__ = (
        Index("ix_evidence_inv_tool", "investigation_id", "tool"),
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

    __table_args__ = (
        Index("ix_relationships_inv_entities", "investigation_id", "source_entity_id", "target_entity_id"),
    )
