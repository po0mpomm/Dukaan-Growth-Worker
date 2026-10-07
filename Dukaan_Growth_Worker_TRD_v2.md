# Dukaan Growth Worker: Technical Requirements Document (TRD) v2.0

**Author:** Anvaya Arsha | **Version:** 2.0 | **Date:** 7 Oct 2026 | **Companion:** PRD v2.0 | **Status:** Build-ready, reviewed

---

## 0. Changes from v1.0 (self-audit)

| # | Issue in v1.0 | Resolution |
| --- | --- | --- |
| 1 | Assumed Docker on a 4 GB shop laptop. Docker Desktop on Windows (WSL2 VM) alone can consume 1 to 2 GB | Docker is for demo, CI, Linux mini-PCs and the cloud plane. Low-end Windows uses a **Portable** native mode (ADR-007) |
| 2 | Per-service memory limits (64 MB gateway, 128 to 192 MB pandas services) were guesses; each Python process with pandas has a large fixed baseline | Limits are now hypotheses to measure (section 16). Default edge shape is one worker container; the `split` profile is the same image run with different entrypoints |
| 3 | k-suppression on the device is impossible (a device does not know other shops) | Banding on device, k-suppression in the cloud query layer (ADR-008) |
| 4 | Redis licence changed in 2024 and 2025 (source-available, then AGPL option); conflicts with open-source-first | **Valkey** (BSD, Redis-compatible) is the default; client code unchanged (ADR-002) |
| 5 | SQLCipher is painful to install on Windows and low-end devices | Field-level AES-256-GCM for the small PII vault using the `cryptography` package; SQLCipher optional (ADR-004) |
| 6 | Everything in one 7-day phase (8 edge and 6 cloud services, Argo CD, Kyverno, cosign) | Tier A / B / C with an explicit cut line (section 21) |
| 7 | PIN-derived keys on a shared family laptop were overstated as protection | Honest threat model: OS disk encryption is the real control; premium hardware-backed keys (section 11) |
| 8 | No schemas, DDL or algorithms, so not implementable without guessing | Added contracts, DDL, hash chain, verification algorithm, FIFO aging (sections 6, 7, 10) |

---

## 1. Purpose and scope

How the Dukaan Growth Worker is built, deployed, secured, observed and operated. It implements the PRD without weakening its promises: **offline-first, privacy by architecture, deterministic numbers, optional small model, escalate over guess.**

In scope: architecture, service contracts, data stores, guardrails, security, containers, Kubernetes, Valkey, CI/CD, testing, observability, reliability, cost. Out of scope: visual design and business rules (PRD).

## 2. Architecture decisions

### 2.1 Two planes

| | **Edge plane (shop device)** | **Control plane (Eko cloud)** |
| --- | --- | --- |
| Purpose | Run the worker, hold all PII, work offline | Receive consented aggregates, distribute signed rule packs, run evaluations, show mission control |
| Runtime | Native Portable, or Docker Compose profiles | Kubernetes (Helm) |
| State | SQLite (WAL) plus transactional outbox | PostgreSQL plus Valkey (streams, locks, rate limits, cache) |
| May hold | Everything, encrypted at rest | Banded aggregates only |
| Network | Zero calls in the analysis path | Public ingress, mTLS from devices |

### 2.2 When is something a real microservice?

A boundary becomes a separate deployable only when it has a **different failure domain, runtime, scaling profile, or trust level**. Applied honestly:

| Boundary | Separate container? | Reason |
| --- | --- | --- |
| llm-svc | **Yes** | Different runtime (llama.cpp/Ollama), 1 GB+ memory, crashes and stalls independently, optional |
| Cloud: aggregate-ingest, config-dist, mission-control | **Yes** | Different scaling, different trust level, different release cadence (rule packs are highest risk) |
| Edge: gateway, orchestrator, ingest, analytics, guardrails, privacy, audit | **Modules by default**, containers in `split` profile | They share one device and one failure domain; separate processes add RAM and latency with little benefit on a 4 GB machine |

**Same image, three shapes.** One edge image contains all modules behind ports (interfaces). The environment variable `SERVICES` selects which modules a container runs:

- `SERVICES=all` is the modular monolith (Portable, `core`, `full`).
- `SERVICES=analytics` (and so on) runs one module as its own service behind HTTP (the `split` profile).

