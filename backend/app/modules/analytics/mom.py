"""Month-on-month engine stub — Phase 4 full implementation."""
from pathlib import Path
from typing import Optional
from app.contracts import MoMComparison, ResultObject


def compute_mom(metrics: dict, month: str, data_dir: Path) -> Optional[MoMComparison]:
    """Compare with prior month snapshot. Full implementation in Phase 4."""
    return MoMComparison(has_prior_month=False)


def save_snapshot(result: ResultObject, data_dir: Path) -> None:
    """Save monthly snapshot to analytics.db. Full implementation in Phase 4."""
    pass
