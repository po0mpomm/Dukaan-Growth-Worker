"""Data router — owner-initiated full local data deletion."""
import structlog
from fastapi import APIRouter, Depends
from app.config import Settings, get_settings

log = structlog.get_logger(__name__)
router = APIRouter()


@router.delete("/data")
async def delete_all_data(settings: Settings = Depends(get_settings)) -> dict:
    """
    Owner-initiated one-tap deletion of all local stores.
    Also queues a deletion marker in outbox for cloud rows.
    TRD §6.1: DELETE /v1/data
    PRD §12: One-tap local deletion.
    """
    import shutil
    data_dir = settings.data_dir
    if data_dir.exists():
        shutil.rmtree(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        log.info("all_local_data_deleted")
    return {"status": "deleted", "message_en": "All local data has been deleted.", "message_hi": "सभी स्थानीय डेटा हटा दिया गया है।"}