The service boundaries, contracts and tests are real in every shape. The `split` profile demonstrates the microservice architecture to reviewers without forcing its cost on a shop device.

### 2.3 ADRs

| ADR | Decision | Rationale and trade-off |
| --- | --- | --- |
| 001 | Modular monolith by default, `split` profile for microservices | Fits 4 GB; boundaries preserved; costs a thin adapter layer |
| 002 | **Valkey**, cloud plane only | Open licence; Redis protocol compatible; edge uses SQLite because an offline 4 GB device cannot afford it |
| 003 | REST + JSON internally, not gRPC | Low call volume; no extra tooling or CPU |
| 004 | Field-level AES-256-GCM vault (`cryptography`); SQLCipher optional | Easy install on Windows and ARM; vault is small |
| 005 | Ed25519-signed rule packs | Edge keeps the last good pack; tampering detected |
| 006 | LangGraph with SQLite checkpointer behind a `WorkflowEngine` port | Plain-Python implementation swappable if LangGraph is too heavy on a device |
| 007 | **Portable native mode** for low-end Windows (PyInstaller or embedded Python zip) | Avoids Docker Desktop overhead on 4 GB machines |
| 008 | Banding on device, k-suppression in cloud views | A device cannot know a segment's population |
| 009 | Transactional outbox for edge to cloud | Offline-safe, exactly-once effect via idempotency keys |
| 010 | Rules, templates, policies as signed data packs | Change behaviour without code release; auditable |

## 3. System overview

```
[Owner/Field agent browser: phone or laptop]
      | HTTPS on LAN (self-signed), PIN login
+-----v------------------ EDGE (Portable | Compose) ------------------+
| gateway --> orchestrator (LangGraph state machine)                   |
|              |--> ingest      parse, validate, completeness          |
|              |--> analytics   metrics, rules, scoring, MoM           |
|              |--> guardrails  G1..G9 policy engine                   |
|              |--> llm-svc     local model, optional (own container)  |
|              |--> privacy     vault, allow-list, banding, outbox     |
|              |--> audit       hash-chained log                       |
| SQLite: runs, snapshots, activity, audit, outbox, vault(encrypted)   |
+-----|---------------------------------------------------------------+
      | consented banded payload (mTLS, via outbox, when online)
+-----v------------------- CONTROL PLANE (Kubernetes) ----------------+
| edge-gateway --> aggregate-ingest --> PostgreSQL                     |
| config-dist (signed packs)   mission-control-api (k>=5)              |
| device-registry   eval-runner (CronJob)   Valkey   Observability     |
+----------------------------------------------------------------------+
```

## 4. Edge module catalog

Each module: one responsibility, a port (interface), its own contract tests, no shared tables.

| Module | Responsibility | Tech | Owns |
| --- | --- | --- | --- |
| gateway | Bilingual UI (static PWA), PIN auth, roles, rate limit, request and correlation IDs | FastAPI, uvicorn | sessions |
| orchestrator | State machine, checkpoints, retries, timeouts, circuit breaker | LangGraph, SQLite saver | `runs.db` |
| ingest | CSV/XLSX parsing, schema validation, completeness, formula-injection neutralising | pandas, pydantic, openpyxl | stateless |
| analytics | Metrics, FIFO aging, weak-area rules, scoring, MoM | pandas | `analytics.db` |
| guardrails | Declarative policy engine for G1 to G9 | pydantic, YAML packs | policy cache |
| llm-svc | Local model wrapper, JSON-constrained generation, timeouts | llama.cpp server or Ollama | model files (read-only) |
| privacy | PII vault, alias map, allow-list export, banding, consent, outbox sender | cryptography | `vault.db`, `outbox.db` |
| audit | Hash-chained append-only log, verify endpoint | SQLite, SHA-256 | `audit.db` |

## 5. Control plane service catalog

| Service | Responsibility | Tier |
| --- | --- | --- |
| edge-gateway | Public ingress for devices: mTLS, rate limits, schema pre-check | B |
| aggregate-ingest | Validate payload against allow-list schema, reject unknown keys, idempotency, write to Postgres | B |
| config-dist | Serve signed rule/policy/template packs, versions, rollback | B |
| mission-control-api | Read-only aggregate views with **k at least 5 suppression** | B |
| device-registry | Enrol devices, rotate pseudonymous IDs, certificate issue and revoke | C (stub in B) |
| eval-runner | Run the harness on candidate packs/models; block regressions | B via GitHub Actions, C as CronJob |
| Valkey | Idempotency keys, rate limits, streams, cache, locks | B |
| PostgreSQL | Aggregates, device registry, pack metadata | B |

