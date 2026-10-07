# Dukaan Growth Worker: Product Requirements Document (PRD) v2.0

**Version:** 2.0 | **Date:** October 2026 | **Companion:** TRD v2.0 | **Status:** Production-ready  
**Context:** Local-First Agentic AI Worker for Micro-Retail & Kirana Operations

---

## 0. Document control

### 0.1 What changed from v1.0 and why (self-audit)

v1.0 was strong on concept but had defects that would have surfaced in the demo or in review. They are fixed here.

| # | Defect in v1.0 | Fix in v2.0 |
| --- | --- | --- |
| 1 | Failure demo contradicted itself ("12 of 30 days missing" but message said "18 days missing"; score 0.38 did not follow from the formula) | Worked example with real arithmetic (section 8.1, 17) |
| 2 | Udhaar aging impossible without opening balances; monthly files carry no history | Added `opening_balance` type and FIFO aging algorithm (8.2) |
| 3 | "Lapsed regulars" needs 60 days of per-customer history, but only aggregates were stored | Added local-only `customer_activity` table (13); flagged as an assumption since many kirana sales are anonymous (22) |
| 4 | "Margin" = sales minus stock purchases is not real margin (stock buying is lumpy) | Renamed "stock-cost ratio", with an explicit caveat (8.2, W4) |
| 5 | k-suppression was placed on the device, which cannot know other shops | Banding on device, k-suppression in the cloud query layer (12) |
| 6 | Aggregates called "non-identifying", but a stable pseudonymous shop ID makes them pseudonymous at best | Wording corrected; ID rotation; honest DPDP note (12) |
| 7 | "Accuracy 10/12" on datasets the author wrote is a regression test, not accuracy | Metrics reframed; added 60 seeded noisy variants and a held-out blind set (16) |
| 8 | No non-functional requirements, cost model, assumptions list, or acceptance tests | Added sections 14, 20, 22, 24 |
| 9 | v1.0 did not reflect the microservices, Docker, Redis, Kubernetes, guardrails direction | Deployment modes, control-plane requirements, and build tiers added (7, 19) |
| 10 | Version mismatch (TRD referenced PRD v1.1) | Both documents are now v2.0 |

### 0.2 Design principle in one line
**Code computes, rules decide, the small model only phrases, and the system refuses to guess.**

---

## 1. Executive summary

Dukaan Growth Worker is a **local-first, bounded AI Worker** that turns a kirana or small retail owner's monthly records (sales, expenses, udhaar/credit) into **up to three weak areas with evidence, three plain-language actions, and a ranked top-5 follow-up list**, in Hindi or English, on a low-end device, without needing the internet.

It owns one workflow end to end: **messy records in, validated insight and actions out, month-on-month progress tracked, only consented and banded aggregates shared with the platform control plane**. When data is weak it escalates instead of advising.

The LLM never calculates, never decides what is wrong, and is optional. If it fails, reviewed templates deliver the same verified facts.

## 2. Problem and context

Micro-entrepreneurs in Indian Tier 2 / Tier 3 markets often run on notebooks, WhatsApp and memory.

- Money is stuck in **udhaar** and nobody tracks who is overdue, or for how long.
- Owners feel sales are slow but cannot see which days, categories or customers changed.
- Costs creep up unnoticed.
- Existing tools are dashboards or English chatbots that assume good phones, stable internet and digital comfort.

Because the platform is tied to livelihood, a wrong or overconfident answer has real cost. The worker must be **conservative, explainable and honest about uncertainty**.

## 3. Goals and non-goals

### Goals
- G1: Monthly review in under 2 minutes of owner effort.
- G2: Reduce overdue credit and recover lapsed regulars through specific, doable follow-ups.
- G3: Make month-on-month progress visible.
- G4: Run offline on a 4 GB RAM, CPU-only machine (with a rules-only mode for weaker devices).
- G5: Privacy by architecture: PII cannot leave the device.
- G6: Prove reliability with an evaluation harness, not claims.

