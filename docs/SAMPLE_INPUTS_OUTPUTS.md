# Sample Inputs & Outputs
**Dukaan Growth Worker — Specification Payloads**

---

### 1. Sample Inputs

#### Sales Register (`sales.csv`)
```csv
date,bill_no,customer_ref,amount,payment_mode
2026-09-01,B1001,CUST_001,450.0,CASH
2026-09-02,B1002,CUST_002,820.0,UPI
2026-09-03,B1003,CUST_003,1250.0,UDHAAR
2026-09-04,B1004,CUST_001,310.0,CASH
... 30 days total ...
```

#### Expenses Register (`expenses.csv`)
```csv
date,category,amount,payment_mode,notes
2026-09-02,STOCK,4500.0,BANK,Rice and Dal wholesale refill
2026-09-08,ELECTRICITY,1200.0,UPI,Shop meter electricity bill
2026-09-12,TRANSPORT,650.0,CASH,Tempo freight from mandi
```

#### Udhaar / Credit Register (`udhaar.csv`)
```csv
customer_ref,opening_balance,credit_taken,repaid_amount,last_payment_date
CUST_001,500.0,0.0,500.0,2026-09-20
CUST_002,1200.0,1930.0,1500.0,2026-09-25
CUST_003,800.0,1250.0,1000.0,2026-09-28
CUST_004,600.0,1150.0,800.0,2026-09-26
```

---

### 2. Sample Output: Full Verified Result (`ResultObject`)

```json
{
  "run_id": "8fa360c7-f14d-409e-b7f3-bf804c8109ad",
  "month": "2026-09",
  "language": "en",
  "completeness": {
    "score": 0.8833,
    "day_coverage": 1.0,
    "expense_coverage": 0.6667,
    "udhaar_integrity": 1.0,
    "flagged_row_ratio": 0.0,
    "block_checks_failed": [],
    "warn_checks": [],
    "outcome": "PROCEED"
  },
  "verdict_en": "Operating expenses spiked relative to sales this month; margin squeeze alert.",
  "verdict_hi": "इस महीने बिक्री की तुलना में दुकान के खर्च बढ़ गए हैं; खर्चों की समीक्षा करें।",
  "weak_areas": [
    {
      "rule_id": "W4",
      "title_en": "Operating Expenses Exceed Target Ratio",
      "title_hi": "दुकान खर्च का अनुपात अधिक",
      "rupee_impact": 17100.0,
      "rank": 1,
      "evidence": "Total expenses reached ₹17,100 (72% of monthly revenue)."
    },
    {
      "rule_id": "W1",
      "title_en": "High Working Capital Locked in Udhaar",
      "title_hi": "उधार में फंसी दुकान की वर्किंग कैपिटल",
      "rupee_impact": 3130.0,
      "rank": 2,
      "evidence": "₹3,130 is locked in unpaid customer credit (13% of monthly revenue)."
    }
  ],
  "actions": [
    {
      "n": 1,
      "title": "Expense Spike / Margin Compression",
      "description": "Audit electricity and transport expenses for unbilled vendor variations.",
      "first_step": "Compare last month's utility bills against current ledger entries.",
      "language": "en",
      "source": "template",
      "rule_id": "W4",
      "done": false
    },
    {
      "n": 2,
      "title": "Low Working Capital / High Credit Lockup",
      "description": "Offer a 2% spot-payment discount to top 5 credit customers this weekend.",
      "first_step": "Review your top credit customer balances before Saturday morning.",
      "language": "en",
      "source": "template",
      "rule_id": "W1",
      "done": false
    },
    {
      "n": 3,
      "title": "Stagnant Inventory / Slow Moving Stock",
      "description": "Bundle slow-moving items with high-velocity staples at a ₹5 combo discount.",
      "first_step": "Place combo display counter near the checkout counter by Friday.",
      "language": "en",
      "source": "template",
      "rule_id": "W2",
      "done": false
    }
  ],
  "followups": [
    {
      "rank": 1,
      "alias": "CUST_002",
      "score": 45.2,
      "reason_code": "HIGH_BALANCE",
      "reason_en": "High credit balance (₹1,630).",
      "reason_hi": "अधिक बकाया राशि (₹1,630)।",
      "outstanding_amount": 1630.0,
      "days_overdue": 15,
      "is_lapsed_regular": false
    }
  ],
  "has_caveat": false,
  "model_used": false
}
```

---

### 3. Sample Output: Banded Consented Cloud Export (`AggregateExportPayload`)

```json
{
  "schema_version": "aggregate/1.0",
  "shop_pid": "anon_8fa360c7",
  "month": "2026-09",
  "region_type": "semi_urban",
  "sales_change_band": "-5..+5",
  "credit_share_band": "10-20",
  "overdue_band": "0-10",
  "rules_fired": ["W4", "W1"],
  "completeness_band": "0.8-1.0",
  "action_completion_band": "33-66"
}
```
*Note: Contains zero customer names, zero phone numbers, and zero exact rupee values.*