For Tier B the first three plus Postgres and Valkey are enough to demonstrate the full path. In a minimal Tier B they may be run as one `cloud-api` container, then split for Kubernetes.

## 6. Contracts

### 6.1 Edge public API (gateway)

| Method and path | Purpose |
| --- | --- |
| `POST /v1/runs` (multipart: sales, expenses, udhaar, month, language) | Create run; returns `202 {run_id}` |
| `GET /v1/runs/{id}` | State, progress, escalation reason if any |
| `GET /v1/runs/{id}/result` | Verified result object (6.3) |
| `POST /v1/runs/{id}/actions/{n}/done` | Mark action done |
| `POST /v1/runs/{id}/export/preview` | Exact payload and its hash |
| `POST /v1/runs/{id}/export/consent` | Body: payload hash, notice version; creates outbox row |
| `DELETE /v1/data` | Wipe local stores, queue cloud deletion marker |
| `GET /v1/audit/verify` | Chain verification result |
| `GET /healthz`, `GET /readyz` | Liveness and readiness |

Every internal call carries `X-Run-Id`, `X-Correlation-Id`, `X-Schema-Version`, `X-Deadline` (ms epoch). State-changing calls accept `Idempotency-Key`. Errors use RFC 7807 problem JSON with a stable `reason_code`.

### 6.2 Findings object (the only thing the model sees)

```json
{
  "schema": "findings/1.0",
  "language": "hi",
  "month": "2026-09",
  "verdict": "money_stuck",
  "weak_areas": [
    {"rule": "W1", "metrics": {"udhaar_outstanding": 38400, "credit_share_pct": 27, "overdue_customers": 5}},
    {"rule": "W3", "metrics": {"weekday": "Wed", "gap_pct": 45}}
  ],
  "followups": [{"alias": "C014", "reason_code": "LARGE_OVERDUE", "days_overdue": 45}],
  "comparison": {"sales_change_pct": -4}
}
```

### 6.3 Model output (strict JSON Schema, exactly 3 actions)

```json
{
  "actions": [
    {"title": "string<=60", "why": "string<=160", "first_step": "string<=120", "language": "hi|en"}
  ]
}
```
`minItems = maxItems = 3`. Invalid output gets one retry, then templates.

### 6.4 Aggregate export payload (allow-list; additional properties forbidden)

```json
{
  "schema": "aggregate/1.0",
  "shop_pid": "9f3c...",
  "month": "2026-09",
  "region_type": "semi_urban",
  "sales_change_band": "-5..+5",
  "credit_share_band": "20-35",
  "overdue_band": "10-25",
  "rules_fired": ["W1", "W3"],
  "completeness_band": "0.8-1.0",
  "action_completion_band": "33-66"
}
```
Bands are fixed enums defined in the rule pack. The cloud JSON Schema uses `additionalProperties: false`, and no field accepts free text.

### 6.5 Cloud API

| Method and path | Purpose |
| --- | --- |
| `POST /v1/aggregates` (mTLS, `Idempotency-Key`) | `202` accepted; `409` replay returns stored result; `422` reject with reason |
| `GET /v1/config/rulepack/latest` | Pack plus detached Ed25519 signature |
| `GET /v1/mc/summary?region=&month=` | Banded counts; any cell under 5 shops returned as `suppressed` |

## 7. Data architecture

### 7.1 Edge SQLite (WAL, `synchronous=NORMAL`, one file per owning module)

```sql
-- analytics.db
CREATE TABLE snapshots(
  month TEXT PRIMARY KEY, total_sales REAL, stock_cost_ratio REAL, credit_share REAL,
  overdue_amount REAL, rules_fired TEXT, actions_json TEXT, actions_done INTEGER, completeness REAL);
CREATE TABLE customer_activity(            -- local only, aliases only, never exported
  alias TEXT PRIMARY KEY, last_purchase DATE, purchases_60d INTEGER, value_90d REAL);

-- audit.db
CREATE TABLE audit(
  seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE, ts TEXT, run_id TEXT,
  kind TEXT, detail TEXT, prev_hash TEXT, hash TEXT);

-- outbox.db
CREATE TABLE outbox(
  id TEXT PRIMARY KEY, payload TEXT, payload_hash TEXT, consent_ts TEXT, notice_version TEXT,
  status TEXT CHECK(status IN ('queued','sent','rejected')), attempts INTEGER, next_try TEXT);

-- vault.db  (values AES-256-GCM encrypted per field; nonce stored with ciphertext)
CREATE TABLE vault(alias TEXT PRIMARY KEY, name_enc BLOB, phone_enc BLOB);
```

