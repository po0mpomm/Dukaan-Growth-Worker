"""Export router — privacy-safe aggregate export with consent flow."""

import hashlib
import json
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.contracts import AggregateExportPayload

log = structlog.get_logger(__name__)
router = APIRouter()

# Import from runs router to share the run store
from app.routers.runs import _runs
from app.contracts import WorkflowState


@router.post("/runs/{run_id}/export/preview")
async def export_preview(run_id: str, settings: Settings = Depends(get_settings)) -> dict:
    """
    Generate exact export payload and its SHA-256 hash for owner preview.
    Owner MUST see this before giving consent.

    TRD §6.1: POST /v1/runs/{id}/export/preview
    PRD §12: Preview of the exact payload and hash match.
    """
    run = _runs.get(run_id)
    if not run or not run.result:
        raise HTTPException(status_code=404, detail="Run or result not found")
    if run.state != WorkflowState.DONE:
        raise HTTPException(status_code=409, detail="Run not yet complete")

    # Build the banded aggregate payload
    from app.modules.privacy.banding import build_aggregate_payload
    payload = build_aggregate_payload(run.result, settings)

    # Compute SHA-256 for integrity verification
    payload_json = payload.model_dump_json(indent=2)
    payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()

    log.info("export_preview_generated", run_id=run_id, payload_hash=payload_hash[:16])
    return {
        "payload": payload.model_dump(),
        "payload_hash": payload_hash,
        "payload_json": payload_json,
        "notice_version": settings.notice_version,
    }


@router.post("/runs/{run_id}/export/consent")
async def export_consent(
    run_id: str,
    body: dict,
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Owner confirms consent. Queues payload in outbox for later sync.
    Payload hash in body MUST match the hash computed at preview time.

    TRD §6.1: POST /v1/runs/{id}/export/consent
    PRD §12: Consent with hash match verification.
    """
    run = _runs.get(run_id)
    if not run or not run.result:
        raise HTTPException(status_code=404, detail="Run or result not found")

    confirmed_hash = body.get("payload_hash", "")
    notice_version = body.get("notice_version", "")

    if not confirmed_hash or not notice_version:
        raise HTTPException(status_code=400, detail="payload_hash and notice_version required")

    # Re-generate payload and verify hash matches (G8 guardrail)
    from app.modules.privacy.banding import build_aggregate_payload
    from app.modules.privacy.outbox import enqueue_payload
    from app.modules.guardrails.g8_export import verify_export_hash

    payload = build_aggregate_payload(run.result, settings)
    payload_json = payload.model_dump_json(indent=2)
    expected_hash = hashlib.sha256(payload_json.encode()).hexdigest()

    if confirmed_hash != expected_hash:
        log.warning("export_hash_mismatch", run_id=run_id)
        raise HTTPException(status_code=422, detail="Hash mismatch — payload was modified")

    # Queue in outbox
    outbox_id = enqueue_payload(
        data_dir=settings.data_dir,
        payload=payload,
        payload_hash=expected_hash,
        notice_version=notice_version,
    )

    # Log to tamper-evident audit trail
    from app.modules.audit.logger import get_audit_logger
    audit_logger = get_audit_logger(settings.data_dir)
    try:
        audit_logger.log_event(
            event_type="EXPORT_CONSENT_GRANTED",
            details={"outbox_id": outbox_id, "notice_version": notice_version, "payload_hash": expected_hash[:16]},
            run_id=run_id,
        )
    except Exception:
        pass

    log.info("export_consented_queued", run_id=run_id, outbox_id=outbox_id)
    return {"status": "queued", "outbox_id": outbox_id, "message_en": "Your data will sync when online."}
