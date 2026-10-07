"""
Deterministic Phrasing Templates (PRD §10, TRD §2.1)

The small model ONLY phrases. In offline / fallback mode, deterministic
reviewed templates are used directly. Every variable is guaranteed fact-checked.
"""

from typing import Dict, Any, List

TEMPLATES_EN = {
    "W1": {
        "title": "Low Working Capital / High Credit Lockup",
        "detail": "₹{uncollected_udhaar} is locked in customer credit across {credit_customer_count} customers. This represents {credit_ratio:.1f}% of total monthly revenue, constraining stock replenishment.",
        "action": "Offer a 2% spot-payment discount to top 5 credit customers this weekend.",
        "first_step": "Review your top credit customer balances before Saturday morning."
    },
    "W2": {
        "title": "Stagnant Inventory / Slow Moving Stock",
        "detail": "Slow-moving items in categories '{slow_categories}' generated only ₹{slow_revenue} in sales against estimated stock value of ₹{slow_stock}.",
        "action": "Bundle slow-moving items with high-velocity staples at a ₹5 combo discount.",
        "first_step": "Place combo display counter near the checkout counter by Friday."
    },
    "W3": {
        "title": "Customer Inactivity / Churn Alert",
        "detail": "{inactive_customer_count} regular customers who visited last month did not make any purchases this month.",
        "action": "Send personalized 'we missed you' WhatsApp check-ins with this week's fresh arrivals list.",
        "first_step": "Copy the draft reminder below and message the top 5 inactive customers."
    },
    "W4": {
        "title": "Expense Spike / Margin Compression",
        "detail": "Total monthly operating expenses rose to ₹{monthly_expense}, exceeding the baseline target by {expense_growth:.1f}%.",
        "action": "Audit electricity and transport expenses for unbilled vendor variations.",
        "first_step": "Compare last month's utility bills against current ledger entries."
    },
    "W5": {
        "title": "High Margin Category Underperforming",
        "detail": "High-margin categories contributed only {high_margin_share:.1f}% of total sales this month.",
        "action": "Reorganize front-shelf eye-level placement to prioritize high-margin goods.",
        "first_step": "Shift premium brands to eye-level shelves tomorrow morning."
    },
    "W6": {
        "title": "Day-of-Week Revenue Slump",
        "detail": "Mid-week revenue ({slump_day}) averages ₹{slump_rev}, {slump_drop:.1f}% lower than weekend average.",
        "action": "Run a '{slump_day} Special' targeted promotion on daily essentials.",
        "first_step": "Put up a notice board special on {slump_day} morning."
    },
    "W7": {
        "title": "Credit Concentration Risk",
        "detail": "Top 3 credit debtors account for {concentration_pct:.1f}% of all uncollected credit (₹{top3_amount}).",
        "action": "Cap new credit extension for top 3 accounts until at least 50% of outstanding balance is cleared.",
        "first_step": "Politely inform the customer of store policy limit upon their next visit."
    }
}

TEMPLATES_HI = {
    "W1": {
        "title": "कम वर्किंग कैपिटल / उधार में फंसा पैसा",
        "detail": "कुल ₹{uncollected_udhaar} {credit_customer_count} ग्राहकों के पास उधार में अटका है। यह मासिक बिक्री का {credit_ratio:.1f}% है।",
        "action": "इस सप्ताहांत शीर्ष 5 उधार ग्राहकों को तुरंत भुगतान पर 2% छूट दें।",
        "first_step": "शनिवार सुबह से पहले अपने सबसे बड़े 5 उधार ग्राहकों की सूची देखें।"
    },
    "W2": {
        "title": "धीमी बिक्री वाला स्टॉक",
        "detail": "'{slow_categories}' श्रेणी का माल धीमा बिका, केवल ₹{slow_revenue} की बिक्री हुई।",
        "action": "धीमी गति वाले सामान को तेज बिकने वाले सामान के साथ कॉम्बो बनाकर बेचें।",
        "first_step": "शुक्रवार तक गल्ले के पास कॉम्बो का छोटा डिस्प्ले लगाएं।"
    },
    "W3": {
        "title": "पुराने ग्राहकों की गैर-हाजिरी",
        "detail": "{inactive_customer_count} नियमित ग्राहक जो पिछले महीने आए थे, इस महीने नहीं आए।",
        "action": "व्हाट्सएप पर 'आपकी याद आई' संदेश भेजें और नए सामान की जानकारी दें।",
        "first_step": "नीचे दिए गए ड्राफ्ट को कॉपी करें और पहले 5 ग्राहकों को भेजें।"
    },
    "W4": {
        "title": "खर्च में अप्रत्याशित बढ़ोतरी",
        "detail": "इस महीने का कुल दुकान खर्च ₹{monthly_expense} रहा, जो पिछले से {expense_growth:.1f}% अधिक है।",
        "action": "बिजली और ढुलाई के खर्चों की जांच करें।",
        "first_step": "पिछले महीने के बिलों से चालू खर्चों की तुलना करें।"
    },
    "W5": {
        "title": "ज्यादा मुनाफे वाली वस्तुओं की कम बिक्री",
        "detail": "उच्च मुनाफे वाली श्रेणियों की हिस्सेदारी कुल बिक्री में केवल {high_margin_share:.1f}% रही।",
        "action": "ज्यादा मुनाफे वाले सामान को दुकान के मुख्य काउंटर पर आगे रखें।",
        "first_step": "कल सुबह प्रीमियम सामान को आंखों के सामने वाली शेल्फ पर लगाएं।"
    },
    "W6": {
        "title": "सप्ताह के बीच में मंदी",
        "detail": "{slump_day} को औसत बिक्री ₹{slump_rev} रही, जो सप्ताहांत से {slump_drop:.1f}% कम है।",
        "action": "{slump_day} को आवश्यक वस्तुओं पर विशेष छूट दें।",
        "first_step": "{slump_day} सुबह दुकान के बाहर विशेष छूट का बोर्ड लगाएं।"
    },
    "W7": {
        "title": "उधार का बड़ा जोखिम (कुछ ही ग्राहकों पर निर्भरता)",
        "detail": "शीर्ष 3 ग्राहकों पर कुल उधार का {concentration_pct:.1f}% (₹{top3_amount}) बकाया है।",
        "action": "इन 3 खातों पर 50% बकाया जमा होने तक नया उधार रोकें।",
        "first_step": "अगली बार आने पर ग्राहक को नई दुकान नीति से अवगत कराएं।"
    }
}