**Hash chain:** `hash_n = SHA256(hash_{n-1} || canonical_json(event))`. `event_id = run_id:node:attempt` makes writes idempotent, so a resume after a power cut never duplicates events. `GET /v1/audit/verify` recomputes the chain.

**Vault key:** Argon2id(PIN, device salt) wraps a random data key. PIN lockout with exponential backoff. See section 11 for honest limits.

### 7.2 Cloud PostgreSQL

```sql
CREATE TABLE devices(pid TEXT PRIMARY KEY, region_type TEXT NOT NULL, enrolled_at TIMESTAMPTZ, revoked BOOL DEFAULT false);
CREATE TABLE aggregates(
  pid TEXT REFERENCES devices, month DATE, sales_change_band TEXT, credit_share_band TEXT,
  overdue_band TEXT, rules_fired TEXT[], completeness_band TEXT, action_completion_band TEXT,
  received_at TIMESTAMPTZ DEFAULT now(), PRIMARY KEY(pid, month));
CREATE TABLE rule_packs(version TEXT PRIMARY KEY, sha256 TEXT, signature TEXT, status TEXT, created_at TIMESTAMPTZ);
-- k-suppressed view: no cell with fewer than 5 devices
CREATE VIEW mc_summary AS
SELECT d.region_type, a.month, a.credit_share_band, count(*) AS shops
FROM aggregates a JOIN devices d USING(pid)
GROUP BY 1,2,3 HAVING count(*) >= 5;
```
No column can hold a name, phone or row-level transaction. Primary key on `(pid, month)` gives natural idempotency.

### 7.3 Retention
Snapshots 13 months; audit 24 months; outbox deleted on delivery; one-tap owner deletion wipes edge stores and sends a deletion marker for the device's cloud rows.

## 8. Orchestration

| Node | Timeout | Retries | On failure |
| --- | --- | --- | --- |
| S0 receive | 5 s | 0 | S_ERROR |
| S1 ingest + validate (G1) | 10 s | 0 | Escalate (validation) or S_ERROR (fault) |
| S2 analytics | 10 s | 1 | S_ERROR, no partial output |
| S3 phrasing (G2 to G4) | 25 s | 1 | Templates; breaker count +1 |
| S4 checking (G5, G6) | 2 s | 0 | Templates |
| S5 review | n/a | n/a | n/a |
| S6 saving | 5 s | 2 | Keep in memory, warn |
| S7 sharing (G8) | 3 s | 0 | Skip or queue |

- Each node is idempotent and persists its output before the transition.
- Retries only for transient faults, with exponential backoff and jitter. Never for validation or policy failures.
- **Circuit breaker** on llm-svc: 3 consecutive failures open it for 10 minutes; templates used immediately; audit `MODEL_FALLBACK`.
- **Degradation order:** model off, then templates; analytics fault, then safe error; any guardrail uncertainty, then escalate.

## 9. Valkey design (control plane only)

| Use | Structure | Key | TTL / notes |
| --- | --- | --- | --- |
| Idempotency | `SET NX` | `idem:{pid}:{key}` | 72 h |
| Rate limit | Token bucket (Lua) | `rl:{pid}:{route}` | 1 min window |
| Ingest pipeline | Streams + consumer groups | `stream:agg`, `stream:dlq` | DLQ after 5 failed deliveries |
| Pack cache | String | `cfg:{pack}:{version}` | 5 min, stale-while-revalidate |
| Locks | `SET NX PX` + fencing token | `lock:{res}` | short, renewed |

Two logical instances: durable (AOF every second, `noeviction`) for streams, idempotency, locks; and cache (`allkeys-lru`). Clients use pools and timeouts. If Valkey is down, ingest **fails closed** with `Retry-After` (the edge outbox retries) and cache reads **fail open**. Postgres remains the source of truth, since idempotency is also enforced by its primary key.

