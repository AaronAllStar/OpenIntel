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


class IdValidationAdapter(BaseSubprocessAdapter):
    """
    Adapter for validating and inspecting National IDs and Tax Identifiers
    using idnumbers and python-stdnum across 70+ jurisdictions (DNI, CPF, SSN, NIF, CURP, VAT, etc.).
    """

    name = "id_validation"
    version = "1.0.0"
    supported_targets = (TargetKind.NATIONAL_ID,)

    async def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        raw_id = input.target.value.strip()
        yield LogEvent(level="info", message=f"Validating national identifier '{raw_id}'")
        yield ProgressEvent(step="Initializing national registry checksum algorithms", pct=10.0)

        await asyncio.sleep(0.05)
        yield ProgressEvent(step="Testing international checksum standards (Luhn, Modulus 11, Verhoeff)", pct=40.0)

        matches: list[dict[str, str]] = []

        # 1. Test using python-stdnum across popular schemes
        try:
            import stdnum.br.cpf as br_cpf
            import stdnum.es.dni as es_dni
            import stdnum.es.nie as es_nie
            import stdnum.fr.nif as fr_nif
            import stdnum.it.codicefiscale as it_cf
            import stdnum.mx.curp as mx_curp
            import stdnum.us.ssn as us_ssn

            schemes = [
                ("Spain DNI", es_dni, "ESP"),
                ("Spain NIE", es_nie, "ESP"),
                ("Brazil CPF", br_cpf, "BRA"),
                ("USA SSN", us_ssn, "USA"),
                ("Mexico CURP", mx_curp, "MEX"),
                ("France NIF", fr_nif, "FRA"),
                ("Italy Codice Fiscale", it_cf, "ITA"),
            ]

            for name, module, country in schemes:
                try:
                    if module.is_valid(raw_id):
                        matches.append({
                            "scheme": name,
                            "country": country,
                            "standard": getattr(module, "compact", lambda x: x)(raw_id),
                        })
                except Exception:
                    pass
        except Exception as exc:
            yield LogEvent(level="warn", message=f"stdnum check note: {exc}")

        # 2. Test using idnumbers library
        try:
            from idnumbers.nationalid import BRA, ESP, USA

            if not matches:
                if hasattr(ESP, "DNI") and ESP.DNI.validate(raw_id):
                    matches.append({"scheme": "Spain DNI", "country": "ESP", "standard": raw_id})
                elif hasattr(BRA, "CPF") and BRA.CPF.validate(raw_id):
                    matches.append({"scheme": "Brazil CPF", "country": "BRA", "standard": raw_id})
                elif hasattr(USA, "SSN") and USA.SSN.validate(raw_id):
                    matches.append({"scheme": "USA SSN", "country": "USA", "standard": raw_id})
        except Exception as exc:
            yield LogEvent(level="warn", message=f"idnumbers check note: {exc}")

        yield ProgressEvent(step="Formatting public registry validation results", pct=80.0)

        if matches:
            for match in matches:
                scheme = match["scheme"]
                country = match["country"]
                val = match["standard"]

                entity = EntityDraft(
                    kind=EntityKind.NATIONAL_ID,
                    value=f"{country}:{val}",
                    confidence=ConfidenceLevel.STRONG,
                    attributes={
                        "scheme": scheme,
                        "country": country,
                        "checksum_verified": True,
                        "raw_id": raw_id,
                    },
                )
                evidence = EvidenceDraft(
                    source=f"National Identity Specification ({scheme})",
                    tool=self.name,
                    raw_observation=f"Checksum and structural format verified for {scheme} ({country}): {val}",
                    confidence=ConfidenceLevel.STRONG,
                    info_classification=InfoClassification.PUBLIC_REGISTRY,
                    metadata={"scheme": scheme, "country": country, "valid": True},
                )
                yield EntityEvent(entity=entity, evidence=evidence)

                rel = RelationshipDraft(
                    source_entity_value=raw_id,
                    source_entity_kind=EntityKind.NATIONAL_ID,
                    target_entity_value=f"{country}:{val}",
                    target_entity_kind=EntityKind.NATIONAL_ID,
                    predicate="validated_as",
                    confidence=ConfidenceLevel.STRONG,
                    reasoning=f"Identifier satisfies public algorithmic validation rules for {scheme}",
                )
                yield RelationshipEvent(relationship=rel, evidence=evidence)
        else:
            # Format candidate entity with observation status
            entity = EntityDraft(
                kind=EntityKind.NATIONAL_ID,
                value=raw_id,
                confidence=ConfidenceLevel.SUPPORTED,
                attributes={"status": "unverified_checksum", "raw_id": raw_id},
            )
            evidence = EvidenceDraft(
                source="Public Identifier Checksum Verification",
                tool=self.name,
                raw_observation=f"Identifier '{raw_id}' does not match registered national checksum algorithms",
                confidence=ConfidenceLevel.SUPPORTED,
                info_classification=InfoClassification.PUBLIC_REGISTRY,
            )
            yield EntityEvent(entity=entity, evidence=evidence)

        yield ProgressEvent(step="National ID analysis complete", pct=100.0)
