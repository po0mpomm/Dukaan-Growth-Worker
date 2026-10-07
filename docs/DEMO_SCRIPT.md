# Video Demo Script & Presentation Guide (3–5 Minutes)
**Dukaan Growth Worker — Walkthrough for Eko Reviewers**

---

### Part 1: Introduction & The Problem (0:00 – 0:45)
- **Visual:** Camera on speaker, or title card showing `🛒 Dukaan Growth Worker` with mobile viewport (375px) alongside the terminal.
- **Narration:**
  > *"Hi Eko team, I'm Anvaya. For micro-entrepreneurs and kirana store owners across India, bahi-khatas and ledgers track their daily livelihood, but at month-end, working capital is often mysteriously locked in customer credit or margin leaks.*  
  > *Existing solutions give them complex dashboards they don't have time to decipher, or generic chatbots that hallucinate numbers and require endless prompting.*  
  > *We built **Dukaan Growth Worker**: a local-first, deterministic AI Worker. The architectural philosophy is simple: **Code computes. Rules decide. The model only phrases. The system refuses to guess.** Let me show you how it works."*

---

### Part 2: Normal Flow — Meena Kirana Store (0:45 – 2:00)
- **Action:** Open browser at `http://localhost:3000` (set DevTools to 375px mobile view).
- **Show UI:** Large 18px+ font, high-contrast buttons, bilingual toggle (`हिंदी / English`).
- **Action:** Click button **"1. Healthy Kirana (Meena's Shop)"**.
- **Show Real-Time Progress:**
  - Progress bar advances smoothly: `S0_RECEIVED` → `S1_VALIDATING` → `S2_ANALYZING` → `S3_PHRASING` → `S_DONE`.
- **Show Result Screen:**
  - **Verdict Banner:** Large, plain-language summary: *"Operating expenses spiked relative to sales this month; margin squeeze alert."*
  - **Top Weak Areas:** Rules W4 and W1 with exact rupee evidence (e.g. ₹17,100 expenses, ₹3,130 uncollected credit).
  - **Exactly 3 Actions:** Each with title, rationale, and immediate first step.
  - **Listen Audio Button:** Click **"🔊 Listen"** — browser reads the action aloud using offline Web Speech API in native English/Hindi accent.
  - **Action Done Toggle:** Click **"✓ Mark Done"** — instantly turns green and tracks completion.
  - **Customer Follow-ups:** Highlight top debtors with **"📱 Copy WhatsApp Draft"** button. Click to show clipboard confirmation:
    > *"Hello CUST_002, gentle reminder from shop regarding pending balance of ₹1,630..."*
    > *(Highlight: Never auto-sent without owner review!)*

---

### Part 3: Intentional Failure Demo — The Escalation Gate (2:00 – 3:00)
- **Narration:**
  > *"Now, here is what separates a true AI Worker from a prompt demo: handling incomplete data."*
- **Action:** Navigate back to Home (`/`). Click button **"2. Incomplete Data (18 Days Missing)"**.
- **Show Escalation Screen:**
  - System **refuses to guess** recommendations for missing days.
  - Completeness score is $0.566 < 0.60$, triggering safety gate `S_ESCALATED`.
  - Banner: *"Action Plan Paused: Sales for 12 days are missing."*
  - Asks at most 2 clarifying questions:
    1. *"Were these days closed, or was the data not written down?"*
    2. *"Can you add the missing sales and upload again?"*

---

### Part 4: Privacy, DPDP Compliance & Audit Trail (3:00 – 4:00)
- **Action:** Click **"🔒 Privacy & Cloud Sync"** (`/privacy`).
- **Show Zero-PII Guarantee:**
  - Customer names and phone numbers never enter the model context or leave the device.
  - Show preview of banded payload: categorical enums only (`50K_150K`, `rules_fired: ["W1"]`).
  - Show SHA-256 hash preview match before consent.
  - Show one-tap **"Erase All Local Data (DPDP)"** button.
- **Action:** Click **"🛡️ Verify Audit Chain"** (`/audit`).
  - UI recomputes cryptographic SHA-256 chain across all logged events in `audit.db`.
  - Status displays: **"Chain Intact & Verified ✓"** with Head Hash.

---

### Part 5: Evaluation Harness & Engineering Rigor (4:00 – 4:30)
- **Action:** Switch to terminal. Run:
  ```bash
  python eval/runner.py
  ```
- **Show Scorecard:**
  - 4/4 Scenarios Passed (100.0%) in **0.28 seconds**.
  - Show `eval/history.csv` tracking the 3-iteration evolution from initial failure to production reliability.
- **Closing:**
  > *"This entire system runs 100% locally on a 4 GB RAM PC, with zero cloud dependency and zero operational token cost. Thank you!"*
