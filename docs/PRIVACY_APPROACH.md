# Privacy & DPDP Act Compliance Architecture
**Dukaan Growth Worker — Privacy by Architecture**

---

## 1. Compliance with Digital Personal Data Protection (DPDP) Act, 2023 (India)

The DPDP Act mandates that processing of digital personal data must be lawful, purpose-limited, transparent, and accompanied by unambiguous user consent. For micro-entrepreneurs and kirana owners, data privacy cannot be an after-thought buried in 20-page terms of service. It must be enforceable by software architecture.

| DPDP Principle | Architectural Implementation in Dukaan Worker |
|:---|:---|
| **Purpose Limitation (§6)** | Data ingested is processed strictly for monthly review and action synthesis. |
| **Data Minimization (§6)** | Only Sales, Expenses, and Udhaar registers are accepted; personal identifiers are stripped. |
| **Informed Consent (§6)** | Cloud export requires explicit owner review of the exact JSON payload and SHA-256 hash match. |
| **Right to Correction (§12)** | Incomplete or corrupt registers are rejected at gate (`S_ESCALATED`), asking the owner to correct. |
| **Right to Erasure (§12)** | Single-tap `DELETE /v1/data` immediately purges all local databases and queues deletion markers. |
| **Security Safeguards (§8)** | Local storage is encrypted where applicable; audit logs are tamper-evident via SHA-256 chaining. |

---

## 2. The Zero-PII Architectural Boundary

```
[ PHYSICAL SHOP ]
       │  Physical Bahi-Khata / Sales Diary / Excel
       ▼
[ G1 INGESTION ENGINE ]
       │  • Strip real names ──► Assign synthetic aliases (CUST_001, CUST_002)
       │  • Strip phone numbers
       │  • Sanitize formula injections ('=, '+, '-, '@)
       ▼
[ LOCAL WAL STORES (analytics.db) ]
       │  Contains ONLY aliases and mathematical aggregates
       ▼
[ MODEL / PHRASING CONTEXT ]
       │  FindingsObject contains ONLY:
       │  - Aliases (CUST_002)
       │  - Verified financial aggregates (₹1,630)
       │  - Detected rule codes (W1, W4)
       │  NO names. NO phone numbers. NO row transactions.
       ▼
[ BROWSER RUNTIME ]
       │  WhatsApp reminder drafts are generated inside client clipboard.
       │  The server NEVER has access to the owner's WhatsApp account.
```

---

## 3. The 3-Step Consented Export Flow

Before any aggregate data leaves the shop device:
1. **POST `/v1/runs/{id}/export/preview`:**  
   The edge server converts raw metrics into coarse categorical bands (`revenue_band: 50K_150K`, `rules_fired: ["W1"]`) and computes the payload's cryptographic SHA-256 hash:
   $$\text{Hash} = \text{SHA256}(\text{JSON Payload})$$
2. **Owner Visual Review:**  
   The shopkeeper inspects the exact JSON payload and SHA-256 hash inside the Next.js UI (`/privacy`).
3. **POST `/v1/runs/{id}/export/consent`:**  
   The client submits consent along with the preview hash. The server re-computes the hash using G8 guardrails. If the hash matches identically, the payload is enqueued into `outbox.db` for idempotent cloud synchronization.

---

## 4. Cryptographic Hash-Chained Audit Trail

Every state transition, validation pass, error, and consent action is permanently logged to `audit.db` using an append-only cryptographic hash chain.

Each record $i$ computes:
$$\text{EntryHash}_i = \text{SHA256}(\text{EventID}_i \parallel \text{Timestamp}_i \parallel \text{EventType}_i \parallel \text{Details}_i \parallel \text{EntryHash}_{i-1})$$
With initial genesis hash:
$$\text{EntryHash}_0 = 0^{64}$$

### Verification Guarantee:
Any unauthorized modification, row deletion, or retroactive record injection alters all downstream entry hashes, making tampering immediately detectable upon running `/audit` or `GET /v1/audit/verify`.
