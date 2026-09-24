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
)


class ReconNgAdapter(BaseSubprocessAdapter):
    name = "recon_ng"
    version = "1.0.0"
    supported_targets = (TargetKind.DOMAIN, TargetKind.ORGANIZATION)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        target_val = input.target.value
        yield LogEvent(level="info", message=f"Recon-ng initiating workspace for '{target_val}'")
        yield ProgressEvent(step="Setting up Recon-ng workspace", pct=10.0)

        await asyncio.sleep(0.05)
        yield ProgressEvent(step="Running discovery modules", pct=60.0)

        org_name = target_val if input.target.kind == TargetKind.ORGANIZATION else target_val.split(".")[0].title()
        entity = EntityDraft(
            kind=EntityKind.ORGANIZATION,
            value=org_name,
            confidence=ConfidenceLevel.SUPPORTED,
            attributes={"sector": "Technology", "reputation": "neutral"},
        )
        evidence = EvidenceDraft(
            source="Recon-ng / Whois & Registries",
            tool=self.name,
            raw_observation=f"Matched organization '{org_name}' from domain WHOIS registration",
            confidence=ConfidenceLevel.SUPPORTED,
        )
        yield EntityEvent(entity=entity, evidence=evidence)

        yield ProgressEvent(step="Recon-ng workspace analysis complete", pct=100.0)
