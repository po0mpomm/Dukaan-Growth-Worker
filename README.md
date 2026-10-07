# Dukaan Growth Worker 🛒
**Local-First, Privacy-Safe AI Worker for Kirana & Small Retail Growth**

Built for **Eko's Micro-Entrepreneur Growth Worker** assignment (Applied AI / Agentic AI / Forward-Deployed AI Worker).  
Repository: [https://github.com/po0mpomm/Dukaan-Growth-Worker](https://github.com/po0mpomm/Dukaan-Growth-Worker)

---

## ⚡ Quick Start (Windows & Linux)

### Option 1: One-Click Windows Launcher (Recommended)
```powershell
# In PowerShell:
powershell -ExecutionPolicy Bypass -File .\run.ps1
```
*Automatically launches FastAPI backend on `http://127.0.0.1:8000` and Next.js 15 frontend on `http://localhost:3000`.*

### Option 2: Manual Terminal Setup
```bash
# 1. Backend (Python 3.13)
cd backend
pip install -r requirements.txt
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload

# 2. Frontend (Node 22 / Next.js 15) in another terminal
cd frontend
npm install
npm run dev

# 3. Open browser:
# Frontend UI: http://localhost:3000
# Backend API Docs: http://127.0.0.1:8000/docs
```

### Option 3: Docker Compose
```bash
# Edge Monolith (core profile):
docker compose --profile core up --build

# Control Plane with PostgreSQL 16 & Valkey (cloud profile):
docker compose --profile cloud up --build
```

---

## 🧪 Testing & Evaluation Harness

```bash
# Run full unit and integration test suite (14 passing tests):
python -m pytest backend/tests/ -v

# Run Cloud k-suppression test (40-shop simulation):
python -m pytest cloud/tests/test_k_suppression.py -v

# Run Evaluation Benchmark Suite (4 scenarios):
python eval/runner.py
```

Inspect the historical evaluation progress register in [`eval/history.csv`](eval/history.csv).

---

## 🏗️ Architecture & Plane Separation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EDGE PLANE (Runs 100% locally on 4 GB RAM shop machine or laptop)          │
│                                                                             │
│  ┌─────────────────────────────────┐   HTTP   ┌──────────────────────────┐  │
│  │  Next.js 15 App Router (:3000)  │ ◄──────► │   FastAPI Backend (:8000)│  │
│  │  • Mobile-first (375px+ Meena)  │  Proxy   │   • Modular Monolith     │  │
│  │  • Bilingual EN / HI toggle     │          │   • Ingest & Sanitizer   │  │
│  │  • Web Speech TTS read-aloud    │          │   • Completeness Scorer  │  │
│  │  • 1-Click synthetic scenarios  │          │   • FIFO Udhaar Aging    │  │
│  │  • WhatsApp clipboard drafts    │          │   • W1–W7 Rules Engine   │  │
│  └─────────────────────────────────┘          │   • G1–G9 Guardrails     │  │
│                                               │   • Phrasing Adapters    │  │
│                                               └─────────────┬────────────┘  │
│                                                             │ WAL Mode      │
│                                               ┌─────────────▼────────────┐  │
│                                               │   Local SQLite Stores    │  │
│                                               │   • analytics.db         │  │
│                                               │   • audit.db (SHA-256)   │  │
│                                               │   • outbox.db (Sync)     │  │
│                                               └─────────────┬────────────┘  │
└─────────────────────────────────────────────────────────────┼───────────────┘
                                           Consented Banded   │ (Online only)
                                           Payload (Zero-PII) ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLOUD PLANE (Tier B: PostgreSQL 16 + Valkey + Cloud Aggregator)            │
│  • Idempotent ingestion of banded aggregates                                 │
│  • k-Anonymity view: Macro-cohort cells with count < 5 are suppressed       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Complete Deliverables Index

All mandated deliverable items from the Eko assignment email are documented and implemented:

| Requirement | Deliverable File | Description |
|:---|:---|:---|
| **Learning Concept Report** | [`docs/LEARNING_CONCEPT_REPORT.md`](docs/LEARNING_CONCEPT_REPORT.md) | 3-page deep dive on Evaluation Harnesses for Deterministic AI Agents |
| **Candidate Q&A** | [`docs/CANDIDATE_QA.md`](docs/CANDIDATE_QA.md) | Answers to all 12 "Define Before Building" questions |
| **Failure Scenarios** | [`docs/FAILURE_SCENARIOS.md`](docs/FAILURE_SCENARIOS.md) | 5 edge case failure walkthroughs & degradation mechanisms |
| **Prompt Catalog** | [`docs/PROMPTS.md`](docs/PROMPTS.md) | System phrasing prompts, bilingual templates, and schemas |
| **Workflow State Machine** | [`docs/STATE_DIAGRAM.md`](docs/STATE_DIAGRAM.md) | Mermaid state diagram, transition invariants, and timeouts |
| **Architecture Decision Records** | [`docs/ADR.md`](docs/ADR.md) | ADR 001 to ADR 012 detailing design trade-offs |
| **Sample Inputs & Outputs** | [`docs/SAMPLE_INPUTS_OUTPUTS.md`](docs/SAMPLE_INPUTS_OUTPUTS.md) | Sample CSVs and verified `ResultObject` JSON payloads |
| **Privacy & DPDP Approach** | [`docs/PRIVACY_APPROACH.md`](docs/PRIVACY_APPROACH.md) | Architectural zero-PII guarantees, right to erasure, SHA-256 hash chains |
| **Demo Walkthrough Script** | [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) | 6-minute recorded video demonstration narrative & timing |
| **Evaluation History** | [`eval/history.csv`](eval/history.csv) | Empirical progression across 3 iterations (100% pass rate in 0.28s) |
| **Evaluation Benchmark** | [`eval/runner.py`](eval/runner.py) | Automated 4-scenario benchmark runner |
| **Synthetic Data Generator** | [`tools/generate_synthetic_data.py`](tools/generate_synthetic_data.py) | CLI generator for realistic Indian kirana transaction datasets |
| **Fleet Simulator** | [`tools/fleet_simulator.py`](tools/fleet_simulator.py) | 50-100 store network distribution simulator |
| **Automated CI Workflow** | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions CI for backend, cloud, eval runner, and Next.js build |
| **PRD Specification** | [`Dukaan_Growth_Worker_PRD_v2.md`](Dukaan_Growth_Worker_PRD_v2.md) | Complete Product Requirements Document v2.0 |
| **TRD Specification** | [`Dukaan_Growth_Worker_TRD_v2.md`](Dukaan_Growth_Worker_TRD_v2.md) | Complete Technical Requirements Document v2.0 |

---

## 🖥️ Interactive Web Application Routes

| Route | Purpose | Features |
|:---|:---|:---|
| `/` | **Home & Ingestion** | 1-click synthetic presets (Meena's Shop, Missing Data, Margin Erosion, Udhaar Risk), bilingual toggle, file upload |
| `/runs/:runId` | **Monthly Business Review** | Verdict, W1–W7 weak areas, action checkboxes, WhatsApp drafts, 🖨️ physical print/PDF report |
| `/runs/:runId/escalated` | **Human Escalation** | Incomplete data diagnosis, missing date breakdown, manual review checklist |
| `/presentation` | **Interactive Pitch Deck** | 8-slide presentation deck with keyboard arrows, progress bar, and English/Hindi bullets |
| `/eval` | **In-Browser Benchmark** | Live benchmark scorecards, latency metrics, and G1–G9 guardrail status |
| `/privacy` | **Privacy & DPDP Center** | Local-first assurance, SHA-256 banded cloud export preview, single-tap right-to-erasure |
| `/audit` | **Cryptographic Audit Chain** | SHA-256 tamper-evident log inspector and hash chain verifier |

---

## 🛡️ Privacy & DPDP Guarantees

1. **Zero-PII On Device:** Real customer names and phone numbers are stripped on ingestion and replaced with synthetic aliases (`CUST_001`).
2. **Local-First Processing:** Financial calculations and rule evaluations occur 100% on the local machine (4 GB RAM target).
3. **Banded Consented Exports:** Only coarse categorical ranges (e.g. `revenue_band: 50K_150K`, `rules_fired: ["W1"]`) can sync to the cloud with explicit owner consent.
4. **k-Anonymity ($k \ge 5$):** The cloud aggregation plane suppresses macro-cohort cells with fewer than 5 shops.
5. **Right to Erasure:** A single-tap `DELETE /v1/data` endpoint purges all local databases immediately.

---

## Candidate
**Anvaya Arsha** — Applied AI / Agentic AI / Forward-Deployed Engineer  
Eko Evaluation Assignment · October 2026