## 10. Guardrails (defence in depth)

A first-class module with versioned, declarative policy packs. Every decision is logged with its rule ID. Policy files are data, tested by fixtures.

| Layer | Checks | On violation |
| --- | --- | --- |
| **G1 Input** | Extension and MIME allow-list, 10 MB and 100k-row caps, encoding, no macros, schema and type checks; cells beginning `= + - @` escaped with a leading apostrophe; category values mapped to a fixed enum (unknown becomes `other`) | Reject; reason code; escalate plainly |
| **G2 Data-to-prompt** | Only the findings object (6.2) reaches the model. Regex PII scan (10-digit phones, emails, ID-like strings) on the whole prompt | Block; audit `PII_BLOCKED` |
| **G3 Prompt injection** | Untrusted text never enters the instruction channel; no free text from files in prompts; model has no tools, network or filesystem; system prompt separate from data | Drop field; audit |
| **G4 Output structure** | JSON Schema (6.3), exactly 3 actions, length caps, language matches request | One retry, then templates |
| **G5 Factuality** | See algorithm below | Discard model text; templates |
| **G6 Content** | Banned topics (loans, interest, legal threats, shaming, medical, tax); coercion and public-naming patterns; reading-level cap; no alias outside the top-5 | Discard; templates; audit |
| **G7 Action** | No outbound messages or external calls from workflow nodes; drafts are text; owner sends. Hard-coded, not configurable | n/a |
| **G8 Export** | Allow-list keys only; fixed band enums; consent present, unexpired; payload hash equals previewed hash | Block; audit `EXPORT_BLOCKED` |
| **G9 Escalation** | Completeness below 0.6, any Block, reconciliation failure, out-of-scope, repeated G4/G5 failure | Stop; at most 2 questions |

**G5 algorithm.** (1) Normalise text: convert Devanagari digits to ASCII, strip currency symbols, remove thousands separators, handle lakh notation. (2) Extract every numeric token and percentage. (3) Each must match a value in the findings object within rounding tolerance (0.5 percent points or 0.5% relative for rupees). (4) Any unmatched number fails the check. Dates and the literal numbers 1, 2, 3 used as list markers are allow-listed. The cloud re-applies G8 (allow-list, schema) so a buggy or compromised edge cannot leak fields.

## 11. Security

| Threat (STRIDE) | Example | Mitigation |
| --- | --- | --- |
| Spoofing | Fake device posts aggregates | Device certificates, mTLS, revocation list; attestation is Tier C |
| Tampering | Edited audit log or rule pack | Hash chain (tamper-evident); Ed25519-signed packs verified before load |
| Repudiation | Disputed consent | Consent record: timestamp, payload hash, notice version |
| Information disclosure | PII in logs or export | Vault isolation, G2/G8, log-scrubbing tests, allow-list schema |
| Denial of service | Huge file or request flood | Caps, rate limits, deadlines, resource limits |
| Elevation | Container escape | Non-root, read-only FS, `cap_drop: ALL`, seccomp, network segmentation |

**Honest limits.** A short PIN gives limited protection against someone who copies the disk, because the salt lives on the same disk. On a shared family laptop the real controls are OS full-disk encryption and not storing names in the first place (the vault is optional; analysis works on aliases). Hardware-backed keys (TPM or Android Keystore) are a Tier C item. Self-signed LAN certificates protect against casual sniffing only.

**Controls.** PIN auth with Argon2id and lockout; roles (owner; field agent with read-only access and no PII); secrets from environment or secret store, never in images; pinned lockfiles; SBOM (Syft); image scan (Trivy); SAST (Semgrep OSS, Bandit); secret scan (gitleaks); keyless cosign signing in GitHub Actions; no telemetry or third-party SDKs on the edge; OWASP ASVS L2 as a target.

## 12. Containerisation

- Multi-stage builds on slim Python base images pinned by digest; target under 200 MB for the edge image (with pandas), model image excluded.
- Non-root fixed UID; `read_only: true`; `tmpfs` for `/tmp`; `cap_drop: [ALL]`; `no-new-privileges`.
- `HEALTHCHECK` (liveness and readiness) on every container; graceful `SIGTERM` with a 20 s drain; one process per container; JSON logs to stdout.
- Memory and CPU limits mandatory. Model files mounted read-only and checksum-verified at start.

