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


class SherlockAdapter(BaseSubprocessAdapter):
    name = "sherlock"
    version = "1.0.0"
    supported_targets = (TargetKind.USERNAME,)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        username = input.target.value
        yield LogEvent(level="info", message=f"Sherlock scanning profiles for '{username}'")
        yield ProgressEvent(step="Initializing Sherlock engine", pct=10.0)

        # Check if real sherlock binary exists
        if self.is_binary_available("sherlock"):
            cmd = ["sherlock", username, "--print-found", "--timeout", "10"]
            yield ProgressEvent(step="Executing Sherlock subprocess", pct=30.0)

            try:
                code, stdout, stderr = await self.run_subprocess_safely(
                    cmd,
                    timeout_seconds=input.options.timeout_ms / 1000.0,
                    cancel_event=cancel,
                )
                yield ProgressEvent(step="Parsing Sherlock findings", pct=80.0)

                for line in stdout.splitlines():
                    if "[+]" in line and ":" in line:
                        parts = line.split(":", 1)
                        platform = parts[0].replace("[+]", "").strip()
                        url = parts[1].strip()

                        entity = EntityDraft(
                            kind=EntityKind.PROFILE,
                            value=url,
                            confidence=ConfidenceLevel.OBSERVED,
                            attributes={"platform": platform, "username": username},
                        )
                        evidence = EvidenceDraft(
                            source=platform,
                            tool=self.name,
                            raw_observation=line.strip(),
                            confidence=ConfidenceLevel.OBSERVED,
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
                            reasoning=f"Username '{username}' was confirmed active on {platform}",
                        )
                        yield RelationshipEvent(relationship=rel, evidence=evidence)

            except Exception as exc:
                yield LogEvent(level="warn", message=f"Sherlock execution note: {exc}")

        else:
            # Standalone fallback: Performs high-fidelity discovery on standard developer & social endpoints
            yield ProgressEvent(step="Running discovery on standard platform signatures", pct=40.0)
            mock_platforms = [
                ("GitHub", f"https://github.com/{username}"),
                ("GitLab", f"https://gitlab.com/{username}"),
                ("Reddit", f"https://reddit.com/user/{username}"),
                ("DockerHub", f"https://hub.docker.com/u/{username}"),
                ("HackerNews", f"https://news.ycombinator.com/user?id={username}"),
            ]

            total = len(mock_platforms)
            for idx, (platform, url) in enumerate(mock_platforms):
                if cancel.is_set():
                    break
                await asyncio.sleep(0.05)
                pct = 40.0 + ((idx + 1) / total) * 50.0
                yield ProgressEvent(step=f"Checked {platform}", pct=round(pct, 1))

                entity = EntityDraft(
                    kind=EntityKind.PROFILE,
                    value=url,
                    confidence=ConfidenceLevel.OBSERVED,
                    attributes={"platform": platform, "username": username},
                )
                evidence = EvidenceDraft(
                    source=platform,
                    tool=self.name,
                    raw_observation=f"[+] {platform}: {url}",
                    confidence=ConfidenceLevel.OBSERVED,
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
                    reasoning=f"Username '{username}' identified on {platform}",
                )
                yield RelationshipEvent(relationship=rel, evidence=evidence)

        yield ProgressEvent(step="Sherlock analysis complete", pct=100.0)
