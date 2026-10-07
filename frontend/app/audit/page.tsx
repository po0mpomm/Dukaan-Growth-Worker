"use client";

import { useEffect, useState } from "react";
import { Language, translations } from "@/lib/i18n";
import { verifyAuditChain } from "@/lib/api";

export default function AuditPage() {
  const [lang, setLang] = useState<Language>("en");
  const [report, setReport] = useState<{
    valid: boolean;
    event_count: number;
    head_hash: string;
    tampered_at_seq?: number;
    error?: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  const t = translations[lang];

  useEffect(() => {
    async function load() {
      try {
        const res = await verifyAuditChain();
        setReport(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="container">
      <header className="header">
        <div>
          <h1 className="brand-title">🛡️ {t.verifyAudit}</h1>
          <p className="brand-tagline">SHA-256 Hash Chained Audit Trail</p>
        </div>
        <button
          className="lang-toggle"
          onClick={() => setLang((p) => (p === "en" ? "hi" : "en"))}
        >
          🌐 {lang === "en" ? "हिंदी" : "English"}
        </button>
      </header>

      {loading ? (
        <div className="card" style={{ textAlign: "center" }}>
          <h2>⏳ Verifying Cryptographic Hashes...</h2>
        </div>
      ) : report ? (
        <section
          className="card"
          style={{
            borderColor: report.valid ? "var(--success-border)" : "var(--danger-border)",
            background: report.valid ? "var(--success-bg)" : "var(--danger-bg)",
          }}
        >
          <div
            className={`badge ${report.valid ? "badge-success" : "badge-danger"}`}
            style={{ marginBottom: "12px" }}
          >
            {report.valid ? t.auditValid : t.auditInvalid}
          </div>

          <h2
            style={{
              color: report.valid ? "var(--success-text)" : "var(--danger-text)",
              marginBottom: "12px",
            }}
          >
            {report.valid ? "Audit Log Integrity Confirmed" : "Tampering Detected"}
          </h2>

          <div
            style={{
              background: "var(--bg-surface)",
              padding: "16px",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.9rem",
              lineHeight: 1.8,
              border: "1px solid var(--border-subtle)",
            }}
          >
            <p>
              <strong>Total Logged Events:</strong> {report.event_count}
            </p>
            <p style={{ wordBreak: "break-all" }}>
              <strong>Head Hash (SHA-256):</strong>{" "}
              <code>{report.head_hash}</code>
            </p>
            {report.tampered_at_seq && (
              <p style={{ color: "var(--danger-text)" }}>
                <strong>Tampered Sequence:</strong> {report.tampered_at_seq}
              </p>
            )}
          </div>
        </section>
      ) : (
        <div className="card">
          <p>Failed to retrieve audit report.</p>
        </div>
      )}

      <footer className="footer-nav">
        <a href="/" className="btn btn-secondary">
          ← Back to Home
        </a>
      </footer>
    </div>
  );
}
