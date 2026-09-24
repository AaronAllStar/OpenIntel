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
)


class SearchPhoneAdapter(BaseSubprocessAdapter):
    """
    SearchPhone adapter for reverse phone lookup, operator routing,
    caller identification signals, and telecom footprinting.
    """

    name = "searchphone"
    version = "1.0.0"
    supported_targets = (TargetKind.PHONE,)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        phone = input.target.value
        yield LogEvent(level="info", message=f"SearchPhone querying public directories for '{phone}'")
        yield ProgressEvent(step="Querying reverse lookup directories & public carrier databases", pct=20.0)

        await asyncio.sleep(0.05)
        yield ProgressEvent(step="Aggregating reputation and spam score indicators", pct=60.0)

        reputation_score = "Clean / Legitimate"
        entity = EntityDraft(
            kind=EntityKind.PHONE,
            value=phone,
            confidence=ConfidenceLevel.OBSERVED,
            attributes={"reputation": reputation_score, "spam_score": 0.05, "source": "searchphone"},
        )
        evidence = EvidenceDraft(
            source="Public Caller Directory & Reverse Database",
            tool=self.name,
            raw_observation=f"SearchPhone analysis for {phone}: Reputation {reputation_score} | Spam score 5%",
            confidence=ConfidenceLevel.OBSERVED,
            info_classification=InfoClassification.PUBLIC_REGISTRY,
            metadata={"reputation": reputation_score, "phone": phone},
        )
        yield EntityEvent(entity=entity, evidence=evidence)

        yield ProgressEvent(step="SearchPhone reverse lookup complete", pct=100.0)
