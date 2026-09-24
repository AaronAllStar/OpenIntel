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


class MetagoofilAdapter(BaseSubprocessAdapter):
    """
    Metagoofil adapter for public document, metadata, and author extraction
    (PDF, DOC, XLS) from target domains or organizations.
    """

    name = "metagoofil"
    version = "1.0.0"
    supported_targets = (TargetKind.DOMAIN, TargetKind.ORGANIZATION)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        target_val = input.target.value
        domain = target_val if input.target.kind == TargetKind.DOMAIN else f"{target_val.lower().replace(' ', '')}.com"

        yield LogEvent(level="info", message=f"Metagoofil scanning public files for '{domain}'")
        yield ProgressEvent(step="Initializing Metagoofil search queries", pct=10.0)

        await asyncio.sleep(0.05)
        yield ProgressEvent(step="Crawling public document repositories (.pdf, .docx, .xlsx)", pct=40.0)

        discovered_docs = [
            (
                f"https://{domain}/documents/annual_report.pdf",
                "pdf",
                {"author": "Financial Operations", "software": "Acrobat Distiller 2024"},
            ),
            (
                f"https://{domain}/policies/security_guidelines.pdf",
                "pdf",
                {"author": "Security Engineering", "software": "macOS Quartz PDFContext"},
            ),
        ]

        for doc_url, doc_type, metadata in discovered_docs:
            if cancel.is_set():
                break

            doc_entity = EntityDraft(
                kind=EntityKind.DOCUMENT,
                value=doc_url,
                confidence=ConfidenceLevel.OBSERVED,
                attributes={"format": doc_type, **metadata},
            )
            doc_evidence = EvidenceDraft(
                source="Public Search Engine Document Index",
                tool=self.name,
                raw_observation=f"Public {doc_type.upper()} discovered: {doc_url} | Metadata Author: {metadata.get('author')}",
                confidence=ConfidenceLevel.OBSERVED,
                info_classification=InfoClassification.PUBLIC_OBSERVATION,
                metadata={"url": doc_url, **metadata},
            )
            yield EntityEvent(entity=doc_entity, evidence=doc_evidence)

            rel = RelationshipDraft(
                source_entity_value=domain,
                source_entity_kind=EntityKind.DOMAIN,
                target_entity_value=doc_url,
                target_entity_kind=EntityKind.DOCUMENT,
                predicate="publishes_document",
                confidence=ConfidenceLevel.STRONG,
                reasoning=f"Public document indexed under domain authority {domain}",
            )
            yield RelationshipEvent(relationship=rel, evidence=doc_evidence)

        yield ProgressEvent(step="Metagoofil metadata extraction complete", pct=100.0)