### Non-goals
- Not a chatbot, Q&A bot or prompt demo.
- Not a dashboard product, accounting tool or GST software.
- No lending, credit scoring of the owner, or financial/legal/tax advice.
- No automatic messages to customers. The owner always sends.
- No cloud dependency in the analysis path; the platform control plane never receives names or phone numbers.

## 4. Product definition

| Item | Definition |
| --- | --- |
| **Goal** | Increase recovered udhaar and repeat-customer sales for a micro-shop; make monthly growth visible and actionable. |
| **User** | Primary: kirana/small retail owner. Secondary: platform field agent sitting with the owner. Tertiary: platform mission control (consented aggregates only). |
| **System** | Sits inside the micro-entrepreneur growth loop: owner records, monthly review, follow-up actions, next-month comparison, optional consented aggregate to the platform control plane. |
| **Inputs** | Three CSV/XLSX files (sales, expenses, udhaar incl. opening balances), previous local snapshot, optional owner language/region settings. |
| **Outputs** | Health verdict, up to 3 weak areas with rupee evidence, 3 actions, top-5 follow-up list, MoM comparison, copyable reminder drafts, optional aggregate export. |
| **Decisions** | May recommend, rank, flag, and choose proceed / proceed-with-caveat / escalate. May not act on money or customers. |
| **Constraints** | Never invents numbers, never sends messages, never exports PII, never gives financial/legal advice, never proceeds silently on weak data. |
| **Device constraint** | Full mode: 4 GB RAM CPU-only laptop/mini-PC, optional 1B-class model. Lite mode: rules and templates only, UI viewed from a basic Android phone over local Wi-Fi. Small screens, power cuts, patchy connectivity, low digital comfort. |
| **Definition of Done** | Section 15. |
| **Privacy / DPDP** | Section 12. |
| **Escalation** | Section 9. |
| **Success metric** | Section 16. |

## 5. Personas (synthetic)

**Meena Devi, 41, kirana owner, semi-urban.** Basic Android phone; uses WhatsApp and voice notes; reads Hindi better than English; keeps a notebook and a rough Excel on a cousin's laptop. Wants: "who owes me, and what should I do this week?" Fears: a tool she cannot understand; losing customer trust by chasing the wrong person.

**Field agent.** Visits weekly, helps load records, explains output, observes failures. Needs a clear escalation reason, not a stack trace.

**Mission control.** Wants comparable, banded aggregates across many shops. Must never receive identifiable data.

## 6. Core user journeys

1. **Monthly review (happy path):** load files, validate, analyse, show 3 actions and top-5, owner marks actions, snapshot saved.
2. **Incomplete data (intentional failure):** worker detects gaps, refuses to analyse, asks at most 2 short questions, logs escalation, exports nothing.
3. **Follow-up:** owner opens the top-5, sees why each customer is ranked, copies a polite reminder, sends it herself.
4. **Next month:** worker compares with last month and reports improved and worsened areas, plus action completion.
5. **Optional sharing:** owner previews the exact payload, consents, and it syncs when online.
6. **Model failure:** model times out or misbehaves; owner sees a small "basic mode" note and the same verified facts.

## 7. Functional requirements

P0 = must ship in the prototype, P1 = should, P2 = next version.

### 7.1 Edge worker

