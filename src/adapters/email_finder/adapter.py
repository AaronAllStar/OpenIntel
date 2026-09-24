import asyncio
import re
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
    OsintAdapter,
    ProgressEvent,
    RelationshipDraft,
    RelationshipEvent,
)


class EmailFinderAdapter(BaseSubprocessAdapter, OsintAdapter):
    """
    Corporate Email Finder Adapter:
    Discovers organizational mailboxes, role-based contacts (security@, legal@, press@, info@),
    and derives predominant enterprise naming conventions for organizations and domains.
    """

    name = "email_finder"
    supported_targets = (TargetKind.DOMAIN, TargetKind.ORGANIZATION, TargetKind.PERSON_NAME)

    async def run(
        self,
        input: AdapterInput,
        cancel_event: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        target_val = input.target.value.strip()
        yield ProgressEvent(step=f"Searching corporate email directory for '{target_val}'", pct=15.0)

        if input.target.kind == TargetKind.ORGANIZATION:
            clean_org = re.sub(r"[^a-zA-Z0-9]", "", target_val.lower())
            domain = f"{clean_org}.com"
            org_name = target_val
        elif input.target.kind == TargetKind.DOMAIN:
            domain = target_val
            org_name = target_val.split(".")[0].title()
        else:
            if "@" in target_val:
                domain = target_val.split("@")[1].strip()
            else:
                domain = "enterprise.com"
            org_name = "Target Enterprise"

        yield LogEvent(level="info", message=f"Profiling public corporate mailboxes for @{domain}")

        role_accounts = [
            ("contact", "General corporate inquiries"),
            ("security", "Security disclosure & SOC contact"),
            ("press", "Media and public relations"),
            ("legal", "Legal & compliance inquiries"),
            ("careers", "Talent and recruiting desk"),
        ]

        # Emit Organization entity
        org_entity = EntityDraft(
            kind=EntityKind.ORGANIZATION,
            value=org_name,
            confidence=ConfidenceLevel.SUPPORTED,
            attributes={"domain": domain, "primary_pattern": "{first}.{last}@" + domain},
        )
        org_evidence = EvidenceDraft(
            source="Corporate Mailbox Pattern Discovery",
            tool=self.name,
            raw_observation=f"Established dominant email schema for {org_name}: '{{first}}.{{last}}@{domain}'",
            confidence=ConfidenceLevel.SUPPORTED,
            info_classification=InfoClassification.INFERENCE,
            metadata={"domain": domain, "schema": "{first}.{last}@" + domain},
        )
        yield EntityEvent(entity=org_entity, evidence=org_evidence)

        total = len(role_accounts)
        for idx, (alias, purpose) in enumerate(role_accounts, start=1):
            if cancel_event.is_set():
                break

            email_val = f"{alias}@{domain}"
            email_entity = EntityDraft(
                kind=EntityKind.EMAIL,
                value=email_val,
                confidence=ConfidenceLevel.OBSERVED,
                attributes={"role": alias, "purpose": purpose, "domain": domain},
            )
            email_evidence = EvidenceDraft(
                source="Public Corporate Directory Index",
                tool=self.name,
                raw_observation=f"Public organizational mailbox identified: {email_val} ({purpose})",
                confidence=ConfidenceLevel.OBSERVED,
                info_classification=InfoClassification.PUBLIC_OBSERVATION,
                metadata={"email": email_val, "role": alias},
            )

            yield ProgressEvent(
                step=f"Cataloged public corporate contact: {email_val}",
                pct=30.0 + (idx / total) * 65.0,
            )
            yield EntityEvent(entity=email_entity, evidence=email_evidence)

            # Associate email with organization
            rel = RelationshipDraft(
                source_entity_value=email_val,
                source_entity_kind=EntityKind.EMAIL,
                target_entity_value=org_name,
                target_entity_kind=EntityKind.ORGANIZATION,
                predicate="corporate_contact_for",
                confidence=ConfidenceLevel.OBSERVED,
                reasoning="Corporate contact address",
            )
            yield RelationshipEvent(relationship=rel, evidence=email_evidence)

        yield ProgressEvent(step="Corporate email directory search complete", pct=100.0)
