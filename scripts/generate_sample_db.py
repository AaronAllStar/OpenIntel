"""
OpenIntel - Sample Database Generator
Creates and populates `openintel_sample.db` with realistic, production-grade OSINT
investigations across all modalities (Person, Phone/WhatsApp, Domain/Leaks, National ID).
"""

import os
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from datetime import UTC, datetime, timedelta
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app.infrastructure.database import Base
from src.app.infrastructure.models import (
    EntityModel,
    EvidenceModel,
    InvestigationModel,
    RelationshipModel,
)

SAMPLE_DB_PATH = "openintel_sample.db"


def generate_sample_database() -> None:
    if os.path.exists(SAMPLE_DB_PATH):
        os.remove(SAMPLE_DB_PATH)

    engine = create_engine(f"sqlite:///{SAMPLE_DB_PATH}")
    Base.metadata.create_all(bind=engine)

    now = datetime.now(UTC)

    with Session(engine) as session:
        # ----------------------------------------------------------------------
        # Case 1: Person (Nombre y Apellido) + Reconocimiento Corporativo
        # ----------------------------------------------------------------------
        inv1_id = uuid.uuid4()
        inv1 = InvestigationModel(
            id=inv1_id,
            name="Elena Navarro - Reconocimiento Corporativo & Perfil",
            target_kind="person_name",
            target_value="Elena Navarro @ cyberdefense.org",
            investigation_type="quick",
            status="final",
            created_at=now - timedelta(hours=3),
            started_at=now - timedelta(hours=3),
            finished_at=now - timedelta(hours=2, minutes=58),
            settings={"timeout_ms": 30000, "max_results": 500},
        )
        session.add(inv1)

        # Entities
        e1_person = EntityModel(
            id=uuid.uuid4(),
            investigation_id=inv1_id,
            kind="person",
            value="Elena Navarro",
            confidence="observed",
            attributes={"full_name": "Elena Navarro", "role": "Chief Information Security Officer (CISO)", "organization": "CyberDefense Alliance"},
            first_seen=now - timedelta(hours=3),
        )
        e1_email = EntityModel(
            id=uuid.uuid4(),
            investigation_id=inv1_id,
            kind="email",
            value="elena.navarro@cyberdefense.org",
            confidence="supported",
            attributes={"pattern": "first.last", "domain": "cyberdefense.org", "mx_validated": True},
            first_seen=now - timedelta(hours=3),
        )
        e1_x = EntityModel(
            id=uuid.uuid4(),
            investigation_id=inv1_id,
            kind="profile",
            value="https://x.com/elena_sec",
            confidence="observed",
            attributes={"platform": "X (Twitter)", "handle": "elena_sec", "followers_count": 4820, "display_name": "Elena Navarro | CISO"},
            first_seen=now - timedelta(hours=3),
        )
        e1_domain = EntityModel(
            id=uuid.uuid4(),
            investigation_id=inv1_id,
            kind="domain",
            value="cyberdefense.org",
            confidence="observed",
            attributes={"mx_servers": ["mail.cyberdefense.org", "aspmx.l.google.com"], "has_mail_service": True},
            first_seen=now - timedelta(hours=3),
        )
        session.add_all([e1_person, e1_email, e1_x, e1_domain])

        # Evidence
        session.add(EvidenceModel(
            id=uuid.uuid4(),
            investigation_id=inv1_id,
            entity_id=e1_x.id,
            source="X Public Syndication Registry",
            tool="twikit",
            raw_observation="Public X profile verified for @elena_sec ('Elena Navarro | CISO') with 4,820 followers.",
            confidence="observed",
            info_classification="PUBLIC_REGISTRY",
            metadata_json={"screen_name": "elena_sec", "followers": 4820},
        ))
        session.add(EvidenceModel(
            id=uuid.uuid4(),
            investigation_id=inv1_id,
            entity_id=e1_email.id,
            source="Corporate Email Pattern Permutation & DNS Validation",
            tool="email_enrich",
            raw_observation="Generated and validated corporate email pattern candidate: elena.navarro@cyberdefense.org (DNS MX verified).",
            confidence="supported",
            info_classification="INFERENCE",
            metadata_json={"email": "elena.navarro@cyberdefense.org", "domain": "cyberdefense.org"},
        ))
        session.add(EvidenceModel(
            id=uuid.uuid4(),
            investigation_id=inv1_id,
            entity_id=e1_domain.id,
            source="DNS MX Exchange Resolution",
            tool="email_enrich",
            raw_observation="Resolved 2 active mail exchange servers for cyberdefense.org: ['mail.cyberdefense.org', 'aspmx.l.google.com'].",
            confidence="observed",
            info_classification="PUBLIC_REGISTRY",
            metadata_json={"domain": "cyberdefense.org"},
        ))

        # Relationships
        session.add(RelationshipModel(
            id=uuid.uuid4(),
            investigation_id=inv1_id,
            source_entity_id=e1_person.id,
            target_entity_id=e1_x.id,
            predicate="operates_x_profile",
            confidence="observed",
            reasoning="Direct name and biometric profile alignment",
        ))
        session.add(RelationshipModel(
            id=uuid.uuid4(),
            investigation_id=inv1_id,
            source_entity_id=e1_email.id,
            target_entity_id=e1_domain.id,
            predicate="hosted_on_domain",
            confidence="supported",
            reasoning="Active MX record corporate routing",
        ))
        session.add(RelationshipModel(
            id=uuid.uuid4(),
            investigation_id=inv1_id,
            source_entity_id=e1_person.id,
            target_entity_id=e1_domain.id,
            predicate="holds_position_at",
            confidence="supported",
            reasoning="Chief Information Security Officer title matching",
        ))

        # ----------------------------------------------------------------------
        # Case 2: Teléfono con Selector de País + WhatsApp & Telecom
        # ----------------------------------------------------------------------
        inv2_id = uuid.uuid4()
        inv2 = InvestigationModel(
            id=inv2_id,
            name="Teléfono +34 612 345 678 (España) - Telecom & WhatsApp",
            target_kind="phone",
            target_value="+34612345678",
            investigation_type="quick",
            status="final",
            created_at=now - timedelta(hours=2),
            started_at=now - timedelta(hours=2),
            finished_at=now - timedelta(hours=1, minutes=58),
            settings={"timeout_ms": 30000, "max_results": 500},
        )
        session.add(inv2)

        e2_phone = EntityModel(
            id=uuid.uuid4(),
            investigation_id=inv2_id,
            kind="phone",
            value="+34612345678",
            confidence="observed",
            attributes={
                "e164": "+34612345678",
                "international": "+34 612 345 678",
                "country": "Spain",
                "country_code": 34,
                "whatsapp_presence": "active",
            },
            first_seen=now - timedelta(hours=2),
        )
        e2_wa = EntityModel(
            id=uuid.uuid4(),
            investigation_id=inv2_id,
            kind="profile",
            value="https://wa.me/34612345678",
            confidence="supported",
            attributes={"platform": "WhatsApp", "chat_url": "https://wa.me/34612345678", "region": "Spain"},
            first_seen=now - timedelta(hours=2),
        )
        e2_carrier = EntityModel(
            id=uuid.uuid4(),
            investigation_id=inv2_id,
            kind="organization",
            value="Vodafone España S.A.U.",
            confidence="observed",
            attributes={"carrier": "Vodafone España", "network_type": "Mobile", "country": "Spain"},
            first_seen=now - timedelta(hours=2),
        )
        session.add_all([e2_phone, e2_wa, e2_carrier])

        session.add(EvidenceModel(
            id=uuid.uuid4(),
            investigation_id=inv2_id,
            entity_id=e2_wa.id,
            source="WhatsApp Click-to-Chat Protocol",
            tool="whatsapp",
            raw_observation="WhatsApp direct endpoint resolved: https://wa.me/34612345678. Contact chat is active and reachable.",
            confidence="observed",
            info_classification="PLATFORM_SIGNAL",
            metadata_json={"wa_link": "https://wa.me/34612345678"},
        ))
        session.add(EvidenceModel(
            id=uuid.uuid4(),
            investigation_id=inv2_id,
            entity_id=e2_phone.id,
            source="ITU-T E.164 National Telecom Numbering Plan",
            tool="phoneinfoga",
            raw_observation="Phone number normalized to E.164: +34612345678. Country: Spain. Assigned Carrier: Vodafone España.",
            confidence="observed",
            info_classification="PUBLIC_REGISTRY",
            metadata_json={"carrier": "Vodafone España", "country": "Spain"},
        ))
        session.add(RelationshipModel(
            id=uuid.uuid4(),
            investigation_id=inv2_id,
            source_entity_id=e2_phone.id,
            target_entity_id=e2_wa.id,
            predicate="has_whatsapp_chat",
            confidence="observed",
            reasoning="Direct verified WhatsApp link",
        ))
        session.add(RelationshipModel(
            id=uuid.uuid4(),
            investigation_id=inv2_id,
            source_entity_id=e2_phone.id,
            target_entity_id=e2_carrier.id,
            predicate="routed_by_carrier",
            confidence="observed",
            reasoning="ITU telecom operator assignment",
        ))

        # ----------------------------------------------------------------------
        # Case 3: Dominio, Infraestructura & Fugas de Secretos
        # ----------------------------------------------------------------------
        inv3_id = uuid.uuid4()
        inv3 = InvestigationModel(
            id=inv3_id,
            name="Acme Cyber Corp - Infraestructura y Fugas",
            target_kind="domain",
            target_value="acmecyber.io",
            investigation_type="full",
            status="final",
            created_at=now - timedelta(hours=1),
            started_at=now - timedelta(hours=1),
            finished_at=now - timedelta(minutes=55),
            settings={"timeout_ms": 30000, "max_results": 500},
        )
        session.add(inv3)

        e3_dom = EntityModel(
            id=uuid.uuid4(),
            investigation_id=inv3_id,
            kind="domain",
            value="acmecyber.io",
            confidence="observed",
            attributes={"subdomains_count": 3, "ip_address": "104.21.55.10"},
            first_seen=now - timedelta(hours=1),
        )
        e3_sub1 = EntityModel(
            id=uuid.uuid4(),
            investigation_id=inv3_id,
            kind="domain",
            value="api.acmecyber.io",
            confidence="observed",
            attributes={"ip_address": "104.21.55.11", "status": "active"},
            first_seen=now - timedelta(hours=1),
        )
        e3_repo = EntityModel(
            id=uuid.uuid4(),
            investigation_id=inv3_id,
            kind="repository",
            value="acmecyber/cloud-infrastructure",
            confidence="observed",
            attributes={"platform": "GitHub", "visibility": "public", "stars": 42},
            first_seen=now - timedelta(hours=1),
        )
        e3_sec_email = EntityModel(
            id=uuid.uuid4(),
            investigation_id=inv3_id,
            kind="email",
            value="security@acmecyber.io",
            confidence="observed",
            attributes={"role": "security", "purpose": "Vulnerability disclosure contact"},
            first_seen=now - timedelta(hours=1),
        )
        session.add_all([e3_dom, e3_sub1, e3_repo, e3_sec_email])

        session.add(EvidenceModel(
            id=uuid.uuid4(),
            investigation_id=inv3_id,
            entity_id=e3_sub1.id,
            source="OWASP Amass External DNS Mapping",
            tool="amass",
            raw_observation="External DNS entry discovered via Amass: api.acmecyber.io resolving to 104.21.55.11.",
            confidence="observed",
            info_classification="PUBLIC_REGISTRY",
            metadata_json={"subdomain": "api.acmecyber.io"},
        ))
        session.add(EvidenceModel(
            id=uuid.uuid4(),
            investigation_id=inv3_id,
            entity_id=e3_repo.id,
            source="TruffleHog Commit Audit",
            tool="trufflehog",
            raw_observation="Scanned public repository acmecyber/cloud-infrastructure: 0 critical credentials exposed, 1 staging endpoint documented.",
            confidence="observed",
            info_classification="PUBLIC_OBSERVATION",
            metadata_json={"repo": "acmecyber/cloud-infrastructure"},
        ))
        session.add(RelationshipModel(
            id=uuid.uuid4(),
            investigation_id=inv3_id,
            source_entity_id=e3_sub1.id,
            target_entity_id=e3_dom.id,
            predicate="subdomain_of",
            confidence="observed",
            reasoning="DNS hierarchy mapping",
        ))
        session.add(RelationshipModel(
            id=uuid.uuid4(),
            investigation_id=inv3_id,
            source_entity_id=e3_repo.id,
            target_entity_id=e3_dom.id,
            predicate="managed_by_organization",
            confidence="observed",
            reasoning="GitHub organization domain link",
        ))

        # ----------------------------------------------------------------------
        # Case 4: Documento de Identidad Nacional (DNI / NIE)
        # ----------------------------------------------------------------------
        inv4_id = uuid.uuid4()
        inv4 = InvestigationModel(
            id=inv4_id,
            name="DNI 12345678Z (España) - Verificación Oficial",
            target_kind="national_id",
            target_value="12345678Z",
            investigation_type="quick",
            status="final",
            created_at=now - timedelta(minutes=30),
            started_at=now - timedelta(minutes=30),
            finished_at=now - timedelta(minutes=29),
            settings={"timeout_ms": 30000, "max_results": 500},
        )
        session.add(inv4)

        e4_id = EntityModel(
            id=uuid.uuid4(),
            investigation_id=inv4_id,
            kind="national_id",
            value="12345678Z",
            confidence="observed",
            attributes={"country": "Spain", "scheme": "DNI", "checksum_valid": True},
            first_seen=now - timedelta(minutes=30),
        )
        session.add(e4_id)

        session.add(EvidenceModel(
            id=uuid.uuid4(),
            investigation_id=inv4_id,
            entity_id=e4_id.id,
            source="National Identity Specification (Spain DNI)",
            tool="id_validation",
            raw_observation="Official checksum algorithm verified for Spain DNI (ESP): 12345678Z. Format and check letter conform to Royal Decree 1553/2005.",
            confidence="observed",
            info_classification="PUBLIC_REGISTRY",
            metadata_json={"country": "ESP", "scheme": "DNI"},
        ))

        session.commit()

    print(f"Successfully generated sample database at: {SAMPLE_DB_PATH}")


if __name__ == "__main__":
    generate_sample_database()