```yaml
# deploy/compose/compose.yaml  (profiles: core, full, split, cloud)
x-hardened: &hardened
  read_only: true
  user: "10001:10001"
  cap_drop: [ALL]
  security_opt: ["no-new-privileges:true"]
  tmpfs: ["/tmp"]

services:
  worker:                       # modular monolith, SERVICES=all
    <<: *hardened
    image: ghcr.io/anvaya/dukaan-edge:${TAG}
    profiles: [core, full]
    environment: {SERVICES: all, LLM_URL: "http://llm:8081"}
    ports: ["8443:8443"]
    mem_limit: 700m
    volumes: [data:/data]
    networks: [internal, lan]
    healthcheck: {test: ["CMD","python","-m","app.health"], interval: 15s}

  llm:                          # genuinely separate: different runtime and failure domain
    profiles: [full]
    image: ghcr.io/ggml-org/llama.cpp:server
    command: ["-m","/models/model.q4.gguf","-c","2048","--threads","2"]
    mem_limit: 1400m
    volumes: ["models:/models:ro"]
    networks: [internal]

  # split profile: same image, one module per container
  gateway:      {<<: *hardened, profiles: [split], image: ghcr.io/anvaya/dukaan-edge:${TAG}, environment: {SERVICES: gateway}}
  orchestrator: {<<: *hardened, profiles: [split], image: ghcr.io/anvaya/dukaan-edge:${TAG}, environment: {SERVICES: orchestrator}}
  analytics:    {<<: *hardened, profiles: [split], image: ghcr.io/anvaya/dukaan-edge:${TAG}, environment: {SERVICES: analytics}}
  guardrails:   {<<: *hardened, profiles: [split], image: ghcr.io/anvaya/dukaan-edge:${TAG}, environment: {SERVICES: guardrails}}
  privacy:      {<<: *hardened, profiles: [split], image: ghcr.io/anvaya/dukaan-edge:${TAG}, environment: {SERVICES: privacy}}
  audit:        {<<: *hardened, profiles: [split], image: ghcr.io/anvaya/dukaan-edge:${TAG}, environment: {SERVICES: audit}}

  cloud-api:                    # Tier B
    <<: *hardened
    profiles: [cloud]
    image: ghcr.io/anvaya/dukaan-cloud:${TAG}
    depends_on: {db: {condition: service_healthy}, valkey: {condition: service_started}}
    networks: [cloudnet]
  db:
    profiles: [cloud]
    image: postgres:16-alpine
    environment: {POSTGRES_PASSWORD_FILE: /run/secrets/pg}
    healthcheck: {test: ["CMD-SHELL","pg_isready"], interval: 10s}
    networks: [cloudnet]
  valkey:
    profiles: [cloud]
    image: valkey/valkey:8-alpine
    command: ["valkey-server","--appendonly","yes","--appendfsync","everysec","--maxmemory-policy","noeviction"]
    networks: [cloudnet]

networks:
  internal: {internal: true}    # no route to the internet
  lan: {}
  cloudnet: {}
volumes: {data: {}, models: {}}
```
Only the privacy outbox sender may reach the cloud, through a dedicated egress network that stays disabled until the owner enables syncing.

## 13. Kubernetes (control plane)

**Demo (Tier B):** k3d or kind on a laptop, the same Helm chart as production.

- **Topology:** namespaces `dukaan-api`, `dukaan-data`, `dukaan-ops`. Production: managed Kubernetes in an Indian region (data residency), at least 3 nodes across 2 zones.
- **Workloads:** Deployments with 2+ replicas for edge-gateway, aggregate-ingest, config-dist, mission-control; CronJob for eval-runner; managed (or StatefulSet) Postgres and Valkey.
- **Resilience:** readiness and liveness probes, PodDisruptionBudgets, topology spread, HPA on CPU and stream lag, rolling updates with `maxUnavailable: 0`, automated rollback.
- **Security:** Pod Security Admission `restricted`; default-deny NetworkPolicies with explicit allows; least-privilege RBAC; External Secrets; Kyverno policies (signed images, no `latest`, limits required) in Tier C.
- **Ingress and TLS:** ingress-nginx with cert-manager; mTLS on device routes; request size limits.
- **Delivery:** Helm plus Kustomize overlays (dev, staging, prod); Argo CD GitOps in Tier C; canary for config-dist because rule packs are the riskiest release.

