# OpenIntel — Agent Instructions & Engineering Handbook

OpenIntel is an **application-first, self-hosted OSINT investigation platform** that orchestrates complex reconnaissance engines behind an intuitive, unified user experience.

These instructions govern all architecture, implementation, security, and interface decisions made by AI agents working on OpenIntel.

---

## 1. The Core Philosophy

### Product-First Rule
Complexity belongs inside OpenIntel, not in the user's workflow.
1. The user interacts with OpenIntel as a single investigation application, not a grab bag of CLI tools.
2. Choose sensible defaults automatically; never ask the user technical questions the system can decide.
3. Keep technical complexity (subprocesses, adapters, raw schemas, normalization algorithms) behind the UI.
4. Minimize user actions: **Target + Type → Start Investigation → Structured Evidence**.

### Transparency Without Cognitive Overload
Hiding complexity does **not** mean hiding evidence provenance. The user must always be able to inspect:
- **Source** (domain, platform, registry)
- **Tool / Engine** that discovered it
- **Timestamp** (UTC)
- **Original Observation** (raw finding or snippet)
- **Confidence Rating** (`Observed`, `Supported`, `Potential association`, `Strong association`)
- **Reason for Association** (human-readable justification)

Never represent inference or correlation as absolute certainty.

---

## 2. Locked Technology Stack

Every agent must strictly adhere to this technical baseline:

| Domain | Technology | Notes / Constraints |
|---|---|---|
| **Backend Runtime** | Python 3.12+ | Managed via `uv` |
| **API Framework** | FastAPI + Uvicorn | Async HTTP & SSE streaming only |
| **Validation / Settings** | Pydantic v2, `pydantic-settings` | Strict validation at boundaries |
| **Database & ORM** | PostgreSQL 16 + SQLAlchemy 2.x (Sync) | Migrations via Alembic |
| **Task Queue & Broker** | Celery 5.x + Redis | Redis serves as broker & result backend |
| **Real-Time Progress** | Redis Pub/Sub → FastAPI SSE → Frontend | **STRICTLY NO WebSockets, NO GraphQL, NO RPC** |
| **Frontend Framework** | React 18 (Plain JavaScript) + Vite | Pure JS (no TypeScript in frontend) |
| **UI & Styling** | Vanilla CSS / CSS Modules | Rich, modern, glassmorphic dark theme |
| **Animation & Graph** | Framer Motion + React Flow | Smooth micro-interactions & entity graph |
| **Client Data Fetching** | Fetch + TanStack Query (or SWR) | Cache and sync server state |
| **Code Hygiene** | Ruff + Mypy (backend), ESLint + Prettier (frontend) | Pre-commit / CI checked |
| **Testing** | Pytest (+ pytest-asyncio) & Vitest + MSW | Playwright for smoke E2E |

---

## 3. System Architecture & Layer Boundaries

```text
┌─────────────────────────────────────────────────────────────┐
│                 Frontend UI (React 18 + Vite)               │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP REST & SSE Events
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Layer (Async)                    │
│      - Endpoints, SSE streaming from Redis, Input Validation │
└──────────────┬──────────────────────────────┬───────────────┘
               │ Dispatch Celery Task         │ Read DB
┌──────────────▼──────────────┐ ┌─────────────▼───────────────┐
│  Redis Broker & Pub/Sub     │ │     PostgreSQL 16 (DB)       │
└──────────────┬──────────────┘ └─────────────▲───────────────┘
               │ Consume Task                 │ Persist Normalized
┌──────────────▼──────────────────────────────┴───────────────┐
│               Celery Worker (Sync Subprocesses)             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Application Layer (Use Cases, Normalization, Events)  │  │
│  └───────────────────────────┬───────────────────────────┘  │
│  ┌───────────────────────────▼───────────────────────────┐  │
│  │ Domain Layer (Entities, Value Objects, Ports, Errors) │  │
│  └───────────────────────────┬───────────────────────────┘  │
│  ┌───────────────────────────▼───────────────────────────┐  │
│  │ Infrastructure / Adapters (Sherlock, Maigret, etc.)    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Architectural Invariants
1. **Sync Workers vs. Async API**:
   - OSINT engines (Sherlock, Maigret, theHarvester, SpiderFoot, Recon-ng, Photon) are blocking, subprocess-heavy tools.
   - Celery workers run synchronously to supervise subprocesses without thread contention or async wrapper pitfalls.
   - FastAPI handles HTTP requests and reads Redis Pub/Sub asynchronously to push Server-Sent Events (SSE) to the browser.
2. **Strict Layer Decoupling**:
   - `UI` communicates only via HTTP REST and SSE.
   - `FastAPI` validates inputs and delegates directly to application services or dispatches tasks.
   - `Application` coordinates adapters, maps events, computes relationships, and orchestrates domain aggregates.
   - `Domain` is completely pure: zero knowledge of databases, SQL, Redis, Celery, or external engines.
   - `Infrastructure` implements database repositories, Redis streaming, logging, and external service clients.
   - `Adapters` wrap specific engines and implement domain ports.

---

## 4. Adapter Contract & Non-Negotiables

All OSINT engines must be wrapped in an adapter located in `src/adapters/<engine>/` conforming to `domain/ports/adapter.py`:

```python
class OsintAdapter(Protocol):
    name: str                    # e.g., "sherlock"
    version: str                 # Adapter version
    supported_targets: tuple[TargetKind, ...]

    def run(
        self,
        input: AdapterInput,
        cancel: asyncio.Event,
    ) -> AsyncIterator[AdapterEvent]: ...
