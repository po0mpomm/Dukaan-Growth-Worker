"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Language, translations } from "@/lib/i18n";
import { createRun, getRunStatus } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [lang, setLang] = useState<Language>("en");
  const [month, setMonth] = useState("2026-09");
  const [salesFile, setSalesFile] = useState<File | null>(null);
  const [expensesFile, setExpensesFile] = useState<File | null>(null);
  const [udhaarFile, setUdhaarFile] = useState<File | null>(null);

  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState("");
  const [error, setError] = useState<string | null>(null);

  const t = translations[lang];

  const handleLangToggle = () => {
    setLang((prev) => (prev === "en" ? "hi" : "en"));
  };

  const pollRun = async (runId: string) => {
    try {
      const interval = setInterval(async () => {
        try {
          const status = await getRunStatus(runId);
          setProgress(status.progress_pct);
          setStatusMsg(lang === "hi" ? status.message_hi : status.message_en);

          if (status.state === "S_DONE") {
            clearInterval(interval);
            router.push(`/runs/${runId}?lang=${lang}`);
          } else if (status.state === "S_ESCALATED") {
            clearInterval(interval);
            router.push(`/runs/${runId}/escalated?lang=${lang}`);
          } else if (status.state === "S_ERROR") {
            clearInterval(interval);
            setLoading(false);
            setError(status.error_message || "Analysis failed. Please check files.");
          }
        } catch (err: any) {
          clearInterval(interval);
          setLoading(false);
          setError(err.message || "Connection error.");
        }
      }, 800);
    } catch (err: any) {
      setLoading(false);
      setError(err.message || "Failed to poll run.");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!salesFile || !expensesFile || !udhaarFile) {
      setError(lang === "hi" ? "कृपया तीनों फ़ाइलें चुनें।" : "Please select all three files.");
      return;
    }

    setLoading(true);
    setError(null);
    setProgress(5);
    setStatusMsg(t.analyzing);

    const formData = new FormData();
    formData.append("sales_file", salesFile);
    formData.append("expenses_file", expensesFile);
    formData.append("udhaar_file", udhaarFile);
    formData.append("month", month);
    formData.append("language", lang);

    try {
      const res = await createRun(formData);
      await pollRun(res.run_id);
    } catch (err: any) {
      setLoading(false);
      setError(err.message || "Failed to start analysis.");
    }
  };

  const handleLaunchScenario = async (scenario: string) => {
    setLoading(true);
    setError(null);
    setProgress(5);
    setStatusMsg(lang === "hi" ? "डेमो लोड हो रहा है..." : "Loading demo fixture...");

    try {
      const [salesBlob, expBlob, udhBlob] = await Promise.all([
        fetch(`/fixtures/${scenario}/sales.csv`).then((r) => r.blob()),
        fetch(`/fixtures/${scenario}/expenses.csv`).then((r) => r.blob()),
        fetch(`/fixtures/${scenario}/udhaar.csv`).then((r) => r.blob()),
      ]);

      const formData = new FormData();
      formData.append("sales_file", new File([salesBlob], "sales.csv", { type: "text/csv" }));
      formData.append("expenses_file", new File([expBlob], "expenses.csv", { type: "text/csv" }));
      formData.append("udhaar_file", new File([udhBlob], "udhaar.csv", { type: "text/csv" }));
      formData.append("month", "2026-09");
      formData.append("language", lang);

      const res = await createRun(formData);
      await pollRun(res.run_id);
    } catch (err: any) {
      setLoading(false);
      setError(err.message || "Failed to load demo scenario.");
    }
  };

  return (
    <div className="container">
      {/* Header */}
      <header className="header">
        <div>
          <h1 className="brand-title">🛒 {t.appTitle}</h1>
          <p className="brand-tagline">{t.tagline}</p>
        </div>
        <button
          className="lang-toggle"
          onClick={handleLangToggle}
          title="Switch Language / भाषा बदलें"
          aria-label="Switch Language"
        >
          🌐 {lang === "en" ? "हिंदी" : "English"}
        </button>
      </header>

      {/* Progress & Status during analysis */}
      {loading && (
        <div className="card" style={{ borderColor: "var(--brand-primary)" }}>
          <h2 className="card-title">⏳ {statusMsg || t.analyzing}</h2>
          <div className="progress-container">
            <div className="progress-bar" style={{ width: `${progress}%` }} />
          </div>
          <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", textAlign: "center" }}>
            {progress}% — {lang === "hi" ? "सत्यापन और गणना जारी है" : "Running deterministic validation & rules"}
          </p>
        </div>
      )}

      {/* Error alert */}
      {error && (
        <div className="card" style={{ borderColor: "var(--danger-border)", background: "var(--danger-bg)" }}>
          <h3 style={{ color: "var(--danger-text)", marginBottom: "4px" }}>⚠️ Error</h3>
          <p style={{ color: "var(--danger-text)", fontSize: "0.95rem" }}>{error}</p>
        </div>
      )}

      {/* 1-Click Demo Scenarios */}
      <section className="card">
        <h2 className="card-title">⚡ {t.demoScenarios}</h2>
        <div className="demo-grid">
          <button
            className="demo-btn"
            disabled={loading}
            onClick={() => handleLaunchScenario("healthy_shop")}
          >
            <div className="demo-btn-title">{t.demoHealthy}</div>
            <div className="demo-btn-desc">30-day complete data, balanced credit</div>
          </button>

          <button
            className="demo-btn"
            disabled={loading}
            onClick={() => handleLaunchScenario("incomplete_18days")}
          >
            <div className="demo-btn-title" style={{ color: "var(--warning-text)" }}>
              {t.demoIncomplete}
            </div>
            <div className="demo-btn-desc">Triggers S_ESCALATED failure gate safely</div>
          </button>

          <button
            className="demo-btn"
            disabled={loading}
            onClick={() => handleLaunchScenario("formula_injection")}
          >
            <div className="demo-btn-title">{t.demoFormula}</div>
            <div className="demo-btn-desc">Tests G1 formula neutralization</div>
          </button>

          <button
            className="demo-btn"
            disabled={loading}
            onClick={() => handleLaunchScenario("udhaar_imbalance")}
          >
            <div className="demo-btn-title" style={{ color: "var(--danger-text)" }}>
              {t.demoUdhaar}
            </div>
            <div className="demo-btn-desc">Fires W1 + W7 rules and aging debtor alerts</div>
          </button>
        </div>
      </section>

      {/* Custom Upload Form */}
      <section className="card">
        <h2 className="card-title">📁 {t.step1Title}</h2>
        <p style={{ fontSize: "0.95rem", color: "var(--text-muted)", marginBottom: "16px" }}>
          {t.step1Subtitle}
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">{t.monthLabel}</label>
            <input
              type="month"
              className="form-input"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">{t.salesLabel}</label>
            <input
              type="file"
              className="form-input"
              accept=".csv,.xlsx"
              onChange={(e) => setSalesFile(e.target.files?.[0] || null)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">{t.expensesLabel}</label>
            <input
              type="file"
              className="form-input"
              accept=".csv,.xlsx"
              onChange={(e) => setExpensesFile(e.target.files?.[0] || null)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">{t.udhaarLabel}</label>
            <input
              type="file"
              className="form-input"
              accept=".csv,.xlsx"
              onChange={(e) => setUdhaarFile(e.target.files?.[0] || null)}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading}
            style={{ marginTop: "12px" }}
          >
            🚀 {loading ? t.analyzing : t.startAnalysis}
          </button>
        </form>
      </section>

      {/* Footer Navigation */}
      <footer className="footer-nav">
        <a href="/presentation" style={{ color: "var(--brand-primary)", fontWeight: 600, textDecoration: "none" }}>
          📽️ Presentation Slides
        </a>
        <a href="/eval" style={{ color: "var(--text-muted)", textDecoration: "none" }}>
          📊 Benchmark
        </a>
        <a href="/privacy" style={{ color: "var(--text-muted)", textDecoration: "none" }}>
          🔒 {t.privacyExport}
        </a>
        <a href="/audit" style={{ color: "var(--text-muted)", textDecoration: "none" }}>
          🛡️ {t.verifyAudit}
        </a>
      </footer>
    </div>
  );
}
