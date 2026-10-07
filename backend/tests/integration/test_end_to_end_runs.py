"""
End-to-End Workflow Integration Tests (PRD §9, TRD §8)
Tests the complete edge workflow from file intake to result, escalation, export consent, and audit verification.
"""

import asyncio
from pathlib import Path
import pytest
from app.config import Settings
from app.contracts import WorkflowState
from app.modules.orchestrator.engine import WorkflowEngine
from app.modules.privacy.banding import build_aggregate_payload
from app.modules.privacy.outbox import enqueue_payload
from app.modules.audit.logger import get_audit_logger


@pytest.fixture
def test_settings(tmp_path):
    return Settings(data_dir=tmp_path)


@pytest.mark.asyncio
async def test_healthy_shop_workflow_e2e(test_settings):
    fixtures_dir = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "public" / "fixtures" / "healthy_shop"
    sales_bytes = (fixtures_dir / "sales.csv").read_bytes()
    expenses_bytes = (fixtures_dir / "expenses.csv").read_bytes()
    udhaar_bytes = (fixtures_dir / "udhaar.csv").read_bytes()

    run_store = {}
    engine = WorkflowEngine(settings=test_settings, run_store=run_store)
    run_id = "test_run_healthy_1"

    # Pre-populate run_store as router does
    from app.contracts import RunStatus
    run_store[run_id] = RunStatus(
        run_id=run_id,
        state=WorkflowState.RECEIVED,
        progress_pct=5,
    )

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

    status = run_store[run_id]
    assert status.state == WorkflowState.DONE
    assert status.result is not None
    assert status.result.completeness.score >= 0.80
    assert len(status.result.actions) == 3
    assert len(status.result.weak_areas) > 0

    # Test export preview & consent flow
    payload = build_aggregate_payload(status.result, test_settings)
    assert payload.month == "2026-09"
    assert payload.region_type == "semi_urban"

    outbox_id = enqueue_payload(
        data_dir=test_settings.data_dir,
        payload=payload,
        payload_hash="dummy_hash_123",
        notice_version=test_settings.notice_version,
    )
    assert outbox_id is not None

    # Test audit verification
    audit_logger = get_audit_logger(test_settings.data_dir)
    audit_logger.log_event("RUN_COMPLETE", {"run_id": run_id})
    verify_res = audit_logger.verify_integrity()
    assert verify_res["valid"] is True


@pytest.mark.asyncio
async def test_incomplete_data_escalation_e2e(test_settings):
    fixtures_dir = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "public" / "fixtures" / "incomplete_18days"
    sales_bytes = (fixtures_dir / "sales.csv").read_bytes()
    expenses_bytes = (fixtures_dir / "expenses.csv").read_bytes()
    udhaar_bytes = (fixtures_dir / "udhaar.csv").read_bytes()

    run_store = {}
    engine = WorkflowEngine(settings=test_settings, run_store=run_store)
    run_id = "test_run_incomplete_1"

    from app.contracts import RunStatus
    run_store[run_id] = RunStatus(
        run_id=run_id,
        state=WorkflowState.RECEIVED,
        progress_pct=5,
    )

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

    status = run_store[run_id]
    assert status.state == WorkflowState.ESCALATED
    assert status.escalation is not None
    assert len(status.escalation.questions) <= 2
    assert "missing" in status.escalation.reason_en.lower()
