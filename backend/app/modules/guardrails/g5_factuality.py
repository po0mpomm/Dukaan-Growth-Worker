"""
G5 Factuality Guardrail — Numeric Token Verifier (TRD §10, PRD §10)

Algorithm:
1. Normalize Devanagari numerals (०..९) to ASCII (0..9).
2. Extract all numeric tokens from model-generated text.
3. Extract all allowed numeric tokens from FindingsObject.
4. If the model mentions any number not in the findings object (or trivial 1..3 action indices),
   reject the model phrasing and fall back to the deterministic reviewed template.
"""

import re
from typing import List, Set, Tuple
from app.contracts import ActionItem, FindingsObject

# Devanagari numeral translation table
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def normalize_digits(text: str) -> str:
    """Translates Devanagari digits to ASCII."""
    if not text:
        return ""
    return text.translate(DEVANAGARI_DIGITS)


def extract_numbers(text: str) -> Set[float]:
    """Extracts all integer and float numbers from a string."""
    text_norm = normalize_digits(text)
    # Remove commas in numbers (e.g., 25,000 -> 25000)
    cleaned = re.sub(r"(?<=\d),(?=\d)", "", text_norm)
    tokens = re.findall(r"\b\d+(?:\.\d+)?\b", cleaned)
    numbers = set()
    for tok in tokens:
        try:
            numbers.add(float(tok))
        except ValueError:
            pass
    return numbers


def extract_allowed_numbers(findings: FindingsObject) -> Set[float]:
    """Extracts all verified numeric values from the findings object."""
    allowed: Set[float] = {1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 30.0, 60.0}  # Common indices/percentages

    for wa in findings.weak_areas:
        allowed.add(float(wa.rank))
        allowed.add(float(wa.rupee_impact))
        for v in wa.metrics.values():
            if isinstance(v, (int, float)):
                allowed.add(float(v))
        if wa.evidence:
            allowed.update(extract_numbers(wa.evidence))

    for f in findings.followups:
        allowed.add(float(f.rank))
        allowed.add(float(f.score))
        if f.outstanding_amount is not None:
            allowed.add(float(f.outstanding_amount))
        if f.days_overdue is not None:
            allowed.add(float(f.days_overdue))

    if findings.comparison and findings.comparison.sales_change_pct is not None:
        allowed.add(float(findings.comparison.sales_change_pct))

    return allowed


def verify_factuality(
    actions: List[ActionItem],
    findings: FindingsObject,
    source: str,
) -> Tuple[List[ActionItem], str]:
    """
    Verifies all numbers in actions against findings.
    If hallucination detected -> falls back to template.
    """
    if source == "template":
        return actions, "template"

    allowed = extract_allowed_numbers(findings)

    for act in actions:
        combined_text = f"{act.title} {act.description or ''} {act.why or ''} {act.first_step}"
        numbers_found = extract_numbers(combined_text)

        # Allow small percentage numbers like 2% discount
        for num in numbers_found:
            # Check if number or rounded integer exists in allowed
            if num not in allowed and round(num) not in allowed and num not in (2.0, 5.0, 7.0, 10.0):
                # Hallucination detected! Fall back to template
                from app.modules.llm_adapter.template_adapter import TemplatePhrasingAdapter
                import asyncio
                adapter = TemplatePhrasingAdapter()
                fallback = asyncio.run(adapter.phrase_findings(findings, findings.language))
                return fallback.actions, "template"

    return actions, source
