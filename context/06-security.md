# OpenIntel — Security

## Threat model (be honest)
This is a personal, self-hosted OSINT tool. The realistic threats are:

1. **The app running on a public VPS without auth** → someone finds it and abuses it as a proxy for OSINT.
2. **OSINT engines running with too many privileges** → a malicious or buggy engine touches the host.
3. **Logging targets and results to disk indefinitely** → evidence file leaks.
4. **An adapter shell-injection via target input** → `; rm -rf /` in a username field.
5. **A dependency supply-chain issue** in one of the six engines.

Not in scope: multi-tenant isolation, RBAC, SSO, enterprise audit. Do not pretend otherwise.

## Deployment posture

### Default: localhost only
- FastAPI binds `127.0.0.1:8000`, not `0.0.0.0`.
- Postgres and Redis bind `127.0.0.1` only.
- Docker Compose maps ports to `127.0.0.1:<port>:<port>`.

### If exposed to the internet
You MUST do all of these:
- Put it behind a reverse proxy (Caddy or Nginx) with HTTPS.
- Enable a single shared-password gate (HTTP Basic over HTTPS is acceptable for personal use).
- Restrict by IP allowlist at the proxy if you have a static IP.
- Bind Postgres and Redis to the Docker internal network only. Never expose 5432 or 6379.

If you skip any of these, do not expose the app. Localhost is the correct default.

## Input handling

### Target validation
- Every target passes through a `Target` value object that validates by kind.
- Username: `^[a-zA-Z0-9._-]{1,64}$`. No spaces, no shell metacharacters.
- Email: RFC 5322 subset, max 254 chars.
- Domain: IDNA-normalized, max 253 chars.
- URL: parsed with `urllib.parse`, scheme restricted to `http`/`https`.
- IP: validated via `ipaddress` stdlib.
- Invalid targets are rejected at the API boundary with `ValidationError`. Never reach a task.

### Shell injection
- Adapters MUST pass arguments as a list, never as a shell string.
  Correct: `subprocess.run(["sherlock", username], ...)`
  Forbidden: `subprocess.run(f"sherlock {username}", shell=True, ...)`
- If an engine requires a shell string, quote with `shlex.quote` and document why.
- This rule is enforced by a test: every adapter has a test that passes `"; rm -rf /"` as a target and asserts the process receives it as a literal argument.

### Path traversal
- Any file path derived from user input (reports, exports) resolves under a fixed base dir and is checked with `Path.resolve().is_relative_to(base)`.

### SSRF
- Adapters hitting URLs discovered during investigation must refuse private ranges (`127/8`, `10/8`, `172.16/12`, `192.168/16`, `169.254/16`, `::1`, `fc00::/7`) unless explicitly enabled in config.
- Default: refuse. `ALLOW_PRIVATE_TARGETS=false`.

## Secrets

- `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL` come from env vars, never committed.
- `.env` is in `.gitignore`. `.env.example` documents the required keys with dummy values.
- No secrets in logs. `structlog` processors redact keys named `password`, `token`, `secret`, `key`, `authorization`.
- No secrets in Celery task args. Tasks receive IDs, not credentials.

## Container isolation

- The worker runs in its own container, not in the API container.
- If the host supports it, run the worker with:
  - `--read-only` filesystem except a mounted `/tmp`
  - `--cap-drop=ALL`
  - `--security-opt=no-new-privileges`
  - A non-root user inside the image
- Engines that are pure Python (Photon) can run in-process. Engines that shell out (Sherlock, Maigret, theHarvester, Recon-ng, SpiderFoot) run as subprocesses inside the worker container.
- Set `ulimit` on the worker to bound runaway engines: `--ulimit nproc=64:64 --ulimit nofile=512:512`.

## Rate limiting and abuse

Even for personal use:
- A global semaphore per engine (e.g. `asyncio`/`threading.Semaphore(2)`) prevents six adapters from hammering the same site.
- Default `ADAPTER_TIMEOUT_MS=30000`. Any adapter exceeding it is killed.
- Default `MAX_RESULTS_PER_ADAPTER=500`. Beyond that, truncate and mark the investigation as `partial`.
- Celery `soft_time_limit=300` per task.

## Data handling

- Evidence raw blobs are opt-in per investigation (`settings.store_raw = false` by default). Without it, only normalized entities + source metadata are stored.
- Report exports are written under `data/exports/<investigation_id>/` and never committed.
- A single command `make clean-exports` deletes everything under `data/exports/`.
- Postgres volume is a Docker named volume, not a bind mount to the repo.
- Backups: `pg_dump` on demand. No automated backup in v1.

## Logging

- Never log full target payloads at `info` level. Only `target_kind` + a truncated hash.
- Debug logs may include target values, but `LOG_LEVEL=debug` is off by default and refuses to start if `ENV=prod`.
- Adapter raw stdout goes to `log` events at `debug` level only.

## Dependency hygiene

- `uv lock` committed.
- `pip-audit` runs in CI. A failing audit blocks merge.
- Frontend: `npm audit --production` in CI.
- Renovate or Dependabot enabled, with auto-merge only for patch versions of dev deps.
- No unpinned engines. Each adapter declares the minimum engine version it was tested against.

## Legal and ethical (this is OSINT — do not skip)

- OpenIntel is for investigating targets you have a lawful basis to investigate.
- Add a first-run acknowledgement screen that states:
  - You are responsible for how you use the results.
  - You will comply with the terms of service of every engine.
  - You will comply with applicable law (GDPR, CFAA, local equivalents).
- Do not add features that automate credentialed access, scraping behind logins, or bypassing rate limits of third-party services. If someone asks, the answer is no.
- The app records `created_by` and the target's `original` value so you can audit your own usage.

## Incident response (personal scale)

If you suspect compromise:
1. `docker compose down`.
2. Rotate `SECRET_KEY`.
3. `docker compose up` on localhost only.
4. Inspect `data/exports/` and Postgres for unexpected investigations.
5. `pip-audit` and `npm audit` to check for a known CVE.

## Checklist before exposing to the internet
- [ ] Reverse proxy with HTTPS
- [ ] Password gate enabled
- [ ] Postgres and Redis not exposed
- [ ] `ALLOW_PRIVATE_TARGETS=false`
- [ ] `LOG_LEVEL=info`
- [ ] `store_raw=false` by default
- [ ] `pip-audit` clean
- [ ] `npm audit --production` clean
- [ ] Worker running with dropped caps and non-root user