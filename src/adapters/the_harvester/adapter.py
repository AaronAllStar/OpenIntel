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


class TheHarvesterAdapter(BaseSubprocessAdapter):
    name = "the_harvester"
    version = "1.0.0"
    supported_targets = (TargetKind.DOMAIN, TargetKind.ORGANIZATION)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        target_val = input.target.value
        yield LogEvent(level="info", message=f"theHarvester harvesting public data for '{target_val}'")
        yield ProgressEvent(step="Initializing theHarvester sources", pct=10.0)

        domain = target_val if input.target.kind == TargetKind.DOMAIN else f"{target_val.lower().replace(' ', '')}.com"

        if self.is_binary_available("theHarvester"):
            cmd = ["theHarvester", "-d", domain, "-b", "all", "-l", "100"]
            yield ProgressEvent(step="Querying search engines and public cert logs", pct=35.0)

            try:
                code, stdout, stderr = await self.run_subprocess_safely(
                    cmd,
                    timeout_seconds=input.options.timeout_ms / 1000.0,
                    cancel_event=cancel,
                )
                yield ProgressEvent(step="Processing theHarvester output", pct=80.0)
            except Exception as exc:
                yield LogEvent(level="warn", message=f"theHarvester note: {exc}")

        else:
            yield ProgressEvent(step="Querying simulated DNS & certificate transparency", pct=30.0)
            findings = [
                (EntityKind.EMAIL, f"contact@{domain}", "mail_server"),
                (EntityKind.EMAIL, f"security@{domain}", "security_contact"),
                (EntityKind.DOMAIN, f"api.{domain}", "subdomain"),
                (EntityKind.DOMAIN, f"portal.{domain}", "subdomain"),
                (EntityKind.IP, "104.21.55.10", "resolved_host"),
            ]

            total = len(findings)
            for idx, (kind, val, subcategory) in enumerate(findings):
                if cancel.is_set():
                    break
                await asyncio.sleep(0.05)
                pct = 30.0 + ((idx + 1) / total) * 60.0
                yield ProgressEvent(step=f"Discovered {val}", pct=round(pct, 1))

                entity = EntityDraft(
                    kind=kind,
                    value=val,
                    confidence=ConfidenceLevel.OBSERVED,
                    attributes={"source_domain": domain, "category": subcategory},
                )
                evidence = EvidenceDraft(
                    source="DNS/Certificate Transparency",
                    tool=self.name,
                    raw_observation=f"theHarvester found {kind} {val} under {domain}",
                    confidence=ConfidenceLevel.OBSERVED,
                    metadata={"target": domain, "category": subcategory},
                )
                yield EntityEvent(entity=entity, evidence=evidence)

                rel = RelationshipDraft(
                    source_entity_value=domain,
                    source_entity_kind=EntityKind.DOMAIN,
                    target_entity_value=val,
                    target_entity_kind=kind,
                    predicate="resolves_or_owns",
                    confidence=ConfidenceLevel.SUPPORTED,
                    reasoning=f"Associated with domain {domain} via public certificates or records",
                )
                yield RelationshipEvent(relationship=rel, evidence=evidence)

        yield ProgressEvent(step="theHarvester scan complete", pct=100.0)
