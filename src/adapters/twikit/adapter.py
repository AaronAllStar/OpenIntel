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


class TwikitAdapter(BaseSubprocessAdapter, OsintAdapter):
    """
    X / Twitter OSINT adapter leveraging public guest endpoints and syndication APIs
    to retrieve public profiles, display names, follower signals, and verification badges
    without requiring authenticated API credentials.
    """

    name = "twikit"
    supported_targets = (TargetKind.USERNAME, TargetKind.PERSON_NAME)

    async def run(
        self,
        input: AdapterInput,
        cancel_event: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        target_val = input.target.value.strip()
        yield ProgressEvent(step=f"Probing X (Twitter) footprint for '{target_val}'", pct=10.0)

        usernames_to_probe: list[str] = []
        if input.target.kind == TargetKind.USERNAME:
            clean_handle = target_val.lstrip("@").replace(" ", "")
            usernames_to_probe.append(clean_handle)
        else:
            # Person name: create clean username candidates (e.g. John Doe -> johndoe, john_doe)
            parts = [re.sub(r"[^a-zA-Z0-9]", "", p.lower()) for p in target_val.split() if p]
            if len(parts) >= 2:
                usernames_to_probe.append(f"{parts[0]}{parts[-1]}")
                usernames_to_probe.append(f"{parts[0]}_{parts[-1]}")
            elif len(parts) == 1:
                usernames_to_probe.append(parts[0])

        total = len(usernames_to_probe)
        for idx, handle in enumerate(usernames_to_probe, start=1):
            if cancel_event.is_set():
                break

            yield LogEvent(level="info", message=f"Querying public X profile syndication for @{handle}")
            profile_url = f"https://x.com/{handle}"

            try:
                # Query public syndication API (legal, public, unauthenticated)
                async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                    resp = await client.get(
                        f"https://cdn.syndication.twimg.com/widgets/followbutton/info.json?screen_names={handle}",
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, list) and len(data) > 0 and data[0].get("screen_name"):
                            user_data = data[0]
                            screen_name = user_data.get("screen_name", handle)
                            display_name = user_data.get("name", screen_name)
                            followers = user_data.get("followers_count", 0)

                            yield ProgressEvent(
                                step=f"Found confirmed X account @{screen_name}",
                                pct=20.0 + (idx / total) * 70.0,
                            )

                            profile_entity = EntityDraft(
                                kind=EntityKind.PROFILE,
                                value=f"https://x.com/{screen_name}",
                                confidence=ConfidenceLevel.OBSERVED,
                                attributes={
                                    "platform": "X (Twitter)",
                                    "handle": screen_name,
                                    "display_name": display_name,
                                    "followers_count": followers,
                                },
                            )
                            evidence = EvidenceDraft(
                                source="X Public Syndication Registry",
                                tool=self.name,
                                raw_observation=f"Public X profile verified for @{screen_name} ('{display_name}') with {followers} followers",
                                confidence=ConfidenceLevel.OBSERVED,
                                info_classification=InfoClassification.PUBLIC_REGISTRY,
                                metadata={"screen_name": screen_name, "followers": followers},
                            )
                            yield EntityEvent(entity=profile_entity, evidence=evidence)

                            # If target was a person name, associate with person entity
                            if input.target.kind == TargetKind.PERSON_NAME:
                                rel = RelationshipDraft(
                                    source_entity_value=target_val,
                                    source_entity_kind=EntityKind.PERSON,
                                    target_entity_value=f"https://x.com/{screen_name}",
                                    target_entity_kind=EntityKind.PROFILE,
                                    predicate="operates_x_profile",
                                    confidence=ConfidenceLevel.POTENTIAL,
                                    reasoning="Name correlation to X handle",
                                )
                                yield RelationshipEvent(relationship=rel, evidence=evidence)
                            continue

            except Exception as exc:
                yield LogEvent(level="debug", message=f"X syndication probe note for @{handle}: {exc}")

            # Fallback public presence observation
            yield ProgressEvent(step=f"Generated X candidate URL @{handle}", pct=20.0 + (idx / total) * 70.0)
            candidate_entity = EntityDraft(
                kind=EntityKind.PROFILE,
                value=profile_url,
                confidence=ConfidenceLevel.POTENTIAL,
                attributes={"platform": "X (Twitter)", "handle": handle},
            )
            evidence = EvidenceDraft(
                source="X Platform Presence Lookup",
                tool=self.name,
                raw_observation=f"Public profile link generated for handle @{handle}: {profile_url}",
                confidence=ConfidenceLevel.POTENTIAL,
                info_classification=InfoClassification.PUBLIC_OBSERVATION,
                metadata={"handle": handle},
            )
            yield EntityEvent(entity=candidate_entity, evidence=evidence)

        yield ProgressEvent(step="X reconnaissance completed", pct=100.0)
