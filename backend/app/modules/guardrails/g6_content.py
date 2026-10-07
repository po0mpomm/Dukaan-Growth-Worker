"""
G6 Content Guardrail (TRD §10)
Verifies tone, prohibited topics (e.g., informal loan sharks, illegal practices, abusive recovery),
and ensures dignity and respect for micro-entrepreneurs.
"""

from app.contracts import ActionItem, FindingsObject
from typing import Tuple, List

PROHIBITED_TERMS = ["loan shark", "illegal", "threaten", "harass", "bribe", "police complaint"]


def check_content(
    actions: List[ActionItem],
    findings: FindingsObject,
    source: str
) -> Tuple[List[ActionItem], str]:
    """Scans actions for prohibited terms or aggressive tone."""
    for act in actions:
        combined = f"{act.title} {act.description} {act.first_step}".lower()
        for term in PROHIBITED_TERMS:
            if term in combined:
                # Fallback to safe template
                from app.modules.llm_adapter.template_adapter import TemplatePhrasingAdapter
                import asyncio
                adapter = TemplatePhrasingAdapter()
                # synchronous fallback creation
                fallback_output = asyncio.run(adapter.phrase_findings(findings, findings.language))
                return fallback_output.actions, "template"

    return actions, source
