from uuid import UUID, uuid4

from src.app.domain.enums import ConfidenceLevel
from src.app.domain.ports.adapter import EntityDraft, EvidenceDraft, RelationshipDraft
from src.app.infrastructure.models import EntityModel, EvidenceModel, RelationshipModel


class EntityNormalizer:
    """Normalizes, deduplicates, and creates associations for discovered OSINT data."""

    def __init__(self, investigation_id: UUID) -> None:
        self.investigation_id = investigation_id
        # Map (kind, value.lower()) -> EntityModel
        self.entity_registry: dict[tuple[str, str], EntityModel] = {}

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
        return new_entity, True

    def create_evidence(
        self,
        draft: EvidenceDraft,
        entity_id: UUID | None = None,
    ) -> EvidenceModel:
        return EvidenceModel(
            id=uuid4(),
            investigation_id=self.investigation_id,
            entity_id=entity_id,
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
    ) -> RelationshipModel | None:
        source_key = (draft.source_entity_kind.value, draft.source_entity_value.strip().lower())
        target_key = (draft.target_entity_kind.value, draft.target_entity_value.strip().lower())

        # Ensure both entities exist in the registry
        if source_key not in self.entity_registry:
            self.normalize_entity(
                EntityDraft(
                    kind=draft.source_entity_kind,
                    value=draft.source_entity_value.strip(),
                    confidence=ConfidenceLevel.OBSERVED,
                )
            )

        if target_key not in self.entity_registry:
            self.normalize_entity(
                EntityDraft(
                    kind=draft.target_entity_kind,
                    value=draft.target_entity_value.strip(),
                    confidence=ConfidenceLevel.OBSERVED,
                )
            )

        source_entity = self.entity_registry[source_key]
        target_entity = self.entity_registry[target_key]

        if source_entity.id == target_entity.id:
            return None

        return RelationshipModel(
            id=uuid4(),
            investigation_id=self.investigation_id,
            source_entity_id=source_entity.id,
            target_entity_id=target_entity.id,
            predicate=draft.predicate,
            confidence=draft.confidence.value,
            reasoning=draft.reasoning
            or f"Relationship discovered between {source_entity.value} and {target_entity.value}",
        )