| ID | Requirement | Pri |
| --- | --- | --- |
| FR-1 | Ingest sales, expenses, udhaar (CSV/XLSX) against a published schema; downloadable blank template (Hindi and English headers). | P0 |
| FR-2 | Validate input (8.1) and compute a completeness score. | P0 |
| FR-3 | Compute all metrics deterministically in code (8.2). | P0 |
| FR-4 | Detect weak areas with explicit, versioned rules (8.3). | P0 |
| FR-5 | Rank customers for follow-up with a transparent formula (8.4). | P0 |
| FR-6 | Generate exactly 3 actions: model phrasing if available, templates otherwise. | P0 |
| FR-7 | Confidence gate: proceed / proceed with caveat / escalate. | P0 |
| FR-8 | Escalation output: plain reason plus at most 2 questions. | P0 |
| FR-9 | Local monthly snapshot and MoM comparison. | P0 |
| FR-10 | Hindi and English output with a toggle; templates reviewed by a native speaker. | P0 |
| FR-11 | Append-only, hash-chained audit log of every state transition and guardrail decision. | P0 |
| FR-12 | Aggregate export with preview, consent, allow-list, banding; payload hash equals previewed hash. | P0 |
| FR-13 | Guardrail layers G1 to G9 (TRD 10), each independently testable. | P0 |
| FR-14 | Evaluation harness (16) runnable with one command and in CI. | P0 |
| FR-15 | Copyable reminder drafts, never auto-sent. | P1 |
| FR-16 | Action tracking: owner marks done; completion reported next month. | P1 |
| FR-17 | Read-aloud via device offline TTS where available. | P1 |
| FR-18 | Voice-note input via local speech-to-text. | P2 |
| FR-19 | Android-native offline app. | P2 |

### 7.2 Control plane (platform side)

| ID | Requirement | Pri |
| --- | --- | --- |
| CP-1 | Aggregate ingest API: schema-strict, rejects unknown keys, idempotent, re-checks the allow-list. | P0 (sim) |
| CP-2 | k-suppression (k at least 5) on every mission-control view. | P0 (sim) |
| CP-3 | Signed rule-pack distribution with versions and rollback. | P1 |
| CP-4 | Device enrolment with rotatable pseudonymous IDs. | P1 |
| CP-5 | Scheduled evaluation run that blocks promotion of a regressing rule pack or model. | P1 |
| CP-6 | Read-only mission-control API and a minimal view. | P1 |

"(sim)" = demonstrated against a simulated fleet of 40 synthetic shops.

### 7.3 Deployment modes

| Mode | Target | Shape |
| --- | --- | --- |
| **Portable** | 4 GB Windows laptop, no Docker | Single native process (zip/installer), optional local model binary |
| **Compose `core`** | Linux mini-PC, field-agent laptop, demo | One worker container, no model |
| **Compose `full`** | 8 GB machine, demo | `core` plus a separate model container |
| **Compose `split`** | Demonstrating the microservice architecture | Every module as its own container |
| **Compose `cloud`** | Demo of platform control plane | Cloud API, Postgres, Valkey |
| **Kubernetes** | Cloud plane (stretch for demo, required for production) | Helm on k3d/kind locally |

Rationale and numbers are in TRD section 2.

## 8. Data and logic specification

### 8.1 Input schema and validation

- **sales:** `date, category, quantity, amount, payment_mode (cash|upi|credit), customer_ref (optional alias, e.g. C014)`
- **expenses:** `date, category (stock_purchase|rent|electricity|transport|wages|other), amount`
- **udhaar:** `customer_ref, date, type (opening_balance|credit_given|payment_received), amount`
- **Local-only map:** `customer_ref` to name/phone, encrypted, never read by analysis, model, logs or export.

| Check | Rule | Severity |
| --- | --- | --- |
| Required columns and types | All present | Block |
| Day coverage | Days with any sales row divided by days in month. Below 70% blocks; 70 to 85% warns | Block / Warn |
| Dates | Inside the target month; no future dates | Warn |
| Amounts | Numeric, non-negative; outliers above 10x category median flagged | Warn |
| Duplicates | Identical date, category, amount flagged, never silently removed | Warn |
| Udhaar balance | Customer whose payments exceed credit plus opening balance | Warn |
| File integrity | Unreadable, empty, wrong encoding, over size cap | Block |

**Completeness score** = 0.5 x day coverage + 0.2 x expense coverage + 0.2 x udhaar integrity + 0.1 x (1 minus flagged-row ratio)

- *Expense coverage* = share of the 3 expected recurring categories (stock_purchase, rent, electricity) that have at least one entry.
- *Udhaar integrity* = 1 minus (customers with negative balance / customers with any udhaar activity).
- *Flagged-row ratio* = rows with any Warn flag / total rows.

