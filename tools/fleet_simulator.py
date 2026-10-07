"""
Fleet Simulator CLI (TRD §16)
Simulates a fleet of 50-100 edge kirana workers syncing banded aggregates to the cloud plane.
Demonstrates macro-cohort aggregation and k-anonymity (k >= 5) cell suppression at scale.
"""

import argparse
import asyncio
import random
import httpx


REGIONS = ["rural", "semi_urban", "urban", "deep_rural"]
SALES_BANDS = ["<-20", "-20..-5", "-5..+5", "+5..+20", ">+20"]
CREDIT_BANDS = ["0-10", "10-20", "20-35", "35-50", ">50"]


async def simulate_fleet(cloud_url: str = "http://127.0.0.1:8001", shop_count: int = 50, month: str = "2026-09"):
    print("=" * 60)
    print(f"  🛒 Simulating Fleet of {shop_count} Kirana Shops -> {cloud_url}")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check cloud health
        try:
            health = await client.get(f"{cloud_url}/healthz")
            if health.status_code != 200:
                print(f"Cloud API returned status {health.status_code}")
                return
        except Exception as e:
            print(f"Could not connect to Cloud API at {cloud_url}: {e}")
            print("Make sure Cloud API is running (e.g. uvicorn cloud.app.main:app --port 8001)")
            return

        print(f"Connected to Cloud API. Ingesting {shop_count} banded shop payloads...")

        synced = 0
        for i in range(1, shop_count + 1):
            region = random.choices(REGIONS, weights=[40, 35, 20, 5])[0]
            # Deep rural has very few shops to demonstrate suppression (< 5)
            sales_band = random.choice(SALES_BANDS)

            payload = {
                "schema_version": "aggregate/1.0",
                "shop_pid": f"shop_{i:04d}",
                "month": month,
                "region_type": region,
                "sales_change_band": sales_band,
                "credit_share_band": random.choice(CREDIT_BANDS),
                "overdue_band": "10-25",
                "rules_fired": random.sample(["W1", "W2", "W4", "W7"], k=random.randint(1, 3)),
                "completeness_band": "0.8-1.0",
                "action_completion_band": "33-66",
            }

            res = await client.post(f"{cloud_url}/v1/aggregates", json=payload)
            if res.status_code in (200, 201):
                synced += 1

        print(f"Successfully synced {synced}/{shop_count} shop aggregates.")
        print("-" * 60)
        print("Querying Macro-Cohort Summary with k >= 5 Suppression:")

        cohort_res = await client.get(f"{cloud_url}/v1/macro-cohorts?month={month}")
        if cohort_res.status_code == 200:
            cohorts = cohort_res.json()
            print(f"{'Region':<14} | {'Sales Change':<12} | {'Shop Count':<12} | {'Status'}")
            print("-" * 55)
            for c in cohorts:
                cnt_str = str(c["shop_count"]) if c["shop_count"] is not None else "[MASKED]"
                print(f"{c['region_type']:<14} | {c['sales_change_band']:<12} | {cnt_str:<12} | {c['status']}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Fleet Simulator for Cloud Plane.")
    parser.add_argument("--url", default="http://127.0.0.1:8001", help="Cloud API Base URL")
    parser.add_argument("--shops", type=int, default=50, help="Number of shops to simulate")
    parser.add_argument("--month", default="2026-09", help="Target month (YYYY-MM)")

    args = parser.parse_args()
    asyncio.run(simulate_fleet(args.url, args.shops, args.month))


if __name__ == "__main__":
    main()
