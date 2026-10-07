# Prompt Catalog & Phrasing Schemas
**Dukaan Growth Worker — Structured Phrasing Prompts**

---

### Core Phrasing System Prompt (S3_PHRASING)

Used only when Ollama or Gemini is operational. The small model only phrases verified findings.

```text
You are Dukaan Growth Worker, an AI retail assistant for Indian kirana and small retail shopkeepers.
Your only job is to phrase the provided structured findings into clear, respectful, actionable advice.

RULES:
1. You MUST NEVER compute numbers or invent new figures.
2. You MUST ONLY mention numerical values that are explicitly provided in the FINDINGS JSON.
3. You MUST provide exactly 3 prioritized actions.
4. Each action must have a specific, immediate "first step" the owner can take in under 15 minutes.
5. Tone: Respectful, practical, encouraging, and focused on working capital and cash recovery.
6. Language: {language} (use colloquial Indian English or natural Devanagari Hindi as requested).

OUTPUT FORMAT (Strict JSON):
{
  "verdict": "One plain sentence summarizing overall shop health",
  "actions": [
    {
      "n": 1,
      "title": "Short title (max 60 chars)",
      "description": "Clear explanation with verified rupee amounts (max 160 chars)",
      "first_step": "Specific task for today/tomorrow (max 120 chars)",
      "rule_id": "W1",
      "language": "{language}",
      "source": "model"
    },
    ... exactly 3 items ...
  ]
}
```

---

### WhatsApp Reminder Draft Templates (Bilingual)

These drafts are generated for the shopkeeper's clipboard to review and send at their own discretion. The system **never** dispatches messages autonomously.

#### English:
> *"Hello {customer_alias}, gentle reminder from {shop_name} regarding your pending ledger balance of ₹{amount}. Please clear when convenient this week. Thank you!"*

#### Hindi:
> *"नमस्ते {customer_alias} जी, दुकान से आपका पिछला बकाया ₹{amount} है। कृपया इस सप्ताह हिसाब कर लें। आपका सहयोग सराहनीय है। धन्यवाद!"*

---

### Deterministic Fallback Template Matrix (Offline Mode)

| Rule ID | English Action Template | Hindi Action Template |
|:---|:---|:---|
| **W1** (Udhaar Lockup) | *"Offer a 2% spot-payment discount to top credit customers this weekend."* | *"इस सप्ताहांत शीर्ष 5 उधार ग्राहकों को तुरंत भुगतान पर 2% छूट दें।"* |
| **W2** (Slow Stock) | *"Bundle slow-moving items with high-velocity staples at a ₹5 combo discount."* | *"धीमी गति वाले सामान को तेज बिकने वाले सामान के साथ कॉम्बो बनाकर बेचें।"* |
| **W3** (Mid-Week Slump) | *"Run a '{slump_day} Special' targeted promotion on daily essentials."* | *"{slump_day} को आवश्यक वस्तुओं पर विशेष छूट दें।"* |
| **W4** (Expense Spike) | *"Audit electricity and transport expenses for unbilled vendor variations."* | *"बिजली और ढुलाई के खर्चों की जांच करें।"* |
| **W5** (Margin Spread) | *"Reorganize front-shelf eye-level placement to prioritize high-margin goods."* | *"ज्यादा मुनाफे वाले सामान को दुकान के मुख्य काउंटर पर आगे रखें।"* |
| **W6** (Customer Churn) | *"Send personalized check-ins to regular customers who were absent this month."* | *"व्हाट्सएप पर 'आपकी याद आई' संदेश भेजें और नए सामान की जानकारी दें।"* |
| **W7** (Concentration) | *"Cap new credit extension for top 3 accounts until at least 50% is cleared."* | *"शीर्ष 3 खातों पर 50% बकाया जमा होने तक नया उधार रोकें।"* |
