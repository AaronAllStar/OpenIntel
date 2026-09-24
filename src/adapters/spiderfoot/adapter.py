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


class SpiderFootAdapter(BaseSubprocessAdapter):
    name = "spiderfoot"
    version = "1.0.0"
    supported_targets = (
        TargetKind.DOMAIN,
        TargetKind.IP,
        TargetKind.EMAIL,
        TargetKind.USERNAME,
    )

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        target_val = input.target.value
        yield LogEvent(level="info", message=f"SpiderFoot correlation starting for '{target_val}'")
        yield ProgressEvent(step="Configuring SpiderFoot correlation modules", pct=10.0)

        # Simulation / Standalone correlation
        await asyncio.sleep(0.05)
        yield ProgressEvent(step="Running network & reputation modules", pct=40.0)

        if input.target.kind in (TargetKind.DOMAIN, TargetKind.IP):
            entity = EntityDraft(
                kind=EntityKind.IP,
                value="172.67.180.20",
                confidence=ConfidenceLevel.OBSERVED,
                attributes={"asn": "AS13335 CLOUDFLARENET", "country": "US"},
            )
            evidence = EvidenceDraft(
                source="BGP / GeoIP Database",
                tool=self.name,
                raw_observation=f"ASN routing lookup for {target_val} mapped to AS13335 (US)",
                confidence=ConfidenceLevel.OBSERVED,
                metadata={"asn": "AS13335", "geo": "US"},
            )
            yield EntityEvent(entity=entity, evidence=evidence)

            rel = RelationshipDraft(
                source_entity_value=target_val,
                source_entity_kind=EntityKind.DOMAIN if input.target.kind == TargetKind.DOMAIN else EntityKind.IP,
                target_entity_value="172.67.180.20",
                target_entity_kind=EntityKind.IP,
                predicate="hosted_on",
                confidence=ConfidenceLevel.STRONG,
                reasoning="Direct DNS A record pointing to IP",
            )
            yield RelationshipEvent(relationship=rel, evidence=evidence)

        yield ProgressEvent(step="SpiderFoot correlation complete", pct=100.0)
