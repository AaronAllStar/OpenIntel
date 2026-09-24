import asyncio
import re
from collections.abc import AsyncIterator

import dns.asyncresolver

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


class EmailEnrichAdapter(BaseSubprocessAdapter, OsintAdapter):
    """
    Business Email Enrichment Adapter:
    Generates corporate email permutations (first.last, f.last, flast, etc.),
    validates active MX mail exchange records for target domains, and associates
    corporate identities with verified email schemas.
    """

    name = "email_enrich"
    supported_targets = (TargetKind.PERSON_NAME, TargetKind.EMAIL, TargetKind.DOMAIN)

    async def _resolve_mx_records(self, domain: str) -> list[str]:
        try:
            resolver = dns.asyncresolver.Resolver()
            resolver.timeout = 4.0
            resolver.lifetime = 4.0
            answers = await resolver.resolve(domain, "MX")
            return sorted([str(r.exchange).rstrip(".") for r in answers])
        except Exception:
            return []

    async def run(
        self,
        input: AdapterInput,
        cancel_event: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        target_val = input.target.value.strip()
        yield ProgressEvent(step=f"Enriching business email patterns for '{target_val}'", pct=10.0)

        first_name = ""
        last_name = ""
        domain = ""

        if input.target.kind == TargetKind.EMAIL:
            parts = target_val.split("@")
            domain = parts[1]
            local = parts[0]
            if "." in local:
                name_parts = local.split(".")
                first_name, last_name = name_parts[0], name_parts[-1]
            else:
                first_name = local
        elif input.target.kind == TargetKind.DOMAIN:
            domain = target_val
            first_name = "contact"
            last_name = "admin"
        elif input.target.kind == TargetKind.PERSON_NAME:
            if "@" in target_val:
                name_part, domain_part = target_val.split("@", 1)
                domain = domain_part.strip()
                name_tokens = name_part.strip().split()
            else:
                name_tokens = target_val.split()
                domain = "company.com"

            if len(name_tokens) >= 2:
                first_name = re.sub(r"[^a-zA-Z]", "", name_tokens[0].lower())
                last_name = re.sub(r"[^a-zA-Z]", "", name_tokens[-1].lower())
            elif len(name_tokens) == 1:
                first_name = re.sub(r"[^a-zA-Z]", "", name_tokens[0].lower())
                last_name = "corp"

        # Check MX records for the domain
        yield LogEvent(level="info", message=f"Verifying DNS MX exchange routing for @{domain}")
        mx_records = await self._resolve_mx_records(domain)
        has_mx = len(mx_records) > 0

        yield ProgressEvent(
            step=f"Domain @{domain} MX records: {', '.join(mx_records[:2]) if has_mx else 'None found'}",
            pct=35.0,
        )

        domain_entity = EntityDraft(
            kind=EntityKind.DOMAIN,
            value=domain,
            confidence=ConfidenceLevel.OBSERVED if has_mx else ConfidenceLevel.POTENTIAL,
            attributes={"mx_servers": mx_records, "has_mail_service": has_mx},
        )
        domain_evidence = EvidenceDraft(
            source="DNS MX Exchange Resolution",
            tool=self.name,
            raw_observation=(
                f"Resolved {len(mx_records)} MX servers for {domain}: {mx_records}"
                if has_mx
                else f"No active MX records found for {domain}"
            ),
            confidence=ConfidenceLevel.OBSERVED if has_mx else ConfidenceLevel.POTENTIAL,
            info_classification=InfoClassification.PUBLIC_REGISTRY,
            metadata={"domain": domain, "mx_records": mx_records},
        )
        yield EntityEvent(entity=domain_entity, evidence=domain_evidence)

        # Generate standard corporate permutations
        f = first_name[:1] if first_name else "u"
        permutations = [
            f"{first_name}.{last_name}@{domain}",
            f"{f}.{last_name}@{domain}",
            f"{f}{last_name}@{domain}",
            f"{first_name}@{domain}",
            f"{last_name}.{first_name}@{domain}",
        ]
        unique_perms = list(dict.fromkeys([p for p in permutations if not p.startswith("@")]))

        total = len(unique_perms)
        for idx, email_addr in enumerate(unique_perms, start=1):
            if cancel_event.is_set():
                break

            email_entity = EntityDraft(
                kind=EntityKind.EMAIL,
                value=email_addr,
                confidence=ConfidenceLevel.SUPPORTED if has_mx else ConfidenceLevel.POTENTIAL,
                attributes={"pattern": email_addr.split("@")[0], "domain": domain, "mx_validated": has_mx},
            )
            email_evidence = EvidenceDraft(
                source="Corporate Email Pattern Permutation & DNS Validation",
                tool=self.name,
                raw_observation=f"Generated and validated corporate email pattern candidate: {email_addr} (MX: {has_mx})",
                confidence=ConfidenceLevel.SUPPORTED if has_mx else ConfidenceLevel.POTENTIAL,
                info_classification=InfoClassification.INFERENCE,
                metadata={"email": email_addr, "domain": domain, "mx_active": has_mx},
            )

            yield ProgressEvent(
                step=f"Evaluated corporate pattern {email_addr}",
                pct=40.0 + (idx / total) * 55.0,
            )
            yield EntityEvent(entity=email_entity, evidence=email_evidence)

            # Associate email with domain
            rel = RelationshipDraft(
                source_entity_value=email_addr,
                source_entity_kind=EntityKind.EMAIL,
                target_entity_value=domain,
                target_entity_kind=EntityKind.DOMAIN,
                predicate="hosted_on_domain",
                confidence=ConfidenceLevel.SUPPORTED,
                reasoning="Email domain association",
            )
            yield RelationshipEvent(relationship=rel, evidence=email_evidence)

        yield ProgressEvent(step="Business email enrichment complete", pct=100.0)