```yaml
# default-deny, then allow ingest -> postgres and valkey only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: default-deny, namespace: dukaan-data}
spec: {podSelector: {}, policyTypes: [Ingress, Egress]}
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: allow-ingest, namespace: dukaan-data}
spec:
  podSelector: {matchLabels: {app: postgres}}
  ingress:
    - from:
        - namespaceSelector: {matchLabels: {name: dukaan-api}}
          podSelector: {matchLabels: {app: aggregate-ingest}}
      ports: [{port: 5432}]
```

## 14. Observability

- **Tier A:** structured JSON logs and the audit log only; a local `/metrics` endpoint with counters (runs, escalations, fallbacks, guardrail blocks by layer, stage latency).
- **Tier B:** Prometheus and Grafana (self-hosted, one dashboard) for the cloud services.
- **Tier C:** OpenTelemetry traces, Loki, Alertmanager.
- **Edge to Eko:** health counters leave the device only inside the consented aggregate (never automatically).
- **SLOs (cloud):** ingest availability 99.5%; p95 ingest latency under 500 ms; DLQ non-empty for over 15 minutes alerts; pack distribution success above 99%.
- **Rule:** no PII or row-level data in any log, trace or metric label. Enforced by a log-scrubbing test and a metric-label cardinality check in CI.

## 15. Reliability and failure handling

| Failure | Behaviour |
| --- | --- |
| Power cut mid-run | Resume from checkpoint; no duplicate audit events |
| Model down, slow, or malformed | Retry once, breaker, templates, `MODEL_FALLBACK` |
| Model states a wrong number | G5 discards it; templates |
| Disk full | Warn, keep run in memory, block export, never corrupt SQLite |
| Corrupt or hostile input | G1 reject, escalate, nothing exported |
| Cloud unreachable | Outbox retains; backoff with jitter; analysis unaffected |
| Cloud rejects payload | 422 reason; outbox marks `rejected`; field agent flagged |
| Valkey down | Ingest fails closed (retry-after); cache fails open |
| Postgres failover | Ingest retried with idempotency keys; no duplicates |
| Bad rule pack | Signature or eval gate blocks; canary; one-command rollback; edge keeps last good pack |

**Backup and DR (cloud, Tier C):** Postgres PITR with daily snapshots, RPO 15 minutes, RTO 1 hour, quarterly restore drills. **Edge:** optional owner-initiated encrypted backup to USB; no cloud backup of PII.

## 16. Performance and capacity (hypotheses to measure, not claims)

| Target | Value | How verified |
| --- | --- | --- |
| Pipeline, 1,500 sales rows, 4 GB CPU | under 3 s | Benchmark in CI and on a throttled container |
| Model stage p95 (1B Q4) | under 25 s, else fallback | Harness latency column |
| Edge memory, `core` (monolith) | under 600 MB (expected 250 to 400) | `docker stats` after a run |
| Edge memory, `split` | about 0.8 to 1.2 GB (expected) | `docker stats`; if above, `split` is demo-only |
| Edge memory, `full` with 1B model | under 2.2 GB | `docker stats` |
| Cloud ingest | 50 req/s per replica | k6 |
| Fleet assumption | 10,000 shops, one export per month; burst at month start, buffered by Valkey Streams | k6 burst test at 10x |

Record measured values in `docs/perf.md`. Any figure in this table that is not measured is labelled "unmeasured" in the README.

## 17. Testing strategy

- **Unit and property tests (Hypothesis):** totals reconcile; scores bounded 0 to 100; ordering stable; FIFO aging conserves balances.
- **Contract tests:** Schemathesis against OpenAPI for each service pair.
- **Evaluation harness (PRD 16):** 12 regression datasets, 60 noisy variants, 10 blind datasets. CI fails if any broken dataset is analysed, any unverified number reaches output, or rule-correctness falls below target. Each run appends to `eval/history.csv`.
- **Guardrail tests:** formula injection, oversized file, bad encoding, injection strings in category fields, planted PII, export with extra keys, tampered rule pack.
- **Privacy tests:** scan logs, outbox, traces and exports for planted PII tokens; zero allowed.
- **Chaos tests (scripts):** kill the model container mid-run, corrupt the SQLite WAL, throttle to 1 CPU, simulate a power cut, drop the cloud connection.
- **Load tests (Tier B):** k6 at 10x burst against cloud-api.
- **Security scans:** Semgrep, Bandit, `pip-audit`, Trivy, gitleaks in CI.

