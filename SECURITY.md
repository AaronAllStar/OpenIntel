# OpenIntel Security Policy & Threat Model

OpenIntel is engineered with a defense-in-depth posture suitable for sensitive cyber-defense and intelligence investigations.

---

## 1. Security Architecture & Threat Model

### 1.1 Network Boundary & Localhost Isolation
- By default, OpenIntel binds strictly to `127.0.0.1` (FastAPI) and loopback interfaces for Postgres and Redis.
- Direct public network binding without a reverse proxy (providing TLS termination, IP whitelisting, and mutual authentication) is strictly discouraged.

### 1.2 SSRF (Server-Side Request Forgery) Defenses
- Target validation in `src/app/domain/value_objects.py` actively parses and blocks:
  - **Cloud Metadata Services**: `169.254.169.254` (AWS, GCP, Azure), `100.100.100.200` (Alibaba Cloud), and `metadata.google.internal`.
  - **Private Address Spaces**: RFC 1918 ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), carrier-grade NAT (`100.64.0.0/10`), link-local (`169.254.0.0/16`, `fe80::/10`).
  - **Loopback and Unspecified**: `127.0.0.0/8`, `0.0.0.0`, `::1`, and IPv4-mapped IPv6 (`::ffff:127.0.0.1`).
  - **Internal TLDs**: `.local`, `.localhost`, `.internal`, `.lan`, `.home`, `.corp`, `.arpa`.
- Override: Scanning internal targets requires explicitly setting `allow_private_targets: true` within investigation settings.

### 1.3 Command Injection Immunity
- Subprocess adapters in `src/adapters/` invoke `asyncio.create_subprocess_exec()` with explicit positional argument lists.
- Shell evaluation (`shell=True`) is strictly prohibited across the entire codebase.
- The `Target` value object enforces rejection of shell control and metacharacters (`[\x00\r\n;|<>&`$]`).

### 1.4 Rate Limiting & DoS Protection
- Sliding-window rate limiters protect resource-intensive endpoints:
  - Investigation Creation: 10 requests / 60 seconds per IP.
  - Report Exports: 30 requests / 60 seconds per IP.
- Rate limit headers (`Retry-After`, `X-RateLimit-*`) inform well-behaved clients of capacity constraints.

### 1.5 Authentication & Access Control (RBAC)
- Role-based access control with two primary tiers:
  - `admin`: Full configuration access, worker management, and viewing the immutable audit trail (`/api/v1/audit`).
  - `analyst`: Creating and executing investigations, viewing graph models, and exporting intelligence reports.
- Authentication mechanisms supported:
  - HMAC-SHA256 JWT Bearer Tokens (`Authorization: Bearer <token>`).
  - Cryptographic API Keys (`X-API-Key: <key>`).

### 1.6 Immutable Audit Trail
- All security-relevant actions (`INVESTIGATION_CREATE`, `INVESTIGATION_CANCEL`, `INVESTIGATION_EXPORT`) are recorded in the relational database with UTC timestamps, user identity, source IP address, and target parameters.

### 1.7 Container Hardening
- Runtime container executes under an unprivileged user `openintel` (UID 10001).
- `no-new-privileges:true` is enforced in Docker Compose to prevent privilege escalation.

---

## 2. Reporting a Vulnerability

If you discover a potential security vulnerability in OpenIntel, please report it privately:

- **Email**: `security@openintel.internal` or open a private GitHub Security Advisory.
- **Response SLA**: Initial triage within 24 hours; patch or mitigation roadmap within 72 hours.
- Please include reproduction steps, Proof of Concept (PoC) scripts, and environment details.
- We request that you observe coordinated vulnerability disclosure and refrain from publishing details until a patch has been made available.
