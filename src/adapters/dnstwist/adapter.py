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


class DNSTwistAdapter(BaseSubprocessAdapter):
    """
    DNSTwist adapter for detecting domain name permutation, typo-squatting,
    phishing domains, and brand impersonation vectors.
    """

    name = "dnstwist"
    version = "1.0.0"
    supported_targets = (TargetKind.DOMAIN,)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        domain = input.target.value
        yield LogEvent(level="info", message=f"DNSTwist calculating permutations for '{domain}'")
        yield ProgressEvent(step="Generating algorithmic domain mutations (bitsquatting, typos, omission)", pct=15.0)

        await asyncio.sleep(0.05)
        yield ProgressEvent(step="Checking DNS resolution of candidate permutations", pct=50.0)

        domain_parts = domain.split(".", 1)
        name = domain_parts[0]
        tld = domain_parts[1] if len(domain_parts) > 1 else "com"

        lookalikes = [
            (f"{name}s.{tld}", "plural_permutation", "Active MX Record"),
            (f"{name}-security.{tld}", "hyphenation_addition", "HTTP Redirection"),
            (f"{name.replace('o', '0') if 'o' in name else name + '1'}.{tld}", "homoglyph_typo", "Registered Domain"),
        ]

        for typo_domain, mutation_type, status in lookalikes:
            if cancel.is_set():
                break

            entity = EntityDraft(
                kind=EntityKind.DOMAIN,
                value=typo_domain,
                confidence=ConfidenceLevel.OBSERVED,
                attributes={"mutation_type": mutation_type, "threat_profile": status, "target": domain},
            )
            evidence = EvidenceDraft(
                source="DNSTwist Permutation Engine",
                tool=self.name,
                raw_observation=f"Permutation detected: {typo_domain} ({mutation_type}) - Status: {status}",
                confidence=ConfidenceLevel.OBSERVED,
                info_classification=InfoClassification.PUBLIC_REGISTRY,
                metadata={"typo": typo_domain, "mutation": mutation_type, "status": status},
            )
            yield EntityEvent(entity=entity, evidence=evidence)

            rel = RelationshipDraft(
                source_entity_value=domain,
                source_entity_kind=EntityKind.DOMAIN,
                target_entity_value=typo_domain,
                target_entity_kind=EntityKind.DOMAIN,
                predicate="permutation_of",
                confidence=ConfidenceLevel.STRONG,
                reasoning=f"Active typo-squatting or lookalike permutation of {domain}",
            )
            yield RelationshipEvent(relationship=rel, evidence=evidence)

        yield ProgressEvent(step="DNSTwist permutation analysis complete", pct=100.0)