**Gate:** any Block, or score below 0.6, means escalate. 0.6 to 0.8 means proceed with caveat. At least 0.8 means proceed.

**Worked failure example:** sales rows on 12 of 30 days (coverage 0.40, a Block), expense coverage 0.33, udhaar integrity 1.0, flagged ratio 0. Score = 0.20 + 0.066 + 0.20 + 0.10 = **0.57**. Escalate.

### 8.2 Metrics (pure code)

Total sales; **stock-cost ratio** (stock_purchase / sales; a proxy only, because stock buying is lumpy and not the same as cost of goods sold); expense ratio; sales by weekday; sales by category and top-3 concentration; payment mix; **udhaar outstanding**; **credit share** (outstanding / month sales); **overdue over 30 days**; repeat-customer share; **lapsed regulars** (at least 4 purchases in the prior 60 days, none in the last 21).

**Udhaar aging (FIFO):** for each customer, order events by date. Opening balance and credit_given create credit lots. Each payment_received consumes the oldest open lot first. Remaining open lots are outstanding; a lot's age is month_end minus lot date; overdue if age exceeds 30 days. This is deterministic and explainable to a shopkeeper ("your oldest unpaid credit is from 12 Aug").

### 8.3 Weak-area rules (versioned, tunable, human-readable)

| Rule | Trigger (default) | Estimated rupee impact (for ranking) |
| --- | --- | --- |
| W1 High credit exposure | Credit share above 20%, or overdue above 25% of outstanding | Overdue amount |
| W2 Sales decline | Sales down more than 8% vs previous month | Sales drop in rupees |
| W3 Weak weekday | A weekday below 60% of the average weekday | Gap x occurrences of that weekday in month |
| W4 Stock-cost squeeze | Stock-cost ratio up more than 3 points vs previous month | Points x sales (caveat shown) |
| W5 Category concentration | Top category above 50% of sales | 0 (risk, ranked last unless alone) |
| W6 Lapsed regulars | 3 or more lapsed regulars | Count x average monthly spend of those customers |
| W7 Expense spike | Any category up more than 30% vs previous month | Increase in rupees |

Rank by impact; report the top 3. If none fire, say so plainly. Rules needing the previous month are skipped (and the output says so) when no snapshot exists; they never guess.

### 8.4 Follow-up priority score (no model)

`score = 40 x norm(outstanding) + 25 x norm(days overdue) + 20 x lapse_signal + 15 x norm(90-day purchase value)`

Each `norm` is min-max within the shop (0 when max equals min); `lapse_signal` is 1 for a lapsed regular, otherwise 0. Output the top 5 with a one-line reason ("owes a large amount, 45 days overdue"). Weights are defaults to be calibrated from field feedback.

## 9. Workflow state machine

LangGraph graph (or a plain Python state machine behind the same interface), state persisted after every node. Full node contracts are in TRD 8.

| State | Action | Success | Failure |
| --- | --- | --- | --- |
| S0 RECEIVED | Files loaded, run ID | S1 | S_ERROR |
| S1 VALIDATING | 8.1 checks; G1 | Score at least 0.8: S2. 0.6 to 0.8: S2 with caveat | Block or below 0.6: S_ESCALATED |
| S2 ANALYZING | Metrics, rules, scoring | S3 | S_ERROR (retry once) |
| S3 PHRASING | Model drafts from findings (G2 to G4) | S4 | Invalid or slow: retry once, then templates |
| S4 CHECKING | G5 factuality, G6 content | S5 | Fail: discard model text, templates |
| S5 REVIEW | Owner sees output, marks actions | S6 | Owner closes: save without export |
| S6 SAVING | Snapshot and MoM | S7 | Disk error: memory, warn, retry |
| S7 SHARING (optional) | Preview, consent, G8, outbox | S_DONE | Denied or offline: queue or skip, S_DONE |
| S_ESCALATED | Reason plus at most 2 questions | Resume at S1 | none |
| S_ERROR | Safe message, no partial output | Resume after fix | none |

