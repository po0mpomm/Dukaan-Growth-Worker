"""
Cloud Plane k-Suppression Test (TRD §7.2, ADR 008)
Simulates 40 synthetic shops across rural and urban regions.
Proves that cohorts with count >= 5 are unmasked, while cohorts with count < 5 are suppressed.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from cloud.app.main import app, _cloud_aggregates


@pytest.mark.asyncio
async def test_k_suppression_with_40_shops():
    _cloud_aggregates.clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Cohort 1: 30 shops in rural region with FLAT growth (>= 5 -> UNMASKED)
        for i in range(30):
            payload = {
                "shop_pid": f"rural_shop_{i}",
                "month": "2026-09",
                "region_type": "rural",
                "sales_change_band": "-5..+5",
                "credit_share_band": "10-20",
                "overdue_band": "0-10",
                "rules_fired": ["W1"],
                "completeness_band": "0.8-1.0",
                "action_completion_band": "33-66",
            }
            res = await client.post("/v1/aggregates", json=payload)
            assert res.status_code == 201

        # Cohort 2: Only 3 shops in urban region with LARGE_DECLINE (< 5 -> SUPPRESSED)
        for i in range(3):
            payload = {
                "shop_pid": f"urban_shop_{i}",
                "month": "2026-09",
                "region_type": "urban",
                "sales_change_band": "<-20",
                "credit_share_band": "35-50",
                "overdue_band": ">50",
                "rules_fired": ["W1", "W7"],
                "completeness_band": "0.8-1.0",
                "action_completion_band": "0-33",
            }
            res = await client.post("/v1/aggregates", json=payload)
            assert res.status_code == 201

        # Query macro-cohorts
        cohort_res = await client.get("/v1/macro-cohorts?month=2026-09")
        assert cohort_res.status_code == 200
        data = cohort_res.json()

        rural_cohort = next(c for c in data if c["region_type"] == "rural")
        urban_cohort = next(c for c in data if c["region_type"] == "urban")

        # Rural cohort count is 30 >= 5 -> UNMASKED
        assert rural_cohort["status"] == "UNMASKED"
        assert rural_cohort["shop_count"] == 30

        # Urban cohort count is 3 < 5 -> SUPPRESSED
        assert urban_cohort["status"] == "SUPPRESSED_K_LT_5"
        assert urban_cohort["shop_count"] is None
