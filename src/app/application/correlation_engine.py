from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.app.domain.enums import ConfidenceLevel, EntityKind, InfoClassification
from src.app.infrastructure.logging import logger
from src.app.infrastructure.models import EntityModel, EvidenceModel, RelationshipModel

# Intrinsic base probability per ConfidenceLevel
CONFIDENCE_BASE_PROBABILITIES: dict[str, float] = {
    ConfidenceLevel.STRONG.value: 0.95,
    ConfidenceLevel.OBSERVED.value: 0.80,
    ConfidenceLevel.SUPPORTED.value: 0.60,
    ConfidenceLevel.POTENTIAL.value: 0.35,
}

# Engine weight / reliability factor W in [0.70, 1.0]
TOOL_RELIABILITY_WEIGHTS: dict[str, float] = {
    # High-trust official registries, cryptographic or direct protocol lookup
    "id_validation": 1.0,
    "dnstwist": 0.98,
    "phoneinfoga": 0.95,
    "amass": 0.95,
    "trufflehog": 0.95,
    # Direct platform APIs / syndication
    "twikit": 0.92,
    "instaloader": 0.92,
    "holehe": 0.92,
    "ghunt": 0.92,
    "whatsapp": 0.92,
    "octosuite": 0.92,
    "sherlock": 0.90,
    "maigret": 0.90,
    "socialscan": 0.90,
    "email_enrich": 0.90,
    "email_finder": 0.88,
    "bellingcat_telegram": 0.88,
    "ignorant": 0.88,
    "searchphone": 0.88,
    # Crawlers & search engines
    "the_harvester": 0.85,
    "spiderfoot": 0.85,
    "photon": 0.85,
    "recon_ng": 0.85,
    "crosslinked": 0.85,
    "metagoofil": 0.80,
    # Inferred / internal
    "correlation_engine": 0.90,
}


def calculate_bayesian_confidence(evidence_items: list[EvidenceModel]) -> tuple[float, ConfidenceLevel]:
    """
    Computes a mathematically grounded aggregated confidence score using
    independent multi-source Bayesian corroboration:
        P(True) = 1 - PROD_{i=1..k} (1 - W_i * P_i)
    Guarantees reproducibility, monotonicity with corroborating sources,
    and returns (confidence_score_float, mapped_confidence_level).
    """
    if not evidence_items:
        return 0.35, ConfidenceLevel.POTENTIAL

    # Group evidence by tool to prevent artificial boost from identical duplicate tool queries
    tool_best_p: dict[str, float] = {}
    for ev in evidence_items:
        w = TOOL_RELIABILITY_WEIGHTS.get(ev.tool, 0.85)
        p = CONFIDENCE_BASE_PROBABILITIES.get(ev.confidence, 0.50)
        effective_p = min(0.99, max(0.01, w * p))
        if ev.tool not in tool_best_p or effective_p > tool_best_p[ev.tool]:
            tool_best_p[ev.tool] = effective_p

    error_product = 1.0
    for eff_p in tool_best_p.values():
        error_product *= (1.0 - eff_p)

    aggregated_p = round(1.0 - error_product, 4)

    # Map aggregated probability to ConfidenceLevel
    if aggregated_p >= 0.90:
        level = ConfidenceLevel.STRONG
    elif aggregated_p >= 0.70:
        level = ConfidenceLevel.OBSERVED
    elif aggregated_p >= 0.45:
        level = ConfidenceLevel.SUPPORTED
    else:
        level = ConfidenceLevel.POTENTIAL

    return aggregated_p, level


@dataclass(frozen=True, slots=True)
class InferredRelationship:
    source_entity_id: UUID
    target_entity_id: UUID
    predicate: str
    confidence: ConfidenceLevel
    confidence_score: float
    reasoning: str
    backing_evidence_ids: list[UUID]


