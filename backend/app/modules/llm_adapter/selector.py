"""
Adapter Selector: Auto-detects available LLM layer at startup.
Order: Ollama (if running) -> Gemini (if key present) -> Deterministic Templates (always ready).
"""

from typing import Optional
import structlog
from app.config import Settings
from app.modules.llm_adapter.base import PhrasingAdapter
from app.modules.llm_adapter.template_adapter import TemplatePhrasingAdapter
from app.modules.llm_adapter.remote_adapters import OllamaPhrasingAdapter, GeminiPhrasingAdapter

log = structlog.get_logger(__name__)

_cached_adapter: Optional[PhrasingAdapter] = None


async def select_adapter(settings: Settings) -> PhrasingAdapter:
    """Auto-detects the best available phrasing adapter and caches it."""
    global _cached_adapter

    if settings.llm_mode == "templates":
        log.info("adapter_forced_to_templates")
        _cached_adapter = TemplatePhrasingAdapter()
        return _cached_adapter

    # Try Ollama if configured
    if settings.llm_mode in ("auto", "ollama"):
        ollama = OllamaPhrasingAdapter(host=settings.ollama_host, model=settings.ollama_model)
        if await ollama.is_available():
            log.info("adapter_selected_ollama", host=settings.ollama_host, model=settings.ollama_model)
            _cached_adapter = ollama
            return _cached_adapter

    # Try Gemini if key is provided
    if settings.llm_mode in ("auto", "gemini") and settings.gemini_api_key:
        gemini = GeminiPhrasingAdapter(api_key=settings.gemini_api_key)
        if await gemini.is_available():
            log.info("adapter_selected_gemini")
            _cached_adapter = gemini
            return _cached_adapter

    # Default: deterministic, field-ready template adapter
    log.info("adapter_selected_templates_default")
    _cached_adapter = TemplatePhrasingAdapter()
    return _cached_adapter


def get_cached_adapter() -> PhrasingAdapter:
    """Returns the cached adapter, or a fresh TemplatePhrasingAdapter if none cached yet."""
    global _cached_adapter
    if _cached_adapter is None:
        _cached_adapter = TemplatePhrasingAdapter()
    return _cached_adapter
