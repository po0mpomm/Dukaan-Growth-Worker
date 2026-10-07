"""
LLM Phrasing Adapter Base Interface (TRD §2.1)
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from app.contracts import FindingsObject, ModelOutput, ActionItem


class PhrasingAdapter(ABC):
    """Abstract base class for all LLM phrasing adapters."""

    @abstractmethod
    async def phrase_findings(
        self,
        findings: FindingsObject,
        language: str = "en"
    ) -> ModelOutput:
        """Phrases findings into structured ModelOutput with exactly 3 actions."""
        pass

    async def phrase(self, findings: FindingsObject) -> List[ActionItem]:
        """Convenience method called by workflow engine; returns List[ActionItem]."""
        output = await self.phrase_findings(findings, findings.language)
        return output.actions

    @abstractmethod
    async def is_available(self) -> bool:
        """Returns True if the adapter is currently operational."""
        pass
