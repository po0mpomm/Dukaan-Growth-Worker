"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

interface Slide {
  badge: string;
  titleEn: string;
  titleHi: string;
  subtitleEn: string;
  subtitleHi: string;
  keyPointsEn: string[];
  keyPointsHi: string[];
  visualBox?: {
    tag: string;
    items: { label: string; value: string; color?: string }[];
  };
  quote?: string;
}

const SLIDES: Slide[] = [
  {
    badge: "SLIDE 1 / 8 • VISION & MISSION",
    titleEn: "Dukaan Growth Worker (दुकान ग्रोथ वर्कर)",
    titleHi: "दुकान ग्रोथ वर्कर (Dukaan Growth Worker)",
    subtitleEn: "Distribution-as-a-Service for 10M+ Kirana Micro-Entrepreneurs",
    subtitleHi: "1 करोड़+ किराना दुकानदारों के लिए डिजिटल सहायक",
    keyPointsEn: [
      "Our Mission: Empowering micro-entrepreneurs who run their community's retail backbone.",
      "Kirana stores operate with razor-thin margins (8-15%) and trapped working capital in uncollected udhaar.",
      "Traditional enterprise software is too complex; generic AI chatbots hallucinate numbers.",
      "Solution: An edge-first, deterministic AI worker that transforms messy bahi-khata spreadsheets into prioritized rupee recovery actions.",
    ],
    keyPointsHi: [
      "हमारा मिशन: समुदाय के सूक्ष्म-उद्यमियों और किराना दुकानदारों को सशक्त बनाना।",
      "किराना दुकानों में कम मार्जिन (8-15%) और फंसे हुए उधार की बड़ी समस्या होती है।",
      "पारंपरिक सॉफ्टवेयर बहुत कठिन है और सामान्य चैटबॉट गलत आंकड़े बना देते हैं।",
      "समाधान: एक लोकल-फर्स्ट, सुरक्षित AI वर्कर जो बही-खाता डेटा से सीधी कमाई और रिकवरी कराता है।",
    ],
    visualBox: {
      tag: "TARGET METRICS",
      items: [
        { label: "Target Hardware", value: "4 GB RAM Laptop / Desktop" },
        { label: "Execution Latency", value: "< 0.5s local runtime" },
        { label: "Privacy Posture", value: "Zero PII to Cloud" },
        { label: "User Interface", value: "Bilingual (Hindi / English)" },
      ],
    },
    quote: "For micro-entrepreneurs, this isn't a portfolio demo. It is tied to their daily livelihood.",
  },
  {
    badge: "SLIDE 2 / 8 • CORE PHILOSOPHY",
    titleEn: "Architectural Tenet: Strict Separation of Concerns",
    titleHi: "मूल सिद्धांत: गणना और भाषा का पूर्ण विभाजन",
    subtitleEn: "'Code computes. Rules decide. The model only phrases. The system refuses to guess.'",
    subtitleHi: "'कोड गणना करता है, नियम निर्णय लेते हैं, मॉडल केवल भाषा बनाता है, सिस्टम कभी अनुमान नहीं लगाता।'",
    keyPointsEn: [
      "Code Computes: Ingestion, completeness scoring (PRD §8.1), FIFO udhaar aging, and profit metrics run in deterministic Python.",
      "Rules Decide: W1 to W7 heuristic rules (margin erosion, dead stock, aging credit, supplier discounts) ranked strictly by rupee impact.",
      "The Model Only Phrases: Small local or remote LLMs (or deterministic fallback) are strictly restricted to linguistic tone adaptation.",
      "The System Refuses to Guess: If data is missing or ambiguous, the system halts with an honest caveat rather than generating plausible fiction.",
    ],
    keyPointsHi: [
      "कोड गणना करता है: बिक्री, खर्च, फीफो (FIFO) उधार और मार्जिन की शुद्ध गणना बिना किसी AI अनुमान के होती है।",
      "नियम निर्णय लेते हैं: W1 से W7 व्यापारिक नियम सीधे रुपये के प्रभाव (Rupee Impact) के अनुसार क्रमबद्ध होते हैं।",
      "मॉडल केवल भाषा बनाता है: AI केवल दुकानदारों के लिए सरल हिंदी/हिंग्लिश वाक्यों की रचना करता है।",
      "सिस्टम कभी तुक्का नहीं लगाता: अधूरा डेटा होने पर अनुमान लगाने के बजाय स्पष्ट चेतावनी दी जाती है।",
    ],
    visualBox: {
      tag: "PIPELINE STACK",
      items: [
        { label: "Math & Ingestion", value: "Pure Python / NumPy", color: "#166534" },
        { label: "Business Decisions", value: "Deterministic W1-W7", color: "#166534" },
        { label: "Phrasing Layer", value: "Template / Local LLM", color: "#0284c7" },
        { label: "Verification Layer", value: "G5 Factuality Enforcer", color: "#854d0e" },
      ],
    },
    quote: "A single hallucinated rupee destroys a shopkeeper's trust forever.",
  },
  {
    badge: "SLIDE 3 / 8 • THE 9-STATE ENGINE",
    titleEn: "Deterministic 9-State Finite State Machine",
    titleHi: "9-चरणीय सुरक्षित स्टेट मशीन आर्किटेक्चर",
    subtitleEn: "Auditable state lifecycle with automatic escalation & degradation",
    subtitleHi: "प्रत्येक रन का पारदर्शी और सुरक्षित नियंत्रण चक्र",
    keyPointsEn: [
      "INGEST -> AGING -> METRICS -> WEAK_AREAS -> SCORING -> PHRASING -> VERIFY_FACTS -> FINALIZE -> LOG_HASH.",
      "Fail-Safe Circuit Breaker: Strict 10-second timeout on external calls.",
      "Degradation Guarantee: If the phrasing model fails or times out, the engine gracefully falls back to deterministic zero-token template phrasing.",
      "Escalation Safety: Critical balance conservation errors or severe data corruption trigger graceful human-in-the-loop escalation.",
    ],
    keyPointsHi: [
      "डेटा लोड -> फीफो बही-खाता -> वित्तीय मेट्रिक्स -> कमजोर क्षेत्र -> प्राथमिकता -> भाषा निर्माण -> तथ्य जांच -> अंतिम रिपोर्ट।",
      "सुरक्षित टाइमआउट: किसी भी कॉल में 10 सेकंड से अधिक देरी होने पर फॉलबैक सक्रिय होता है।",
      "टेम्पलेट फॉलबैक: यदि AI मॉडल धीमा हो या अनुपलब्ध हो, तो टेम्पलेट इंजन तुरंत परिणाम देता है।",
      "गंभीर त्रुटियों पर मानवीय एस्केलेशन की पूर्ण सुविधा।",
    ],
    visualBox: {
      tag: "STATE INTEGRITY",
      items: [
        { label: "Total States", value: "9 Auditable States" },
        { label: "Fallback Latency", value: "< 2 milliseconds" },
        { label: "Integrity Verification", value: "Balance Conservation Test" },
        { label: "State Isolation", value: "Pure Stateless Functions" },
      ],
    },
  },
  {
    badge: "SLIDE 4 / 8 • GUARDRAIL SUITE (G1 - G9)",
    titleEn: "G1–G9 Guardrails & G5 Factuality Verifier",
    titleHi: "G1 से G9 गार्डरेल्स और G5 तथ्य सत्यापन",
    subtitleEn: "Mathematical impossibility of hallucinatory numbers reaching the shopkeeper",
    subtitleHi: "दुकानदार तक केवल 100% सत्य और सत्यापित संख्याएं पहुंचना अनिवार्य",
    keyPointsEn: [
      "G1 Ingestion Sanitizer: Formula injection neutralization (=, @, +, - escaped).",
      "G2/G3 Input & Output Filters: Strict PII screening and length caps.",
      "G5 Mathematical Factuality Verifier: Converts Devanagari numerals (०-९) to ASCII, tokenizes all numbers in output, and checks strict set containment against computed evidence.",
      "Zero-Tolerance Fallback: Any hallucinated number triggers immediate rejection and switches output to verified template phrasing.",
    ],
    keyPointsHi: [
      "G1 फॉर्मूला सैनिटाइजर: एक्सेल या CSV फॉर्मूला इंजेक्शन हमलों की रोकथाम।",
      "G2/G3 सुरक्षा: व्यक्तिगत जानकारी (PII) का पूर्ण फ़िल्टरिंग।",
      "G5 मैथेमेटिकल वेरिफ़ायर: हिंदी अंकों (०-९) को सामान्य कर सभी संख्याओं की जांच करता है।",
      "शून्य त्रुटि नीति: यदि AI कोई भी अपुष्ट संख्या जोड़ता है, तो उसे तुरंत निरस्त कर सुरक्षित टेम्पलेट दिखाया जाता है।",
    ],
    visualBox: {
      tag: "GUARDRAIL CHECKS",
      items: [
        { label: "G1 Formula Defense", value: "Active Sanitization" },
        { label: "G5 Fact Verifier", value: "Set-Containment Math" },
        { label: "Devanagari Normalization", value: "Supported (०-९ to 0-9)" },
        { label: "Hallucination Defense", value: "Automated Template Reset" },
      ],
    },
    quote: "Every number in the UI has an audit trail back to an exact transaction row.",
  },
  {
    badge: "SLIDE 5 / 8 • DPDP ACT PRIVACY",
    titleEn: "India DPDP Act Compliant Privacy Architecture",
    titleHi: "भारत DPDP अधिनियम के अनुरूप गोपनीयता",
    subtitleEn: "Edge-First processing with mathematical differential privacy",
    subtitleHi: "लोकल-फर्स्ट आर्किटेक्चर और गणितीय अंतर-गोपनीयता (Differential Privacy)",
    keyPointsEn: [
      "Local Isolation: Customer ledger, phone numbers, and daily transactions remain solely in local SQLite on device.",
      "SHA-256 Pseudonymization: Customer identifiers hashed locally with per-shop salt.",
      "Interval Banding: Rupee amounts and counts are categorized into coarse brackets (e.g., ₹20k-50k, 10-25 transactions).",
      "Cloud Plane k >= 5 Suppression: Multi-shop benchmark view suppresses any segment with fewer than 5 contributing shops to prevent reverse inference.",
    ],
    keyPointsHi: [
      "लोकल आइसोलेशन: ग्राहकों का फोन नंबर, नाम और लेनदेन सिर्फ दुकानदार के कंप्यूटर पर रहता है।",
      "SHA-256 सीडेड हैशिंग: ग्राहक की पहचान पूरी तरह कोडित रहती है।",
      "ब्रैकेटेड बैंडिंग: सटीक आंकड़ों के बजाय सुरक्षित रेंज (जैसे ₹20k-₹50k) साझा होती है।",
      "क्लाउड k >= 5 सप्रेशन: कम से कम 5 दुकानों का समूह होने पर ही तुलनात्मक रिपोर्ट बनती है।",
    ],
    visualBox: {
      tag: "PRIVACY CONTROLS",
      items: [
        { label: "Customer Names Uploaded", value: "0% (Zero)" },
        { label: "Phone Numbers Uploaded", value: "0% (Zero)" },
        { label: "k-Anonymity Threshold", value: "k >= 5 Shops" },
        { label: "Regulatory Standard", value: "India DPDP Act 2023" },
      ],
    },
  },
  {
    badge: "SLIDE 6 / 8 • RIGOROUS EVALUATION",
    titleEn: "Automated Evaluation Harness & Benchmark",
    titleHi: "स्वचालित मूल्यांकन और बेंचमार्क सुइट",
    subtitleEn: "100% pass rate across 4 distinct edge cases in 0.28 seconds",
    subtitleHi: "4 जटिल परिदृश्यों में 100% सफलता (मात्र 0.28 सेकंड में)",
    keyPointsEn: [
      "Scenario 1 (Clean Healthy Shop): Passes all metrics, detects high-performing revenue, verifies W4 rule.",
      "Scenario 2 (Data Loss / High Gap): Detects missing days, sets completeness < 70%, forces caveat banner (G9).",
      "Scenario 3 (High Margin Decay): Flags W2 margin erosion, recommends supplier renegotiation.",
      "Scenario 4 (High Udhaar Crisis): Calculates 60+ day aging balance, prioritizes top debtor with recovery action.",
      "Cryptographic Audit Trail: SHA-256 hash-chained log verifier guarantees tamper detection.",
    ],
    keyPointsHi: [
      "परिदृश्य 1 (स्वस्थ दुकान): सभी मेट्रिक्स सही, कोई चेतावनी नहीं, उच्च बिक्री।",
      "परिदृश्य 2 (अधूरा डेटा): 70% से कम पूर्णता पर तुरंत चेतावनी बैनर प्रदर्शित।",
      "परिदृश्य 3 (मार्जिन संकट): घटते मुनाफे की पहचान और सप्लायर से बातचीत की सलाह।",
      "परिदृश्य 4 (उधार संकट): 60 दिन से पुराने बकायेदारों की पहचान और रिकवरी एक्शन।",
      "SHA-256 हैश-चेन ऑडिट लॉग: किसी भी रिकॉर्ड में बदलाव तुरंत पकड़ा जाता है।",
    ],
    visualBox: {
      tag: "BENCHMARK STATS",
      items: [
        { label: "Test Scenarios", value: "4 Scenarios" },
        { label: "Harness Runtime", value: "0.28 seconds" },
        { label: "Verification Pass Rate", value: "100% (4/4 Passed)" },
        { label: "Audit Hash Chaining", value: "SHA-256 Verified" },
      ],
    },
  },
  {
    badge: "SLIDE 7 / 8 • KIRANA-FIRST UX",
    titleEn: "Human-Centered Kirana Experience",
    titleHi: "दुकानदार-केंद्रित सरल और प्रभावी इंटरफ़ेस",
    subtitleEn: "Mobile-responsive, bilingual, and actionable in 1 click",
    subtitleHi: "मोबाइल फ्रेंडली, हिंदी/अंग्रेजी और 1-क्लिक समाधान",
    keyPointsEn: [
      "Bilingual Toggle: Instant switch between conversational Hindi and English with zero page reload.",
      "Rule Ranking by Rupee Impact: Actions show exactly how much money can be saved or collected.",
      "1-Click WhatsApp Draft: Formats a polite, culturally respectful collection reminder with pre-filled balance.",
      "Printable Physical Report: Clean one-page printable format for offline reviews or field staff.",
    ],
    keyPointsHi: [
      "द्विभाषी टॉगल: हिंदी और अंग्रेजी के बीच तुरंत बदलाव बिना पेज रीलोड किए।",
      "रुपये के प्रभाव अनुसार क्रम: दुकानदार तुरंत देखता है कि किस काम से सबसे ज्यादा बचत होगी।",
      "1-क्लिक व्हाट्सएप ड्राफ्ट: सम्मानजनक भाषा में ग्राहक को बकाया याद दिलाने का मैसेज।",
      "प्रिंट और PDF सुविधा: दुकान या फील्ड एजेंट के लिए साफ सुथरा 1-पेज का फिजिकल प्रिंटआउट।",
    ],
    visualBox: {
      tag: "UX FEATURES",
      items: [
        { label: "WhatsApp Deep Link", value: "wa.me/?text=..." },
        { label: "Printable CSS", value: "1-Page PDF / Paper" },
        { label: "Action Checkboxes", value: "Persistent State Tracking" },
        { label: "Mobile First", value: "Responsive on 360px+ screens" },
      ],
    },
  },
  {
    badge: "SLIDE 8 / 8 • DEPLOYMENT & ROADMAP",
    titleEn: "Production Architecture & Forward-Deployed Rollout",
    titleHi: "उत्पादन तत्परता और भविष्य की रूपरेखा",
    subtitleEn: "Containerized, CI-verified, and ready for forward deployment",
    subtitleHi: "कंटेनरयुक्त, निरंतर परीक्षण (CI) और फील्ड में लागू करने हेतु तैयार",
    keyPointsEn: [
      "Docker Compose: Single command local deployment with health checks.",
      "GitHub Actions CI: Fully automated test pipeline running backend tests, cloud suppression tests, eval suite, and Next.js build.",
      "Fleet Simulator: Generates realistic 50-100 store networks to evaluate regional distribution trends.",
      "Progressive Web App: Offline-capable PWA manifest with mobile installability.",
      "Forward-Deployed Ready: Can be installed on a low-cost Android tablet or budget laptop in under 3 minutes.",
    ],
    keyPointsHi: [
      "डॉकर कम्पोज़ (Docker Compose): एक कमांड में संपूर्ण सिस्टम चालू।",
      "गिटहब सीआई (GitHub CI): बैकएंड, क्लाउड और फ्रंटएंड का स्वचालित निरंतर परीक्षण।",
      "फ्लीट सिम्युलेटर: 50-100 दुकानों के नेटवर्क पर वितरण रुझानों का विश्लेषण।",
      "ऑफ़लाइन PWA: दुकान में इंटरनेट कमजोर होने पर भी काम करने में सक्षम।",
      "फील्ड में लागू होने हेतु तैयार: 4GB रैम वाले किसी भी साधारण कंप्यूटर पर तुरंत चालू।",
    ],
    visualBox: {
      tag: "DELIVERABLE ASSETS",
      items: [
        { label: "GitHub CI Pipeline", value: ".github/workflows/ci.yml" },
        { label: "Evaluation Suite", value: "eval/runner.py & history.csv" },
        { label: "Documentation Suite", value: "8 Complete Reports in /docs" },
        { label: "Demo & Walkthrough", value: "docs/DEMO_SCRIPT.md & WebP" },
      ],
    },
    quote: "Built with the discipline of a production financial core and the simplicity a kirana shopkeeper deserves.",
  },
];

