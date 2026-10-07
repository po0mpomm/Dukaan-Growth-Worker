# =============================================================================
# Dukaan Growth Worker — Makefile
# Targets: dev, backend, frontend, test, eval, lint, typecheck, docker-core, clean
# =============================================================================

.PHONY: dev backend frontend test eval lint typecheck docker-core docker-cloud clean install

# ── Start both servers for local development ──────────────────────────────────
dev:
	powershell -ExecutionPolicy Bypass -File .\run.ps1

# ── Backend only ──────────────────────────────────────────────────────────────
backend:
	cd backend && python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload

# ── Frontend only ─────────────────────────────────────────────────────────────
frontend:
	cd frontend && npm run dev

# ── Install all dependencies ──────────────────────────────────────────────────
install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

# ── Run all backend & cloud tests ─────────────────────────────────────────────
test:
	python -m pytest backend/tests -v
	python -m pytest cloud/tests -v

# ── Run evaluation harness ───────────────────────────────────────────────────
eval:
	python eval/runner.py

# ── Run end-to-end live smoke test ────────────────────────────────────────────
smoke:
	python tools/smoke_test.py

# ── Type-check frontend ───────────────────────────────────────────────────────
typecheck:
	cd frontend && npm run build

# ── Docker: core profile (edge monolith) ──────────────────────────────────────
docker-core:
	docker compose --profile core up --build

# ── Docker: cloud profile (Tier B) ───────────────────────────────────────────
docker-cloud:
	docker compose --profile cloud up --build

# ── Generate synthetic Kirana dataset ─────────────────────────────────────────
generate-data:
	python tools/generate_synthetic_data.py

# ── Fleet simulator ───────────────────────────────────────────────────────────
fleet-sim:
	python tools/fleet_simulator.py

# ── Clean build artifacts ─────────────────────────────────────────────────────
clean:
	powershell -Command "Remove-Item -Recurse -Force frontend\.next, backend\__pycache__, .pytest_cache -ErrorAction SilentlyContinue"
