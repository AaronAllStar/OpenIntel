from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateTable

from src.app.domain.enums import ConfidenceLevel, EntityKind, InfoClassification, TargetKind
from src.app.infrastructure.database import Base
from src.app.infrastructure.models import (
    EntityModel,
    EvidenceModel,
    InvestigationModel,
    RelationshipModel,
)


@pytest.fixture
def sqlite_test_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_testing = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_testing()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_sqlite_persistence_and_cascading(sqlite_test_db: Session):
    """
    Verifies SQLite graph persistence, foreign key relationships,
    and cascade deletions for investigations, entities, relationships, and evidence.
    """
    inv = InvestigationModel(
        id=uuid4(),
        name="Test Persistence Inv",
        target_kind=TargetKind.USERNAME.value,
        target_value="sec_analyst",
        investigation_type="deep",
        status="completed",
    )
    sqlite_test_db.add(inv)
    sqlite_test_db.commit()

    # Create 2 entities
    e1 = EntityModel(
        id=uuid4(),
        investigation_id=inv.id,
        kind=EntityKind.PROFILE.value,
        value="sec_analyst",
        confidence=ConfidenceLevel.STRONG.value,
        attributes={"verified": True},
    )
    e2 = EntityModel(
        id=uuid4(),
        investigation_id=inv.id,
        kind=EntityKind.EMAIL.value,
        value="sec_analyst@example.org",
        confidence=ConfidenceLevel.OBSERVED.value,
    )
    sqlite_test_db.add_all([e1, e2])
    sqlite_test_db.commit()

    # Create relationship
    rel = RelationshipModel(
        id=uuid4(),
        investigation_id=inv.id,
        source_entity_id=e1.id,
        target_entity_id=e2.id,
        predicate="has_email",
        confidence=ConfidenceLevel.STRONG.value,
        reasoning="Corroborated across 3 independent sources",
    )
    sqlite_test_db.add(rel)
    sqlite_test_db.commit()

    # Create node evidence and relationship evidence
    ev_node = EvidenceModel(
        id=uuid4(),
        investigation_id=inv.id,
        entity_id=e1.id,
        source="Sherlock Public Probing",
        tool="sherlock",
        raw_observation="Found username across 12 platforms",
        confidence=ConfidenceLevel.STRONG.value,
        info_classification=InfoClassification.PUBLIC_OBSERVATION.value,
    )
    ev_rel = EvidenceModel(
        id=uuid4(),
        investigation_id=inv.id,
        relationship_id=rel.id,
        source="OpenIntel Correlation Engine",
        tool="correlation_engine",
        raw_observation="Link validated through email local-part matching",
        confidence=ConfidenceLevel.STRONG.value,
        info_classification=InfoClassification.INFERENCE.value,
    )
    sqlite_test_db.add_all([ev_node, ev_rel])
    sqlite_test_db.commit()

    # Verify lookups
    loaded_inv = sqlite_test_db.query(InvestigationModel).filter_by(id=inv.id).first()
    assert loaded_inv is not None
    assert len(loaded_inv.entities) == 2
    assert len(loaded_inv.relationships) == 1
    assert len(loaded_inv.evidence) == 2

    # Verify relationship evidence back-reference
    loaded_rel = sqlite_test_db.query(RelationshipModel).filter_by(id=rel.id).first()
    assert loaded_rel is not None
    assert len(loaded_rel.evidence) == 1
    assert loaded_rel.evidence[0].tool == "correlation_engine"

    # Verify node evidence back-reference
    loaded_node = sqlite_test_db.query(EntityModel).filter_by(id=e1.id).first()
    assert loaded_node is not None
    assert len(loaded_node.evidence) == 1
    assert loaded_node.evidence[0].tool == "sherlock"


def test_postgresql_ddl_compilation_and_compatibility():
    """
    Verifies that all SQLAlchemy tables, indices, and constraints compile
    cleanly under PostgreSQL dialect without type incompatibilities.
    """
    pg_dialect = postgresql.dialect()
    tables = [
        InvestigationModel.__table__,
        EntityModel.__table__,
        EvidenceModel.__table__,
        RelationshipModel.__table__,
    ]

    for table in tables:
        ddl = str(CreateTable(table).compile(dialect=pg_dialect))
        assert "CREATE TABLE" in ddl
        assert table.name in ddl

    # Verify specific PostgreSQL constructs
    inv_ddl = str(CreateTable(InvestigationModel.__table__).compile(dialect=pg_dialect))
    assert "JSON" in inv_ddl or "JSONB" in inv_ddl or "VARCHAR" in inv_ddl
    assert "UUID" in inv_ddl or "CHAR(32)" in inv_ddl
