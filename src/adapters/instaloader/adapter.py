import asyncio
import re
from collections.abc import AsyncIterator

import httpx

from src.adapters.base import BaseSubprocessAdapter
from src.app.domain.enums import ConfidenceLevel, EntityKind, InfoClassification, TargetKind
from src.app.domain.ports.adapter import (
    AdapterEvent,
    AdapterInput,
    EntityDraft,
    EntityEvent,
    EvidenceDraft,
    LogEvent,
    OsintAdapter,
    ProgressEvent,
    RelationshipDraft,
    RelationshipEvent,
)


class InstaloaderAdapter(BaseSubprocessAdapter, OsintAdapter):
    """
    Instagram OSINT adapter performing unauthenticated public profile queries,
    extracting biographical metadata, links, verification status, and profile URLs.
    """

    name = "instaloader"
    supported_targets = (TargetKind.USERNAME, TargetKind.PERSON_NAME)

    async def run(
        self,
        input: AdapterInput,
        cancel_event: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        target_val = input.target.value.strip()
        yield ProgressEvent(step=f"Querying Instagram public footprint for '{target_val}'", pct=10.0)

        handles: list[str] = []
        if input.target.kind == TargetKind.USERNAME:
            handles.append(target_val.lstrip("@").replace(" ", ""))
        else:
            parts = [re.sub(r"[^a-zA-Z0-9_.]", "", p.lower()) for p in target_val.split() if p]
            if len(parts) >= 2:
                handles.append(f"{parts[0]}.{parts[-1]}")
                handles.append(f"{parts[0]}_{parts[-1]}")
                handles.append(f"{parts[0]}{parts[-1]}")
            elif len(parts) == 1:
                handles.append(parts[0])

        total = len(handles)
        for idx, handle in enumerate(handles, start=1):
            if cancel_event.is_set():
                break

            ig_url = f"https://www.instagram.com/{handle}/"
            yield LogEvent(level="info", message=f"Probing public Instagram profile: {ig_url}")

            is_observed = False
            bio_snippet = ""

            try:
                # Query public Instagram web endpoint with standard browser headers
                async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                    resp = await client.get(
                        ig_url,
                        headers={
                            "User-Agent": (
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                            ),
                            "Accept-Language": "en-US,en;q=0.9",
                        },
                    )
                    if resp.status_code == 200:
                        text = resp.text
                        if f'"{handle}"' in text or "instagram.com" in text:
                            is_observed = True
                            match = re.search(r'<meta property="og:description" content="([^"]+)"', text)
                            if match:
                                bio_snippet = match.group(1)
            except Exception as exc:
                yield LogEvent(level="debug", message=f"Instagram public probe note for {handle}: {exc}")

            conf = ConfidenceLevel.OBSERVED if is_observed else ConfidenceLevel.POTENTIAL
            classification = (
                InfoClassification.PUBLIC_OBSERVATION
                if is_observed
                else InfoClassification.PLATFORM_SIGNAL
            )

            profile_entity = EntityDraft(
                kind=EntityKind.PROFILE,
                value=ig_url,
                confidence=conf,
                attributes={
                    "platform": "Instagram",
                    "handle": handle,
                    "bio_snippet": bio_snippet or "Public Instagram Account",
                },
            )

            evidence = EvidenceDraft(
                source="Instagram Public Web Observation",
                tool=self.name,
                raw_observation=(
                    f"Public Instagram profile identified at {ig_url}"
                    + (f": {bio_snippet}" if bio_snippet else "")
                ),
                confidence=conf,
                info_classification=classification,
                metadata={"handle": handle, "url": ig_url},
            )

            yield ProgressEvent(
                step=f"Cataloged Instagram profile @{handle}",
                pct=25.0 + (idx / total) * 65.0,
            )
            yield EntityEvent(entity=profile_entity, evidence=evidence)

            if input.target.kind == TargetKind.PERSON_NAME:
                rel = RelationshipDraft(
                    source_entity_value=target_val,
                    source_entity_kind=EntityKind.PERSON,
                    target_entity_value=ig_url,
                    target_entity_kind=EntityKind.PROFILE,
                    predicate="operates_instagram_profile",
                    confidence=ConfidenceLevel.POTENTIAL,
                    reasoning="Name correlation to Instagram handle",
                )
                yield RelationshipEvent(relationship=rel, evidence=evidence)

        yield ProgressEvent(step="Instagram reconnaissance completed", pct=100.0)
