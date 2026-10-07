# Failure Scenarios & Edge Case Handling
**Dukaan Growth Worker — Resilience & Degradation Matrix**

---

### Scenario 1: Missing Register Dates (Incomplete Ingestion)
- **Trigger:** Shopkeeper uploads sales register containing only 12 days of transactions out of a 30-day month.
- **Architectural Behavior:**
  1. `completeness.py` computes `day_coverage = 12 / 30 = 0.40`.
  2. Because $0.40 < 0.50$ (the hard block threshold), `DAY_COVERAGE_BLOCK` is added to `block_checks_failed`.
  3. Total completeness score evaluates to $0.566 < 0.60$.
  4. Workflow state machine halts transition to analysis and immediately routes to `S_ESCALATED`.
  5. The UI displays: *"I cannot give reliable advice yet. Sales for 18 days are missing."* along with clarifying questions: *"Were these days closed, or was the data not written down?"*
- **Guarantee:** The AI never invents phantom sales or gives irresponsible recommendations based on partial data.

---

### Scenario 2: Formula Injection Attack (CSV/Excel Exploits)
- **Trigger:** A file contains cells such as `=SUM(A1:A10)`, `@cmd|' /C calc'!A0`, `+1+2`, or `-500`.
- **Architectural Behavior:**
  1. `sanitizer.py` checks the first character of all string columns during parsing.
  2. If the leading character is `=,+,-,@`, it is immediately prefixed with a single quote `'` (`'=SUM(A1:A10)`).
  3. The formula cannot execute in spreadsheet viewers or internal pandas evaluators.
- **Guarantee:** 100% interception of CSV formula injection attacks before data reaches memory.

---

### Scenario 3: LLM Numerical Hallucination
- **Trigger:** A local or cloud LLM attempts to generate advice containing unverified numbers (e.g. *"You will recover ₹89,450 this week"* when verified uncollected credit is only ₹15,000).
- **Architectural Behavior:**
  1. In state `S4_CHECKING`, `g5_factuality.py` normalizes all numerals (including Devanagari $०..९$).
  2. Extracts all numeric tokens from the generated string and compares against $S_{allowed}$ from `FindingsObject`.
  3. Finding the ungrounded token `89450`, G5 rejects the model output.
  4. The engine falls back to the deterministic, human-reviewed template for rule W1: *"Offer a 2% spot-payment discount to top 5 credit customers this weekend."*
- **Guarantee:** 0% ungrounded numerical claims reach the shopkeeper.

---

### Scenario 4: External Network Outage During Cloud Sync
- **Trigger:** Shopkeeper grants consent to sync anonymous macro-aggregates, but edge device internet drops mid-transmission.
- **Architectural Behavior:**
  1. Payload is not sent directly over HTTP. Instead, `export.py` enqueues the banded payload into `outbox.db` in `QUEUED` status.
  2. The background outbox sender polls for connectivity using exponential backoff.
  3. When connectivity restores, the outbox dispatcher performs an idempotent POST to `/v1/aggregates`.
- **Guarantee:** Zero data loss, exactly-once delivery, zero blocking of edge UI.

---

### Scenario 5: Local Database Tampering or File Corruption
- **Trigger:** An unauthorized user or malicious script modifies an event row in `audit.db` to conceal a data export.
- **Architectural Behavior:**
  1. `audit.py` invokes `verify_chain(data_dir)`.
  2. The verifier recomputes SHA-256 hashes sequentially from sequence 1 to head:
     $$\text{hash}_n = \text{SHA256}(\text{event\_id} \parallel \text{timestamp} \parallel \text{event\_type} \parallel \text{details} \parallel \text{hash}_{n-1})$$
  3. The modified row produces a hash mismatch.
  4. The UI displays an alert: *"Tampering Detected ✗ at sequence #N"*, highlighting the exact sequence number that was altered.
- **Guarantee:** Immutable, tamper-evident audit record.
