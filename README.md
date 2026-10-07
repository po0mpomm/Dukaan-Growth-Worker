# Dukaan Growth Worker 🛒

**A local-first, privacy-safe AI Worker that helps kirana and small retail owners review monthly business activity, identify weak areas, create follow-up actions, and track month-on-month growth.**

Built for **Eko's Micro-Entrepreneur Growth Worker** assignment — Applied AI / Agentic AI / Forward-Deployed AI Worker evaluation.

---

## Quick Start (No Docker Needed)

```bash
# 1. Clone
git clone https://github.com/po0mpomm/Dukaan-Growth-Worker.git
cd Dukaan-Growth-Worker

# 2. Backend (Python 3.13+)
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r backend/requirements.txt

# 3. Frontend (Node 22+)
cd frontend && npm install && cd ..

# 4. Run both
make dev
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## Architecture

```
Next.js 15 (Frontend, :3000)  ←→  FastAPI (Backend, :8000)  ←→  SQLite (Local)
                                         ↓
                              Optional: Eko Cloud API (Tier B)
                              Only banded aggregates, with consent
```

See [docs/TRD_v2.md](docs/TRD_v2.md) for full architecture.

---

## Eko Assignment Checklist

| Item | Location |
|:---|:---|
| Goal and system definition | [docs/PRD_v2.md §4](docs/PRD_v2.md) |
| Definition of Done | [docs/PRD_v2.md §15](docs/PRD_v2.md) |
| Sample inputs | [eval/datasets/01_healthy/](eval/datasets/01_healthy/) |
| Sample outputs | [docs/sample_output.json](docs/sample_output.json) |
| Prompts, rules, logic | [packages/templates/](packages/templates/) + [packages/rules/](packages/rules/) |
| Workflow states | [docs/STATE_DIAGRAM.md](docs/STATE_DIAGRAM.md) |
| Memory/state strategy | [docs/TRD_v2.md §7](docs/TRD_v2.md) |
| Exception handling | [docs/TRD_v2.md §15](docs/TRD_v2.md) |
| Privacy / DPDP | [docs/PRIVACY_DPDP_NOTE.md](docs/PRIVACY_DPDP_NOTE.md) |
| Audit logging | `backend/app/modules/audit/` |
| Intentional failure demo | DemoSwitcher → "18 Days Missing" |
| Autonomous vs human-led | [docs/PRD_v2.md §18](docs/PRD_v2.md) |
| Next version roadmap | [docs/PRD_v2.md §23](docs/PRD_v2.md) |
| Learning concept | [docs/LEARNING_CONCEPT.md](docs/LEARNING_CONCEPT.md) |

---

## Repository Layout

```
backend/           Python 3.13 FastAPI — modular monolith
frontend/          Next.js 15 App Router — self-hosted PWA
packages/          Signed data packs: rules, templates, policies
eval/              Evaluation harness + history.csv
tools/             Synthetic data generator, fleet simulator
deploy/            Docker Compose profiles + Helm chart + portable script
cloud/             Tier B: FastAPI cloud control plane
docs/              PRD, TRD, ADRs, state diagram, privacy note, learning concept
tests/             Unit, contract, chaos tests
```

---

## Privacy

- Customer names and phone numbers **never leave the device**
- Only banded aggregates (no amounts, no aliases) may sync to Eko **with explicit owner consent**
- All analysis runs fully offline
- AES-256-GCM encrypted customer vault

See [docs/PRIVACY_DPDP_NOTE.md](docs/PRIVACY_DPDP_NOTE.md).

---

## Candidate

**Anvaya Arsha** — Applied AI / Agentic AI / Forward-Deployed Engineering  
Eko Evaluation Assignment · Oct 2026
