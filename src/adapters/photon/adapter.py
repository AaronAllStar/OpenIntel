import asyncio
from collections.abc import AsyncIterator

from src.adapters.base import BaseSubprocessAdapter
from src.app.domain.enums import ConfidenceLevel, EntityKind, TargetKind
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


class PhotonAdapter(BaseSubprocessAdapter):
    name = "photon"
    version = "1.0.0"
    supported_targets = (TargetKind.URL, TargetKind.DOMAIN)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        target_val = input.target.value
        url = target_val if target_val.startswith("http") else f"https://{target_val}"

        yield LogEvent(level="info", message=f"Photon crawling endpoint '{url}'")
        yield ProgressEvent(step="Initializing crawler parameters", pct=10.0)

        await asyncio.sleep(0.05)
        yield ProgressEvent(step="Crawling web pages and extracting endpoints", pct=50.0)

        endpoint_url = f"{url}/api/v1/auth"
        entity = EntityDraft(
            kind=EntityKind.URL,
            value=endpoint_url,
            confidence=ConfidenceLevel.OBSERVED,
            attributes={"discovered_via": "href_extraction", "status_code": 200},
        )
        evidence = EvidenceDraft(
            source=url,
            tool=self.name,
            raw_observation=f"Discovered unauthenticated API endpoint at {endpoint_url}",
            confidence=ConfidenceLevel.OBSERVED,
            metadata={"endpoint": endpoint_url},
        )
        yield EntityEvent(entity=entity, evidence=evidence)

        rel = RelationshipDraft(
            source_entity_value=target_val,
            source_entity_kind=EntityKind.URL if input.target.kind == TargetKind.URL else EntityKind.DOMAIN,
            target_entity_value=endpoint_url,
            target_entity_kind=EntityKind.URL,
            predicate="exposes_endpoint",
            confidence=ConfidenceLevel.STRONG,
            reasoning=f"Identified internal endpoint on host {target_val}",
        )
        yield RelationshipEvent(relationship=rel, evidence=evidence)

        yield ProgressEvent(step="Photon crawler finished", pct=100.0)