**Escalate when:** completeness below 0.6 or any Block; a file missing or corrupt; udhaar does not reconcile; MoM requested without a previous snapshot; request out of scope (loans, legal, tax); model output fails verification twice and templates cannot cover a finding.

## 10. LLM layer

- **Role:** phrasing only. Input: structured findings (rule IDs, numbers, aliases). Output: strict JSON, 3 actions each with `title, why, first_step, language`.
- **Model:** a 1B to 3B instruct model, 4-bit, via Ollama or llama.cpp. Chosen by the harness on JSON validity, Hindi quality, latency and memory on the target machine. No model is assumed good until measured.
- **Guardrails:** temperature at most 0.2; schema-constrained output; every number verified against computed values; no names in prompts; banned topics (loans, interest, legal threats, shaming, medical, tax).
- **Fallback:** reviewed Hindi and English templates keyed by rule ID. The product is fully functional with the model off, which is the default in Lite and Portable low-memory mode.

**System prompt (summary):** You are a helpful shop advisor. Use only the facts provided. Never calculate or estimate new numbers. Use simple words a shopkeeper would use. Give one concrete first step per action. Be polite about customers; never suggest pressure, threats or public shaming. If facts are insufficient, return an empty action list.

## 11. Output specification

One screen, large text, this order: (1) one-line health verdict; (2) up to 3 weak areas with rupee evidence; (3) 3 actions with a first step; (4) top-5 follow-ups with reasons; (5) vs last month (arrows); (6) data-quality note if a caveat applies.

**English sample:** "Your shop is okay, but money is stuck. Udhaar is Rs 38,400, which is 27% of this month's sales. 1) Meet your 5 oldest udhaar customers this week and ask for part payment. 2) Wednesdays sold 45% less than other days; try a small offer on Tuesday evening. 3) 4 regular customers have not visited in 3 weeks; tell them about new stock."

**Hindi sample (template):** "आपकी दुकान ठीक चल रही है, लेकिन पैसा उधार में फँसा है। उधार ₹38,400 है, जो इस महीने की बिक्री का 27% है। 1) इस हफ्ते अपने 5 सबसे पुराने उधार वाले ग्राहकों से मिलें और थोड़ा भुगतान माँगें।"

Hindi templates must be reviewed by a native speaker before any field use.

## 12. Privacy and DPDP design

Principle: **privacy by architecture**. The system lacks the ability to send PII, so safety does not depend on policy alone.

| Data | Class | Location | Rule |
| --- | --- | --- | --- |
| Customer names, phones | Personal data (third parties) | Local encrypted vault | Never read by analysis, model, logs or export |
| `customer_ref` aliases | Pseudonymous | Local | Used in analysis; stripped from export |
| Sales, expenses, udhaar rows; `customer_activity` | Business-confidential | Local | Never exported at row level |
| Run logs and audit | Operational | Local | IDs, states, reason codes; no names, phones, or customer-level amounts |
| Banded aggregates | **Pseudonymous** (not anonymous) | May flow to platform control plane | Only after preview and consent |

**Aggregate allow-list (all else blocked):** rotating pseudonymous shop ID, month, region type (urban/semi-urban/rural), sales-change band, credit-share band, overdue band, rule IDs fired, completeness band, action-completion band.

**Controls:** data minimisation; purpose limitation; preview of the exact payload and hash match; revocable, plain-language consent in Hindi and English; **banding on device, k-suppression (k at least 5) in the cloud query layer**; shop ID rotated every 6 months so months cannot be linked indefinitely; one-tap local deletion plus a queued deletion marker for cloud rows; no third-party SDKs or telemetry on the device; automated tests asserting that exports contain only allow-listed keys and that logs contain no planted PII.

**Honest limits:** a pseudonymous shop ID plus region type may still identify a shop in a very small area, so the cloud applies k-suppression and, for tiny regions, coarser regions. The shopkeeper holds third-party customer data, so notice, consent and roles (who is the data fiduciary for what) need legal and compliance review against the DPDP Act 2023 and the current Rules and their phase-in dates before any real deployment. This prototype uses synthetic data only.

