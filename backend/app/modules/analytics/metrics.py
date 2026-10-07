"""
Comprehensive Analytics Metrics Computation (PRD §8.2, TRD §2.1)
Computes all financial, operational, and customer metrics deterministically.
"""

from collections import defaultdict
from typing import Dict, Any, List, Tuple
import pandas as pd
from app.modules.ingest.parser import ParsedData
from app.modules.analytics.fifo_aging import compute_fifo_aging


def compute_metrics(parsed: ParsedData, month: str) -> Dict[str, Any]:
    """Computes all deterministic metrics from parsed data."""
    sales_df = parsed.sales
    expenses_df = parsed.expenses
    udhaar_df = parsed.udhaar

    # Sales metrics
    total_sales = 0.0
    cash_sales = 0.0
    upi_sales = 0.0
    udhaar_sales = 0.0
    unique_customers = 0
    day_of_week_sales: Dict[str, float] = {}
    slump_day = "Wednesday"
    slump_drop_pct = 0.0

    if not sales_df.empty:
        if "amount" in sales_df.columns:
            total_sales = float(sales_df["amount"].sum())

            if "payment_mode" in sales_df.columns:
                cash_sales = float(sales_df[sales_df["payment_mode"] == "CASH"]["amount"].sum())
                upi_sales = float(sales_df[sales_df["payment_mode"] == "UPI"]["amount"].sum())
                udhaar_sales = float(sales_df[sales_df["payment_mode"] == "UDHAAR"]["amount"].sum())

        # Accurate footfall / unique customers estimation (BUG 5)
        identified_refs = set()
        if "customer_ref" in sales_df.columns:
            for ref in sales_df["customer_ref"].dropna():
                sref = str(ref).strip()
                if sref and sref.upper() not in {"NAN", "NONE", "NULL", ""}:
                    identified_refs.add(sref)

        anon_cash_transactions = 0
        if "customer_ref" in sales_df.columns:
            anon_mask = (
                sales_df["customer_ref"].isna()
                | sales_df["customer_ref"].astype(str).str.strip().isin(["", "nan", "None", "null", "NaN"])
            )
        else:
            anon_mask = pd.Series(True, index=sales_df.index)

        anon_df = sales_df[anon_mask]
        if not anon_df.empty:
            if "bill_no" in anon_df.columns and not anon_df["bill_no"].isna().all():
                anon_cash_transactions = int(anon_df["bill_no"].dropna().nunique())
            else:
                anon_cash_transactions = len(anon_df)

        unique_customers = len(identified_refs) + anon_cash_transactions
        if unique_customers == 0 and not sales_df.empty:
            unique_customers = len(sales_df)

        # DSA-5: Single-pass accumulation with defaultdict for day-of-week averages
        if "date" in sales_df.columns and not sales_df["date"].isna().all():
            sales_df["day_name"] = sales_df["date"].dt.day_name()
            day_totals: defaultdict[str, float] = defaultdict(float)
            day_counts: defaultdict[str, int] = defaultdict(int)
            for dname, amt in zip(sales_df["day_name"], sales_df["amount"]):
                if pd.notna(dname) and pd.notna(amt):
                    day_totals[str(dname)] += float(amt)
                    day_counts[str(dname)] += 1

            day_of_week_sales = {
                d: round(day_totals[d] / day_counts[d], 2)
                for d in day_totals
                if day_counts[d] > 0
            }

            weekend_avg = (day_of_week_sales.get("Saturday", 0.0) + day_of_week_sales.get("Sunday", 0.0)) / 2.0
            if weekend_avg > 0:
                midweek = ["Tuesday", "Wednesday", "Thursday"]
                lowest_day = min(midweek, key=lambda d: day_of_week_sales.get(d, 0.0))
                lowest_val = day_of_week_sales.get(lowest_day, 0.0)
                if lowest_val < weekend_avg:
                    slump_day = lowest_day
                    slump_drop_pct = round(((weekend_avg - lowest_val) / weekend_avg) * 100.0, 1)

    # Expenses metrics
    total_expenses = 0.0
    stock_expenses = 0.0
    operating_expenses = 0.0

    if not expenses_df.empty and "amount" in expenses_df.columns:
        total_expenses = float(expenses_df["amount"].sum())
        if "category" in expenses_df.columns:
            stock_mask = expenses_df["category"].str.upper().str.contains("STOCK", na=False)
            stock_expenses = float(expenses_df[stock_mask]["amount"].sum())
            operating_expenses = total_expenses - stock_expenses
        else:
            operating_expenses = total_expenses

    # Udhaar and Aging metrics (historical month anchoring)
    aging_records = compute_fifo_aging(udhaar_df, sales_df, month=month)
    uncollected_udhaar = sum(rec.total_outstanding for rec in aging_records.values())

    # Debtors ranking
    sorted_debtors = sorted(
        aging_records.values(),
        key=lambda r: r.total_outstanding,
        reverse=True
    )
    top_debtors = [
        {
            "alias": d.alias,
            "total_outstanding": d.total_outstanding,
            "days_overdue": d.days_overdue,
            "bucket_60_plus": d.bucket_60_plus
        }
        for d in sorted_debtors[:5]
    ]

    top3_total = sum(d["total_outstanding"] for d in top_debtors[:3])
    top3_concentration_pct = (
        round((top3_total / uncollected_udhaar) * 100.0, 1) if uncollected_udhaar > 0 else 0.0
    )

    credit_ratio = (
        round((uncollected_udhaar / total_sales) * 100.0, 1) if total_sales > 0 else 0.0
    )
    expense_ratio = (
        round((total_expenses / total_sales) * 100.0, 1) if total_sales > 0 else 0.0
    )
    # Gross margin metric (PRD §8.3 W5)
    gross_margin_pct = (
        round(((total_sales - stock_expenses) / total_sales) * 100.0, 1)
        if total_sales > 0 else 0.0
    )

    return {
        "month": month,
        "total_sales": round(total_sales, 2),
        "cash_sales": round(cash_sales, 2),
        "upi_sales": round(upi_sales, 2),
        "udhaar_sales": round(udhaar_sales, 2),
        "credit_ratio": credit_ratio,
        "total_expenses": round(total_expenses, 2),
        "stock_expenses": round(stock_expenses, 2),
        "operating_expenses": round(operating_expenses, 2),
        "expense_ratio": expense_ratio,
        "gross_margin_pct": gross_margin_pct,
        "uncollected_udhaar": round(uncollected_udhaar, 2),
        "unique_customers": unique_customers,
        "day_of_week_sales": day_of_week_sales,
        "slump_day": slump_day,
        "slump_drop_pct": slump_drop_pct,
        "top_debtors": top_debtors,
        "top3_concentration_pct": top3_concentration_pct,
        "aging_records": aging_records,
    }


