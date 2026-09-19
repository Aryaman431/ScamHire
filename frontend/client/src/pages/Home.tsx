import { useState, useRef, useCallback } from "react";
import {
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronRight,
  CircleCheck,
  ClipboardCheck,
  FileSearch,
  FileText,
  LockKeyhole,
  Menu,
  MessageSquareText,
  ScanText,
  ShieldCheck,
  X,
  Loader2,
  Upload,
} from "lucide-react";
import { Link } from "wouter";
import PageStack from "../components/PageStack";
import { analyzeText, analyzeFile, ApiError, AnalyzeTextResponse, Indicator } from "../lib/api";

type AnalyzerMode = "upload" | "paste";
type AnalyzerState = "idle" | "uploading" | "analyzing" | "results" | "error";

function LogoMark() {
  return (
    <span className="logo-mark" aria-hidden="true">
      <span />
      <span />
      <span />
    </span>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="section-label">
      <span className="section-label-line" />
      {children}
    </p>
  );
}

function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "2-digit" });
  } catch {
    return dateString;
  }
}

function getSeverityClass(severity: string): string {
  switch (severity.toUpperCase()) {
    case "HIGH": return "finding-high";
    case "MEDIUM": return "finding-review";
    case "LOW": return "finding-low";
    default: return "finding-info";
  }
}