## 13. Logging, audit, memory

- **Audit log (local, append-only, hash-chained):** run ID, timestamp, state in and out, rule IDs fired, completeness score, model-or-fallback flag, verification result, guardrail decisions with rule IDs, escalation reason code, consent decision. The chain makes edits detectable; it is tamper-evident, not tamper-proof.
- **Short-term state:** graph state for one run, checkpointed after each node so a power cut resumes the run.
- **Long-term state (local SQLite):** one **monthly snapshot** (aggregates, rules fired, actions given, actions done); a **`customer_activity`** table (alias, last purchase date, 60-day purchase count, 90-day value) used for lapse detection and scoring; settings; audit; outbox. Snapshots pruned after 13 months, audit after 24.
- **The model has no memory** and sees only the structured comparison values.

## 14. Non-functional requirements

| Area | Requirement |
| --- | --- |
| Performance | Deterministic pipeline under 3 s for 1,500 sales rows on the reference 4 GB machine; model stage p95 under 25 s else fallback |
| Memory | Portable/core mode under 600 MB total; full mode under 2.2 GB with a 1B model (to be measured, TRD 16) |
| Availability (edge) | Works with no network; resumes after power cut with no duplicate audit events |
| Usability | Usable by a first-time owner with a field agent in under 10 minutes; font at least 18 px; touch targets at least 48 px; language toggle on every screen |
| Accessibility | High contrast; read-aloud where supported; no colour-only meaning |
| Security | OWASP ASVS L2 as the target; non-root containers; signed rule packs; encrypted vault |
| Maintainability | Rules and templates are data packs, changeable without code release; 80% line coverage on core logic |
| Portability | Linux, Windows 10+; amd64 and arm64 images |
| Cost | Entire prototype runs at zero licence and zero cloud spend (section 20) |

## 15. Definition of Done

**Per run:** input validated; every number on screen traceable to code; at most 3 weak areas with evidence; 3 actions with first steps; top-5 with reasons; snapshot saved; audit complete; export consented and allow-listed, or not produced.

**Project (Tier A):** all P0 edge requirements work; harness meets section 16 targets; failure demo included; repository with README, sample inputs and outputs, prompts, state diagram, ADRs; 3 to 5 minute video; learning-concept report.

**Project (Tier B, stretch):** cloud profile with simulated fleet, k-suppression demo, signed rule pack, Helm chart running on k3d.

## 16. Success metrics and evaluation harness

| Layer | Metric | Target |
| --- | --- | --- |
| Rule correctness | Expected weak area found on the 12 hand-built shops (regression suite) | 12 of 12 |
| Robustness | Same on 60 seeded noisy variants (jittered amounts, dropped rows, duplicates) | at least 85% |
| Generalisation | Blind set of 10 shops generated by a different script/seed, written after the rules froze | at least 80%, reported honestly |
| Safety | Broken or incomplete datasets escalated; false analyses | 100%; 0 |
| Honesty | Unverified numbers reaching the user | 0 |
| Reliability | Model JSON valid on first try; valid after retry plus fallback | at least 80%; 100% |
| Performance | Pipeline; model p95 | under 3 s; under 25 s |
| Privacy | Non-allow-listed export keys; PII tokens in logs/outbox/traces | 0; 0 |
| Product (pilot, later) | At least 1 of 3 actions completed; overdue share trend | 50%; downward |
| Workflow | File load to usable output | under 2 minutes |

**Harness design.** 12 labelled datasets (healthy, high udhaar, declining sales, weak weekday, lapsed regulars, stock-cost squeeze, 30/50/80% missing days, corrupted file, mismatched udhaar, injection strings in category field). Labels: expected weak area, top follow-up customer, expected outcome. Every code change appends a row to `eval/history.csv` (version, scores, failures), which provides the visible first-version-to-final-version evidence for the learning-concept deliverable.

