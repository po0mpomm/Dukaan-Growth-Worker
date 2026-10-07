"use client";

import { useEffect, useState, use } from "react";
import { useSearchParams } from "next/navigation";
import { ResultObject, ActionItem } from "@/lib/types";
import { getRunResult, markActionDone } from "@/lib/api";
import { Language, translations } from "@/lib/i18n";

export default function RunResultPage({ params }: { params: Promise<{ runId: string }> }) {
  const resolvedParams = use(params);
  const runId = resolvedParams.runId;

  const searchParams = useSearchParams();
  const initialLang = (searchParams.get("lang") as Language) || "en";

  const [lang, setLang] = useState<Language>(initialLang);
  const [result, setResult] = useState<ResultObject | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [speakingActionId, setSpeakingActionId] = useState<number | null>(null);
  const [copiedCustomer, setCopiedCustomer] = useState<string | null>(null);

  const t = translations[lang];

  useEffect(() => {
    async function load() {
      try {
        const res = await getRunResult(runId);
        if (res.result) {
          setResult(res.result);
        } else {
          setError("No result found for this run.");
        }
      } catch (err: any) {
        setError(err.message || "Failed to load run result.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [runId]);

  const handleLangToggle = () => {
    setLang((prev) => (prev === "en" ? "hi" : "en"));
  };

  const handleSpeech = (actionN: number, text: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      alert("Text-to-speech not supported in this browser.");
      return;
    }

    if (speakingActionId === actionN) {
      window.speechSynthesis.cancel();
      setSpeakingActionId(null);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const targetLang = lang === "hi" ? "hi-IN" : "en-IN";
    utterance.lang = targetLang;

    // Prefer regional native voice if available
    const voices = window.speechSynthesis.getVoices();
    const regionalVoice = voices.find((v) => v.lang.startsWith(lang === "hi" ? "hi" : "en-IN"));
    if (regionalVoice) {
      utterance.voice = regionalVoice;
    }

    utterance.onend = () => setSpeakingActionId(null);
    utterance.onerror = () => setSpeakingActionId(null);

    setSpeakingActionId(actionN);
    window.speechSynthesis.speak(utterance);
  };

  const handleToggleDone = async (actionN: number) => {
    if (!result) return;
    try {
      await markActionDone(runId, actionN);
      setResult((prev) => {
        if (!prev) return prev;
        const updated = prev.actions.map((act) =>
          act.n === actionN ? { ...act, done: !act.done } : act
        );
        return { ...prev, actions: updated };
      });
    } catch (err: any) {
      console.error(err);
    }
  };

  const getDraftText = (alias: string, amount?: number) => {
    return lang === "hi"
      ? `नमस्ते ${alias} जी, दुकान से आपका पिछला बकाया ₹${amount || 0} है। कृपया इस सप्ताह हिसाब कर लें। धन्यवाद!`
      : `Hello ${alias}, gentle reminder from the shop regarding your pending balance of ₹${amount || 0}. Please clear when convenient. Thank you!`;
  };

  const handleCopyDraft = (alias: string, amount?: number) => {
    const draftText = getDraftText(alias, amount);
    navigator.clipboard.writeText(draftText);
    setCopiedCustomer(alias);
    setTimeout(() => setCopiedCustomer(null), 2500);
  };

  const handleOpenWhatsApp = (alias: string, amount?: number) => {
    const draftText = getDraftText(alias, amount);
    const url = `https://wa.me/?text=${encodeURIComponent(draftText)}`;
    window.open(url, "_blank");
  };

  if (loading) {
    return (
      <div className="container" style={{ textAlign: "center", paddingTop: "40px" }}>
        <h2>⏳ {t.analyzing}</h2>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="container" style={{ paddingTop: "40px" }}>
        <div className="card" style={{ borderColor: "var(--danger-border)" }}>
          <h2 style={{ color: "var(--danger-text)" }}>⚠️ Error</h2>
          <p>{error || "Result not found"}</p>
          <a href="/" className="btn btn-secondary" style={{ marginTop: "16px" }}>
            ← Back to Home
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      {/* Header */}
      <header className="header">
        <div>
          <h1 className="brand-title">📊 {t.appTitle}</h1>
          <p className="brand-tagline">
            {result.month} • {lang === "hi" ? "मासिक रिपोर्ट" : "Monthly Review"}
          </p>
        </div>
        <button className="lang-toggle" onClick={handleLangToggle}>
          🌐 {lang === "en" ? "हिंदी" : "English"}
        </button>
      </header>

      {/* Caveat Banner if applicable */}
      {result.has_caveat && (
        <div className="card" style={{ borderColor: "var(--warning-border)", background: "var(--warning-bg)" }}>
          <h3 style={{ color: "var(--warning-text)", marginBottom: "4px" }}>
            ⚠️ {t.caveatBannerTitle}
          </h3>
          <p style={{ color: "var(--warning-text)", fontSize: "0.95rem" }}>
            {lang === "hi" ? result.caveat_hi : result.caveat_en}
          </p>
        </div>
      )}

      {/* Section 1: Verdict */}
      <div className="verdict-banner">
        <div className="action-number">{t.verdictTitle}</div>
        <div className="verdict-text">
          {lang === "hi" ? result.verdict_hi : result.verdict_en}
        </div>
      </div>

      {/* Section 2: Weak Areas */}
      {result.weak_areas && result.weak_areas.length > 0 && (
        <section className="card">
          <h2 className="card-title">🔍 {t.weakAreasTitle}</h2>
          {result.weak_areas.map((wa, i) => (
            <div
              key={wa.rule_id || i}
              style={{
                padding: "10px 0",
                borderBottom: i < result.weak_areas.length - 1 ? "1px solid var(--border-subtle)" : "none",
              }}
            >
              <div style={{ fontWeight: 700, fontSize: "1.05rem", color: "var(--brand-primary)" }}>
                {wa.rule_id}: {lang === "hi" ? wa.title_hi : wa.title_en}
              </div>
              <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", marginTop: "4px" }}>
                {wa.evidence || "Evidence computed from ledger transactions."}
              </p>
            </div>
          ))}
        </section>
      )}

      {/* Section 3: 3 Action Items */}
      <section style={{ marginBottom: "24px" }}>
        <h2 style={{ fontSize: "1.3rem", fontWeight: 800, marginBottom: "14px" }}>
          🎯 {t.actionsTitle}
        </h2>
        {result.actions.map((act) => (
          <div
            key={act.n}
            className="action-card"
            style={{
              opacity: act.done ? 0.75 : 1,
              borderLeftColor: act.done ? "var(--success-border)" : "var(--brand-primary)",
            }}
          >
            <div className="action-header">
              <span className="action-number">
                Action {act.n} • {act.rule_id}
              </span>
              <span
                className={`badge ${act.done ? "badge-success" : "badge-warning"}`}
              >
                {act.done ? t.actionCompleted : "Pending"}
              </span>
            </div>

            <h3 className="action-title" style={{ textDecoration: act.done ? "line-through" : "none" }}>
              {act.title}
            </h3>

            <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)" }}>
              {act.description || act.why}
            </p>

            <div className="action-first-step">
              <strong>{t.firstStepLabel}</strong> {act.first_step}
            </div>

            <div className="action-actions">
              <button
                className={`btn btn-sm ${act.done ? "btn-secondary" : "btn-primary"}`}
                onClick={() => handleToggleDone(act.n)}
              >
                {act.done ? "↺ Undo" : `✓ ${t.markDone}`}
              </button>

              <button
                className="btn btn-sm btn-secondary"
                onClick={() => handleSpeech(act.n, `${act.title}. ${act.first_step}`)}
              >
                {speakingActionId === act.n ? `⏹ ${t.stopAudio}` : `🔊 ${t.readAloud}`}
              </button>
            </div>
          </div>
        ))}
      </section>

      {/* Section 4: Customer Follow-ups */}
      {result.followups && result.followups.length > 0 && (
        <section className="card">
          <h2 className="card-title">👥 {t.followupsTitle}</h2>
          {result.followups.map((f) => (
            <div key={f.alias} className="followup-card">
              <div>
                <div className="followup-alias">
                  #{f.rank} {f.alias}
                </div>
                <div className="followup-reason">
                  {lang === "hi" ? f.reason_hi : f.reason_en}
                </div>
              </div>

              <div style={{ textAlign: "right" }}>
                {f.outstanding_amount !== undefined && (
                  <div className="followup-amount">
                    ₹{f.outstanding_amount.toLocaleString("en-IN")}
                  </div>
                )}
                <div style={{ display: "flex", gap: "6px", marginTop: "6px", justifyContent: "flex-end" }}>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => handleCopyDraft(f.alias, f.outstanding_amount)}
                  >
                    {copiedCustomer === f.alias ? `✓ ${t.copied}` : `📋 ${t.copyDraft}`}
                  </button>
                  <button
                    className="btn btn-sm btn-primary"
                    title="Open WhatsApp Draft"
                    onClick={() => handleOpenWhatsApp(f.alias, f.outstanding_amount)}
                  >
                    💬 WhatsApp
                  </button>
                </div>
              </div>
            </div>
          ))}
        </section>
      )}

      {/* Section 5: Month-on-Month Growth */}
      <section className="card">
        <h2 className="card-title">📈 {t.momTitle}</h2>
        {result.comparison && result.comparison.has_prior_month ? (
          <div>
            <p>
              Sales change:{" "}
              <strong>
                {result.comparison.sales_change_pct && result.comparison.sales_change_pct > 0 ? "+" : ""}
                {result.comparison.sales_change_pct}%
              </strong>
            </p>
          </div>
        ) : (
          <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>{t.noPriorMonth}</p>
        )}
      </section>

      {/* Footer Navigation */}
      <footer className="footer-nav">
        <a href="/" className="btn btn-secondary">
          ← {t.reupload}
        </a>
        <a href="/privacy" className="btn btn-primary">
          🔒 {t.privacyExport}
        </a>
      </footer>
    </div>
  );
}
