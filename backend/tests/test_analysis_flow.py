import pytest
from unittest.mock import AsyncMock, patch
from app.services.analysis_service import AnalysisService
from app.ai.schemas import JobExtraction, SuspiciousSignal


@pytest.mark.asyncio
async def test_analyze_job_text_new_format():
    '''Test the new format analysis endpoint.'''
    service = AnalysisService()
    
    # Mock the AI provider to return a known extraction
    mock_extraction = JobExtraction(
        job_title='Remote Operations Specialist',
        company='Apex Logistics',
        recruiter='Alex Mercer',
        recruiter_email='alex@apex-logistics.com',
        description='Pay \ equipment fee',
        suspicious_signals=[
            SuspiciousSignal(
                signal_type='UPFRONT_PAYMENT',
                evidence='Pay \ equipment fee',
                confidence=95,
                reasoning='Job posting requests upfront payment from applicant.',
            )
        ],
        missing_information=[],
    )
    
    with patch.object(service.ai, 'extract_job_information', new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = mock_extraction
        result = await service.analyze_job_text_new_format('Test job with upfront payment', user_id='test_user')
    
    assert 'analysis_id' in result
    assert result['risk_level'] == 'MODERATE'
    assert result['risk_score'] == 30
    assert len(result['indicators']) == 1
    assert result['indicators'][0]['type'] == 'UPFRONT_PAYMENT'
    assert result['indicators'][0]['severity'] == 'HIGH'
    assert len(result['recommendations']) > 0


@pytest.mark.asyncio
async def test_analyze_job_text_clean():
    '''Test analysis of a clean job posting.'''
    service = AnalysisService()
    
    mock_extraction = JobExtraction(
        job_title='Software Engineer',
        company='Google',
        recruiter='Jane Doe',
        recruiter_email='jane@google.com',
        description='Standard software engineering role with great benefits',
        suspicious_signals=[],
        missing_information=[],
    )
    
    with patch.object(service.ai, 'extract_job_information', new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = mock_extraction
        result = await service.analyze_job_text_new_format('Clean job posting', user_id='test_user')
    
    assert result['risk_level'] == 'LOW'
    assert result['risk_score'] == 0
    assert len(result['indicators']) == 0
    assert 'Verify the employer through its official website' in result['recommendations'][0]


@pytest.mark.asyncio
async def test_analyze_job_file_new_format():
    '''Test file analysis with new format.'''
    service = AnalysisService()
    
    mock_extraction = JobExtraction(
        job_title='Remote Operations Specialist',
        company='Apex Logistics',
        recruiter='Alex Mercer',
        recruiter_email='alex@apex-logistics.com',
        description='Pay \ equipment fee',
        suspicious_signals=[
            SuspiciousSignal(
                signal_type='UPFRONT_PAYMENT',
                evidence='Pay \ equipment fee',
                confidence=95,
                reasoning='Job posting requests upfront payment from applicant.',
            )
        ],
        missing_information=[],
    )
    
    with patch.object(service.ai, 'extract_job_information_from_document', new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = mock_extraction
        with patch('app.services.analysis_service.upload_file', return_value='test-s3-key'):
            result = await service.analyze_job_file_new_format(
                b'fake file content', 'test.pdf', 'application/pdf', user_id='test_user'
            )
    
    assert 'analysis_id' in result
    assert result['risk_level'] == 'MODERATE'
    assert result['risk_score'] == 30
    assert len(result['indicators']) == 1
