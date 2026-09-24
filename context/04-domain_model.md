# OpenIntel — Domain Model

## Purpose
Single source of truth for the objects every layer uses.
If a name or field is not here, it does not exist yet.

## Conventions
- Domain entities are Python `@dataclass(frozen=True, slots=True)` unless mutation is required.
- Value objects are frozen dataclasses with validation in `__post_init__`.
- IDs are `uuid.UUID`. Timestamps are timezone-aware `datetime` in UTC.
- Enums are `enum.StrEnum` so they serialize cleanly in FastAPI.

## Aggregates

### Investigation
Root aggregate. Owns everything produced by one run.

```python
@dataclass(slots=True)
class Investigation:
    id: UUID
    name: str
    target: Target
    type: InvestigationType
    status: InvestigationStatus
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    created_by: UserId
    settings: InvestigationSettings
```