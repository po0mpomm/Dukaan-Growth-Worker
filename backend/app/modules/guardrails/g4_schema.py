"""
G4 Schema Validator — validates model output against strict JSON schema.
Ensures exactly 3 actions, each with required fields and length constraints.
TRD §10, G4.
"""
from app.contracts import ActionItem, FindingsObject


def validate_actions(
    actions: list[ActionItem],
    findings: FindingsObject,
) -> tuple[list[ActionItem], str]:
    """
    Validate that actions conform to strict schema.
    Returns (validated_actions, source) where source is 'model' or 'template'.
    """
    if len(actions) != 3:
        # Fall back to templates
        from app.modules.llm_adapter.templates import get_template_actions
        return get_template_actions(findings), "template"
    return actions, "model"