```

### Adapter Rules
- **Isolation**: Adapters never import from `app/domain` or `app/application`. They communicate strictly via portable DTOs (`AdapterInput`, `AdapterEvent`).
- **No Database Access**: Adapters never touch SQLAlchemy, PostgreSQL, or Redis. They yield events; the application worker persists them.
- **No Inter-Adapter Coupling**: Adapters never invoke or depend on other adapters.
- **Subprocess Safety**: Pass arguments as lists: `subprocess.run(["sherlock", username], ...)`. **NEVER use `shell=True` or string interpolation.**
- **Standard Event Stream**: Adapters yield only:
  - `ProgressEvent(step: str, pct: float | None)`
  - `EntityEvent(entity: EntityDraft, evidence: EvidenceDraft)`
  - `RelationshipEvent(relationship: RelationshipDraft, evidence: EvidenceDraft)`
  - `LogEvent(level: "debug" | "info" | "warn", message: str)`
  - `ErrorEvent(error: AdapterError)`

---

## 5. Domain Model & Lifecycle

### Conventions
- Domain entities are `@dataclass(frozen=True, slots=True)`.
- Value objects enforce invariant validation in `__post_init__`.
- IDs are `uuid.UUID`. Timestamps are timezone-aware UTC `datetime`.
- Enums are `enum.StrEnum`.

### Investigation Lifecycle
```text
PENDING  ──► RUNNING ──► WORKING ──► REVIEW ──► FINAL
   │             │           │
   │             ▼           ▼
   └───────► CANCELLED     ERROR
```
- `PENDING`: Created via API, queued in Redis.
- `RUNNING`: Picked up by Celery worker.
- `WORKING`: Adapters actively executing, streaming progress and draft entities.
- `REVIEW`: Adapters complete; normalized entities and relationships ready for user analysis.
- `FINAL`: Investigation marked complete, closed, or exported.
- `CANCELLED`: Aborted by user or exceeded timeout.
- `ERROR`: Fatal engine failure or unrecoverable error.

---

## 6. Security & Operational Rules

1. **Localhost First**: Binds strictly to `127.0.0.1:8000` (FastAPI) and `127.0.0.1` (Postgres, Redis). No public exposure without reverse proxy (TLS + HTTP Basic Auth + IP restriction).
2. **Target Input Validation**: Validate strictly via `Target` value object before reaching Celery or adapters:
   - Username: `^[a-zA-Z0-9._-]{1,64}$`
   - Email: RFC 5322 subset (max 254 chars)
   - Domain: IDNA-normalized (max 253 chars)
   - URL: `http`/`https` only via `urllib.parse`
   - IP: Standard `ipaddress` validation
3. **SSRF Guard**: Refuse private/loopback IP ranges (`127/8`, `10/8`, `172.16/12`, `192.168/16`, `169.254/16`, `::1`, `fc00::/7`) unless `ALLOW_PRIVATE_TARGETS=true`.
4. **Injection Testing**: Every adapter must include an automated test ensuring malicious input (e.g. `"; rm -rf /"`) is treated as literal argument.
5. **Execution Guardrails**:
   - `ADAPTER_TIMEOUT_MS = 30000` (30s default timeout per adapter).
   - `MAX_RESULTS_PER_ADAPTER = 500` (truncate and flag as partial beyond this).
   - Celery `soft_time_limit = 300` seconds per task.
   - Global semaphore (2 concurrent runs per engine) to prevent hammering targets.
6. **Data Privacy**: Raw response blobs are opt-in (`settings.store_raw = false` by default). Export directory `data/exports/` is ephemeral.
7. **Ethical First-Run Notice**: Present an ethical & legal usage notice on first launch requiring user confirmation.

---

## 7. UX & Frontend Directives

- **Progressive Disclosure**:
  - Default view: clean input (`Target`, `Investigation Type`, `[Start Investigation]`).
  - Advanced view (collapsible): engine selection, rate limits, concurrency, depth, timeout.
- **Stage Progression UI**:
  - Never display raw terminal dumps as the primary progress interface.
  - Display checklist stages: `Target validated` → `Username discovery` → `Profile analysis` → `Relationship analysis` → `Ready for review`.
- **Layered Results Navigation**:
  - **Overview**: High-level metrics (entities discovered, sources queried, high-confidence associations).
  - **Entities**: Cards and structured tables organized by category (Profiles, Emails, Domains, IPs, URLs).
  - **Evidence**: Detailed provenance modal/drawer showing tool, source, timestamp, raw observation, and confidence.
  - **Relationships**: Graph visualization via React Flow with search, zoom, filter, and readable relationship predicates.
  - **Reports**: Markdown / JSON / PDF export capability.

---

## 8. Definition of Done

A task, feature, or adapter is only complete when:
```text
Backend Code
  +
Automated Tests (Pytest / Vitest)
  +
Error Handling & Timeout Resilience
  +
FastAPI Endpoints & Schemas
  +
Frontend UI & State Integration
  +
Documentation / OpenAPI Specs
```
are coherent, operational, and verified.