"use client";

import { useEffect, useState, use } from "react";
import { useSearchParams } from "next/navigation";
import { EscalationResult } from "@/lib/types";
import { getRunResult } from "@/lib/api";
import { Language, translations } from "@/lib/i18n";

export default function EscalatedPage({ params }: { params: Promise<{ runId: string }> }) {
  const resolvedParams = use(params);
  const runId = resolvedParams.runId;

  const searchParams = useSearchParams();
  const initialLang = (searchParams.get("lang") as Language) || "en";

  const [lang, setLang] = useState<Language>(initialLang);
  const [escalation, setEscalation] = useState<EscalationResult | null>(null);
  const [loading, setLoading] = useState(true);

  const t = translations[lang];

  useEffect(() => {
    async function load() {
      try {
        const res = await getRunResult(runId);
        if (res.escalation) {
          setEscalation(res.escalation);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [runId]);

  return (
    <div className="container">
      <header className="header">
        <div>
          <h1 className="brand-title">🛡️ {t.appTitle}</h1>
          <p className="brand-tagline">{t.escalatedTitle}</p>
        </div>
        <button
          className="lang-toggle"
          onClick={() => setLang((p) => (p === "en" ? "hi" : "en"))}
        >
          🌐 {lang === "en" ? "हिंदी" : "English"}
        </button>
      </header>

      <div
        className="card"
        style={{
          borderColor: "var(--warning-border)",
          background: "var(--warning-bg)",
          marginBottom: "24px",
        }}
      >
        <div className="badge badge-warning" style={{ marginBottom: "12px" }}>
          Safety Gate Triggered: {escalation?.reason_code || "INCOMPLETE_DATA"}
        </div>
        <h2 style={{ color: "var(--warning-text)", fontSize: "1.3rem", marginBottom: "8px" }}>
          {lang === "hi" ? escalation?.reason_hi : escalation?.reason_en}
        </h2>
        <p style={{ color: "var(--warning-text)", fontSize: "0.95rem" }}>
          {t.escalatedSubtitle}
        </p>
      </div>

      {escalation?.questions && escalation.questions.length > 0 && (
        <section className="card">
          <h3 className="card-title">❓ Clarifying Questions for Shop Owner</h3>
          <ul style={{ paddingLeft: "20px", marginTop: "10px" }}>
            {escalation.questions.map((q, idx) => (
              <li key={idx} style={{ marginBottom: "10px", fontSize: "1rem" }}>
                {q}
              </li>
            ))}
          </ul>
        </section>
      )}

      <footer className="footer-nav">
        <a href="/" className="btn btn-primary btn-block">
          🔄 {t.reupload}
        </a>
      </footer>
    </div>
  );
}
