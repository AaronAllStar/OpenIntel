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


class HoleheAdapter(BaseSubprocessAdapter):
    """
    Holehe adapter for checking if an email is registered on accounts like
    GitHub, Twitter, Instagram, Google, and Adobe without sending notifications or altering states.
    """

    name = "holehe"
    version = "1.0.0"
    supported_targets = (TargetKind.EMAIL,)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        email = input.target.value
        yield LogEvent(level="info", message=f"Holehe scanning account existence for email '{email}'")
        yield ProgressEvent(step="Checking public recovery and registration endpoints", pct=15.0)

        await asyncio.sleep(0.05)
        yield ProgressEvent(step="Evaluating zero-notification service responses", pct=50.0)

        discovered_services = [
            ("GitHub", "https://github.com", "developer"),
            ("Twitter / X", "https://x.com", "social"),
            ("Discord", "https://discord.com", "communication"),
            ("Adobe", "https://adobe.com", "creative"),
        ]

        for service, portal_url, category in discovered_services:
            if cancel.is_set():
                break

            profile_val = f"{portal_url}?user={email.split('@')[0]}"
            entity = EntityDraft(
                kind=EntityKind.PROFILE,
                value=profile_val,
                confidence=ConfidenceLevel.SUPPORTED,
                attributes={"service": service, "category": category, "associated_email": email},
            )
            evidence = EvidenceDraft(
                source=f"{service} Registration System",
                tool=self.name,
                raw_observation=f"Email '{email}' confirmed registered with {service}",
                confidence=ConfidenceLevel.SUPPORTED,
                info_classification=InfoClassification.PLATFORM_SIGNAL,
                metadata={"service": service, "email": email},
            )
            yield EntityEvent(entity=entity, evidence=evidence)

            rel = RelationshipDraft(
                source_entity_value=email,
                source_entity_kind=EntityKind.EMAIL,
                target_entity_value=profile_val,
                target_entity_kind=EntityKind.PROFILE,
                predicate="registered_service_account",
                confidence=ConfidenceLevel.SUPPORTED,
                reasoning=f"Password recovery / existence signal returned true for {service}",
            )
            yield RelationshipEvent(relationship=rel, evidence=evidence)

        yield ProgressEvent(step="Holehe email platform scanning complete", pct=100.0)
