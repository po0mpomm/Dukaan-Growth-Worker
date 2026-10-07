"""
Ollama and Gemini Phrasing Adapters (Optional enhancement layers)
Always fall back gracefully to TemplatePhrasingAdapter if unavailable.
"""

import httpx
import structlog
from typing import Optional
from app.contracts import FindingsObject, ModelOutput
from app.modules.llm_adapter.base import PhrasingAdapter
from app.modules.llm_adapter.template_adapter import TemplatePhrasingAdapter
from app.modules.llm_adapter.breaker import CircuitBreaker

log = structlog.get_logger(__name__)


class OllamaPhrasingAdapter(PhrasingAdapter):
    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen2.5:1.5b"):
        self.host = host
        self.model = model
        self.breaker = CircuitBreaker()
        self.fallback = TemplatePhrasingAdapter()

    async def is_available(self) -> bool:
        if not self.breaker.can_attempt():
            return False
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.get(f"{self.host}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def phrase_findings(self, findings: FindingsObject, language: str = "en") -> ModelOutput:
        # If unavailable or circuit open, fall back to templates
        if not await self.is_available():
            return await self.fallback.phrase_findings(findings, language)
        try:
            # For phase 0, if Ollama is not configured with exact prompt pipeline, fallback reliably
            return await self.fallback.phrase_findings(findings, language)
        except Exception as e:
            self.breaker.record_failure()
            log.warning("ollama_phrasing_failed_fallback_to_template", error=str(e))
            return await self.fallback.phrase_findings(findings, language)


class GeminiPhrasingAdapter(PhrasingAdapter):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.breaker = CircuitBreaker()
        self.fallback = TemplatePhrasingAdapter()

    async def is_available(self) -> bool:
        return bool(self.api_key) and self.breaker.can_attempt()

    async def phrase_findings(self, findings: FindingsObject, language: str = "en") -> ModelOutput:
        if not await self.is_available():
            return await self.fallback.phrase_findings(findings, language)
        # Safe fallback
        return await self.fallback.phrase_findings(findings, language)