class CorrelationEngine:
    """
    Normalizes, correlates, and links entities across distinct OSINT engine observations.
    Computes mathematically grounded multi-source confidence scores and guarantees
    100% evidence provenance on every discovered or inferred edge and node.
    """

    def __init__(self, db: Session, investigation_id: UUID) -> None:
        self.db = db
        self.investigation_id = investigation_id

    def run_correlation(self) -> dict[str, Any]:
        """
        Executes full correlation pass:
        1. Recalculates mathematically grounded Bayesian confidence for all entities based on backing evidence.
        2. Discovers deterministic and probabilistic cross-entity relationships (Email-Username, Profile-Domain, etc.).
        3. Persists inferred relationships with complete provenance links.
        """
        logger.info("Starting correlation pass", investigation_id=str(self.investigation_id))

        entities = (
            self.db.query(EntityModel)
            .filter_by(investigation_id=self.investigation_id)
            .all()
        )
        if not entities:
            return {"updated_entities": 0, "inferred_relationships": 0}

        evidence_items = (
            self.db.query(EvidenceModel)
            .filter_by(investigation_id=self.investigation_id)
            .all()
        )

        # Index evidence by entity_id
        evidence_by_entity: dict[UUID, list[EvidenceModel]] = defaultdict(list)
        for ev in evidence_items:
            if ev.entity_id:
                evidence_by_entity[ev.entity_id].append(ev)

        # 1. Update entities with Bayesian confidence & corroboration counts
        updated_entities_count = 0
        for ent in entities:
            ent_evidence = evidence_by_entity.get(ent.id, [])
            if ent_evidence:
                score, level = calculate_bayesian_confidence(ent_evidence)
                ent.confidence = level.value
                attrs = dict(ent.attributes or {})
                attrs["confidence_score"] = score
                attrs["evidence_count"] = len(ent_evidence)
                attrs["corroborating_tools"] = list({ev.tool for ev in ent_evidence})
                ent.attributes = attrs
                updated_entities_count += 1

        # 2. Index existing relationships to avoid duplicates
        existing_rels = (
            self.db.query(RelationshipModel)
            .filter_by(investigation_id=self.investigation_id)
            .all()
        )
        existing_edges: set[tuple[UUID, str, UUID]] = {
            (r.source_entity_id, r.predicate, r.target_entity_id) for r in existing_rels
        }

        # 3. Discover Inferred Cross-Entity Links
        inferred = self._correlate_entities(entities, evidence_by_entity, existing_edges)

        # 4. Persist Inferred Relationships with explicit Evidence Provenance
        new_rels_count = 0
        now = datetime.now(UTC)
        for inf in inferred:
            edge_key = (inf.source_entity_id, inf.predicate, inf.target_entity_id)
            if edge_key in existing_edges:
                continue
            existing_edges.add(edge_key)

            rel_model = RelationshipModel(
                id=uuid4(),
                investigation_id=self.investigation_id,
                source_entity_id=inf.source_entity_id,
                target_entity_id=inf.target_entity_id,
                predicate=inf.predicate,
                confidence=inf.confidence.value,
                reasoning=inf.reasoning,
                created_at=now,
            )
            self.db.add(rel_model)
            self.db.flush()

            # Create explicit evidence provenance for the inferred relationship
            rel_evidence = EvidenceModel(
                id=uuid4(),
                investigation_id=self.investigation_id,
                relationship_id=rel_model.id,
                source="OpenIntel Correlation Engine",
                tool="correlation_engine",
                timestamp=now,
                raw_observation=inf.reasoning,
                confidence=inf.confidence.value,
                info_classification=InfoClassification.INFERENCE.value,
                metadata_json={
                    "confidence_score": inf.confidence_score,
                    "derived_from_evidence_ids": [str(eid) for eid in inf.backing_evidence_ids],
                },
            )
            self.db.add(rel_evidence)
            new_rels_count += 1

        self.db.commit()
        logger.info(
            "Correlation pass complete",
            investigation_id=str(self.investigation_id),
            updated_entities=updated_entities_count,
            inferred_relationships=new_rels_count,
        )
        return {
            "updated_entities": updated_entities_count,
            "inferred_relationships": new_rels_count,
        }

    def _correlate_entities(
        self,
        entities: list[EntityModel],
        evidence_by_entity: dict[UUID, list[EvidenceModel]],
        existing_edges: set[tuple[UUID, str, UUID]],
    ) -> list[InferredRelationship]:
        """Runs heuristic and semantic correlation rules."""
        inferred: list[InferredRelationship] = []

        # Index entities by kind
        emails = [e for e in entities if e.kind == EntityKind.EMAIL.value]
        profiles = [e for e in entities if e.kind == EntityKind.PROFILE.value]
        domains = [e for e in entities if e.kind == EntityKind.DOMAIN.value]
        persons = [e for e in entities if e.kind == EntityKind.PERSON.value]

        # Index profiles by value, handle attribute, or URL path component
        username_map: dict[str, EntityModel] = {}
        for p in profiles:
            val = p.value.strip().lower()
            username_map[val] = p
            handle = (p.attributes or {}).get("handle")
            if handle:
                username_map[str(handle).strip().lower()] = p
            if "/" in val:
                last_seg = val.rstrip("/").split("/")[-1].lstrip("@")
                if last_seg:
                    username_map[last_seg] = p

        domain_map = {d.value.strip().lower(): d for d in domains}

        # Rule 1: Email <-> Username local-part matching
        for email in emails:
            val = email.value.strip().lower()
            if "@" in val:
                local_part, domain_part = val.split("@", 1)
                clean_local = local_part.replace(".", "").replace("_", "").replace("-", "")

                # Check exact or normalized local part match with username
                matched_user = username_map.get(local_part) or username_map.get(clean_local)
                if matched_user and (email.id, "has_username", matched_user.id) not in existing_edges:
                    ev_ids = [e.id for e in evidence_by_entity.get(email.id, [])] + [
                        e.id for e in evidence_by_entity.get(matched_user.id, [])
                    ]
                    inferred.append(
                        InferredRelationship(
                            source_entity_id=email.id,
                            target_entity_id=matched_user.id,
                            predicate="has_username",
                            confidence=ConfidenceLevel.STRONG,
                            confidence_score=0.92,
                            reasoning=f"Email '{email.value}' local part matches username handle '{matched_user.value}'",
                            backing_evidence_ids=ev_ids,
                        )
                    )

                # Check domain part match with domain entities
                matched_domain = domain_map.get(domain_part)
                if matched_domain and (email.id, "hosted_on_domain", matched_domain.id) not in existing_edges:
                    ev_ids = [e.id for e in evidence_by_entity.get(email.id, [])] + [
                        e.id for e in evidence_by_entity.get(matched_domain.id, [])
                    ]
                    inferred.append(
                        InferredRelationship(
                            source_entity_id=email.id,
                            target_entity_id=matched_domain.id,
                            predicate="hosted_on_domain",
                            confidence=ConfidenceLevel.STRONG,
                            confidence_score=0.95,
                            reasoning=f"Email domain '@{domain_part}' corresponds to discovered domain '{matched_domain.value}'",
                            backing_evidence_ids=ev_ids,
                        )
                    )

        # Rule 2: Profile URL <-> Domain & Username correlation
        for profile in profiles:
            try:
                parsed = urlparse(profile.value.strip())
                hostname = parsed.netloc.lower()
                if hostname.startswith("www."):
                    hostname = hostname[4:]

                # Match host with domain
                matched_domain = domain_map.get(hostname)
                if matched_domain and (matched_domain.id, "hosts_profile", profile.id) not in existing_edges:
                    ev_ids = [e.id for e in evidence_by_entity.get(profile.id, [])]
                    inferred.append(
                        InferredRelationship(
                            source_entity_id=matched_domain.id,
                            target_entity_id=profile.id,
                            predicate="hosts_profile",
                            confidence=ConfidenceLevel.STRONG,
                            confidence_score=0.95,
                            reasoning=f"Domain '{matched_domain.value}' hosts social profile '{profile.value}'",
                            backing_evidence_ids=ev_ids,
                        )
                    )

                # Extract handle from profile path (e.g. /john_doe or /in/john_doe)
                path_parts = [p for p in parsed.path.strip("/").split("/") if p and p not in ("in", "user", "u")]
                if path_parts:
                    candidate_handle = path_parts[0].lower().lstrip("@")
                    matched_user = username_map.get(candidate_handle)
                    if matched_user and (profile.id, "belongs_to_handle", matched_user.id) not in existing_edges:
                        ev_ids = [e.id for e in evidence_by_entity.get(profile.id, [])] + [
                            e.id for e in evidence_by_entity.get(matched_user.id, [])
                        ]
                        inferred.append(
                            InferredRelationship(
                                source_entity_id=profile.id,
                                target_entity_id=matched_user.id,
                                predicate="belongs_to_handle",
                                confidence=ConfidenceLevel.SUPPORTED,
                                confidence_score=0.88,
                                reasoning=f"Profile URL path matches username '{matched_user.value}'",
                                backing_evidence_ids=ev_ids,
                            )
                        )
            except Exception:
                pass

        # Rule 3: Person Name <-> Profile / Email correlation
        for person in persons:
            person_clean = person.value.strip().lower()
            for profile in profiles:
                # Check if profile attributes contain display name matching person
                disp_name = (profile.attributes or {}).get("display_name", "").lower()
                if disp_name and (person_clean in disp_name or disp_name in person_clean):
                    if (person.id, "operates_profile", profile.id) not in existing_edges:
                        ev_ids = [e.id for e in evidence_by_entity.get(person.id, [])] + [
                            e.id for e in evidence_by_entity.get(profile.id, [])
                        ]
                        inferred.append(
                            InferredRelationship(
                                source_entity_id=person.id,
                                target_entity_id=profile.id,
                                predicate="operates_profile",
                                confidence=ConfidenceLevel.STRONG,
                                confidence_score=0.90,
                                reasoning=f"Person name '{person.value}' matches profile display name '{disp_name}'",
                                backing_evidence_ids=ev_ids,
                            )
                        )

        # Rule 4: Domain <-> Subdomain hierarchy
        for d1 in domains:
            v1 = d1.value.strip().lower()
            for d2 in domains:
                if d1.id != d2.id:
                    v2 = d2.value.strip().lower()
                    if v1.endswith("." + v2) and (d1.id, "subdomain_of", d2.id) not in existing_edges:
                        ev_ids = [e.id for e in evidence_by_entity.get(d1.id, [])] + [
                            e.id for e in evidence_by_entity.get(d2.id, [])
                        ]
                        inferred.append(
                            InferredRelationship(
                                source_entity_id=d1.id,
                                target_entity_id=d2.id,
                                predicate="subdomain_of",
                                confidence=ConfidenceLevel.STRONG,
                                confidence_score=0.98,
                                reasoning=f"Domain '{d1.value}' is a hierarchical subdomain of '{d2.value}'",
                                backing_evidence_ids=ev_ids,
                            )
                        )

        return inferred