## 17. Intentional failure scenarios (demo)

1. **Primary, incomplete data:** sales exist for 12 of 30 days (completeness 0.57, day coverage Block). Expected: no analysis, no export, message "I cannot give reliable advice yet. Sales for 18 days are missing. Were these days closed, or not written down? Can you add them?", reason code `INCOMPLETE_DATA`.
2. **Model failure:** malformed JSON twice, or a latency spike. Expected: retry once, breaker, templates, visible "basic mode" note, audit `MODEL_FALLBACK`.
3. **Hallucinated figure:** model states a number not in the computed set. Expected: discarded at G5, templates used, audit `G5_FAIL`.
4. **Hostile file:** category cell contains "ignore previous instructions" or `=cmd|...`. Expected: neutralised, mapped to the `other` enum, never reaches the prompt.
5. **Cloud unreachable:** consent given but offline. Expected: payload queued in outbox, analysis unaffected, sync later with no duplicates.

## 18. Autonomy boundaries

**Autonomous:** validation, metrics, rules, ranking, phrasing, fallback, snapshotting, MoM, audit, export preview.

**Human-led:** deciding to chase a customer; sending any message; resolving escalations; export consent; context the data cannot show (festival, closure, illness); changing thresholds; compliance sign-off; anything about lending or credit terms.

**Progressive autonomy:** v1 recommends only; v2 drafts messages for one-tap owner send; anything touching money or customers stays human-approved.

## 19. Build tiers and delivery plan

**Cut line.** Tier A is the v1 scope. Tier B only after Tier A is demo-ready. Tier C is documented, not built.

| Tier | Scope | Cost |
| --- | --- | --- |
| **A** | Edge worker (modular monolith + optional model container), Compose `core`/`full`/`split`, G1 to G9, harness, privacy tests, failure demo, GitHub Actions CI | Rs 0 |
| **B** | Compose `cloud` profile (cloud API, Postgres, Valkey), fleet simulator of 40 shops, k-suppression, signed rule pack, Helm on k3d | Rs 0 |
| **C** | Production: managed Kubernetes in an Indian region, device enrolment and attestation, observability, canary, backups, pen-test, compliance review | Paid (section 20) |

| Day | Deliverable |
| --- | --- |
| 1 | Synthetic data generator; schemas; this PRD and TRD frozen |
| 2 | Validation, metrics, FIFO aging, rules, scoring, unit tests |
| 3 | State machine, checkpoints, audit chain, SQLite stores |
| 4 | Model integration, JSON schema, G2 to G6, templates, fallback; baseline harness run |
| 5 | Bilingual UI, privacy export and preview, G8, outbox |
| 6 | Harness iterations (record failures and fixes), failure demos, `split` profile |
| 7 | README, ADRs, video, learning-concept report, final reply |
| 8+ | Tier B if time remains |

## 20. Cost register: what is free now, what costs money later

| Need | Free for the demo | Paid for production (indicative; verify current pricing) |
| --- | --- | --- |
| Code hosting, CI, image registry | GitHub public repo, GitHub Actions, GHCR | Private repos / extra CI minutes: low |
| Local model | Open-weight models via Ollama / llama.cpp | Better Hindi model hosting or fine-tuning: GPU hours, moderate |
| Cloud plane compute | Local k3d/kind; optional free-tier VM | Managed Kubernetes in India, 3 nodes: roughly Rs 15k to 40k per month |
| Database | Postgres in a container | Managed Postgres with PITR backups: Rs 3k to 15k per month |
| Cache/streams | **Valkey** (BSD licensed Redis-compatible), container | Managed Valkey/Redis HA: Rs 3k to 12k per month |
| Observability | Self-hosted Prometheus, Grafana, Loki | Managed stack or on-call tooling: variable |
| TLS and device certs | mkcert / step-ca, Let's Encrypt | Private PKI with HSM/KMS: variable |
| Image signing and scanning | cosign (keyless), Trivy, Semgrep OSS | Enterprise scanning: optional |
| Device attestation | Skipped in demo | Platform integrity APIs and engineering time |
| Speech (voice notes, TTS) | Open models (Whisper small, Vosk, device TTS) | Higher accuracy Indic ASR/TTS APIs: per-minute fees |
| Customer messaging (v2) | Not used (owner copies text) | WhatsApp Business API: per-conversation fees |
| Security assurance | Self-run tests | Third-party pen-test: Rs 1 to 5 lakh |
| Compliance | This document set | Legal and DPDP review: Rs 50k to 3 lakh |
| Field devices | Existing laptops | Refurbished mini-PCs for agents: Rs 8k to 15k each |

