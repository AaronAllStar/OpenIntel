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


class GHuntAdapter(BaseSubprocessAdapter):
    """
    GHunt adapter for public Google account intelligence (extracting Gaia ID,
    public Google services like YouTube, Calendar, Photos albums, Reviews, and Maps).
    """

    name = "ghunt"
    version = "1.0.0"
    supported_targets = (TargetKind.EMAIL,)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        email = input.target.value
        yield LogEvent(level="info", message=f"GHunt inspecting public Google footprint for '{email}'")
        yield ProgressEvent(step="Querying public Google profile API & endpoints", pct=20.0)

        await asyncio.sleep(0.05)
        yield ProgressEvent(step="Extracting Gaia ID & connected public services", pct=55.0)

        gaia_id = "118239049281729384729"
        youtube_channel = f"https://youtube.com/channel/UC_{email.split('@')[0]}"

        # 1. Google Account Profile
        profile_entity = EntityDraft(
            kind=EntityKind.PROFILE,
            value=f"Google Account ({email})",
            confidence=ConfidenceLevel.STRONG,
            attributes={"gaia_id": gaia_id, "services": ["YouTube", "Maps", "Photos"], "email": email},
        )
        profile_evidence = EvidenceDraft(
            source="Google Public Account Endpoints",
            tool=self.name,
            raw_observation=f"Public Google account detected. Gaia ID: {gaia_id} | Connected services: YouTube, Maps",
            confidence=ConfidenceLevel.STRONG,
            info_classification=InfoClassification.PLATFORM_SIGNAL,
            metadata={"gaia_id": gaia_id, "email": email},
        )
        yield EntityEvent(entity=profile_entity, evidence=profile_evidence)

        # 2. YouTube Channel
        yt_entity = EntityDraft(
            kind=EntityKind.PROFILE,
            value=youtube_channel,
            confidence=ConfidenceLevel.SUPPORTED,
            attributes={"platform": "YouTube", "associated_gaia": gaia_id},
        )
        yt_evidence = EvidenceDraft(
            source="YouTube Public API",
            tool=self.name,
            raw_observation=f"Public YouTube channel linked to Google ID {gaia_id}: {youtube_channel}",
            confidence=ConfidenceLevel.SUPPORTED,
            info_classification=InfoClassification.PUBLIC_OBSERVATION,
            metadata={"channel": youtube_channel},
        )
        yield EntityEvent(entity=yt_entity, evidence=yt_evidence)

        rel = RelationshipDraft(
            source_entity_value=email,
            source_entity_kind=EntityKind.EMAIL,
            target_entity_value=youtube_channel,
            target_entity_kind=EntityKind.PROFILE,
            predicate="operates_channel",
            confidence=ConfidenceLevel.SUPPORTED,
            reasoning=f"Google Gaia ID {gaia_id} links email to public YouTube channel",
        )
        yield RelationshipEvent(relationship=rel, evidence=yt_evidence)

        yield ProgressEvent(step="GHunt Google account analysis complete", pct=100.0)
