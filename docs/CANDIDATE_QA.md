# Candidate Q&A: Define Before Building
**Dukaan Growth Worker — 12 Foundational Architectural Responses**  
**Author:** Anvaya Arsha | **Role:** AI / Forward-Deployed Engineer Candidate  

---

### Q1: What specific business problem does this solve, and why does an AI Worker make sense instead of a simple CRUD dashboard or a generic chatbot?
**Answer:**  
Kirana store owners track operations using physical bahi-khatas or basic spreadsheets, but lack financial analysis tools to identify why cash is tight at month-end.  
A traditional CRUD dashboard fails because it presents overwhelming tables and charts without clear action guidance, requiring analytical skills shopkeepers don't have time for.  
A generic chatbot fails because it hallucinates numbers, cannot execute deterministic FIFO aging, and requires endless conversational prompting.  
An **Agentic AI Worker** is the exact right abstraction: it takes raw ledger inputs, executes deterministic validation and business logic, and synthesizes exactly 3 prioritized, plain-language actions with first steps and follow-up drafts.

---

### Q2: Who is the target user, what is their operational reality, and what constraints does that impose on the software?
**Answer:**  
The primary persona is **Meena (Kirana Owner, Semi-Urban/Rural India)**:
- **Device:** Android smartphone connected to a shop laptop or mini-PC via local Wi-Fi, or a low-end 4 GB RAM Windows PC.
- **Connectivity:** Intermittent 2G/4G connectivity or completely offline during power/network cuts.
- **Language:** Prefers colloquial Hindi (हिंदी) or simple English.
- **Time constraint:** Has under 3 minutes between customers to review advice.
- **Constraints imposed:**
  - Zero external cloud requirement for core analysis.
  - Base font size $\ge 18\text{px}$, touch targets $\ge 48\text{px}$.
  - Offline text-to-speech audio read-aloud via Web Speech API.
  - Max memory footprint under 300 MB RAM.

---

### Q3: What is the core workflow of the worker, and how does state transition deterministically from input to output?
**Answer:**  
The worker implements a strict 9-state machine:
$$\text{S0\_RECEIVED} \to \text{S1\_VALIDATING} \to \text{S2\_ANALYZING} \to \text{S3\_PHRASING} \to \text{S4\_CHECKING} \to \text{S5\_REVIEW} \to \text{S6\_SAVING} \to \text{S\_DONE}$$
- **S0:** Intake of Sales, Expenses, and Udhaar registers (CSV/XLSX).
- **S1:** G1 formula sanitization + PRD §8.1 completeness score evaluation. If $\text{score} < 0.60$, state halts to **S_ESCALATED**.
- **S2:** Deterministic computation of financial metrics, FIFO udhaar aging, W1–W7 rules, and follow-up rankings.
- **S3:** LLM phrasing (or deterministic template generation) into structured findings.
- **S4:** G4 JSON schema validation + G5 numeric factuality verification.
- **S5 & S6:** Owner review and SQLite snapshot persistence in WAL mode.

---

### Q4: Where are the strict autonomy boundaries—what does the worker do autonomously vs. what requires human review?
**Answer:**  
- **Autonomous:**
  - Parsing and neutralizing formula injection.
  - Computing balances, ratios, aging buckets, and completeness scores.
  - Detecting weak areas and ranking follow-up priorities.
  - Rejecting hallucinated numbers via G5 and falling back to templates.
  - Generating cryptographic SHA-256 hash chains in `audit.db`.
- **Requires Explicit Human Review & Action:**
  - Sending WhatsApp messages (rendered in clipboard, never auto-dispatched).
  - Marking actions as completed.
  - Consenting to cloud aggregate sync (previewing banded JSON and matching SHA-256 hash).
  - Irreversible data erasure under DPDP.

---

### Q5: How does the system handle failures, data gaps, or corruption?
**Answer:**  
The system adheres to the core philosophy: **"The system refuses to guess."**
- **Incomplete data ($< 18$ days of sales or missing files):** Completeness score drops below 0.60, triggering `S_ESCALATED`. The owner receives a clear, honest explanation and at most 2 clarifying questions.
- **Formula injection:** Cells starting with `=,+,-,@` are automatically escaped with `'`.
- **LLM timeout or hallucination:** If an external LLM times out or introduces ungrounded numbers, the circuit breaker opens and the system falls back to deterministic reviewed templates.
- **Database tampering:** Audit logger verifies the SHA-256 hash chain on startup. Any modified row flags the exact sequence number where tampering occurred.

