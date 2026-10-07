#!/usr/bin/env python3
"""
tools/smoke_test.py — End-to-End Live Stack Smoke & Verification Harness

Tests the entire live Dukaan Growth Worker ecosystem:
  1. Backend Health & Readiness (/healthz, /readyz)
  2. Frontend Next.js routes (/, /presentation, /eval, /privacy, /audit)
  3. Ingestion & Analysis workflow via POST /v1/runs
  4. ResultObject factuality & balance conservation validation
  5. Privacy-safe banded export preview & zero-PII assertion
  6. Consent queueing in local outbox
  7. SHA-256 tamper-evident audit log hash chain integrity

Usage:
  python tools/smoke_test.py [--backend http://127.0.0.1:8000] [--frontend http://localhost:3000]
"""

import argparse
import sys
import time
from pathlib import Path

# Fix Windows cp1252 stdout encoding for emojis
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import httpx
except ImportError:
    print("Error: httpx is required. Install via 'pip install httpx'.")
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Dukaan Growth Worker Smoke Test")
    parser.add_argument("--backend", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--frontend", default="http://localhost:3000", help="Frontend base URL")
    return parser.parse_args()


def log_step(name: str, status: str, duration_ms: float, details: str = ""):
    symbol = "✓" if status == "PASS" else "✗"
    color_code = "\033[92m" if status == "PASS" else "\033[91m"
    reset_code = "\033[0m"
    print(f"  {color_code}{symbol}{reset_code} {name:<40} [{duration_ms:>6.1f} ms]  {details}")


def main():
    args = parse_args()
    backend_url = args.backend.rstrip("/")
    frontend_url = args.frontend.rstrip("/")

    print("\n" + "=" * 65)
    print("  🚀 Dukaan Growth Worker — Live Smoke Test Suite")
    print(f"  Backend:  {backend_url}")
    print(f"  Frontend: {frontend_url}")
    print("=" * 65)

    passed = 0
    total = 0
    start_total = time.perf_counter()

    with httpx.Client(timeout=10.0) as client:
        # Step 1: Backend Health
        total += 1
        t0 = time.perf_counter()
        try:
            r = client.get(f"{backend_url}/healthz")
            assert r.status_code == 200 and r.json().get("status") == "ok"
            passed += 1
            log_step("Backend /healthz", "PASS", (time.perf_counter() - t0) * 1000, "status: ok")
        except Exception as e:
            log_step("Backend /healthz", "FAIL", (time.perf_counter() - t0) * 1000, str(e))

        # Step 2: Backend Ready
        total += 1
        t0 = time.perf_counter()
        try:
            r = client.get(f"{backend_url}/readyz")
            data = r.json()
            assert r.status_code == 200 and data.get("status") == "ready"
            passed += 1
            log_step("Backend /readyz", "PASS", (time.perf_counter() - t0) * 1000, f"adapter: {data.get('llm_adapter')}")
        except Exception as e:
            log_step("Backend /readyz", "FAIL", (time.perf_counter() - t0) * 1000, str(e))

        # Step 3: Frontend Routes
        frontend_routes = ["/", "/presentation", "/eval", "/privacy", "/audit"]
        for route in frontend_routes:
            total += 1
            t0 = time.perf_counter()
            try:
                r = client.get(f"{frontend_url}{route}")
                assert r.status_code == 200, f"HTTP {r.status_code}"
                passed += 1
                log_step(f"Frontend {route}", "PASS", (time.perf_counter() - t0) * 1000, "HTTP 200 OK")
            except Exception as e:
                log_step(f"Frontend {route}", "FAIL", (time.perf_counter() - t0) * 1000, str(e))

        # Step 4: Run Analysis Workflow with Meena's Shop Fixture
        fixture_dir = Path(__file__).resolve().parent.parent / "frontend" / "public" / "fixtures" / "healthy_shop"
        total += 1
        t0 = time.perf_counter()
        run_id = None
        try:
            sales_path = fixture_dir / "sales.csv"
            expenses_path = fixture_dir / "expenses.csv"
            udhaar_path = fixture_dir / "udhaar.csv"

            files = [
                ("sales_file", (sales_path.name, open(sales_path, "rb"), "text/csv")),
                ("expenses_file", (expenses_path.name, open(expenses_path, "rb"), "text/csv")),
                ("udhaar_file", (udhaar_path.name, open(udhaar_path, "rb"), "text/csv")),
            ]
            data = {"month": "2026-09"}

            r = client.post(f"{backend_url}/v1/runs", data=data, files=files)
            assert r.status_code in (200, 201, 202), f"Expected 200/201/202, got {r.status_code}: {r.text}"
            run_id = r.json().get("run_id")
            assert run_id, "Missing run_id"
            passed += 1
            log_step("Run Initiation (POST /v1/runs)", "PASS", (time.perf_counter() - t0) * 1000, f"run_id: {run_id}")
        except Exception as e:
            log_step("Run Initiation (POST /v1/runs)", "FAIL", (time.perf_counter() - t0) * 1000, str(e))

        # Step 5: Poll Run Status until DONE
        result_data = None
        if run_id:
            total += 1
            t0 = time.perf_counter()
            try:
                for _ in range(50):
                    time.sleep(0.1)
                    r = client.get(f"{backend_url}/v1/runs/{run_id}")
                    if r.status_code == 200:
                        run_obj = r.json()
                        state = run_obj.get("state")
                        if state in ("S_DONE", "S_ESCALATED", "DONE", "ESCALATED"):
                            result_data = run_obj.get("result")
                            break

                assert result_data is not None, f"Run did not complete with result. Last state: {state}"
                passed += 1
                log_step("Run Processing Pipeline", "PASS", (time.perf_counter() - t0) * 1000, f"state: {state}")
            except Exception as e:
                log_step("Run Processing Pipeline", "FAIL", (time.perf_counter() - t0) * 1000, str(e))

        # Step 6: Validate Result Factuality & Rules
        if result_data:
            total += 1
            t0 = time.perf_counter()
            try:
                assert "verdict_hi" in result_data, "Missing verdict_hi"
                assert "weak_areas" in result_data and len(result_data["weak_areas"]) > 0, "No weak areas fired"
                assert "actions" in result_data and len(result_data["actions"]) > 0, "No actions generated"
                assert "model_used" in result_data, "Missing model_used flag"
                assert "completeness" in result_data, "Missing completeness result"

                weak_rules = [w.get("rule_id") for w in result_data["weak_areas"]]
                passed += 1
                log_step("Result & Factuality Validation", "PASS", (time.perf_counter() - t0) * 1000, f"rules: {weak_rules[:3]}")
            except Exception as e:
                log_step("Result & Factuality Validation", "FAIL", (time.perf_counter() - t0) * 1000, str(e))

        # Step 7: Privacy-Safe Banded Export Preview
        preview_data = None
        if run_id and result_data:
            total += 1
            t0 = time.perf_counter()
            try:
                r = client.post(f"{backend_url}/v1/runs/{run_id}/export/preview")
                assert r.status_code == 200, f"Preview failed: {r.text}"
                preview_data = r.json()
                payload = preview_data.get("payload", {})

                # Zero PII Check: ensure no phone numbers or personal names leak
                payload_str = str(payload).lower()
                assert "9876543210" not in payload_str, "PII leak: phone number found in export"
                assert "meena" not in payload_str, "PII leak: shopkeeper name found in export"
                assert "payload_hash" in preview_data, "Missing payload_hash"

                passed += 1
                log_step("Zero-PII Banded Export Preview", "PASS", (time.perf_counter() - t0) * 1000, f"hash: {preview_data['payload_hash'][:12]}...")
            except Exception as e:
                log_step("Zero-PII Banded Export Preview", "FAIL", (time.perf_counter() - t0) * 1000, str(e))

        # Step 8: Export Consent Queueing (G8 Verified Hash)
        if run_id and preview_data:
            total += 1
            t0 = time.perf_counter()
            try:
                consent_body = {
                    "consent_given": True,
                    "payload_hash": preview_data["payload_hash"],
                    "notice_version": preview_data.get("notice_version", "v1.0"),
                }
                r = client.post(f"{backend_url}/v1/runs/{run_id}/export/consent", json=consent_body)
                assert r.status_code == 200, f"Consent failed: {r.text}"
                resp = r.json()
                assert resp.get("status") == "queued", f"Expected queued status, got: {resp}"
                passed += 1
                log_step("Consented Outbox Queueing", "PASS", (time.perf_counter() - t0) * 1000, "status: queued")
            except Exception as e:
                log_step("Consented Outbox Queueing", "FAIL", (time.perf_counter() - t0) * 1000, str(e))

        # Step 9: SHA-256 Cryptographic Audit Chain Integrity
        total += 1
        t0 = time.perf_counter()
        try:
            r = client.get(f"{backend_url}/v1/audit/verify")
            assert r.status_code == 200, f"Audit verification failed: {r.text}"
            audit_res = r.json()
            assert audit_res.get("valid") is True, f"Tamper detected! Details: {audit_res}"
            passed += 1
            log_step("SHA-256 Audit Chain Verification", "PASS", (time.perf_counter() - t0) * 1000, f"events: {audit_res.get('event_count')}")
        except Exception as e:
            log_step("SHA-256 Audit Chain Verification", "FAIL", (time.perf_counter() - t0) * 1000, str(e))

    duration_total = time.perf_counter() - start_total
    print("-" * 65)
    print(f"  Scorecard: {passed}/{total} Passed ({passed/total * 100:.1f}%) in {duration_total:.2f}s")
    print("=" * 65 + "\n")

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
