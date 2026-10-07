"""
Input Schema Aliases and Enums (PRD §8.1, TRD §6)
Maps diverse Hindi and English column headers found in real kirana registers
to standardized internal column names.
"""

from typing import Dict

# English & Hindi column aliases for Sales Register
SALES_COLUMN_ALIASES: Dict[str, str] = {
    # Date
    "date": "date",
    "tareekh": "date",
    "tarikh": "date",
    "तारीख": "date",
    "दिनांक": "date",
    "day": "date",
    # Bill / Invoice
    "bill_no": "bill_no",
    "bill": "bill_no",
    "invoice": "bill_no",
    "बिल": "bill_no",
    "बिल नंबर": "bill_no",
    "receipt": "bill_no",
    # Customer
    "customer_ref": "customer_ref",
    "customer": "customer_ref",
    "cust": "customer_ref",
    "ग्राहक": "customer_ref",
    "नाम": "customer_ref",
    "phone": "customer_ref",
    # Amount
    "amount": "amount",
    "total": "amount",
    "sale": "amount",
    "बिक्री": "amount",
    "रकम": "amount",
    "मूल्य": "amount",
    # Payment mode
    "payment_mode": "payment_mode",
    "mode": "payment_mode",
    "type": "payment_mode",
    "भुगतान": "payment_mode",
    "माध्यम": "payment_mode",
}

# English & Hindi column aliases for Expenses Register
EXPENSES_COLUMN_ALIASES: Dict[str, str] = {
    "date": "date",
    "tareekh": "date",
    "तारीख": "date",
    "दिनांक": "date",
    "category": "category",
    "item": "category",
    "खर्च": "category",
    "मद": "category",
    "श्रेणी": "category",
    "amount": "amount",
    "रकम": "amount",
    "लागत": "amount",
    "payment_mode": "payment_mode",
    "भुगतान": "payment_mode",
    "notes": "notes",
    "विवरण": "notes",
}

# English & Hindi column aliases for Udhaar Register
UDHAAR_COLUMN_ALIASES: Dict[str, str] = {
    "customer_ref": "customer_ref",
    "customer": "customer_ref",
    "ग्राहक": "customer_ref",
    "नाम": "customer_ref",
    "opening_balance": "opening_balance",
    "opening": "opening_balance",
    "पुराना बाकी": "opening_balance",
    "पिछला बकाया": "opening_balance",
    "credit_taken": "credit_taken",
    "नया उधार": "credit_taken",
    "repaid_amount": "repaid_amount",
    "जमा": "repaid_amount",
    "last_payment_date": "last_payment_date",
    "अंतिम भुगतान": "last_payment_date",
}
