"""
Cloud Plane Aggregator Service (FastAPI)
TRD §7.2, ADR 008

Receives banded consented payloads from edge outboxes, enforces idempotency,
and exposes privacy-preserving macro-cohort queries with k >= 5 suppression.
"""

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="Dukaan Growth Worker — Cloud Aggregator",
    version="1.0.0",
    description="Privacy-preserving aggregate receiver with k-suppression.",
)

# In-memory store for standalone demo / lightweight execution
_cloud_aggregates: Dict[str, Dict[str, Any]] = {}


class CloudAggregatePayload(BaseModel):
    schema_version: str = "aggregate/1.0"
    shop_pid: str
    month: str
    region_type: str
    sales_change_band: str
    credit_share_band: str
    overdue_band: str
    rules_fired: List[str]
    completeness_band: str
    action_completion_band: str


@app.post("/v1/aggregates", status_code=status.HTTP_201_CREATED)
async def ingest_aggregate(payload: CloudAggregatePayload) -> Dict[str, str]:
    """Ingests consented banded payload. Idempotent per (shop_pid, month)."""
    key = f"{payload.shop_pid}:{payload.month}"
    _cloud_aggregates[key] = payload.model_dump()
    return {"status": "ingested", "key": key}


@app.get("/v1/macro-cohorts")
async def get_macro_cohorts(month: str) -> List[Dict[str, Any]]:
    """
    Returns regional macro-cohort summary with strict k >= 5 suppression.
    Any cell with count < 5 is suppressed to protect kirana identities.
    """
    # Group by region_type and sales_change_band
    cohorts: Dict[str, int] = {}
    for agg in _cloud_aggregates.values():
        if agg["month"] == month:
            cohort_key = f"{agg['region_type']}:{agg['sales_change_band']}"
            cohorts[cohort_key] = cohorts.get(cohort_key, 0) + 1

    results = []
    for c_key, count in cohorts.items():
        region, band = c_key.split(":")
        if count >= 5:
            results.append({
                "region_type": region,
                "sales_change_band": band,
                "shop_count": count,
                "status": "UNMASKED",
            })
        else:
            results.append({
                "region_type": region,
                "sales_change_band": band,
                "shop_count": None,
                "status": "SUPPRESSED_K_LT_5",
            })

    return results


@app.get("/healthz")
async def healthz() -> Dict[str, str]:
    return {"status": "ok"}
