import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.ai.provider import AIProvider
from app.ai.bedrock import BedrockProvider
from app.risk.engine import RiskEngine
from app.risk.rules import get_signal_score, RiskSignalType
from app.core.dynamodb import save_analysis, get_analysis
from app.core.s3 import upload_file

logger = logging.getLogger(__name__)


def _build_result_record(
    analysis_id: str,
    extraction,
    risk_result: dict,
    *,
    input_source: str = 'TEXT',
    s3_key: str | None = None,
    user_id: str = 'demo_user',
) -> dict:
    '''Build a DynamoDB record matching the frontend's expected shape.'''
    company_data = None
    if extraction.company:
        company_data = {
            'id': str(uuid.uuid4()),
            'name': extraction.company,
            'domain': None,
            'verification_status': 'UNVERIFIED',
        }
        if extraction.application_url:
            from urllib.parse import urlsplit
            try:
                parsed = urlsplit(extraction.application_url)
                domain = parsed.hostname
                if domain:
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    company_data['domain'] = domain
            except Exception:
                pass

    recruiter_data = None
    if extraction.recruiter or extraction.recruiter_email:
        recruiter_data = {
            'id': str(uuid.uuid4()),
            'name': extraction.recruiter or 'Unknown',
            'email': extraction.recruiter_email,
            'verification_status': 'UNVERIFIED',
        }

    signals = []
    for sig in risk_result['signal_details']:
        signals.append({
            'type': sig['signal_type'],
            'contribution': sig['score_contribution'],
            'reasoning': sig['reasoning'],
            'evidence': sig['evidence'],
        })

    return {
        'id': analysis_id,
        'title': extraction.job_title or 'Untitled Opportunity',
        'company': company_data,
        'recruiter': recruiter_data,
        'risk_score': risk_result['risk_score'],
        'risk_level': risk_result['risk_level'],
        'confidence': risk_result['confidence'],
        'input_source': input_source,
        'signals': signals,
        's3_key': s3_key,
        'user_id': user_id,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }


def _build_new_format_response(
    analysis_id: str,
    extraction,
    risk_result: dict,
    *,
    input_source: str = 'TEXT',
    s3_key: str | None = None,
) -> dict:
    '''Build response in the new API format.'''
    signals = risk_result['signal_details']
    
    indicators = []
    for sig in signals:
        indicators.append({
            'type': sig['signal_type'],
            'severity': _score_to_severity(sig['score_contribution']),
            'evidence': sig['evidence'],
            'explanation': sig['reasoning'],
        })
    
    recommendations = _build_recommendations(signals)
    summary = _build_summary(risk_result, extraction)
    
    return {
        'analysis_id': analysis_id,
        'risk_level': risk_result['risk_level'],
        'risk_score': risk_result['risk_score'],
        'summary': summary,
        'indicators': indicators,
        'recommendations': recommendations,
    }


def _score_to_severity(score: int) -> str:
    if score >= 25:
        return 'HIGH'
    elif score >= 15:
        return 'MEDIUM'
    elif score >= 10:
        return 'LOW'
    return 'INFO'


def _build_summary(risk_result: dict, extraction) -> str:
    signals = risk_result['signal_details']
    if not signals:
        return 'No significant risk signals detected in this job posting.'
    
    high_signals = [s for s in signals if s['score_contribution'] >= 20]
    if high_signals:
        sig_type = high_signals[0]['signal_type'].lower().replace('_', ' ')
        return f'Detected {len(high_signals)} high-severity risk signal(s) including {sig_type}.'
    
    return f'Detected {len(signals)} risk signal(s) requiring attention.'


def _build_recommendations(signals: list) -> list[str]:
    recommendations = []
    signal_types = {s['signal_type'] for s in signals}
    
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
    
    if not recommendations:
        recommendations.append('Verify the employer through its official website and career portal.')
        recommendations.append('Confirm the recruiter\'s identity through corporate channels.')
    
    return recommendations