export default function PresentationPage() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [lang, setLang] = useState<"en" | "hi">("en");

  const slide = SLIDES[currentSlide];

  const handleNext = () => {
    if (currentSlide < SLIDES.length - 1) {
      setCurrentSlide((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentSlide > 0) {
      setCurrentSlide((prev) => prev - 1);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
        e.preventDefault();
        setCurrentSlide((prev) => (prev < SLIDES.length - 1 ? prev + 1 : prev));
      } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
        e.preventDefault();
        setCurrentSlide((prev) => (prev > 0 ? prev - 1 : prev));
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="container" style={{ maxWidth: "860px" }}>
      {/* Top Header & Navigation */}
      <header className="header" style={{ alignItems: "center" }}>
        <div>
          <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--brand-primary)", letterSpacing: "1px" }}>
            {slide.badge}
          </span>
          <div style={{ display: "flex", gap: "8px", alignItems: "center", marginTop: "4px" }}>
            <Link href="/" className="btn btn-sm btn-secondary">
              🏠 Home
            </Link>
            <Link href="/eval" className="btn btn-sm btn-secondary">
              📊 Benchmark
            </Link>
          </div>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <button
            className="lang-toggle"
            onClick={() => setLang((prev) => (prev === "en" ? "hi" : "en"))}
          >
            🌐 {lang === "en" ? "हिंदी बुलेट्स" : "English Bullets"}
          </button>
        </div>
      </header>

      {/* Progress Bar */}
      <div
        style={{
          width: "100%",
          height: "6px",
          background: "var(--border-subtle)",
          borderRadius: "3px",
          margin: "12px 0 20px 0",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${((currentSlide + 1) / SLIDES.length) * 100}%`,
            background: "var(--brand-primary)",
            transition: "width 0.3s ease",
          }}
        />
      </div>

      {/* Slide Canvas */}
      <article
        className="card"
        style={{
          minHeight: "440px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          border: "2px solid var(--border-subtle)",
          boxShadow: "var(--shadow-md)",
          padding: "24px 28px",
        }}
      >
        <div>
          <h1
            style={{
              fontSize: "1.7rem",
              fontWeight: 800,
              lineHeight: 1.25,
              color: "var(--text-primary)",
              marginBottom: "8px",
            }}
          >
            {lang === "hi" ? slide.titleHi : slide.titleEn}
          </h1>
          <p
            style={{
              fontSize: "1.1rem",
              fontWeight: 500,
              color: "var(--brand-primary)",
              marginBottom: "20px",
            }}
          >
            {lang === "hi" ? slide.subtitleHi : slide.subtitleEn}
          </p>

          {/* Key Bullet Points */}
          <ul style={{ paddingLeft: "20px", margin: "16px 0", display: "flex", flexDirection: "column", gap: "10px" }}>
            {(lang === "hi" ? slide.keyPointsHi : slide.keyPointsEn).map((pt, i) => (
              <li
                key={i}
                style={{
                  fontSize: "1rem",
                  lineHeight: 1.5,
                  color: "var(--text-secondary)",
                }}
              >
                {pt}
              </li>
            ))}
          </ul>

          {/* Visual Highlight Box */}
          {slide.visualBox && (
            <div
              style={{
                marginTop: "20px",
                padding: "14px 16px",
                background: "var(--bg-primary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
              }}
            >
              <div
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 800,
                  letterSpacing: "1px",
                  color: "var(--text-muted)",
                  marginBottom: "8px",
                }}
              >
                {slide.visualBox.tag}
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                  gap: "10px",
                }}
              >
                {slide.visualBox.items.map((item, idx) => (
                  <div key={idx} style={{ fontSize: "0.85rem" }}>
                    <div style={{ color: "var(--text-muted)" }}>{item.label}</div>
                    <div
                      style={{
                        fontWeight: 700,
                        color: item.color || "var(--text-primary)",
                        marginTop: "2px",
                      }}
                    >
                      {item.value}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quote Block if present */}
          {slide.quote && (
            <div
              style={{
                marginTop: "16px",
                padding: "10px 14px",
                borderLeft: "4px solid var(--brand-primary)",
                background: "var(--brand-light)",
                fontStyle: "italic",
                fontSize: "0.95rem",
                color: "var(--text-primary)",
              }}
            >
              "{slide.quote}"
            </div>
          )}
        </div>

        {/* Slide Controls & Dots */}
        <div
          style={{
            marginTop: "24px",
            paddingTop: "16px",
            borderTop: "1px solid var(--border-subtle)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <button
            className="btn btn-secondary btn-sm"
            onClick={handlePrev}
            disabled={currentSlide === 0}
          >
            ← Previous
          </button>

          {/* Indicator dots */}
          <div style={{ display: "flex", gap: "6px" }}>
            {SLIDES.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentSlide(idx)}
                style={{
                  width: idx === currentSlide ? "22px" : "10px",
                  height: "10px",
                  borderRadius: "5px",
                  border: "none",
                  cursor: "pointer",
                  background: idx === currentSlide ? "var(--brand-primary)" : "var(--border-subtle)",
                  transition: "all 0.2s ease",
                }}
                aria-label={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>

          <button
            className="btn btn-primary btn-sm"
            onClick={handleNext}
            disabled={currentSlide === SLIDES.length - 1}
          >
            Next →
          </button>
        </div>
      </article>

      {/* Instructions footer */}
      <footer style={{ marginTop: "16px", textAlign: "center", fontSize: "0.85rem", color: "var(--text-muted)" }}>
        ⌨️ Use <strong>Left / Right Arrow Keys</strong> or <strong>Spacebar</strong> to navigate slides.
      </footer>
    </div>
  );
}
