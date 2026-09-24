# OpenIntel — Testing

## Philosophy
Tests exist to let you change the code without fear.
For a personal project, that means: fast unit tests for the parts that change often,
fewer integration tests for the parts that glue things together,
and a thin smoke test that proves the whole thing still boots.

Do not chase coverage percentages. Chase confidence per second of test runtime.

## Layers and what to test

| Layer | Test type | Speed | Mocking |
|---|---|---|---|
| Domain (entities, value objects) | Pure unit | ms | None |
| Application (use cases) | Unit with fake ports | ms | Fakes, not mocks |
| Adapters | Contract against fixtures | 10–100ms | No network |
| DB repositories | Integration with test Postgres | 100ms | Real DB |
| FastAPI routes | Integration via httpx | 50ms | Real app, test DB |
| Celery tasks | Unit with `task_always_eager=True` | ms | Fake ports |
| Frontend hooks | Vitest + Testing Library | ms | MSW |
| End-to-end | Playwright smoke | seconds | Real stack |

## Tools
- pytest, pytest-asyncio, pytest-cov
- `httpx.AsyncClient` with `ASGITransport` for FastAPI
- `testcontainers` or a plain `docker compose` test DB
- `factory-boy` or plain fixtures — plain fixtures are fine at this scale
- `responses` or `vcrpy` for HTTP-recorded adapter fixtures
- Vitest + `@testing-library/react` for frontend
- MSW for frontend network mocking
- Playwright for one end-to-end flow

## Running tests

```bash
make test            # everything
make test-unit       # domain + application only, fast
make test-adapters   # contract tests
make test-api        # FastAPI routes
make test-frontend   # vitest
make test-e2e        # playwright, needs full stack up