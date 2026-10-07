"use client";

import { useState } from "react";
import { Language, translations } from "@/lib/i18n";
import { deleteAllData } from "@/lib/api";

export default function PrivacyPage() {
  const [lang, setLang] = useState<Language>("en");
  const [deletedMsg, setDeletedMsg] = useState<string | null>(null);

  const t = translations[lang];

  const handleDeleteAll = async () => {
    if (confirm(t.deleteConfirm)) {
      try {
        const res = await deleteAllData();
        setDeletedMsg(lang === "hi" ? res.message_hi : res.message_en);
      } catch (err: any) {
        alert("Failed to delete: " + err.message);
      }
    }
  };

  return (
    <div className="container">
      <header className="header">
        <div>
          <h1 className="brand-title">🔒 {t.privacyExport}</h1>
          <p className="brand-tagline">DPDP Act (India) Architectural Compliance</p>
        </div>
        <button
          className="lang-toggle"
          onClick={() => setLang((p) => (p === "en" ? "hi" : "en"))}
        >
          🌐 {lang === "en" ? "हिंदी" : "English"}
        </button>
      </header>

      {deletedMsg && (
        <div className="card" style={{ borderColor: "var(--success-border)", background: "var(--success-bg)" }}>
          <p style={{ color: "var(--success-text)", fontWeight: 700 }}>✓ {deletedMsg}</p>
        </div>
      )}

      <section className="card">
        <h2 className="card-title">🛡️ Zero-PII Architectural Guarantee</h2>
        <p style={{ marginBottom: "12px", fontSize: "0.95rem" }}>
          {t.privacyExplanation}
        </p>
        <ul style={{ paddingLeft: "20px", fontSize: "0.95rem", lineHeight: 1.8 }}>
          <li><strong>No Customer Names:</strong> Replaced with synthetic aliases on ingestion.</li>
          <li><strong>No Phone Numbers:</strong> WhatsApp messages are generated only in your browser clipboard for you to review and send.</li>
          <li><strong>Local-First Processing:</strong> Machine learning, rule evaluations, and calculations run entirely on your local machine.</li>
          <li><strong>Banded Exports Only:</strong> If cloud sync is authorized, only high-level categories (e.g. "Revenue 50k-150k") leave the device.</li>
        </ul>
      </section>

      <section className="card">
        <h2 className="card-title">🗑️ Right to Erasure (DPDP §12)</h2>
        <p style={{ marginBottom: "16px", fontSize: "0.95rem", color: "var(--text-secondary)" }}>
          You have the absolute right to wipe all local ledger records, monthly snapshots, and audit events at any time with a single tap.
        </p>
        <button className="btn btn-danger btn-block" onClick={handleDeleteAll}>
          ⚠️ {t.deleteData}
        </button>
      </section>

      <footer className="footer-nav">
        <a href="/" className="btn btn-secondary">
          ← Back to Home
        </a>
        <a href="/eval" className="btn btn-secondary">
          📊 Evaluation & Benchmark
        </a>
        <a href="/audit" className="btn btn-secondary">
          🛡️ {t.verifyAudit}
        </a>
      </footer>
    </div>
  );
}
