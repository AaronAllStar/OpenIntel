# Developer Guide: Writing an OpenIntel OSINT Adapter

OpenIntel uses a decoupled, event-driven adapter architecture. Every intelligence engine runs as an independent plugin that consumes a standardized target, streams typed events (entities, relationships, evidence, progress, logs), and declares its legal classification and health status.

This architecture guarantees that:
1. **Adding an adapter requires zero core runner changes.**
2. **Every observation has unbreakable evidence provenance and legal classification.**
3. **Execution is resilient to process stalls, crashes, timeouts, and rate limits.**

---

## 1. The Core Adapter Contract

All adapters implement the [`OsintAdapter`](file:///c:/Users/damed/Downloads/OpenIntel/src/app/domain/ports/adapter.py) protocol or inherit from [`BaseSubprocessAdapter`](file:///c:/Users/damed/Downloads/OpenIntel/src/adapters/base.py) / [`BaseAdapter`](file:///c:/Users/damed/Downloads/OpenIntel/src/app/domain/ports/adapter.py).

### Adapter Protocol Definition

```python
class OsintAdapter(Protocol):
    name: str
    version: str
    capabilities: tuple[str, ...]
    supported_targets: tuple[TargetKind, ...]
    legality_metadata: LegalityMetadata

    def health_check(self) -> HealthStatus: ...

    def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]: ...
```

---

## 2. Event Types & Output Schemas

Adapters stream events asynchronously via an `AsyncIterator[AdapterEvent]`. The supported event types are:

| Event Type | Purpose | Mandatory Fields |
|---|---|---|
| [`ProgressEvent`](file:///c:/Users/damed/Downloads/OpenIntel/src/app/domain/ports/adapter.py) | Updates investigation progress percentage and stage label | `step: str`, `pct: float \| None` |
| [`EntityEvent`](file:///c:/Users/damed/Downloads/OpenIntel/src/app/domain/ports/adapter.py) | Discovers a new entity with tied provenance evidence | `entity: EntityDraft`, `evidence: EvidenceDraft` |
| [`RelationshipEvent`](file:///c:/Users/damed/Downloads/OpenIntel/src/app/domain/ports/adapter.py) | Links two entities with a predicate and tied evidence | `relationship: RelationshipDraft`, `evidence: EvidenceDraft` |
| [`LogEvent`](file:///c:/Users/damed/Downloads/OpenIntel/src/app/domain/ports/adapter.py) | Emits structured diagnostic log messages | `level: "debug" \| "info" \| "warn"`, `message: str` |
| [`ErrorEvent`](file:///c:/Users/damed/Downloads/OpenIntel/src/app/domain/ports/adapter.py) | Signals a recoverable or non-fatal adapter error | `error: AdapterError` |

---

## 3. Evidence Provenance & Legal Classification

Every `EntityEvent` and `RelationshipEvent` **must** include an [`EvidenceDraft`](file:///c:/Users/damed/Downloads/OpenIntel/src/app/domain/ports/adapter.py). Observations without provenance are rejected by the core normalizer.

### Information Classifications (`InfoClassification`)

- `PUBLIC_OBSERVATION`: Information directly observable on the public internet without bypassing access controls (e.g. public website, social media public profile, certificate transparency log).
- `PUBLIC_REGISTRY`: Data obtained from official public registers, WHOIS, DNS records, or government databases.
- `PLATFORM_SIGNAL`: Metadata inferred or derived from platform response headers, error codes, or timing discrepancies (e.g. "password reset page confirms email exists").
- `INFERENCE`: Algorithmic deductions, graph correlations, or confidence calculations produced by analysis.

### Confidence Levels (`ConfidenceLevel`)

- `OBSERVED`: Directly observed in the target response or registry record.
- `CONFIRMED`: Corroborated by multiple independent engines or cryptographic/official sources.
- `SUPPORTED`: Plausible correlation supported by circumstantial evidence.
- `TENTATIVE`: Weak match requiring analyst validation.

---

## 4. Health Checks

Every adapter must implement `health_check() -> HealthStatus`. The core executor and admin health endpoints query this method to verify engine readiness before dispatching tasks:

```python
@dataclass(frozen=True, slots=True)
class HealthStatus:
    is_healthy: bool
    status: Literal["ready", "degraded", "unavailable"]
    message: str
    details: dict[str, Any] = field(default_factory=dict)
```

Common health check tasks:
- Verify CLI binaries exist on `$PATH` (e.g. `shutil.which("amass")`).
- Verify required environment variables / API keys exist if applicable.
- Confirm local cache directories are writable.

---

## 5. Complete Minimal Working Example

Here is a complete, production-ready adapter implementation that adheres to all OpenIntel contracts:

```python
# src/adapters/threat_feed/adapter.py
import asyncio
from collections.abc import AsyncIterator
import shutil

from src.adapters.base import BaseSubprocessAdapter
from src.app.domain.enums import (
    ConfidenceLevel,
    EntityKind,
    InfoClassification,
    TargetKind,
)
from src.app.domain.ports.adapter import (
    AdapterEvent,
    AdapterInput,
    EntityDraft,
    EntityEvent,
    EvidenceDraft,
    HealthStatus,
    LegalityMetadata,
    ProgressEvent,
)


class ThreatFeedAdapter(BaseSubprocessAdapter):
    """Checks public threat intelligence blocklists for suspicious IP addresses."""

    name = "threat_feed"
    version = "1.0.0"
    capabilities = ("ip_reputation", "threat_intel")
    supported_targets = (TargetKind.IP, TargetKind.DOMAIN)
    legality_metadata = LegalityMetadata(
        default_classification=InfoClassification.PUBLIC_OBSERVATION,
        requires_auth=False,
        requires_network=True,
        requires_binary=False,
        description="Public threat reputation lookup feed",
    )

    def health_check(self) -> HealthStatus:
        return HealthStatus(
            is_healthy=True,
            status="ready",
            message="ThreatFeedAdapter is operational",
            details={"version": self.version},
        )

    async def run(
        self,
        input: AdapterInput,
        cancel_event: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]:
        target_val = input.target.value.strip()

        yield ProgressEvent(step=f"Querying threat feed for {target_val}", pct=25.0)

        if cancel_event.is_set():
            return

        # Perform asynchronous lookup (e.g. via httpx)
        # Yield normalized entity with mandatory evidence provenance
        entity = EntityDraft(
            kind=EntityKind.IP if input.target.kind == TargetKind.IP else EntityKind.DOMAIN,
            value=target_val,
            confidence=ConfidenceLevel.OBSERVED,
            attributes={"reputation_score": 10, "threat_type": "clean"},
        )
        evidence = EvidenceDraft(
            source="Public Threat Intelligence Community Feed",
            tool=self.name,
            raw_observation=f"Target {target_val} is not listed on current threat feeds",
            confidence=ConfidenceLevel.OBSERVED,
            info_classification=self.legality_metadata.default_classification,
            metadata={"indicator": target_val},
        )

        yield EntityEvent(entity=entity, evidence=evidence)
        yield ProgressEvent(step="Threat feed check complete", pct=100.0)
```

---

## 6. Registration & Discovery

### Option A: Built-in Registration
Add the adapter to [`src/adapters/registry.py`](file:///c:/Users/damed/Downloads/OpenIntel/src/adapters/registry.py) in `_register_builtin_adapters()`.

### Option B: Zero-Code Dynamic Plugin Entry Point
OpenIntel scans standard Python entry points under the group `openintel.adapters`. If you distribute an adapter as an independent package or wheel, define it in your `pyproject.toml`:

```toml
[project.entry-points."openintel.adapters"]
threat_feed = "my_custom_package.threat_feed:ThreatFeedAdapter"
```

OpenIntel automatically discovers, registers, and exposes your adapter on startup without requiring any modifications to the core codebase.

---

## 7. Testing Your Adapter

Every adapter must satisfy the contract test suite in [`tests/adapters/test_adapter_contract.py`](file:///c:/Users/damed/Downloads/OpenIntel/tests/adapters/test_adapter_contract.py):

1. **Metadata Contract**: Valid name, version, capabilities, targets, and legality metadata.
2. **Health Check Contract**: Non-crashing `health_check()` returning `HealthStatus`.
3. **Execution Contract**: Offline, CI-safe asynchronous execution yielding properly formatted events with evidence and legal classification.

Run the test suite with:
```bash
uv run pytest tests/adapters/test_adapter_contract.py -v
```
