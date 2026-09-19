from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.auth.dependencies import get_current_user_id
from app.services.analysis_service import get_result, list_user_analyses
from app.api.schemas import AnalysisHistoryResponse, AnalysisHistoryItem, AnalysisDetailResponse

router = APIRouter()


@router.get('/analyses', response_model=AnalysisHistoryResponse)
async def list_analyses(
    current_user: str = Depends(get_current_user_id),
    limit: int = 20,
):
    '''Return recent analyses from DynamoDB.'''
    analyses = list_user_analyses(user_id=current_user, limit=limit)
    
    items = []
    for a in analyses:
        # Build summary from signals
        signals = a.get('signals', [])
        summary_parts = []
        for s in signals[:3]:
            sig_type = s.get('type', 'UNKNOWN')
            evidence = s.get('evidence', '')[:50]
            summary_parts.append(f'{sig_type}: {evidence}')
        summary = '; '.join(summary_parts) if summary_parts else 'No risk signals detected'
        
        items.append(AnalysisHistoryItem(
            analysis_id=a.get('id', ''),
            created_at=a.get('created_at', ''),
            input_type=a.get('input_source', 'TEXT'),
            risk_score=a.get('risk_score', 0),
            risk_level=a.get('risk_level', 'LOW'),
            summary=summary,
        ))
    
    return AnalysisHistoryResponse(analyses=items)


@router.get('/analyses/{analysis_id}', response_model=AnalysisDetailResponse)
async def get_analysis(
    analysis_id: str,
    current_user: str = Depends(get_current_user_id),
):
    '''Return a specific analysis.'''
    result = get_result(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail='Analysis not found')
    
    # Verify ownership
    if result.get('user_id') != current_user:
        raise HTTPException(status_code=403, detail='Access denied')
    
    signals = result.get('signals', [])
    indicators = []
    for s in signals:
        indicators.append({
            'type': s.get('type', 'UNKNOWN'),
            'severity': _score_to_severity(s.get('contribution', 0)),
            'evidence': s.get('evidence', ''),
            'explanation': s.get('reasoning', ''),
        })
    
    # Build recommendations based on signals
    recommendations = _build_recommendations(signals)
    
    return AnalysisDetailResponse(
        analysis_id=result.get('id', ''),
        created_at=result.get('created_at', ''),
        input_type=result.get('input_source', 'TEXT'),
        source_info={'s3_key': result.get('s3_key')} if result.get('s3_key') else None,
        risk_score=result.get('risk_score', 0),
        risk_level=result.get('risk_level', 'LOW'),
        summary=_build_summary(result),
        indicators=indicators,
        recommendations=recommendations,
        ai_findings={'signals': signals},
        deterministic_findings={'risk_score': result.get('risk_score'), 'confidence': result.get('confidence')},
    )


def _score_to_severity(score: int) -> str:
    if score >= 25:
        return 'HIGH'
    elif score >= 15:
        return 'MEDIUM'
    elif score >= 10:
        return 'LOW'
    return 'INFO'


def _build_summary(result: dict) -> str:
    signals = result.get('signals', [])
    if not signals:
        return 'No significant risk signals detected in this job posting.'
    
    high_signals = [s for s in signals if s.get('contribution', 0) >= 20]
    if high_signals:
        sig_type = high_signals[0].get('type', 'unknown').lower().replace('_', ' ')
        return f'Detected {len(high_signals)} high-severity risk signal(s) including {sig_type}.'
    
    return f'Detected {len(signals)} risk signal(s) requiring attention.'


def _build_recommendations(signals: List[dict]) -> List[str]:
    recommendations = []
    signal_types = {s.get('type') for s in signals}
    
    if 'UPFRONT_PAYMENT' in signal_types:
        recommendations.append('Do not make any payment for equipment, training, or onboarding fees.')
    if 'OFF_PLATFORM_COMMUNICATION' in signal_types:
        recommendations.append('Do not move communication to Telegram, WhatsApp, Signal, or other messaging apps.')
    if 'SUSPICIOUS_PAYMENT_METHOD' in signal_types:
        recommendations.append('Do not send money via cryptocurrency, wire transfer, CashApp, Venmo, or gift cards.')
    if 'HIGH_PRESSURE_LANGUAGE' in signal_types:
        recommendations.append('Take time to verify the opportunity. Legitimate employers do not enforce arbitrary deadlines.')
    if 'UNREALISTIC_PROMISES' in signal_types or 'UNREALISTIC_COMPENSATION' in signal_types:
        recommendations.append('Verify compensation and role details through the company\'s official career page.')
    if 'POSSIBLE_IMPERSONATION' in signal_types:
        recommendations.append('Verify the recruiter\'s identity through the company\'s official HR department.')
    if 'SENSITIVE_INFORMATION_REQUEST' in signal_types:
        recommendations.append('Never share SSN, passport, banking details, or other sensitive info before official onboarding.')
    
    # Default recommendations
    if not recommendations:
        recommendations.append('Verify the employer through its official website and career portal.')
        recommendations.append('Confirm the recruiter\'s identity through corporate channels.')
    
    return recommendations