---

### Q6: What is the memory and persistence strategy across months?
**Answer:**  
The edge plane utilizes local SQLite stores running in WAL (Write-Ahead Logging) mode:
1. `analytics.db`: Stores monthly summary snapshots and customer activity aggregates. Enables Month-on-Month (MoM) comparison (e.g. sales change %, credit share change %, resolved rules).
2. `audit.db`: Append-only, hash-chained log of every state transition, validation outcome, and error.
3. `outbox.db`: Transactional outbox pattern for queued, consented banded payloads. Survives offline periods until network connectivity is detected.

---

### Q7: How are LLMs integrated, and what prevents token bloat and hallucination?
**Answer:**  
The LLM is treated as a **rendering adapter**, not a reasoning engine:
- The LLM never sees raw transactions, customer names, or phone numbers. It receives only a compact `FindingsObject` containing verified aggregates, aliases, and rule IDs.
- Deterministic prompt schemas enforce single-turn completion with strict JSON output schemas.
- If Ollama or Gemini are absent or disconnected, the worker operates with zero degradation using built-in, culturally vetted Hindi/English templates.

---

### Q8: What is your privacy and data protection approach, specifically regarding the Digital Personal Data Protection (DPDP) Act of India?
**Answer:**  
Privacy is achieved **by architecture, not by policy**:
1. **Zero-PII On Device:** Real customer names and phone numbers never enter the model context or log files; they are replaced with synthetic aliases (`CUST_001`).
2. **Local-First Boundary:** Raw financial data never leaves the shop device.
3. **Banded Aggregate Sync:** Cloud synchronization (when enabled by explicit owner consent) transmits only coarse categorical bands (e.g., `revenue_band: 50K_150K`, `rules_fired: ["W1"]`).
4. **k-Anonymity ($k \ge 5$):** The cloud aggregation plane suppresses any macro-cohort with fewer than 5 shops.
5. **Right to Erasure:** A single-tap `DELETE /v1/data` endpoint purges all local databases immediately.

---

### Q9: How do you verify factual grounding and prevent numerical hallucinations?
**Answer:**  
Through the **G5 Factuality Verifier**:
Every number in the generated action plan is extracted using regex (with Devanagari numerals $०..९$ normalized to ASCII $0..9$). The extracted numbers are compared against the mathematical set of verified values from the deterministic findings object. If even a single ungrounded number is present, the model's text is discarded and replaced with the deterministic template.

---

### Q10: How does the solution meet performance and resource constraints on a 4 GB RAM machine?
**Answer:**  
- **FastAPI backend:** Lightweight modular monolith using Python 3.13 stdlib and optimized libraries (~60 MB RAM).
- **Next.js frontend:** Pre-rendered static pages with minimal client JS bundles (~103 KB shared JS, ~120 MB Node server memory).
- **SQLite WAL mode:** Lightweight local storage with zero server daemon overhead (~10 MB RAM).
- **Total system memory:** ~200 MB RAM, leaving over 3.5 GB for the operating system.

---

### Q11: How do you evaluate worker quality and progress over time?
**Answer:**  
Through our automated evaluation harness (`eval/runner.py`) and historical benchmark register (`eval/history.csv`):
We measure completeness gate accuracy, G5 numeric factuality pass rate, formula neutralization rate, and latency. Each system evolution is recorded transparently to demonstrate regression prevention.

---

### Q12: What is the roadmap for future versions?
**Answer:**  
- **v2.1:** On-device voice input in regional dialects using whisper.cpp quantized models.
- **v2.2:** Optical Character Recognition (OCR) for handwritten physical ledger photo intake via edge-optimized Tesseract/PaddleOCR.
- **v2.3:** Peer-to-peer federated learning across shop clusters to benchmark regional supply pricing without sharing private ledgers.
