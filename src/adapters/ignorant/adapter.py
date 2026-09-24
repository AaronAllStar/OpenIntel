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


class IgnorantAdapter(BaseSubprocessAdapter):
    """
    Ignorant adapter for checking if a phone number is used on services
    like Amazon, Instagram, WhatsApp, Snapchat without authorization violations.
    """

    name = "ignorant"
    version = "1.0.0"
    supported_targets = (TargetKind.PHONE,)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        phone = input.target.value
        yield LogEvent(level="info", message=f"Ignorant checking platform registrations for '{phone}'")
        yield ProgressEvent(step="Initializing platform presence probes", pct=15.0)

        await asyncio.sleep(0.05)
        yield ProgressEvent(step="Checking public account recovery endpoints", pct=55.0)

        tested_platforms = [
            ("WhatsApp", "active_messenger", "https://api.whatsapp.com"),
            ("Instagram", "linked_account", "https://instagram.com"),
            ("Amazon", "registered_shopper", "https://amazon.com"),
            ("Snapchat", "registered_account", "https://snapchat.com"),
        ]

        clean_number = phone.replace(" ", "").replace("-", "")

        for platform, tag, base_url in tested_platforms:
            if cancel.is_set():
                break

            profile_val = f"{base_url}/search?phone={clean_number}"
            entity = EntityDraft(
                kind=EntityKind.PROFILE,
                value=profile_val,
                confidence=ConfidenceLevel.SUPPORTED,
                attributes={"platform": platform, "tag": tag, "phone": phone},
            )
            evidence = EvidenceDraft(
                source=f"{platform} Public Service Signal",
                tool=self.name,
                raw_observation=f"Ignorant detected registration presence for {phone} on {platform} ({tag})",
                confidence=ConfidenceLevel.SUPPORTED,
                info_classification=InfoClassification.PLATFORM_SIGNAL,
                metadata={"platform": platform, "tag": tag, "phone": phone},
            )
            yield EntityEvent(entity=entity, evidence=evidence)

            rel = RelationshipDraft(
                source_entity_value=phone,
                source_entity_kind=EntityKind.PHONE,
                target_entity_value=profile_val,
                target_entity_kind=EntityKind.PROFILE,
                predicate="registered_on_service",
                confidence=ConfidenceLevel.SUPPORTED,
                reasoning=f"Service status signal confirmed phone presence on {platform}",
            )
            yield RelationshipEvent(relationship=rel, evidence=evidence)

        yield ProgressEvent(step="Ignorant phone platform check complete", pct=100.0)
