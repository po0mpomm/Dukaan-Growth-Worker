"""
Month-on-Month Comparison Engine & Snapshot Store (PRD §8.2, TRD §7.1)
Persists monthly snapshots to analytics.db and derives growth metrics against prior month.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import structlog

from app.contracts import MoMComparison, ResultObject
from app.db.base import get_connection, ANALYTICS_DDL

log = structlog.get_logger(__name__)


def _ensure_snapshots_table(conn) -> None:
    """Ensure analytics schema is created before queries or insertions."""
    conn.executescript(ANALYTICS_DDL)
    conn.commit()


def compute_mom(metrics: dict, month: str, data_dir: Path) -> Optional[MoMComparison]:
    """
    Compare current month metrics against prior month snapshot from analytics.db.
    Calculates sales change %, credit share change %, and rules resolved/new.
    """
    # Determine prior month YYYY-MM
    try:
        y, m = int(month[:4]), int(month[5:7])
        if m == 1:
            prior_month = f"{y - 1:04d}-12"
        else:
            prior_month = f"{y:04d}-{m - 1:02d}"
    except (ValueError, IndexError):
        return MoMComparison(has_prior_month=False)

    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "analytics.db"

    conn = get_connection(db_path)
    try:
        _ensure_snapshots_table(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM snapshots WHERE month = ?", (prior_month,))
        row = cursor.fetchone()
        if not row:
            return MoMComparison(has_prior_month=False)

        prior_sales = float(row["total_sales"] or 0.0)
        curr_sales = float(metrics.get("total_sales", 0.0))
        sales_change_pct = (
            round(((curr_sales - prior_sales) / prior_sales) * 100.0, 1)
            if prior_sales > 0 else 0.0
        )

        prior_credit_share = float(row["credit_share"] or 0.0)
        curr_credit_share = float(metrics.get("credit_ratio", 0.0))
        credit_share_change_pct = round(curr_credit_share - prior_credit_share, 1)

        prior_overdue = float(row["overdue_amount"] or 0.0)
        curr_overdue = float(metrics.get("uncollected_udhaar", 0.0))
        overdue_change_pct = (
            round(((curr_overdue - prior_overdue) / prior_overdue) * 100.0, 1)
            if prior_overdue > 0 else 0.0
        )

        prior_rules = json.loads(row["rules_fired"]) if row["rules_fired"] else []
        curr_rules = [w.rule_id for w in metrics.get("weak_areas", [])]
        rules_resolved = [r for r in prior_rules if r not in curr_rules]
        rules_new = [r for r in curr_rules if r not in prior_rules]

        actions_completed = int(row["actions_done"] or 0)
        actions_total = len(json.loads(row["actions_json"])) if row["actions_json"] else 3

        return MoMComparison(
            has_prior_month=True,
            prior_month=prior_month,
            sales_change_pct=sales_change_pct,
            credit_share_change_pct=credit_share_change_pct,
            overdue_change_pct=overdue_change_pct,
            rules_resolved=rules_resolved,
            rules_new=rules_new,
            actions_completed=actions_completed,
            actions_total=actions_total,
        )
    except Exception as exc:
        log.warning("compute_mom_failed", error=str(exc), month=month)
        return MoMComparison(has_prior_month=False)
    finally:
        conn.close()


def save_snapshot(result: ResultObject, data_dir: Path) -> None:
    """Save completed monthly run snapshot to analytics.db for MoM comparisons."""
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "analytics.db"
    conn = get_connection(db_path)
    try:
        _ensure_snapshots_table(conn)
        rules_fired = json.dumps([w.rule_id for w in result.weak_areas])
        actions_json = json.dumps([a.model_dump() for a in result.actions])
        actions_done = sum(1 for a in result.actions if a.done)

        metrics = result.metrics or {}
        total_sales = float(metrics.get("total_sales", 0.0))
        credit_share = float(metrics.get("credit_ratio", 0.0))
        overdue_amount = float(metrics.get("uncollected_udhaar", 0.0))
        stock_expenses = float(metrics.get("stock_expenses", 0.0))
        stock_cost_ratio = (stock_expenses / total_sales) if total_sales > 0 else 0.0

        conn.execute(
            """
            INSERT INTO snapshots (
                month, total_sales, stock_cost_ratio, credit_share,
                overdue_amount, rules_fired, actions_json, actions_done,
                completeness, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(month) DO UPDATE SET
                total_sales=excluded.total_sales,
                stock_cost_ratio=excluded.stock_cost_ratio,
                credit_share=excluded.credit_share,
                overdue_amount=excluded.overdue_amount,
                rules_fired=excluded.rules_fired,
                actions_json=excluded.actions_json,
                actions_done=excluded.actions_done,
                completeness=excluded.completeness,
                created_at=excluded.created_at
            """,
            (
                result.month,
                total_sales,
                stock_cost_ratio,
                credit_share,
                overdue_amount,
                rules_fired,
                actions_json,
                actions_done,
                result.completeness.score if result.completeness else 1.0,
                result.created_at,
            ),
        )
        conn.commit()
        log.info("snapshot_saved", month=result.month, total_sales=total_sales)
    except Exception as exc:
        log.error("save_snapshot_failed", error=str(exc), month=result.month)
    finally:
        conn.close()

