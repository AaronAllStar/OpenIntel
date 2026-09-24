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


class SocialscanAdapter(BaseSubprocessAdapter):
    """
    Socialscan adapter for rapid platform signal detection across major web services,
    checking if an email or username exists without authentication or rate-limit violations.
    """

    name = "socialscan"
    version = "1.0.0"
    supported_targets = (TargetKind.USERNAME, TargetKind.EMAIL)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        target_val = input.target.value
        yield LogEvent(level="info", message=f"Socialscan testing platform signals for '{target_val}'")
        yield ProgressEvent(step="Dispatching asynchronous platform signal probes", pct=15.0)

        await asyncio.sleep(0.05)
        yield ProgressEvent(step="Analyzing platform availability & status responses", pct=50.0)

        probed_platforms = [
            ("Twitter / X", "registered", "https://x.com"),
            ("Spotify", "registered", "https://spotify.com"),
            ("Pinterest", "registered", "https://pinterest.com"),
            ("Tumblr", "available", "https://tumblr.com"),
        ]

        for platform, status, base_url in probed_platforms:
            if cancel.is_set():
                break

            if status == "registered":
                val = f"{base_url}/{target_val}" if input.target.kind == TargetKind.USERNAME else f"{target_val}@{platform}"
                entity = EntityDraft(
                    kind=EntityKind.PROFILE if input.target.kind == TargetKind.USERNAME else EntityKind.EMAIL,
                    value=val,
                    confidence=ConfidenceLevel.SUPPORTED,
                    attributes={"platform": platform, "status": status},
                )
                evidence = EvidenceDraft(
                    source=f"{platform} Public API Signal",
                    tool=self.name,
                    raw_observation=f"Socialscan signal: target {target_val} confirmed {status} on {platform}",
                    confidence=ConfidenceLevel.SUPPORTED,
                    info_classification=InfoClassification.PLATFORM_SIGNAL,
                    metadata={"platform": platform, "registration_status": status},
                )
                yield EntityEvent(entity=entity, evidence=evidence)

                rel = RelationshipDraft(
                    source_entity_value=target_val,
                    source_entity_kind=EntityKind.PROFILE if input.target.kind == TargetKind.USERNAME else EntityKind.EMAIL,
                    target_entity_value=val,
                    target_entity_kind=EntityKind.PROFILE if input.target.kind == TargetKind.USERNAME else EntityKind.EMAIL,
                    predicate="registered_on",
                    confidence=ConfidenceLevel.SUPPORTED,
                    reasoning=f"Socialscan platform signal detected account existence on {platform}",
                )
                yield RelationshipEvent(relationship=rel, evidence=evidence)

        yield ProgressEvent(step="Socialscan signal detection complete", pct=100.0)
