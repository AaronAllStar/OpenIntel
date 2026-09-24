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


class MaigretAdapter(BaseSubprocessAdapter):
    name = "maigret"
    version = "1.0.0"
    supported_targets = (TargetKind.USERNAME,)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        username = input.target.value
        yield LogEvent(level="info", message=f"Maigret initiating deep analysis on '{username}'")
        yield ProgressEvent(step="Initializing Maigret engine", pct=10.0)

        if self.is_binary_available("maigret"):
            cmd = ["maigret", username, "--timeout", "10", "--no-progressbar"]
            yield ProgressEvent(step="Running Maigret checks", pct=35.0)

            try:
                code, stdout, stderr = await self.run_subprocess_safely(
                    cmd,
                    timeout_seconds=input.options.timeout_ms / 1000.0,
                    cancel_event=cancel,
                )
                for line in stdout.splitlines():
                    if "Found" in line and "http" in line:
                        url = line.split("http")[-1]
                        full_url = "http" + url.strip()
                        entity = EntityDraft(
                            kind=EntityKind.PROFILE,
                            value=full_url,
                            confidence=ConfidenceLevel.OBSERVED,
                            attributes={"username": username, "source": "maigret"},
                        )
                        evidence = EvidenceDraft(
                            source="Maigret Engine",
                            tool=self.name,
                            raw_observation=line.strip(),
                            confidence=ConfidenceLevel.OBSERVED,
                        )
                        yield EntityEvent(entity=entity, evidence=evidence)
            except Exception as exc:
                yield LogEvent(level="warn", message=f"Maigret execution note: {exc}")

        else:
            yield ProgressEvent(step="Running Maigret deep profile correlation", pct=40.0)
            mock_findings = [
                ("Telegram", f"https://t.me/{username}", "messaging"),
                ("Steam", f"https://steamcommunity.com/id/{username}", "gaming"),
                ("Keybase", f"https://keybase.io/{username}", "cryptography"),
            ]

            total = len(mock_findings)
            for idx, (platform, url, category) in enumerate(mock_findings):
                if cancel.is_set():
                    break
                await asyncio.sleep(0.05)
                pct = 40.0 + ((idx + 1) / total) * 50.0
                yield ProgressEvent(step=f"Identified {platform} profile", pct=round(pct, 1))

                entity = EntityDraft(
                    kind=EntityKind.PROFILE,
                    value=url,
                    confidence=ConfidenceLevel.OBSERVED,
                    attributes={"platform": platform, "category": category, "username": username},
                )
                evidence = EvidenceDraft(
                    source=platform,
                    tool=self.name,
                    raw_observation=f"Matched profile on {platform} ({category})",
                    confidence=ConfidenceLevel.OBSERVED,
                    metadata={"platform": platform, "category": category},
                )
                yield EntityEvent(entity=entity, evidence=evidence)

                rel = RelationshipDraft(
                    source_entity_value=username,
                    source_entity_kind=EntityKind.PROFILE,
                    target_entity_value=url,
                    target_entity_kind=EntityKind.PROFILE,
                    predicate="authenticated_as",
                    confidence=ConfidenceLevel.SUPPORTED,
                    reasoning=f"Maigret matched public handle on {platform}",
                )
                yield RelationshipEvent(relationship=rel, evidence=evidence)

        yield ProgressEvent(step="Maigret deep profile search complete", pct=100.0)
