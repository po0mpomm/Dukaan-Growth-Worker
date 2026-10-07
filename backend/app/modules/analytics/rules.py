"""
W1–W7 Rules Engine (PRD §8.3, TRD §2.1)
Evaluates shop metrics against deterministic rules, ranking detected weak areas
by quantifiable rupee impact.
"""

from typing import List, Dict, Any
from app.config import Settings
from app.contracts import WeakArea


def detect_weak_areas(metrics: Dict[str, Any], settings: Settings) -> List[WeakArea]:
    """Detects and ranks weak areas (W1..W7) with rupee evidence."""
    detected: List[WeakArea] = []

    total_sales = metrics.get("total_sales", 0.0)
    uncollected_udhaar = metrics.get("uncollected_udhaar", 0.0)
    credit_ratio = metrics.get("credit_ratio", 0.0)
    total_expenses = metrics.get("total_expenses", 0.0)
    expense_ratio = metrics.get("expense_ratio", 0.0)
    slump_drop_pct = metrics.get("slump_drop_pct", 0.0)
    slump_day = metrics.get("slump_day", "Wednesday")
    top3_concentration = metrics.get("top3_concentration_pct", 0.0)
    unique_customers = metrics.get("unique_customers", 20)

    # W1: High Udhaar Lockup
    if credit_ratio >= 20.0 or uncollected_udhaar >= 5000.0:
        detected.append(
            WeakArea(
                rule_id="W1",
                title_en="High Working Capital Locked in Udhaar",
                title_hi="उधार में फंसी दुकान की वर्किंग कैपिटल",
                title="High Working Capital Locked in Udhaar",
                metrics={"uncollected_udhaar": uncollected_udhaar, "credit_ratio": credit_ratio},
                rupee_impact=float(uncollected_udhaar),
                evidence=f"₹{uncollected_udhaar:,.0f} is locked in unpaid customer credit ({credit_ratio}% of monthly revenue).",
                recommended_action="Offer a 2% spot-payment discount to top credit customers this weekend.",
                rank=1,
            )
        )

    # W7: Debtor Concentration Risk
    if top3_concentration >= 40.0 and uncollected_udhaar >= 3000.0:
        top3_impact = uncollected_udhaar * (top3_concentration / 100.0)
        detected.append(
            WeakArea(
                rule_id="W7",
                title_en="Credit Concentration Risk in Top Debtors",
                title_hi="उधार का बड़ा जोखिम (कुछ ही ग्राहकों पर निर्भरता)",
                title="Credit Concentration Risk in Top Debtors",
                metrics={"top3_concentration_pct": top3_concentration},
                rupee_impact=float(top3_impact),
                evidence=f"Top 3 debtors account for {top3_concentration}% of all outstanding credit.",
                recommended_action="Cap new credit extension for top 3 accounts until at least 50% is cleared.",
                rank=2,
            )
        )

    # W4: Expense Spike / Margin Squeeze
    if expense_ratio >= 22.0 or total_expenses >= 8000.0:
        detected.append(
            WeakArea(
                rule_id="W4",
                title_en="Operating Expenses Exceed Target Ratio",
                title_hi="दुकान खर्च का अनुपात अधिक",
                title="Operating Expenses Exceed Target Ratio",
                metrics={"total_expenses": total_expenses, "expense_ratio": expense_ratio},
                rupee_impact=float(total_expenses),
                evidence=f"Total expenses reached ₹{total_expenses:,.0f} ({expense_ratio}% of monthly revenue).",
                recommended_action="Audit electricity and transportation bills for unbilled vendor variations.",
                rank=3,
            )
        )

    # W3: Mid-Week Sales Slump
    if slump_drop_pct >= 20.0:
        detected.append(
            WeakArea(
                rule_id="W3",
                title_en=f"Mid-Week Revenue Slump on {slump_day}s",
                title_hi=f"{slump_day} को बिक्री में गिरावट",
                title=f"Mid-Week Revenue Slump on {slump_day}s",
                metrics={"slump_drop_pct": slump_drop_pct, "slump_day": slump_day},
                rupee_impact=3500.0,
                evidence=f"{slump_day} revenue averages {slump_drop_pct}% lower than weekend peaks.",
                recommended_action=f"Run a '{slump_day} Special' targeted promotion on daily essentials.",
                rank=4,
            )
        )

    # W5: Supplier Price Increase / Margin Decay (PRD §8.3)
    gross_margin_pct = metrics.get("gross_margin_pct", 25.0)
    stock_expenses = metrics.get("stock_expenses", 0.0)
    min_gross_margin = getattr(settings, "min_gross_margin_pct", 15.0)
    if gross_margin_pct < min_gross_margin and total_sales > 0 and stock_expenses > 0:
        margin_gap = max(0.0, (20.0 - gross_margin_pct) / 100.0) * total_sales
        detected.append(
            WeakArea(
                rule_id="W5",
                title_en="Supplier Margin Decay / Low Gross Margin",
                title_hi="सप्लायर लागत वृद्धि और घटता मुनाफा",
                title="Supplier Margin Decay / Low Gross Margin",
                metrics={"gross_margin_pct": gross_margin_pct, "stock_expenses": stock_expenses},
                rupee_impact=float(round(margin_gap, 2)) if margin_gap > 0 else 3200.0,
                evidence=f"Gross margin is thin at {gross_margin_pct}% (Stock purchase ₹{stock_expenses:,.0f} vs Sales ₹{total_sales:,.0f}).",
                recommended_action="Negotiate volume discounts with wholesale suppliers or review category pricing.",
                rank=5,
            )
        )

    # W6: Customer Inactivity / Footfall Drop
    min_cust = getattr(settings, "min_unique_customers", 15)
    if unique_customers < min_cust:
        detected.append(
            WeakArea(
                rule_id="W6",
                title_en="Low Customer Diversity / Footfall Drop",
                title_hi="दुकान में ग्राहकों की कम संख्या",
                title="Low Customer Diversity / Footfall Drop",
                metrics={"unique_customers": unique_customers},
                rupee_impact=4000.0,
                evidence=f"Only {unique_customers} distinct purchasing customers recorded this month.",
                recommended_action="Send personalized WhatsApp greetings to inactive regular customers.",
                rank=6,
            )
        )

    # W2: Slow-Moving Stock
    min_sales = getattr(settings, "min_monthly_sales_target", 25000.0)
    if total_sales < min_sales:
        gap = max(0.0, (min_sales + 5000.0) - total_sales)
        detected.append(
            WeakArea(
                rule_id="W2",
                title_en="Below-Average Monthly Sales Velocity",
                title_hi="धीमी बिक्री और माल का ठहराव",
                title="Below-Average Monthly Sales Velocity",
                metrics={"total_sales": total_sales},
                rupee_impact=float(gap),
                evidence=f"Total monthly revenue of ₹{total_sales:,.0f} shows room for inventory turnover improvements.",
                recommended_action="Bundle slow-moving items with high-velocity staples at a small combo discount.",
                rank=7,
            )
        )

    # DSA-1: Priority ranking via min-heap selection (heapq.nlargest)
    import heapq
    ranked = heapq.nlargest(len(detected), detected, key=lambda w: w.rupee_impact)

    # Update rank 1..N
    for i, w in enumerate(ranked):
        w.rank = i + 1

    return ranked
