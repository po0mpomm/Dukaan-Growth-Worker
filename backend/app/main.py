"""
Dukaan Growth Worker — FastAPI Application Factory

Design principles (PRD §0.2):
  Code computes. Rules decide. The small model only phrases.
  The system refuses to guess.

Architecture (TRD §2.1):
  Modular monolith: all modules loaded in one process.
  Same code runs as split microservices in Docker `split` profile
  via the SERVICES environment variable.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db.base import init_all_databases
from app.routers import audit, data, export, runs
from app.modules.llm_adapter.selector import select_adapter
from app.modules.audit.logger import get_audit_logger

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle."""
    settings = get_settings()

    log.info(
        "dukaan_worker_starting",
        version="0.1.0",
        data_dir=str(settings.data_dir),
        llm_mode="auto-detecting",
    )

    # Initialize all SQLite databases (creates tables if not exist)
    init_all_databases(settings.data_dir)
    log.info("databases_initialized")

    # Auto-detect LLM adapter: Templates → Ollama → Gemini
    adapter = await select_adapter(settings)
    app.state.llm_adapter = adapter
    log.info("llm_adapter_selected", adapter=adapter.__class__.__name__)

    # Record startup in audit log
    audit_logger = get_audit_logger(settings.data_dir)
    app.state.audit_logger = audit_logger

    yield

    # Graceful shutdown
    log.info("dukaan_worker_shutting_down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Dukaan Growth Worker",
        description=(
            "Local-first AI Worker for kirana/small retail growth. "
            "Deterministic analytics, privacy by architecture, offline-first."
        ),
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Security: only accept requests from localhost (the Next.js proxy)
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "::1"],
        )

    # CORS: only allow the Next.js dev server origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    # Include all routers
    app.include_router(runs.router, prefix="/v1", tags=["runs"])
    app.include_router(export.router, prefix="/v1", tags=["export"])
    app.include_router(audit.router, prefix="/v1", tags=["audit"])
    app.include_router(data.router, prefix="/v1", tags=["data"])

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict:
        return {"status": "ok", "service": "dukaan-growth-worker"}

    @app.get("/readyz", tags=["health"])
    async def readyz() -> dict:
        """Returns 200 only when all DBs are initialized and adapter selected."""
        return {"status": "ready", "llm_adapter": app.state.llm_adapter.__class__.__name__}

    return app


app = create_app()