class AnalysisService:
    def __init__(self, ai_provider: AIProvider | None = None):
        self.ai = ai_provider or BedrockProvider()

    async def analyze_job_text(self, text: str, user_id: str = 'demo_user') -> str:
        '''Analyze job text. Returns the analysis ID.'''
        analysis_id = str(uuid.uuid4())

        extraction = await self.ai.extract_job_information(text)
        risk_result = RiskEngine.calculate_risk(extraction)

        record = _build_result_record(
            analysis_id, extraction, risk_result,
            input_source='TEXT', user_id=user_id,
        )
        save_analysis(record)
        return analysis_id

    async def analyze_job_text_new_format(self, text: str, user_id: str = 'demo_user') -> dict:
        '''Analyze job text and return new format response.'''
        analysis_id = str(uuid.uuid4())

        extraction = await self.ai.extract_job_information(text)
        risk_result = RiskEngine.calculate_risk(extraction)

        record = _build_result_record(
            analysis_id, extraction, risk_result,
            input_source='TEXT', user_id=user_id,
        )
        save_analysis(record)
        
        return _build_new_format_response(analysis_id, extraction, risk_result, input_source='TEXT')

    async def analyze_job_file(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        user_id: str = 'demo_user',
    ) -> str:
        '''Analyze an uploaded file. Uploads to S3, extracts, and returns the analysis ID.'''
        analysis_id = str(uuid.uuid4())

        # Upload to S3
        s3_key = upload_file(file_bytes, filename, mime_type)

        # Try to extract text from PDF
        extracted_text = None
        is_pdf = mime_type == 'application/pdf'
        input_source = 'PDF' if is_pdf else 'IMAGE'

        if is_pdf:
            try:
                from pypdf import PdfReader
                import io

                reader = PdfReader(io.BytesIO(file_bytes))
                text_parts = []
                for page in reader.pages[:20]:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                pdf_text = '\n'.join(text_parts).strip()
                if len(pdf_text) > 100:
                    extracted_text = pdf_text
            except Exception as e:
                logger.warning(f'PDF text extraction failed: {e}')

        # Use Bedrock for extraction
        if extracted_text:
            extraction = await self.ai.extract_job_information(extracted_text)
        else:
            extraction = await self.ai.extract_job_information_from_document(file_bytes, mime_type)

        risk_result = RiskEngine.calculate_risk(extraction)

        record = _build_result_record(
            analysis_id, extraction, risk_result,
            input_source=input_source, s3_key=s3_key, user_id=user_id,
        )
        save_analysis(record)
        return analysis_id

    async def analyze_job_file_new_format(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        user_id: str = 'demo_user',
    ) -> dict:
        '''Analyze an uploaded file and return new format response.'''
        analysis_id = str(uuid.uuid4())

        # Upload to S3
        s3_key = upload_file(file_bytes, filename, mime_type)

        # Try to extract text from PDF
        extracted_text = None
        is_pdf = mime_type == 'application/pdf'
        input_source = 'PDF' if is_pdf else 'IMAGE'

        if is_pdf:
            try:
                from pypdf import PdfReader
                import io

                reader = PdfReader(io.BytesIO(file_bytes))
                text_parts = []
                for page in reader.pages[:20]:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                pdf_text = '\n'.join(text_parts).strip()
                if len(pdf_text) > 100:
                    extracted_text = pdf_text
            except Exception as e:
                logger.warning(f'PDF text extraction failed: {e}')

        # Use Bedrock for extraction
        if extracted_text:
            extraction = await self.ai.extract_job_information(extracted_text)
        else:
            extraction = await self.ai.extract_job_information_from_document(file_bytes, mime_type)

        risk_result = RiskEngine.calculate_risk(extraction)

        record = _build_result_record(
            analysis_id, extraction, risk_result,
            input_source=input_source, s3_key=s3_key, user_id=user_id,
        )
        save_analysis(record)
        
        return _build_new_format_response(analysis_id, extraction, risk_result, input_source=input_source, s3_key=s3_key)


def get_result(analysis_id: str) -> dict | None:
    '''Retrieve a stored analysis result.'''
    return get_analysis(analysis_id)


def list_user_analyses(user_id: str = 'demo_user', limit: int = 20) -> list[dict]:
    '''List previous analyses for a user.'''
    from app.core.dynamodb import list_analyses as _list
    return _list(user_id=user_id, limit=limit)
