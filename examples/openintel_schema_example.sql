-- ==============================================================================
-- OpenIntel — Public PostgreSQL Schema & Demonstration Database
-- Reference implementation for GitHub viewers and local development onboarding.
-- ==============================================================================

-- 1. Investigations Table
CREATE TABLE IF NOT EXISTS investigations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    target_kind VARCHAR(50) NOT NULL,
    target_value VARCHAR(512) NOT NULL,
    investigation_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_by UUID NOT NULL,
    error_message TEXT,
    settings JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_investigations_status ON investigations(status);
CREATE INDEX IF NOT EXISTS ix_investigations_created_at ON investigations(created_at);

-- 2. Entities Table (Normalized OSINT Nodes)
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY,
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    kind VARCHAR(50) NOT NULL,
    value VARCHAR(1024) NOT NULL,
    canonical_key VARCHAR(1024) NOT NULL,
    confidence VARCHAR(50) NOT NULL,
    attributes JSONB DEFAULT '{}'::jsonb,
    first_seen TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_entities_inv_canonical ON entities(investigation_id, canonical_key);
CREATE INDEX IF NOT EXISTS ix_entities_investigation_id ON entities(investigation_id);
CREATE INDEX IF NOT EXISTS ix_entities_kind ON entities(kind);

-- 3. Relationships Table (Graph Edges with Provenance)
CREATE TABLE IF NOT EXISTS relationships (
    id UUID PRIMARY KEY,
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    source_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    predicate VARCHAR(100) NOT NULL DEFAULT 'associated_with',
    confidence VARCHAR(50) NOT NULL DEFAULT 'supported',
    reasoning TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_relationships_inv_entities ON relationships(investigation_id, source_entity_id, target_entity_id);
CREATE INDEX IF NOT EXISTS ix_relationships_source ON relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS ix_relationships_target ON relationships(target_entity_id);

-- 4. Evidence Table (Observations & Legal Classifications)
CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY,
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    relationship_id UUID REFERENCES relationships(id) ON DELETE CASCADE,
    source VARCHAR(255) NOT NULL,
    tool VARCHAR(100) NOT NULL,
    raw_observation TEXT NOT NULL,
    confidence VARCHAR(50) NOT NULL,
    info_classification VARCHAR(50) NOT NULL DEFAULT 'PUBLIC_OBSERVATION',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_evidence_inv_tool ON evidence(investigation_id, tool);
CREATE INDEX IF NOT EXISTS ix_evidence_inv_entity ON evidence(investigation_id, entity_id);
CREATE INDEX IF NOT EXISTS ix_evidence_inv_rel ON evidence(investigation_id, relationship_id);
CREATE INDEX IF NOT EXISTS ix_evidence_entity_id ON evidence(entity_id);
CREATE INDEX IF NOT EXISTS ix_evidence_relationship_id ON evidence(relationship_id);

-- 5. Audit Logs Table (Tamper-Evident Operational Trail)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100) NOT NULL,
    ip_address VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'SUCCESS',
    details_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS ix_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- ==============================================================================
-- Sanitized Demonstration Seed Data
-- ==============================================================================

INSERT INTO investigations (
    id, name, target_kind, target_value, investigation_type, status, created_at, started_at, finished_at, created_by, error_message, settings
) VALUES (
    '11111111-1111-1111-1111-111111111111',
    'Demonstration OSINT Investigation — Acme Security Target',
    'domain',
    'example-target.org',
    'deep_pivot',
    'completed',
    CURRENT_TIMESTAMP - INTERVAL '2 hours',
    CURRENT_TIMESTAMP - INTERVAL '118 minutes',
    CURRENT_TIMESTAMP - INTERVAL '110 minutes',
    '00000000-0000-0000-0000-000000000001',
    NULL,
    '{"max_depth": 2, "timeout_ms": 30000, "concurrency": 4}'::jsonb
) ON CONFLICT (id) DO NOTHING;

INSERT INTO entities (
    id, investigation_id, kind, value, canonical_key, confidence, attributes, first_seen
) VALUES (
    '22222222-2222-2222-2222-222222222221',
    '11111111-1111-1111-1111-111111111111',
    'domain',
    'example-target.org',
    'domain:example-target.org',
    'confirmed',
    '{"apex_domain": "example-target.org", "dnssec": true, "asn": "AS15169"}'::jsonb,
    CURRENT_TIMESTAMP - INTERVAL '118 minutes'
), (
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'national_id',
    'ESP:12345678Z',
    'national_id:ESP:12345678Z',
    'strong',
    '{"scheme": "Spain DNI", "country": "ESP", "checksum_verified": true}'::jsonb,
    CURRENT_TIMESTAMP - INTERVAL '115 minutes'
), (
    '22222222-2222-2222-2222-222222222223',
    '11111111-1111-1111-1111-111111111111',
    'email',
    'security-contact@example-target.org',
    'email:security-contact@example-target.org',
    'strong',
    '{"mx_verified": true, "disposable": false}'::jsonb,
    CURRENT_TIMESTAMP - INTERVAL '114 minutes'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO relationships (
    id, investigation_id, source_entity_id, target_entity_id, predicate, confidence, reasoning, created_at
) VALUES (
    '33333333-3333-3333-3333-333333333331',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222221',
    '22222222-2222-2222-2222-222222222223',
    'has_security_contact',
    'strong',
    'security.txt standard discovered on HTTP apex host points directly to address',
    CURRENT_TIMESTAMP - INTERVAL '113 minutes'
), (
    '33333333-3333-3333-3333-333333333332',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222221',
    '22222222-2222-2222-2222-222222222222',
    'officer_national_identifier',
    'strong',
    'Public corporate registry filing links domain holding entity to verified administrator DNI',
    CURRENT_TIMESTAMP - INTERVAL '112 minutes'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO evidence (
    id, investigation_id, entity_id, relationship_id, source, tool, raw_observation, confidence, info_classification, timestamp, metadata
) VALUES (
    '44444444-4444-4444-4444-444444444441',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    NULL,
    'National Registry Checksum Algorithm (Spain DNI)',
    'openintel_core_rust',
    'Mod-23 control digit verified for 12345678Z in 1.2 microseconds',
    'strong',
    'PUBLIC_REGISTRY',
    CURRENT_TIMESTAMP - INTERVAL '115 minutes',
    '{"engine": "rust_core", "subsystem": "id_validation", "validated": true}'::jsonb
), (
    '44444444-4444-4444-4444-444444444442',
    '11111111-1111-1111-1111-111111111111',
    NULL,
    '33333333-3333-3333-3333-333333333331',
    'RFC 9116 security.txt Endpoint',
    'http_scanner',
    'Parsed valid RFC 9116 security contact declaration at /.well-known/security.txt',
    'strong',
    'PUBLIC_OBSERVATION',
    CURRENT_TIMESTAMP - INTERVAL '113 minutes',
    '{"status_code": 200, "mime": "text/plain"}'::jsonb
) ON CONFLICT (id) DO NOTHING;

INSERT INTO audit_logs (
    id, timestamp, user_id, role, action, resource_type, resource_id, ip_address, status, details_json
) VALUES (
    '55555555-5555-5555-5555-555555555551',
    CURRENT_TIMESTAMP - INTERVAL '118 minutes',
    'lead-cyber-analyst',
    'analyst',
    'create_investigation',
    'investigation',
    '11111111-1111-1111-1111-111111111111',
    '127.0.0.1',
    'SUCCESS',
    '{"target_kind": "domain", "target_value": "example-target.org"}'::jsonb
) ON CONFLICT (id) DO NOTHING;
