import asyncio
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.adapters.base import BaseSubprocessAdapter
from src.adapters.registry import get_adapter_registry
from src.app.domain.enums import (
    ConfidenceLevel,
    EntityKind,
    InfoClassification,
    TargetKind,
)
from src.app.domain.ports.adapter import (
    AdapterEvent,
    AdapterInput,
    AdapterOptions,
    EntityDraft,
    EntityEvent,
    EvidenceDraft,
    HealthStatus,
    LegalityMetadata,
    OsintAdapter,
    ProgressEvent,
    RelationshipDraft,
    RelationshipEvent,
)
from src.app.domain.value_objects import Target

ALL_ADAPTERS = get_adapter_registry().list_all()


# Sample valid values per TargetKind for offline contract tests
SAMPLE_TARGET_VALUES = {
    TargetKind.USERNAME: "contract_analyst",
    TargetKind.EMAIL: "analyst@example.com",
    TargetKind.DOMAIN: "target.org",
    TargetKind.PHONE: "+1 202-555-0143",
    TargetKind.URL: "https://target.org/page",
    TargetKind.IP: "8.8.8.8",
    TargetKind.ORGANIZATION: "Cyber Corp",
    TargetKind.PERSON_NAME: "Carlos Navarro",
    TargetKind.LOCATION: "Madrid, Spain",
    TargetKind.NATIONAL_ID: "12345678Z",
    TargetKind.REPOSITORY: "octocat/Hello-World",
}


@pytest.mark.parametrize("adapter", ALL_ADAPTERS, ids=lambda a: a.name)
def test_adapter_metadata_contract(adapter: OsintAdapter):
    """
    Contract Requirement:
    Every adapter must specify name, version, capabilities, supported_targets,
    and valid legality_metadata.
    """
    assert isinstance(adapter.name, str) and len(adapter.name) > 0
    assert isinstance(adapter.version, str) and len(adapter.version) > 0
    assert isinstance(adapter.capabilities, tuple)
    assert isinstance(adapter.supported_targets, tuple) and len(adapter.supported_targets) > 0
    assert isinstance(adapter.legality_metadata, LegalityMetadata)
    assert adapter.legality_metadata.default_classification in InfoClassification


@pytest.mark.parametrize("adapter", ALL_ADAPTERS, ids=lambda a: a.name)
def test_adapter_health_check_contract(adapter: OsintAdapter):
    """
    Contract Requirement:
    Every adapter must implement health_check() returning a HealthStatus.
    """
    status = adapter.health_check()
    assert isinstance(status, HealthStatus)
    assert status.status in ("ready", "degraded", "unavailable")
    assert isinstance(status.is_healthy, bool)
    assert isinstance(status.message, str) and len(status.message) > 0
    assert isinstance(status.details, dict)


@pytest.mark.parametrize("adapter", ALL_ADAPTERS, ids=lambda a: a.name)
@pytest.mark.asyncio
async def test_adapter_execution_contract_no_network(adapter: OsintAdapter):
    """
    Contract Requirement:
    Every adapter must execute cleanly without external network calls (CI compliant),
    yielding valid events with mandatory evidence provenance and legal classification.
    """
    primary_kind = adapter.supported_targets[0]
    sample_val = SAMPLE_TARGET_VALUES[primary_kind]
    target = Target(kind=primary_kind, value=sample_val)

    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(timeout_ms=5000),
    )
    cancel_event = asyncio.Event()

    # Mock external network and subprocess dependencies to guarantee 100% offline execution
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"screen_name": "contract_analyst", "followers_count": 100}]
    mock_resp.text = "Mocked unauthenticated platform response"

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.post.return_value = mock_resp
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with (
        patch("httpx.AsyncClient", return_value=mock_client),
        patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec,
    ):
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"[+] Mock Platform: https://example.com/profile", b"")
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc

        events: list[AdapterEvent] = []
        async for event in adapter.run(adapter_input, cancel_event):
            events.append(event)

        assert len(events) > 0, f"Adapter {adapter.name} yielded 0 events"

        # Check mandatory evidence provenance and legal classification on all emitted entity events
        entity_events = [e for e in events if isinstance(e, EntityEvent)]
        for ee in entity_events:
            ev = ee.evidence
            assert isinstance(ev, EvidenceDraft)
            assert isinstance(ev.source, str) and len(ev.source) > 0
            assert ev.tool == adapter.name
            assert isinstance(ev.raw_observation, str) and len(ev.raw_observation) > 0
            assert ev.confidence in ConfidenceLevel
            assert ev.info_classification in InfoClassification
            assert isinstance(ev.metadata, dict)

        # Check relationships consistency
        rel_events = [e for e in events if isinstance(e, RelationshipEvent)]
        for re in rel_events:
            rel = re.relationship
            assert isinstance(rel, RelationshipDraft)
            assert isinstance(rel.source_entity_value, str) and len(rel.source_entity_value) > 0
            assert isinstance(rel.target_entity_value, str) and len(rel.target_entity_value) > 0
            assert isinstance(rel.predicate, str) and len(rel.predicate) > 0
            assert rel.confidence in ConfidenceLevel


def test_new_adapter_single_file_contract_acceptance():
    """
    Acceptance Criteria:
    Adding a new adapter takes a single file and passes the contract suite.
    Demonstrates zero-core-change pluggability.
    """

    class CustomIntelAdapter(BaseSubprocessAdapter):
        name = "custom_threat_intel"
        version = "1.0.0"
        capabilities = ("threat_lookup", "domain_reputation")
        supported_targets = (TargetKind.DOMAIN,)
        legality_metadata = LegalityMetadata(
            default_classification=InfoClassification.PUBLIC_OBSERVATION,
            description="Custom domain intelligence feed",
        )

        async def run(
            self,
            input: AdapterInput,
            cancel: asyncio.Event,
        ) -> AsyncIterator[AdapterEvent]:
            yield ProgressEvent(step="Checking custom threat reputation", pct=50.0)

            entity = EntityDraft(
                kind=EntityKind.DOMAIN,
                value=input.target.value,
                confidence=ConfidenceLevel.SUPPORTED,
                attributes={"reputation_score": 95},
            )
            evidence = EvidenceDraft(
                source="Custom Threat Intelligence Provider",
                tool=self.name,
                raw_observation=f"Threat score 95/100 for domain {input.target.value}",
                confidence=ConfidenceLevel.SUPPORTED,
                info_classification=InfoClassification.PUBLIC_OBSERVATION,
            )
            yield EntityEvent(entity=entity, evidence=evidence)
            yield ProgressEvent(step="Custom threat analysis complete", pct=100.0)

    # 1. Register in dynamic registry
    registry = get_adapter_registry()
    adapter = CustomIntelAdapter()
    registry.register(adapter)

    # 2. Verify metadata contract
    test_adapter_metadata_contract(adapter)

    # 3. Verify health check contract
    test_adapter_health_check_contract(adapter)

    # 4. Verify discovery by target
    domain_adapters = registry.get_for_target(TargetKind.DOMAIN)
    assert any(a.name == "custom_threat_intel" for a in domain_adapters)
