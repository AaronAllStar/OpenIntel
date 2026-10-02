from uuid import UUID, uuid4

from src.app.domain.enums import ConfidenceLevel
from src.app.domain.ports.adapter import EntityDraft, EvidenceDraft, RelationshipDraft
from src.app.infrastructure.models import EntityModel, EvidenceModel, RelationshipModel


class EntityNormalizer:
    """
    Normalizes, deduplicates, and creates associations for discovered OSINT data.
    Ensures relational consistency, prevents duplicate edges, and manages entity lookups.
    """

    def __init__(self, investigation_id: UUID) -> None:
        self.investigation_id = investigation_id
        # Map (kind, value.lower()) -> EntityModel
        self.entity_registry: dict[tuple[str, str], EntityModel] = {}
        # Map entity_id -> EntityModel
        self.entities_by_id: dict[UUID, EntityModel] = {}
        # Set of (source_id, predicate, target_id) to avoid duplicate edges
        self.relationship_keys: set[tuple[UUID, str, UUID]] = set()

    def get_entity_by_id(self, entity_id: UUID) -> EntityModel | None:
        return self.entities_by_id.get(entity_id)

    def normalize_entity(self, draft: EntityDraft) -> tuple[EntityModel, bool]:
        """
        Deduplicates entity by (kind, normalized_value).
        Returns (EntityModel, is_new).
        """
        clean_val = draft.value.strip()
        key = (draft.kind.value, clean_val.lower())

        if key in self.entity_registry:
            existing = self.entity_registry[key]
            # Merge any new attributes
            if draft.attributes:
                existing.attributes = {**existing.attributes, **draft.attributes}
            return existing, False

        new_entity = EntityModel(
            id=uuid4(),
            investigation_id=self.investigation_id,
            kind=draft.kind.value,
            value=clean_val,
            confidence=draft.confidence.value,
            attributes=draft.attributes or {},
        )
        self.entity_registry[key] = new_entity
        self.entities_by_id[new_entity.id] = new_entity
        return new_entity, True

    def create_evidence(
        self,
        draft: EvidenceDraft,
        entity_id: UUID | None = None,
        relationship_id: UUID | None = None,
    ) -> EvidenceModel:
        return EvidenceModel(
            id=uuid4(),
            investigation_id=self.investigation_id,
            entity_id=entity_id,
            relationship_id=relationship_id,
            source=draft.source,
            tool=draft.tool,
            raw_observation=draft.raw_observation,
            confidence=draft.confidence.value,
            info_classification=draft.info_classification.value,
            metadata_json=draft.metadata or {},
        )

    def normalize_relationship(
        self,
        draft: RelationshipDraft,
    ) -> tuple[RelationshipModel | None, list[EntityModel]]:
        """
        Normalizes relationship and returns (rel_model, newly_created_entities).
        The returned entities must be added to the database session before committing rel_model.
        """
        source_key = (draft.source_entity_kind.value, draft.source_entity_value.strip().lower())
        target_key = (draft.target_entity_kind.value, draft.target_entity_value.strip().lower())

        new_entities: list[EntityModel] = []

        # Ensure both entities exist in the registry
        if source_key not in self.entity_registry:
            source_ent, is_new = self.normalize_entity(
                EntityDraft(
                    kind=draft.source_entity_kind,
                    value=draft.source_entity_value.strip(),
                    confidence=ConfidenceLevel.OBSERVED,
                )
            )
            if is_new:
                new_entities.append(source_ent)

        if target_key not in self.entity_registry:
            target_ent, is_new = self.normalize_entity(
                EntityDraft(
                    kind=draft.target_entity_kind,
                    value=draft.target_entity_value.strip(),
                    confidence=ConfidenceLevel.OBSERVED,
                )
            )
            if is_new:
                new_entities.append(target_ent)

        source_entity = self.entity_registry[source_key]
        target_entity = self.entity_registry[target_key]

        if source_entity.id == target_entity.id:
            return None, new_entities

        edge_key = (source_entity.id, draft.predicate, target_entity.id)
        if edge_key in self.relationship_keys:
            # Duplicate relationship edge, deduplicate
            return None, new_entities

        self.relationship_keys.add(edge_key)

        rel = RelationshipModel(
            id=uuid4(),
            investigation_id=self.investigation_id,
            source_entity_id=source_entity.id,
            target_entity_id=target_entity.id,
            predicate=draft.predicate,
            confidence=draft.confidence.value,
            reasoning=draft.reasoning
            or f"Relationship discovered between {source_entity.value} and {target_entity.value}",
        )
        return rel, new_entities
