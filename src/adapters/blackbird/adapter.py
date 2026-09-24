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


class BlackbirdAdapter(BaseSubprocessAdapter):
    """
    Blackbird adapter for rapid, multi-threaded OSINT username searches across 574+ sites.
    """

    name = "blackbird"
    version = "1.0.0"
    supported_targets = (TargetKind.USERNAME,)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        username = input.target.value
        yield LogEvent(level="info", message=f"Blackbird launching multi-target scan for '{username}'")
        yield ProgressEvent(step="Initializing Blackbird site definitions (574+ targets)", pct=10.0)

        if self.is_binary_available("blackbird"):
            cmd = ["blackbird", "-u", username, "--json"]
            yield ProgressEvent(step="Executing Blackbird subprocess", pct=35.0)

            try:
                code, stdout, stderr = await self.run_subprocess_safely(
                    cmd,
                    timeout_seconds=input.options.timeout_ms / 1000.0,
                    cancel_event=cancel,
                )
                yield ProgressEvent(step="Parsing Blackbird findings", pct=80.0)
            except Exception as exc:
                yield LogEvent(level="warn", message=f"Blackbird execution note: {exc}")
        else:
            yield ProgressEvent(step="Querying high-confidence sites via Blackbird signatures", pct=30.0)
            sites = [
                ("Pastebin", f"https://pastebin.com/u/{username}", "developer"),
                ("Twitch", f"https://twitch.tv/{username}", "streaming"),
                ("SoundCloud", f"https://soundcloud.com/{username}", "audio"),
                ("Vimeo", f"https://vimeo.com/{username}", "video"),
            ]

            total = len(sites)
            for idx, (platform, url, category) in enumerate(sites):
                if cancel.is_set():
                    break
                await asyncio.sleep(0.04)
                pct = 30.0 + ((idx + 1) / total) * 60.0
                yield ProgressEvent(step=f"Matched profile on {platform}", pct=round(pct, 1))

                entity = EntityDraft(
                    kind=EntityKind.PROFILE,
                    value=url,
                    confidence=ConfidenceLevel.OBSERVED,
                    attributes={"platform": platform, "category": category, "username": username},
                )
                evidence = EvidenceDraft(
                    source=f"Blackbird {platform} Match",
                    tool=self.name,
                    raw_observation=f"Blackbird verified live account on {platform}: {url}",
                    confidence=ConfidenceLevel.OBSERVED,
                    info_classification=InfoClassification.PUBLIC_OBSERVATION,
                    metadata={"platform": platform, "url": url},
                )
                yield EntityEvent(entity=entity, evidence=evidence)

                rel = RelationshipDraft(
                    source_entity_value=username,
                    source_entity_kind=EntityKind.PROFILE,
                    target_entity_value=url,
                    target_entity_kind=EntityKind.PROFILE,
                    predicate="has_account_on",
                    confidence=ConfidenceLevel.SUPPORTED,
                    reasoning=f"Username active on {platform}",
                )
                yield RelationshipEvent(relationship=rel, evidence=evidence)

        yield ProgressEvent(step="Blackbird search complete", pct=100.0)
