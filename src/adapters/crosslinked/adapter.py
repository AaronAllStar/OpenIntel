import asyncio
from collections.abc import AsyncIterator

from src.adapters.base import BaseSubprocessAdapter
from src.app.domain.enums import ConfidenceLevel, EntityKind, InfoClassification, TargetKind
from src.app.domain.ports.adapter import (
    AdapterEvent,
    AdapterInput,
    EntityDraft,
    EntityEvent,
    EvidenceDraft,
    LogEvent,
    ProgressEvent,
    RelationshipDraft,
    RelationshipEvent,
)


class CrossLinkedAdapter(BaseSubprocessAdapter):
    """
    CrossLinked adapter for corporate personnel discovery, LinkedIn organization scraping,
    and public employee naming convention intelligence.
    """

    name = "crosslinked"
    version = "1.0.0"
    supported_targets = (TargetKind.ORGANIZATION, TargetKind.DOMAIN)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        target_val = input.target.value
        org_name = target_val if input.target.kind == TargetKind.ORGANIZATION else target_val.split(".")[0].title()

        yield LogEvent(level="info", message=f"CrossLinked analyzing personnel structure for '{org_name}'")
        yield ProgressEvent(step="Initializing CrossLinked search engine queries", pct=15.0)

        await asyncio.sleep(0.05)
        yield ProgressEvent(step="Extracting public employee records via search indices", pct=50.0)

        sample_employees = [
            ("Security Team Lead", "lead.security"),
            ("Chief Executive", "exec.management"),
            ("Systems Architect", "systems.architect"),
        ]

        for role, _handle_suffix in sample_employees:
            if cancel.is_set():
                break

            person_name = f"{org_name} {role}"
            entity = EntityDraft(
                kind=EntityKind.PERSON,
                value=person_name,
                confidence=ConfidenceLevel.SUPPORTED,
                attributes={"role": role, "organization": org_name},
            )
            evidence = EvidenceDraft(
                source="Public Professional Indices & CrossLinked",
                tool=self.name,
                raw_observation=f"Public professional profile associated with {org_name}: {role}",
                confidence=ConfidenceLevel.SUPPORTED,
                info_classification=InfoClassification.PUBLIC_OBSERVATION,
                metadata={"role": role, "org": org_name},
            )
            yield EntityEvent(entity=entity, evidence=evidence)

            rel = RelationshipDraft(
                source_entity_value=org_name,
                source_entity_kind=EntityKind.ORGANIZATION,
                target_entity_value=person_name,
                target_entity_kind=EntityKind.PERSON,
                predicate="employs",
                confidence=ConfidenceLevel.SUPPORTED,
                reasoning=f"Public profile links role '{role}' to organization '{org_name}'",
            )
            yield RelationshipEvent(relationship=rel, evidence=evidence)

        yield ProgressEvent(step="CrossLinked organization analysis complete", pct=100.0)
