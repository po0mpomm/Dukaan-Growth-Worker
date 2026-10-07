"""Runs router — the primary API surface for the frontend."""

import uuid
from pathlib import Path
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi import BackgroundTasks

from app.config import Settings, get_settings
from app.contracts import RunStatus, WorkflowState
from app.modules.orchestrator.engine import WorkflowEngine

log = structlog.get_logger(__name__)
router = APIRouter()

# In-memory run store (Phase 0 scaffold — replaced by SQLite checkpointer in Phase 4)
_runs: dict[str, RunStatus] = {}


@router.post("/runs", status_code=status.HTTP_202_ACCEPTED)
async def create_run(
    background_tasks: BackgroundTasks,
    sales_file: UploadFile = File(..., description="Sales CSV/XLSX (PRD §8.1)"),
    expenses_file: UploadFile = File(..., description="Expenses CSV/XLSX"),
    udhaar_file: UploadFile = File(..., description="Udhaar CSV/XLSX with opening balances"),
    month: str = Form(..., description="Target month YYYY-MM"),
    language: str = Form("en", description="Output language: en or hi"),
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Create a new analysis run. Returns 202 with run_id immediately.
    The workflow runs asynchronously; poll GET /v1/runs/{run_id} for status.

    TRD §6.1: POST /v1/runs (multipart: sales, expenses, udhaar, month, language)
    """
    run_id = str(uuid.uuid4())

    # Read file bytes
    sales_bytes = await sales_file.read()
    expenses_bytes = await expenses_file.read()
    udhaar_bytes = await udhaar_file.read()

    # Initialize run status
    _runs[run_id] = RunStatus(
        run_id=run_id,
        state=WorkflowState.RECEIVED,
        progress_pct=5,
        message_en="Files received. Starting validation...",
        message_hi="फ़ाइलें मिल गईं। सत्यापन शुरू हो रहा है...",
    )

    # Launch workflow in background
    engine = WorkflowEngine(settings=settings, run_store=_runs)
    background_tasks.add_task(
        engine.execute,
        run_id=run_id,
        sales_bytes=sales_bytes,
        expenses_bytes=expenses_bytes,
        udhaar_bytes=udhaar_bytes,
        sales_filename=sales_file.filename or "sales.csv",
        expenses_filename=expenses_file.filename or "expenses.csv",
        udhaar_filename=udhaar_file.filename or "udhaar.csv",
        month=month,
        language=language,
    )

    log.info("run_created", run_id=run_id, month=month, language=language)
    return {"run_id": run_id, "status": WorkflowState.RECEIVED}


@router.get("/runs/{run_id}", response_model=RunStatus)
async def get_run_status(run_id: str) -> RunStatus:
    """
    Get current run state and progress.
    Frontend polls this every second until state is DONE, ESCALATED, or ERROR.

    TRD §6.1: GET /v1/runs/{id}
    """
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@router.get("/runs/{run_id}/result")
async def get_run_result(run_id: str) -> dict:
    """
    Get the verified result object. Only available when state == DONE.

    TRD §6.1: GET /v1/runs/{id}/result
    """
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    if run.state == WorkflowState.ESCALATED:
        return {"escalation": run.escalation}
    if run.state != WorkflowState.DONE:
        raise HTTPException(status_code=409, detail="Run not yet complete")
    return {"result": run.result}


@router.post("/runs/{run_id}/actions/{action_n}/done")
async def mark_action_done(run_id: str, action_n: int) -> dict:
    """
    Owner marks an action as done. Stored in analytics.db for MoM tracking.

    TRD §6.1: POST /v1/runs/{id}/actions/{n}/done
    """
    run = _runs.get(run_id)
    if not run or not run.result:
        raise HTTPException(status_code=404, detail="Run or result not found")
    if action_n < 1 or action_n > 3:
        raise HTTPException(status_code=400, detail="Action number must be 1, 2, or 3")

    for action in run.result.actions:
        if action.n == action_n:
            action.done = True
            log.info("action_marked_done", run_id=run_id, action_n=action_n)
            return {"status": "ok", "action_n": action_n}

    raise HTTPException(status_code=404, detail=f"Action {action_n} not found")