## 18. CI/CD (GitHub Actions, free for public repos)

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install -r requirements.lock
      - run: ruff check . && mypy services packages
      - run: pytest -q --cov=services --cov-fail-under=80
      - run: python -m eval.runner --gate          # fails on regressions
      - run: python -m tests.privacy_scan
  build-scan-sign:
    needs: test
    runs-on: ubuntu-latest
    permissions: {contents: read, packages: write, id-token: write}
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t ghcr.io/${{ github.repository }}/edge:${{ github.sha }} -f deploy/edge.Dockerfile .
      - run: trivy image --severity HIGH,CRITICAL --exit-code 1 ghcr.io/${{ github.repository }}/edge:${{ github.sha }}
      # push to GHCR and cosign keyless signing follow
```
Tier C adds staging deploy through Argo CD, smoke and load tests, a manual production gate and canary. Edge releases are versioned bundles (image plus signed pack), delivered by the field agent or when online; devices never update mid-month.

## 19. Repository layout

```
/services/edge/{gateway,orchestrator,ingest,analytics,guardrails,llm,privacy,audit}
/services/cloud/{aggregate-ingest,config-dist,mission-control,edge-gateway}
/packages/{contracts,rules,policies,templates,common}
/deploy/{compose,helm,portable}
/eval/{datasets,blind,expected,runner,history.csv}
/tools/{synthetic-data,fleet-sim,chaos,loadtest}
/docs/{prd,trd,adr,runbooks,dpdp-note,perf.md}
/tests
```

## 20. Technology summary (all open source)

| Concern | Choice |
| --- | --- |
| Language | Python 3.11, lockfiles |
| API | FastAPI, pydantic v2, uvicorn |
| Orchestration | LangGraph, SQLite checkpointer (behind a port) |
| Data | pandas, SQLite WAL, PostgreSQL 16 (cloud) |
| Crypto | `cryptography` (AES-GCM, Ed25519), Argon2id |
| Model runtime | llama.cpp server or Ollama; 1B to 3B 4-bit model chosen by the harness |
| Messaging and cache | Valkey (Streams, Lua) |
| Containers | Docker, BuildKit, Compose profiles |
| Cloud orchestration | k3d/kind then managed Kubernetes; Helm, Kustomize |
| Supply chain | Trivy, Syft, cosign, Semgrep, gitleaks |
| Observability | Prometheus, Grafana (Tier B); OpenTelemetry, Loki (Tier C) |
| Testing | pytest, Hypothesis, Schemathesis, k6 |

## 21. Build tiers and cut line

| Tier | Scope | Cost |
| --- | --- | --- |
| **A (Days 1 to 7)** | Edge worker (modules + `llm` container); Portable run script; Compose `core`, `full`, `split`; G1 to G9; harness (regression, noisy, blind); privacy and chaos tests; failure demos; CI | Rs 0 |
| **B (Days 8 to 10, only if A is demo-ready)** | Compose `cloud`; fleet simulator (40 shops); k-suppressed mission-control view; signed rule pack; Helm chart on k3d; Grafana dashboard | Rs 0 |
| **C (after joining, paid)** | Managed Kubernetes in India, device enrolment and attestation, hardware-backed keys, full observability, Argo CD canaries, backups and DR, pen-test, compliance review | See PRD section 20 |

**Rule:** if Tier A slips by more than a day, drop `split` polish and the Hindi read-aloud before touching the harness, the failure demo or the privacy tests. Those are what Eko evaluates.

## 22. Risks, decisions, open questions

| Item | Note |
| --- | --- |
| Microservice overhead on 4 GB | ADR-001, ADR-007; measure and publish numbers |
| Small-model Hindi quality | Templates default; harness decides; model never required |
| Cloud cost | Tier A and B cost nothing; Tier C is mostly managed Kubernetes and Postgres |
| DPDP interpretation | Notice, consent, roles and residency reviewed by Eko compliance |
| Free-tier terms change | Demo uses local containers, not free-tier SaaS; verify any hosted free tier before depending on it |
| Open: attestation on Android and low-end laptops | Decide in Tier C with field constraints |
| Open: managed versus self-hosted Postgres/Valkey for Eko | Affects Tier C cost and operations |
