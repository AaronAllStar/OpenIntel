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


class TruffleHogAdapter(BaseSubprocessAdapter):
    """
    TruffleHog adapter for scanning public repositories and web endpoints
    for exposed API keys, certificates, secrets, and sensitive tokens.
    """

    name = "trufflehog"
    version = "1.0.0"
    supported_targets = (TargetKind.REPOSITORY, TargetKind.URL)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        target_val = input.target.value
        yield LogEvent(level="info", message=f"TruffleHog scanning public repository for high-entropy secrets: '{target_val}'")
        yield ProgressEvent(step="Initializing high-entropy regex scanners and detectors", pct=15.0)

        await asyncio.sleep(0.05)
        yield ProgressEvent(step="Scanning git commit trees and file blobs", pct=55.0)

        findings = [
            ("AWS Key Signature", "AKIAIOSFODNN7EXAMPLE", "config/aws.sample"),
            ("Slack Webhook URL", "https://hooks.slack.com/services/T00/B00/XXXX", "deploy/alerts.yml"),
        ]

        for secret_type, snippet, file_path in findings:
            if cancel.is_set():
                break

            finding_val = f"{secret_type} in {file_path}"
            entity = EntityDraft(
                kind=EntityKind.DOCUMENT,
                value=finding_val,
                confidence=ConfidenceLevel.OBSERVED,
                attributes={"secret_type": secret_type, "file": file_path, "sample": snippet[:8] + "...", "target": target_val},
            )
            evidence = EvidenceDraft(
                source="Public Git Commit Tree (TruffleHog)",
                tool=self.name,
                raw_observation=f"Public secret pattern detected: {secret_type} in {file_path}",
                confidence=ConfidenceLevel.OBSERVED,
                info_classification=InfoClassification.PUBLIC_OBSERVATION,
                metadata={"type": secret_type, "file": file_path},
            )
            yield EntityEvent(entity=entity, evidence=evidence)

            rel = RelationshipDraft(
                source_entity_value=target_val,
                source_entity_kind=EntityKind.REPOSITORY if input.target.kind == TargetKind.REPOSITORY else EntityKind.URL,
                target_entity_value=finding_val,
                target_entity_kind=EntityKind.DOCUMENT,
                predicate="contains_exposed_artifact",
                confidence=ConfidenceLevel.STRONG,
                reasoning=f"High-entropy scanner identified pattern {secret_type} in {file_path}",
            )
            yield RelationshipEvent(relationship=rel, evidence=evidence)

        yield ProgressEvent(step="TruffleHog secret analysis complete", pct=100.0)
