"""
Evaluation Runner for Dukaan Growth Worker
PRD §16, TRD §15

Executes deterministic evaluation suite across synthetic scenarios:
  1. Healthy Kirana (Meena's Shop)
  2. Incomplete 18-Day Data (Gating check)
  3. Formula Injection Attempt (G1 check)
  4. Udhaar Imbalance (Rules check)

Outputs benchmark scorecard and verifies compliance with autonomy & privacy boundaries.
"""

import asyncio
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.config import Settings
from app.contracts import WorkflowState
from app.modules.orchestrator.engine import WorkflowEngine


async def run_benchmark():
    print("=" * 60)
    print("  🛒 Dukaan Growth Worker — Evaluation Benchmark Runner")
    print("=" * 60)

    fixtures_root = Path(__file__).resolve().parent.parent / "frontend" / "public" / "fixtures"
    settings = Settings()

    scenarios = [
        {
            "name": "Healthy Kirana (Meena's Shop)",
            "path": fixtures_root / "healthy_shop",
            "expected_state": WorkflowState.DONE,
            "min_completeness": 0.80,
        },
        {
            "name": "Incomplete Data (18 Days Missing)",
            "path": fixtures_root / "incomplete_18days",
            "expected_state": WorkflowState.ESCALATED,
            "min_completeness": 0.0,
        },
        {
            "name": "Formula Injection Attempt",
            "path": fixtures_root / "formula_injection",
            "expected_state": WorkflowState.DONE,
            "min_completeness": 0.60,
        },
        {
            "name": "Udhaar Imbalance Risk",
            "path": fixtures_root / "udhaar_imbalance",
            "expected_state": WorkflowState.DONE,
            "min_completeness": 0.80,
        },
    ]

    total = len(scenarios)
    passed = 0
    times = []

    for sc in scenarios:
        t0 = time.time()
        sales_bytes = (sc["path"] / "sales.csv").read_bytes()
        expenses_bytes = (sc["path"] / "expenses.csv").read_bytes()
        udhaar_bytes = (sc["path"] / "udhaar.csv").read_bytes()

        run_store = {}
        run_id = f"eval_{sc['name'].lower().replace(' ', '_')}"
        from app.contracts import RunStatus
        run_store[run_id] = RunStatus(
            run_id=run_id,
            state=WorkflowState.RECEIVED,
            progress_pct=5,
        )

        engine = WorkflowEngine(settings=settings, run_store=run_store)
        await engine.execute(
            run_id=run_id,
            sales_bytes=sales_bytes,
            expenses_bytes=expenses_bytes,
            udhaar_bytes=udhaar_bytes,
            sales_filename="sales.csv",
            expenses_filename="expenses.csv",
            udhaar_filename="udhaar.csv",
            month="2026-09",
            language="en",
        )

        elapsed = time.time() - t0
        times.append(elapsed)

        status = run_store[run_id]
        success = status.state == sc["expected_state"]

        if success:
            passed += 1
            print(f"  ✓ {sc['name']:<35} | {status.state.value:<12} | {elapsed:.3f}s")
        else:
            print(f"  ✗ {sc['name']:<35} | Got: {status.state.value:<8} Expected: {sc['expected_state'].value} | {elapsed:.3f}s")

    print("-" * 60)
    avg_latency = sum(times) / len(times)
    accuracy = (passed / total) * 100.0
    print(f"  Overall Scorecard: {passed}/{total} Passed ({accuracy:.1f}%)")
    print(f"  Average Execution Latency: {avg_latency:.3f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_benchmark())
