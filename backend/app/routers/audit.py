"""Audit router — hash chain verification endpoint."""
import structlog
from fastapi import APIRouter, Depends
from app.config import Settings, get_settings

log = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/audit/verify")
async def verify_audit_chain(settings: Settings = Depends(get_settings)) -> dict:
    """
    Recompute the full SHA-256 hash chain and return verification result.
    TRD §6.1: GET /v1/audit/verify
    """
    from app.modules.audit.verifier import verify_chain
    result = verify_chain(settings.data_dir)
    log.info("audit_chain_verified", valid=result["valid"], events=result["event_count"])
    return result
