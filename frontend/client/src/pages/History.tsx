import { useState, useEffect } from 'react';
import { ArrowLeft, ArrowUpRight, AlertTriangle, CircleCheck, FileText, Clock, ShieldCheck, ChevronRight } from 'lucide-react';
import { Link } from 'wouter';
import { getAnalyses, getAnalysis, AnalysisHistoryItem, AnalysisDetailResponse, ApiError } from '../lib/api';
import { LogoMark } from './Home';

export default function History() {
  const [analyses, setAnalyses] = useState<AnalysisHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    loadAnalyses();
  }, []);

  const loadAnalyses = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getAnalyses(50);
      setAnalyses(response.analyses);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load analysis history. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleViewAnalysis = async (analysisId: string) => {
    try {
      setDetailLoading(true);
      const detail = await getAnalysis(analysisId);
      setSelectedAnalysis(detail);
    } catch (err) {
      if (err instanceof ApiError) {
        alert(err.message);
      } else {
        alert('Failed to load analysis details.');
      }
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedAnalysis(null);
  };

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit', hour: '2-digit', minute: '2-digit' });
    } catch {
      return dateString;
    }
  };

  const getRiskLevelClass = (level: string): string => {
    switch (level.toUpperCase()) {
      case 'HIGH': return 'risk-high';
      case 'MEDIUM': return 'risk-medium';
      case 'LOW': return 'risk-low';
      default: return 'risk-info';
    }
  };

  const getRiskLevelLabel = (level: string): string => {
    switch (level.toUpperCase()) {
      case 'HIGH': return 'High';
      case 'MEDIUM': return 'Review';
      case 'LOW': return 'Low';
      default: return level;
    }
  };

  if (selectedAnalysis) {
    return (
      <div className='legal-shell'>
        <header className='site-header legal-header'>
          <Link className='brand' href='/'>
            <LogoMark />
            <span>Hire<span>Shield</span></span>
          </Link>
          <button className='back-link' onClick={handleCloseDetail}>
            <ArrowLeft size={15} /> Back to history
          </button>
        </header>
        <main className='legal-main'>
          <div className='legal-kicker'>
            <FileText size={15} /> Analysis Detail
          </div>
          <h1>Analysis <span style={{ color: 'var(--signal)' }}>{selectedAnalysis.analysis_id.slice(0, 8)}…</span></h1>
          <p className='legal-lede'>Completed {formatDate(selectedAnalysis.created_at)} · {selectedAnalysis.input_type} input</p>

          <div className='legal-notice' style={{ marginTop: 24 }}>
            <ShieldCheck size={18} />
            <p><strong>Risk Score:</strong> {selectedAnalysis.risk_score}/100 · <strong>Level:</strong> <span className={getRiskLevelClass(selectedAnalysis.risk_level)}>{getRiskLevelLabel(selectedAnalysis.risk_level)}</span></p>
          </div>

          <div className='legal-body'>
            <h2>Summary</h2>
            <p>{selectedAnalysis.summary}</p>

            {selectedAnalysis.indicators.length > 0 && (
              <>
                <h2>Risk Indicators</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 16 }}>
                  {selectedAnalysis.indicators.map((indicator, index) => (
                    <div key={index} style={{ padding: '16px', border: '1px solid var(--line)', borderRadius: 4, background: 'rgba(16,18,18,.02)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                        <strong style={{ fontSize: 13, textTransform: 'capitalize' }}>{indicator.type.replace(/_/g, ' ')}</strong>
                        <span className={getRiskLevelClass(indicator.severity)} style={{ fontSize: 10, padding: '4px 8px', borderRadius: 2, textTransform: 'uppercase', fontFamily: 'var(--mono)' }}>
                          {indicator.severity}
                        </span>
                      </div>
                      <p style={{ marginBottom: 8, color: 'var(--muted-ink)', fontSize: 12 }}>{indicator.explanation}</p>
                      <p style={{ fontSize: 11, fontFamily: 'var(--mono)', color: 'var(--signal)' }}><strong>Evidence:</strong> {indicator.evidence}</p>
                    </div>
                  ))}
                </div>
              </>
            )}

            {selectedAnalysis.recommendations.length > 0 && (
              <>
                <h2>Recommendations</h2>
                <ul style={{ marginTop: 16, paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {selectedAnalysis.recommendations.map((rec, index) => (
                    <li key={index} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, lineHeight: 1.6 }}>
                      <CircleCheck size={16} style={{ flexShrink: 0, color: 'var(--signal)', marginTop: 2 }} />
                      {rec}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className='legal-shell'>
      <header className='site-header legal-header'>
        <Link className='brand' href='/'>
          <LogoMark />
          <span>Hire<span>Shield</span></span>
        </Link>
        <Link className='back-link' href='/'>
          <ArrowLeft size={15} /> Back to home
        </Link>
      </header>
      <main className='legal-main'>
        <div className='legal-kicker'>
          <Clock size={15} /> Analysis History
        </div>
        <h1>Your previous checks</h1>
        <p className='legal-lede'>Review past analyses to track patterns and revisit findings.</p>

        {error && (
          <div className='legal-notice' style={{ background: 'rgba(245,120,75,.13)', borderColor: 'rgba(245,120,75,.35)', color: '#a95032', marginTop: 24 }}>
            <AlertTriangle size={18} />
            <p>{error}</p>
            <button className='button button-ghost' onClick={loadAnalyses} style={{ marginTop: 12, minHeight: 36 }}>
              Try again
            </button>
          </div>
        )}

        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <div className='spinner' style={{ width: 32, height: 32, margin: '0 auto 16px', border: '3px solid var(--line)', borderTopColor: 'var(--signal)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
            <p className='modal-copy'>Loading history…</p>
          </div>
        ) : analyses.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <FileText size={48} style={{ marginBottom: 16, color: 'var(--muted-ink)' }} />
            <h2 style={{ marginBottom: 8 }}>No analyses yet</h2>
            <p className='legal-lede' style={{ maxWidth: 400, margin: '0 auto 24px' }}>Your analysis history will appear here after you check your first job offer.</p>
            <Link href='/' className='button button-primary' style={{ display: 'inline-flex' }}>
              <ArrowUpRight size={16} /> Analyze a job offer
            </Link>
          </div>
        ) : (
          <div style={{ marginTop: 32 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid var(--line)' }}>
              <span style={{ fontSize: 12, color: 'var(--muted-ink)', fontFamily: 'var(--mono)' }}>{analyses.length} analysis{analyses.length !== 1 ? 'es' : ''}</span>
              <Link href='/' className='button button-primary' style={{ minHeight: 36 }}>
                <ArrowUpRight size={14} /> New analysis
              </Link>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {analyses.map((analysis) => (
                <button
                  key={analysis.analysis_id}
                  onClick={() => handleViewAnalysis(analysis.analysis_id)}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'auto 1fr auto',
                    gap: 16,
                    alignItems: 'center',
                    padding: '16px 20px',
                    background: 'var(--paper)',
                    color: 'var(--ink)',
                    border: '1px solid var(--line)',
                    borderRadius: 4,
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'border-color 180ms ease, box-shadow 180ms ease',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--signal)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,.1)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--line)'; e.currentTarget.style.boxShadow = 'none'; }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <FileText size={20} style={{ color: 'var(--signal)' }} />
                    <div>
                      <p style={{ fontWeight: 600, fontSize: 13 }}>Analysis {analysis.analysis_id.slice(0, 8)}…</p>
                      <p style={{ fontSize: 11, color: 'var(--muted-ink)', fontFamily: 'var(--mono)' }}>{formatDate(analysis.created_at)} · {analysis.input_type}</p>
                    </div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <p style={{ fontSize: 24, fontWeight: 500, letterSpacing: '-0.05em' }}>{analysis.risk_score}</p>
                    <p style={{ fontSize: 10, color: 'var(--muted-ink)', textTransform: 'uppercase' }}>Risk Score</p>
                  </div>
                  <div style={{ textAlign: 'right', minWidth: 100 }}>
                    <span className={getRiskLevelClass(analysis.risk_level)} style={{ fontSize: 10, padding: '4px 10px', borderRadius: 2, textTransform: 'uppercase', fontFamily: 'var(--mono)', display: 'inline-block' }}>
                      {getRiskLevelLabel(analysis.risk_level)}
                    </span>
                    <p style={{ marginTop: 4, fontSize: 11, color: 'var(--muted-ink)', maxWidth: 200 }}>{analysis.summary}</p>
                    <ChevronRight size={16} style={{ marginTop: 8, color: 'var(--muted-ink)' }} />
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
