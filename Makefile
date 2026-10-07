# =============================================================================
# Dukaan Growth Worker — Makefile
# Targets: dev, backend, frontend, test, eval, lint, docker-core, docker-full, clean
# =============================================================================

.PHONY: dev backend frontend test eval lint typecheck docker-core docker-full docker-cloud clean install

# ── Start both servers for local development ──────────────────────────────────
dev:
	@echo "Starting backend on :8000 and frontend on :3000..."
	@Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd backend; ..\.venv\Scripts\activate; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
	@cd frontend; npm run dev

# ── Backend only ──────────────────────────────────────────────────────────────
backend:
	.venv\Scripts\activate
	cd backend; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# ── Frontend only ─────────────────────────────────────────────────────────────
frontend:
	cd frontend; npm run dev

# ── Install all dependencies ──────────────────────────────────────────────────
install:
	python -m venv .venv
	.venv\Scripts\pip install -r backend/requirements.txt
	cd frontend; npm install

# ── Run all backend tests ─────────────────────────────────────────────────────
test:
	.venv\Scripts\pytest backend/tests -q --cov=backend/app --cov-fail-under=80 -v

# ── Run evaluation harness (CI-blocking) ──────────────────────────────────────
eval:
	.venv\Scripts\python -m eval.runner --gate

# ── Lint + type-check backend ─────────────────────────────────────────────────
lint:
	.venv\Scripts\ruff check backend/
	.venv\Scripts\mypy backend/app --ignore-missing-imports

# ── Type-check frontend ───────────────────────────────────────────────────────
typecheck:
	cd frontend; npx tsc --noEmit

# ── Docker: core profile (backend only, no model) ────────────────────────────
docker-core:
	docker compose --profile core up --build

# ── Docker: full profile (backend + llm container) ───────────────────────────
docker-full:
	docker compose --profile full up --build

# ── Docker: cloud profile (Tier B) ───────────────────────────────────────────
docker-cloud:
	docker compose --profile cloud up --build

# ── Privacy scan (asserts 0 PII in outputs) ───────────────────────────────────
privacy-scan:
	.venv\Scripts\python -m tests.privacy_scan

# ── Generate all synthetic datasets ──────────────────────────────────────────
generate-data:
	.venv\Scripts\python tools/synthetic_data/generator.py

# ── Clean build artifacts ─────────────────────────────────────────────────────
clean:
	Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force frontend\.next -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force frontend\node_modules -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force backend\__pycache__ -ErrorAction SilentlyContinue
