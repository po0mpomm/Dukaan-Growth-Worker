"""Analytics metrics stub — Phase 2 full implementation."""
from app.modules.ingest.parser import ParsedData


def compute_metrics(parsed: ParsedData, month: str) -> dict:
    """Compute all metrics from PRD §8.2. Full implementation in Phase 2."""
    return {"month": month, "total_sales": 0, "stub": True}


def build_verdict_text(weak_areas: list, metrics: dict) -> tuple[str, str]:
    """Return (verdict_en, verdict_hi)."""
    if not weak_areas:
        return "Your shop looks healthy this month.", "आपकी दुकान इस महीने ठीक दिख रही है।"
    rule = weak_areas[0].rule_id
    verdicts = {
        "W1": ("Your shop is okay, but money is stuck in udhaar.", "आपकी दुकान ठीक है, लेकिन पैसा उधार में फँसा है।"),
        "W2": ("Sales have declined this month.", "इस महीने बिक्री कम हुई है।"),
        "W3": ("Some days of the week have weak sales.", "सप्ताह के कुछ दिनों में बिक्री कम है।"),
        "W4": ("Stock costs have risen relative to sales.", "बिक्री की तुलना में स्टॉक लागत बढ़ी है।"),
        "W5": ("Sales are concentrated in too few categories.", "बिक्री बहुत कम श्रेणियों में सीमित है।"),
        "W6": ("Some regular customers have not visited recently.", "कुछ नियमित ग्राहक हाल ही में नहीं आए हैं।"),
        "W7": ("One or more expenses have spiked this month.", "इस महीने एक या अधिक खर्च बढ़ गए हैं।"),
    }
    return verdicts.get(rule, ("Your shop needs attention.", "आपकी दुकान को ध्यान देने की जरूरत है।"))