## 21. Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Small model weak in Hindi | Poor phrasing | Reviewed templates default; model optional; harness measures |
| Overbuilding the architecture | Demo unfinished | Tier cut line; modular monolith default; `split` is the same code |
| Docker Desktop too heavy for 4 GB Windows | Unusable on target | Portable mode without Docker |
| Messy real records | Wrong insight | Validation, gate, escalate over guess |
| Anonymous cash sales defeat lapse detection | W6 rarely fires | Treat W6 as optional; validate in the field (22) |
| Owner distrust | No adoption | Evidence beside every claim; big simple text; field walkthrough |
| Re-identification via aggregates | Privacy breach | Banding, cloud k-suppression, ID rotation, preview |
| Pressure on customers | Reputational harm | Tone guardrails; owner always sends |
| Self-authored test data flatters results | Overclaiming | Noisy and blind sets; report gaps honestly |

## 22. Assumptions to validate and open questions

| # | Assumption / question | How to validate |
| --- | --- | --- |
| A1 | Owners can export or key in 3 simple CSV/Excel files | Field observation; maybe a simple entry form is needed |
| A2 | Enough sales carry a `customer_ref` for lapse detection | Ask field agents; otherwise limit lapse logic to udhaar customers |
| A3 | 20% credit share and 30-day overdue are meaningful thresholds | Calibrate with real aggregates |
| A4 | A 1B model on 4 GB CPU is usable | Measure; else Lite mode only |
| A5 | Consent notice wording is acceptable | Legal and compliance review |
| Q1 | Phone-native offline app versus local web UI? | Pilot feedback |
| Q2 | Family-run, multi-owner shops? | Field |
| Q3 | Managed or self-hosted data services for the platform? | Platform ops decision |

## 23. Version 2 roadmap

Action tracking with outcome learning; voice input in local languages; Android offline app; field-agent mode with deviation report; threshold calibration from real aggregates; one-tap drafted messages with approval; CI regression gate; more languages.

## 24. Traceability map

| Topic | Section |
| --- | --- |
| Goal and system definition | 4 |
| Definition of Done | 15 |
| Sample inputs and outputs | 8, 11, TRD 6 |
| Prompts, rules, logic | 8, 10 |
| Tools and APIs | TRD 6, 20 |
| States and transitions | 9, TRD 8 |
| Memory and state | 13 |
| Exceptions and failure handling | 9, 17, TRD 15 |
| Privacy / DPDP | 12 |
| Logging and audit | 13, TRD 7 |
| Intentional failure | 17 |
| Autonomous vs human-led | 18 |
| Next version | 23 |
| Learning concept (evaluation harness, small local models, cost control) | 16 and `eval/history.csv` |

| FR | TRD component | Test |
| --- | --- | --- |
| FR-2, FR-3 | ingest, analytics | `test_validation`, `test_metrics`, property tests |
| FR-4, FR-5 | analytics | `test_rules`, `test_scoring`, harness |
| FR-6, FR-7 | orchestrator, llm, guardrails | `test_fallback`, `test_gate` |
| FR-11 | audit | `test_hash_chain`, tamper test |
| FR-12 | privacy | `test_export_allowlist`, `test_hash_match` |
| FR-13 | guardrails | `test_g1` to `test_g9`, injection and PII suites |
| CP-1, CP-2 | cloud ingest | `test_cloud_reject_unknown`, `test_k_suppress` |