function AnalyzerModal({ onClose }: { onClose: () => void }) {
  const [mode, setMode] = useState<AnalyzerMode>("upload");
  const [state, setState] = useState<AnalyzerState>("idle");
  const [textInput, setTextInput] = useState("");
  const [fileInput, setFileInput] = useState<File | null>(null);
  const [result, setResult] = useState<AnalyzeTextResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resetAnalyzer = useCallback(() => {
    setState("idle");
    setTextInput("");
    setFileInput(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (textareaRef.current) textareaRef.current.value = "";
  }, []);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const allowedTypes = ["application/pdf", "image/png", "image/jpeg", "image/webp"];
      if (!allowedTypes.includes(file.type)) {
        setError("Unsupported file type. Please upload PDF, PNG, JPEG, or WebP.");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setError("File too large. Maximum size is 10 MB.");
        return;
      }
      setFileInput(file);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (mode === "upload") {
      if (!fileInput) {
        setError("Please select a file first.");
        return;
      }
      setState("uploading");
      try {
        setState("analyzing");
        const response = await analyzeFile(fileInput);
        setResult(response);
        setState("results");
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("An unexpected error occurred. Please try again.");
        }
        setState("error");
      }
    } else {
      if (!textInput.trim() || textInput.trim().length < 10) {
        setError("Please enter at least 10 characters of text to analyze.");
        return;
      }
      setState("analyzing");
      try {
        const response = await analyzeText(textInput.trim());
        setResult(response);
        setState("results");
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("An unexpected error occurred. Please try again.");
        }
        setState("error");
      }
    }
  };

  const handleRetry = () => {
    setState("idle");
    setError(null);
  };

  const handleNewAnalysis = () => {
    resetAnalyzer();
  };

  const renderButtonContent = () => {
    switch (state) {
      case "uploading":
        return (
          <>
            <Loader2 size={16} className="animate-spin" />
            Uploading…
          </>
        );
      case "analyzing":
        return (
          <>
            <Loader2 size={16} className="animate-spin" />
            Analyzing…
          </>
        );
      default:
        return (
          <>
            Analyze <ArrowRight size={16} />
          </>
        );
    }
  };

  const renderContent = () => {
    switch (state) {
      case "idle":
        return (
          <>
            <p className="modal-copy">
              Add the text or file you want to review. HireShield looks for common recruitment warning signs and gives you evidence to review.
            </p>
            <div className="mode-switch" role="tablist" aria-label="Analyzer input type">
              <button className={mode === "upload" ? "active" : ""} onClick={() => { setMode("upload"); resetAnalyzer(); }} role="tab" aria-selected={mode === "upload"}>
                Upload a file
              </button>
              <button className={mode === "paste" ? "active" : ""} onClick={() => { setMode("paste"); resetAnalyzer(); }} role="tab" aria-selected={mode === "paste"}>
                Paste text
              </button>
            </div>
            {mode === "upload" ? (
              <div className="upload-zone">
                <div className="upload-icon"><FileText size={22} /></div>
                <strong>Drop a job posting, message, or offer letter</strong>
                <span>PDF, PNG, JPEG, WebP · Up to 10 MB</span>
                <label className="button button-ghost" htmlFor="file-upload">
                  <Upload size={14} style={{ marginRight: 6 }} />
                  Choose a file
                </label>
                <input
                  id="file-upload"
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  accept=".pdf,.png,.jpg,.jpeg,.webp"
                  className="visually-hidden"
                  disabled={state !== "idle"}
                />
                {fileInput && (
                  <p className="selected-file" style={{ marginTop: 8, fontSize: 11, color: "#7c902d" }}>
                    Selected: {fileInput.name} ({(fileInput.size / 1024).toFixed(1)} KB)
                  </p>
                )}
              </div>
            ) : (
              <textarea
                ref={textareaRef}
                className="offer-textarea"
                placeholder="Paste the message or offer you want to check…"
                aria-label="Job offer text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                disabled={state !== "idle"}
              />
            )}
            <div className="privacy-note">
              <LockKeyhole size={15} />
              <span>Your document is used for this check only. Read our <Link href="/privacy">privacy policy</Link>.</span>
            </div>
            {error && (
              <div className="error-message" style={{ marginTop: 12, padding: "10px 12px", background: "rgba(245,120,75,.13)", color: "#a95032", fontSize: 11, fontFamily: "var(--mono)", textTransform: "uppercase", borderRadius: 2 }}>
                <AlertTriangle size={12} style={{ marginRight: 6, verticalAlign: "middle" }} />
                {error}
              </div>
            )}
            <button
              className="button button-primary full-width"
              onClick={handleAnalyze}
              disabled={state !== "idle" || (mode === "upload" && !fileInput) || (mode === "paste" && !textInput.trim())}
            >
              {renderButtonContent()}
            </button>
          </>
        );

      case "uploading":
        return (
          <div className="analyzing-state" style={{ textAlign: "center", padding: "40px 20px" }}>
            <Loader2 size={32} className="animate-spin" style={{ margin: "0 auto 16px", color: "var(--signal)" }} />
            <p className="modal-copy">Uploading document…</p>
          </div>
        );

      case "analyzing":
        return (
          <div className="analyzing-state" style={{ textAlign: "center", padding: "40px 20px" }}>
            <Loader2 size={32} className="animate-spin" style={{ margin: "0 auto 16px", color: "var(--signal)" }} />
            <p className="modal-copy">Analyzing for risk signals…</p>
            <p style={{ marginTop: 8, fontSize: 11, color: "var(--muted-ink)", fontFamily: "var(--mono)" }}>This usually takes a few seconds</p>
          </div>
        );

      case "error":
        return (
          <div className="error-state" style={{ textAlign: "center", padding: "20px" }}>
            <AlertTriangle size={32} style={{ marginBottom: 16, color: "var(--warning)" }} />
            <h3 style={{ marginBottom: 8, fontSize: 16 }}>Analysis failed</h3>
            <p className="modal-copy" style={{ marginBottom: 20 }}>{error}</p>
            <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
              <button className="button button-primary" onClick={handleRetry}>Try again</button>
              <button className="button button-ghost" onClick={handleNewAnalysis}>Start over</button>
            </div>
          </div>
        );

      case "results":
        if (!result) return null;
        return (
          <div className="sample-result">
            <div className="result-summary">
              <div className="result-status">
                <AlertTriangle size={17} />
                {result.risk_score >= 70 ? "High risk" : result.risk_score >= 40 ? "Review recommended" : "Low risk"}
              </div>
              <div className="risk-score">
                <span>Risk score</span>
                <strong>{result.risk_score}</strong>
                <small>/ 100</small>
              </div>
            </div>
            <p className="modal-copy">{result.summary}</p>

            {result.indicators.length > 0 && (
              <div className="indicator-list">
                {result.indicators.map((indicator: Indicator, index: number) => (
                  <div className="indicator-row" key={index}>
                    <AlertTriangle size={15} style={{ color: indicator.severity === "HIGH" ? "var(--warning)" : "var(--signal)" }} />
                    <div>
                      <strong style={{ display: "block", fontSize: 11 }}>{indicator.type.replace(/_/g, " ")}</strong>
                      <span style={{ fontSize: 10, color: "var(--muted-ink)" }}>{indicator.evidence}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {result.recommendations.length > 0 && (
              <div className="result-actions">
                {result.recommendations.map((rec, index) => (
                  <div key={index}><CircleCheck size={16} /><span>{rec}</span></div>
                ))}
              </div>
            )}

            <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
              <button className="button button-primary full-width" onClick={handleNewAnalysis} style={{ flex: 1 }}>
                Analyze another <ArrowRight size={16} />
              </button>
              <button className="button button-ghost" onClick={onClose} style={{ flex: 1 }}>Close</button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={state === "results" ? onClose : undefined}>
      <section
        className="analyzer-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="analyzer-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-head">
          <div>
            <span className="eyebrow">Private preview</span>
            <h2 id="analyzer-title">Check a job offer</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close analyzer" disabled={state === "analyzing" || state === "uploading"}>
            <X size={18} />
          </button>
        </div>

        {renderContent()}

      </section>
    </div>
  );
}

function ProductPreview({ onOpen }: { onOpen: () => void }) {
  return (
    <div className="preview-wrap">
      <div className="preview-orbit orbit-one" />
      <div className="preview-orbit orbit-two" />
      <div className="product-window tile tile-hoverable">
        <div className="window-bar">
          <div className="window-dots"><i /><i /><i /></div>
          <span>hireshield / analysis</span>
          <span className="window-lock"><LockKeyhole size={12} /> encrypted session</span>
        </div>
        <div className="analysis-header">
          <div>
            <span className="eyebrow">Offer letter · 04.18.26</span>
            <h3>Product Operations Associate</h3>
            <p>Northline Systems · forwarded email</p>
          </div>
          <div className="review-badge"><span /> Review</div>
        </div>
        <div className="score-grid">
          <div className="score-panel">
            <span className="data-label">Risk score</span>
            <div className="score-number">68<span>/100</span></div>
            <div className="meter"><span /></div>
            <div className="meter-labels"><span>Low</span><span>Review</span><span>High</span></div>
          </div>
          <div className="score-panel evidence-panel">
            <span className="data-label">Evidence found</span>
            <strong>03 <small>indicators</small></strong>
            <div className="evidence-pips"><span /><span /><span /></div>
            <button onClick={onOpen}>Open evidence <ArrowUpRight size={14} /></button>
          </div>
        </div>
        <div className="preview-divider" />
        <div className="finding-list">
          <div className="finding-row"><span className="finding-number">01</span><span className="finding-copy"><strong>Payment request</strong><small>Asks candidate to purchase equipment before start date.</small></span><span className="finding-state finding-high">High</span></div>
          <div className="finding-row"><span className="finding-number">02</span><span className="finding-copy"><strong>Sender mismatch</strong><small>Reply-to address uses a free email provider.</small></span><span className="finding-state finding-review">Review</span></div>
        </div>
        <div className="window-footer"><span><ShieldCheck size={14} /> Risk indicators, not accusations</span><button onClick={onOpen}>View full check <ChevronRight size={14} /></button></div>
      </div>
      <div className="floating-note note-top"><span className="note-dot green" /> Source checked <strong>03/03</strong></div>
      <div className="floating-note note-bottom"><span className="note-dot orange" /> Decision support, not a verdict</div>
    </div>
  );
}

export default function Home() {
  const [isAnalyzerOpen, setIsAnalyzerOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const scrollTo = (id: string) => {
    const targetMap: Record<string, number> = { "how-it-works": 1, "why-hireshield": 2, privacy: 3 };
    const target = targetMap[id];
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const finePointer = window.matchMedia("(pointer: fine)").matches;
    if (typeof target === "number" && finePointer && !reduced) {
      window.dispatchEvent(new CustomEvent<number>("page-stack:navigate", { detail: target }));
    } else {
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    }
    setMenuOpen(false);
  };

  return (
    <div className="site-shell">
      <header className="site-header landing-header">
        <a className="brand" href="#top" aria-label="HireShield home"><LogoMark /><span>Hire<span>Shield</span></span></a>
        <nav className={menuOpen ? "main-nav open" : "main-nav"} aria-label="Primary navigation">
          <button onClick={() => scrollTo("how-it-works")}>How it works</button>
          <button onClick={() => scrollTo("why-hireshield")}>Why HireShield</button>
          <Link href="/history">History</Link>
          <button onClick={() => scrollTo("privacy")}>Privacy</button>
          <Link href="/terms">Terms</Link>
          <button className="nav-cta" onClick={() => setIsAnalyzerOpen(true)}>Analyze a job <ArrowUpRight size={14} /></button>
        </nav>
        <button className="mobile-menu" onClick={() => setMenuOpen((open) => !open)} aria-label="Toggle menu" aria-expanded={menuOpen}>{menuOpen ? <X size={20} /> : <Menu size={20} />}</button>
      </header>

      <main id="top">
        <PageStack>
          <div className="hero-page">
            <div className="hero-section">
              <div className="hero-copy">
                <div className="status-line"><span className="status-pulse" /> A calmer second opinion for your next opportunity</div>
                <h1>Check a job offer <em>before</em> you trust it.</h1>
                <p className="hero-lede">Analyze job postings, recruitment messages, and offer letters for warning signs, supporting evidence, and practical next steps.</p>
                <div className="hero-actions">
                  <button className="button button-primary" onClick={() => setIsAnalyzerOpen(true)}>Analyze a job <ArrowRight size={17} /></button>
                  <button className="button button-text" onClick={() => scrollTo("how-it-works")}>See how it works <span className="button-arrow">↘</span></button>
                </div>
                <div className="trust-strip"><span><ShieldCheck size={15} /> Built for careful decisions</span><span><LockKeyhole size={15} /> Private by design</span></div>
              </div>
              <ProductPreview onOpen={() => setIsAnalyzerOpen(true)} />
            </div>

            <section className="signal-band" aria-label="What HireShield checks">
              <div className="container signal-band-inner"><span className="signal-intro">One useful check<br /><strong>before you reply.</strong></span><div className="signal-item"><span className="signal-index">01</span><FileSearch size={19} /><span>Job postings</span></div><div className="signal-item"><span className="signal-index">02</span><MessageSquareText size={19} /><span>Recruitment messages</span></div><div className="signal-item"><span className="signal-index">03</span><ClipboardCheck size={19} /><span>Offer letters</span></div></div>
            </section>
          </div>

          <section className="section light-section" id="how-it-works">
            <div className="container">
              <div className="section-intro"><div><SectionLabel>How it works</SectionLabel><h2>Clarity, in three<br /><span>quiet steps.</span></h2></div><p>Good opportunities can still arrive with confusing details. HireShield helps you slow down, see the signals, and choose your next move with more context.</p></div>
              <div className="steps-grid">
                <article className="step-card tile-hoverable"><span className="step-no">01</span><div className="step-icon"><ScanText size={21} /></div><h3>Share the details</h3><p>Upload or paste the job posting, message, or offer letter you want a second look at.</p><a onClick={() => setIsAnalyzerOpen(true)}>Start with a sample <ArrowUpRight size={14} /></a></article>
                <article className="step-card tile-hoverable"><span className="step-no">02</span><div className="step-icon"><AlertTriangle size={21} /></div><h3>Review the signals</h3><p>See specific indicators, the evidence behind them, and what still needs to be verified.</p><a onClick={() => scrollTo("why-hireshield")}>What we look for <ArrowUpRight size={14} /></a></article>
                <article className="step-card tile-hoverable"><span className="step-no">03</span><div className="step-icon"><CircleCheck size={21} /></div><h3>Choose your next move</h3><p>Use practical guidance to verify the opportunity, pause the conversation, or walk away.</p><a onClick={() => scrollTo("privacy")}>Our approach <ArrowUpRight size={14} /></a></article>
              </div>
            </div>
          </section>

          <section className="section dark-section closing-page" id="why-hireshield">
            <div className="container split-section"><div className="split-copy"><SectionLabel>Built for the moment before</SectionLabel><h2>No verdicts.<br /><span>Just better context.</span></h2><p>HireShield does not decide whether an opportunity is real. It organizes the signals worth checking so you can protect your time, money, and personal information.</p><button className="button button-light" onClick={() => setIsAnalyzerOpen(true)}>Try a sample check <ArrowRight size={16} /></button></div><div className="principles-grid"><div className="principle"><span className="principle-mark">01</span><h3>Specific over sensational</h3><p>Every finding points to a detail you can inspect, not a vague confidence score.</p></div><div className="principle"><span className="principle-mark">02</span><h3>Evidence over anxiety</h3><p>We separate what was observed from what still needs confirmation.</p></div><div className="principle"><span className="principle-mark">03</span><h3>Private by default</h3><p>Clear handling notes tell you what happens to the material you share.</p></div><div className="principle"><span className="principle-mark">04</span><h3>Human decisions stay human</h3><p>The final choice remains yours, with room for nuance and common sense.</p></div></div></div>
          </section>

          <section className="section final-page" id="privacy">
            <div className="closing-security privacy-section">
              <div className="container privacy-grid"><div><SectionLabel>Trust, made visible</SectionLabel><h2>The details matter.<br /><span>So does how we handle them.</span></h2></div><div className="privacy-copy"><div className="privacy-item"><LockKeyhole size={19} /><div><h3>Secure document handling</h3><p>Documents are used to create your analysis and are not used to build a public profile about you.</p></div></div><div className="privacy-item"><ShieldCheck size={19} /><div><h3>A measured result</h3><p>Results are risk indicators, not definitive accusations. Always verify independently before acting.</p></div></div><Link className="inline-link" href="/privacy">Read the full privacy policy <ArrowUpRight size={15} /></Link></div></div>
            </div>

            <div className="final-cta-section"><div className="container final-cta"><div><span className="eyebrow">Before you hit send</span><h2>Take a second look.</h2><p>A clear next step is worth more than a confident guess.</p></div><button className="button button-primary" onClick={() => setIsAnalyzerOpen(true)}>Analyze a job <ArrowRight size={17} /></button></div></div>
            <footer className="site-footer"><div className="container footer-page-terms"><div><span className="eyebrow">Terms & Conditions / sample copy</span><h2>Use HireShield with care.</h2><p>This placeholder copy is here to complete the presentation layout. Replace it with approved legal language before launch.</p></div><div className="footer-term-grid"><div><strong>Informational support</strong><span>Results are risk indicators, not definitive accusations or professional advice.</span></div><div><strong>Your responsibility</strong><span>Only submit material you have the right to share, and verify opportunities independently.</span></div><div><strong>Service boundaries</strong><span>Do not rely on a single result before sending money, passwords, or identity documents.</span></div></div><Link className="inline-link footer-term-link" href="/terms">Read the full Terms & Conditions <ArrowUpRight size={15} /></Link></div><div className="container footer-top"><a className="brand footer-brand" href="#top"><LogoMark /><span>Hire<span>Shield</span></span></a><p>Practical context for uncertain opportunities.</p><div className="footer-links"><Link href="/privacy">Privacy</Link><Link href="/terms">Terms</Link><a href="mailto:support@hireshield.example">Contact</a></div></div><div className="container footer-bottom"><span>© 2026 HireShield</span><span>Results are indicators, not definitive accusations.</span><span>Made for careful decisions.</span></div></footer>
          </section>
        </PageStack>
      </main>

      {isAnalyzerOpen && <AnalyzerModal onClose={() => setIsAnalyzerOpen(false)} />}
    </div>
  );
}

export { LogoMark };
