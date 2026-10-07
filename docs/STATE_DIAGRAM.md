# Workflow State Machine Diagram
**Dukaan Growth Worker — 9-State Execution Lifecycle**

The workflow implements a finite state machine where transitions are idempotent, guarded by validation gates, and checkpointed to local SQLite storage.

```mermaid
stateDiagram-v2
    [*] --> S0_RECEIVED: Upload CSV/XLSX Files

    S0_RECEIVED --> S1_VALIDATING: Parse & Sanitize Formulas (G1)
    
    state S1_VALIDATING {
        [*] --> CheckCompleteness
        CheckCompleteness --> DayCoverageCheck: Compute Days (0..30)
        DayCoverageCheck --> ExpenseCoverageCheck: Check Categories
        ExpenseCoverageCheck --> UdhaarIntegrityCheck: Negative Balance Check
    }

    S1_VALIDATING --> S_ESCALATED: Score < 0.60 or Block Check Failed
    S1_VALIDATING --> S2_ANALYZING: Score >= 0.60 (Proceed or Caveat)

    state S2_ANALYZING {
        [*] --> FinancialMetrics: Sales, Udhaar, Expenses
        FinancialMetrics --> FIFOUdhaarAging: 0-30, 31-60, 60+ Days
        FIFOUdhaarAging --> RulesEngine: Evaluate W1..W7
        RulesEngine --> FollowUpScoring: Rank Top Customers
        FollowUpScoring --> MoMComparison: Compare with Prior Snapshot
    }

    S2_ANALYZING --> S3_PHRASING: Findings Object Created

    state S3_PHRASING {
        [*] --> SelectAdapter
        SelectAdapter --> LocalLLM: Ollama Available
        SelectAdapter --> CloudLLM: Gemini API Key Present
        SelectAdapter --> Templates: Offline Fallback
    }

    S3_PHRASING --> S4_CHECKING: Model Output Produced

    state S4_CHECKING {
        [*] --> G4_SchemaValidation: Exactly 3 Actions?
        G4_SchemaValidation --> G5_FactualityVerifier: Verify All Numbers Grounded
        G5_FactualityVerifier --> G6_ContentCheck: Professional Tone & Dignity
    }

    S4_CHECKING --> S5_REVIEW: Verified Result Object
    S4_CHECKING --> S3_PHRASING: Fallback to Template if Hallucination Detected

    state S5_REVIEW {
        [*] --> DisplayVerdict
        DisplayVerdict --> AudioReadAloud: Web Speech API
        AudioReadAloud --> ActionDoneToggle: Owner Marks Tasks
        ActionDoneToggle --> CopyWhatsAppDraft: Clipboard Reminder
    }

    S5_REVIEW --> S6_SAVING: Persist Monthly Snapshot
    S6_SAVING --> S_DONE: Ready for Next Month

    S_ESCALATED --> S0_RECEIVED: Owner Uploads Missing Data
    S2_ANALYZING --> S_ERROR: Unexpected Exception (Caught & Logged)
    S3_PHRASING --> S_ERROR: Unrecoverable Fault
```

### State Definitions & Timeout Invariants

| State | Name | Primary Responsibility | Timeout | Fallback / Escalation |
|:---|:---|:---|:---:|:---|
| **S0** | `RECEIVED` | Multipart file upload and temporary buffering | 5s | HTTP 400 Bad Request |
| **S1** | `VALIDATING` | Formula sanitization (G1) & completeness score computation | 10s | Routes to `S_ESCALATED` if score < 0.60 |
| **S2** | `ANALYZING` | Metric math, FIFO udhaar aging, W1–W7 rules, MoM comparison | 10s | Routes to `S_ERROR` if unhandled exception |
| **S3** | `PHRASING` | Converting structured findings to natural language | 15s | Auto-switches to reviewed offline templates |
| **S4** | `CHECKING` | G4 schema, G5 factuality verifier, G6 content check | 5s | Replaces text with template on any hallucination |
| **S5** | `REVIEW` | Interactive UI presentation, audio TTS, clipboard drafts | $\infty$ | User interactive state |
| **S6** | `SAVING` | Persists snapshot to `analytics.db` in WAL mode | 5s | Retries with SQLite busy handler |
| **S_DONE** | `DONE` | Successful workflow terminal state | — | Baseline available for next month |
| **S_ESCALATED** | `ESCALATED` | Safe pause state: explains data gap, asks max 2 questions | — | Owner uploads missing days |
| **S_ERROR** | `ERROR` | Unexpected fault state: no partial advice shown | — | Safe retry |
