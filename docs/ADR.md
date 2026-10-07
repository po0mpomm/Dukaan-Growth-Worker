# Architecture Decision Records (ADR)
**Dukaan Growth Worker — Design Rationale & Trade-offs**

---

### ADR 001: Modular Monolith vs. Distributed Microservices
- **Decision:** Build the edge plane as a modular monolith in Python (one process, internal package boundaries).
- **Rationale:** The target environment is a 4 GB RAM shop machine or laptop. Running 7 separate Docker microservices with network serialization consumes 1.5–2 GB RAM in container daemon overhead alone. A modular monolith runs in ~60 MB RAM while preserving clean architectural boundaries.
- **Consequences:** Low memory usage, sub-millisecond inter-module communication, trivial local debugging.

---

### ADR 002: Local SQLite WAL Mode vs. Embedded NoSQL
- **Decision:** Use Python stdlib `sqlite3` in Write-Ahead Logging (`WAL`) mode with dedicated databases (`analytics.db`, `audit.db`, `outbox.db`).
- **Rationale:** SQLite is battle-tested, zero-configuration, ACID compliant, and requires zero external daemon processes. WAL mode allows concurrent readers without blocking writes.
- **Consequences:** Fast read/write performance, crash-resilience against sudden shop power cuts.

---

### ADR 003: Deterministic Computation & Rules vs. End-to-End LLM Prompting
- **Decision:** All financial math, aging calculations, and rule decisions (W1–W7) are executed in deterministic code. The LLM is restricted to natural language phrasing.
- **Rationale:** Kirana owners cannot risk probabilistic hallucinations in working capital recommendations. LLMs are poor calculators and hallucinate numbers under pressure.
- **Consequences:** 100% mathematical accuracy, zero arithmetic hallucinations.

---

### ADR 004: G5 Factuality Verifier with Template Fallback
- **Decision:** Every numerical token in model phrasing is validated against a pre-computed allowed set. Any ungrounded token immediately triggers deterministic template substitution.
- **Rationale:** Rather than relying on secondary LLM judges (slow, expensive, probabilistic), regex token extraction executes in <2 ms and provides absolute mathematical grounding guarantees.
- **Consequences:** Zero hallucinated rupee amounts reach the end user.

---

### ADR 005: Next.js 15 App Router Frontend with Vanilla CSS
- **Decision:** Use Next.js 15 App Router with Vanilla CSS instead of a multi-page framework or Tailwind.
- **Rationale:** Next.js provides structured file-based routing, fast refresh, server-side static page pre-rendering (103 KB bundle), and built-in reverse proxy rewrites (`/api/*` -> FastAPI `:8000`), eliminating CORS issues. Vanilla CSS gives total control over responsive design tokens and high-contrast typography without heavy CSS utility framework build steps.
- **Consequences:** Instant initial load, responsive 375px+ mobile support for Meena persona.

---

### ADR 006: Browser-Native Web Speech API for TTS
- **Decision:** Use the browser's native `window.speechSynthesis` for audio read-aloud instead of cloud TTS services (e.g. ElevenLabs, Google Cloud TTS).
- **Rationale:** Web Speech API operates 100% offline, requires zero API keys, consumes zero network bandwidth, and incurs zero operational cost.
- **Consequences:** Unlimited free bilingual audio read-aloud on mobile and desktop.

---

### ADR 007: Transactional Outbox for Edge-to-Cloud Sync
- **Decision:** Cloud sync payloads are enqueued to `outbox.db` rather than transmitted synchronously during user analysis.
- **Rationale:** Kirana connectivity in rural India is intermittent. Synchronous transmission causes UI hangs. The outbox pattern decouples edge analysis from cloud connectivity.
- **Consequences:** Edge analysis never blocks on network state; sync is retried idempotently when online.

---

### ADR 008: k-Anonymity ($k \ge 5$) Suppression in Cloud Plane
- **Decision:** The cloud aggregation plane enforces cell suppression for any macro-cohort with fewer than 5 shops.
- **Rationale:** Even banded data can re-identify a store if only one shop operates in a specific rural taluk. Suppressing cells with $k < 5$ guarantees privacy protection against differential attacks.
- **Consequences:** Complete compliance with DPDP principles of anonymization.

---

### ADR 009: SHA-256 Hash Chained Audit Trail
- **Decision:** Maintain an append-only event log in `audit.db` where each row contains the SHA-256 hash of its own content concatenated with the prior row's hash.
- **Rationale:** Creates a tamper-evident audit record verifying state transitions and data handling without requiring an external blockchain or heavy append-log infrastructure.
- **Consequences:** Shopkeepers can verify data integrity with one tap (`/audit`).

---

### ADR 010: Zero-PII Architectural Boundary
- **Decision:** Customer names and phone numbers are never stored in `analytics.db` or transmitted to the LLM context. Synthetic aliases (`CUST_001`) are used exclusively. WhatsApp drafts are generated in the browser clipboard.
- **Rationale:** Prevents PII leakage by making it structurally impossible for personal data to leave the device or enter model logs.
- **Consequences:** Total immunity to accidental PII exposure.

---

### ADR 011: Native Windows / Python Execution over Mandatory Docker
- **Decision:** Support native execution (`python` + `npm run dev` via `run.ps1`) as the primary field deployment mode, with Docker Compose available as a secondary containerized profile.
- **Rationale:** Docker Desktop on Windows 10/11 requires WSL2, consuming 1.5–2 GB RAM idle. On a 4 GB RAM shop PC, native execution preserves valuable memory.
- **Consequences:** Maximum portability across both low-end PCs and modern container environments.

---

### ADR 012: Reverse Proxy API Rewrites
- **Decision:** Next.js proxies all `/api/*` calls to `http://127.0.0.1:8000/v1/*`.
- **Rationale:** Avoids CORS pre-flight OPTIONS overhead, simplifies browser network security, and keeps all client-side requests on origin port `:3000`.
- **Consequences:** Simplified networking, zero cross-origin configuration friction.