def build_verdict_text(weak_areas: list, metrics: dict) -> Tuple[str, str]:
    """Return (verdict_en, verdict_hi) based on detected weak areas."""
    if not weak_areas:
        return (
            "Your shop operations and cash flow look healthy this month.",
            "आपकी दुकान का परिचालन और नकद प्रवाह इस महीने पूरी तरह स्वस्थ दिख रहा है।"
        )
    top_rule = weak_areas[0].rule_id
    verdicts = {
        "W1": (
            "Your sales are steady, but too much working capital is locked in customer credit.",
            "बिक्री स्थिर है, लेकिन दुकान की पूंजी का बड़ा हिस्सा ग्राहकों के उधार में अटका हुआ है।"
        ),
        "W2": (
            "Sales have dipped below optimal targets this month; focus on moving stock.",
            "इस महीने बिक्री सामान्य से कम रही है; तेजी से माल निकालने पर ध्यान दें।"
        ),
        "W3": (
            "Mid-week sales slump detected; customer footfall needs a mid-week boost.",
            "सप्ताह के बीच में बिक्री में गिरावट देखी गई है; ग्राहकों को बुलाने के लिए पहल करें।"
        ),
        "W4": (
            "Operating expenses spiked relative to sales this month; margin squeeze alert.",
            "इस महीने बिक्री की तुलना में दुकान के खर्च बढ़ गए हैं; खर्चों की समीक्षा करें।"
        ),
        "W5": (
            "High margin categories underperformed; reposition higher margin inventory.",
            "ज्यादा मुनाफे वाले सामान की बिक्री कम रही; उन्हें आगे की शेल्फ पर रखें।"
        ),
        "W6": (
            "Several regular customers from last month did not visit this month.",
            "पिछले महीने के कई नियमित ग्राहक इस महीने दुकान पर नहीं आए।"
        ),
        "W7": (
            "Credit concentration is risky: majority of outstanding credit is with top 3 debtors.",
            "उधार का बड़ा जोखिम: अधिकांश बकाया केवल 3 बड़े ग्राहकों के पास जमा है।"
        ),
    }
    return verdicts.get(
        top_rule,
        (
            "Your shop needs attention in 3 specific areas this month.",
            "आपकी दुकान को इस महीने 3 विशिष्ट क्षेत्रों में ध्यान देने की आवश्यकता है।"
        )
    )
