"""
Unit tests for WorkflowEngine Audit Trail Integration (PRD §9, §13, TRD §7.1, §8)
"""

import tempfile
from pathlib import Path
import pytest
from app.config import Settings
from app.contracts import WorkflowState, RunStatus
from app.modules.orchestrator.engine import WorkflowEngine
from app.modules.audit.logger import get_audit_logger


@pytest.mark.asyncio
async def test_workflow_records_audit_events():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        settings = Settings(data_dir=data_dir)
        audit_logger = get_audit_logger(data_dir)

        run_store = {}
        engine = WorkflowEngine(settings=settings, run_store=run_store, audit_logger=audit_logger)
        run_id = "test_audit_chain_run_1"

        run_store[run_id] = RunStatus(
            run_id=run_id,
            state=WorkflowState.RECEIVED,
            progress_pct=5,
        )

        fixtures_dir = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "public" / "fixtures" / "healthy_shop"
        sales_bytes = (fixtures_dir / "sales.csv").read_bytes()
        expenses_bytes = (fixtures_dir / "expenses.csv").read_bytes()
        udhaar_bytes = (fixtures_dir / "udhaar.csv").read_bytes()

        await engine.execute(
            run_id=run_id,
            sales_bytes=sales_bytes,
            expenses_bytes=expenses_bytes,
            udhaar_bytes=udhaar_bytes,
            sales_filename="sales.csv",
            expenses_filename="expenses.csv",
            udhaar_filename="udhaar.csv",
            month="2026-09",
            language="en",
        )

        # Integrity verification of the audit chain
        verify_result = audit_logger.verify_integrity()
        assert verify_result["valid"] is True
        # Must have recorded all state transitions (VALIDATING, ANALYZING, PHRASING, CHECKING, SAVING, DONE, RUN_COMPLETED)
        assert verify_result["count"] >= 6
