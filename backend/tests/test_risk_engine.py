import pytest
from app.risk.engine import RiskEngine
from app.ai.schemas import JobExtraction, SuspiciousSignal


def test_risk_engine_low_risk():
    '''Test that a clean job posting gets LOW risk.'''
    extraction = JobExtraction(
        job_title='Software Engineer',
        company='Google',
        recruiter='Jane Doe',
        recruiter_email='jane@google.com',
        description='Standard software engineering role',
        suspicious_signals=[],
        missing_information=[],
    )
    result = RiskEngine.calculate_risk(extraction)
    assert result['risk_score'] == 0
    assert result['risk_level'] == 'LOW'
    assert result['confidence'] == 100


def test_risk_engine_upfront_payment():
    '''Test that UPFRONT_PAYMENT signal increases risk score.'''
    extraction = JobExtraction(
        job_title='Remote Operations Specialist',
        company='Apex Logistics',
        recruiter='Alex Mercer',
        recruiter_email='alex@apex-logistics.com',
        description='Pay  equipment fee',
        suspicious_signals=[
            SuspiciousSignal(
                signal_type='UPFRONT_PAYMENT',
                evidence='Pay  equipment fee',
                confidence=95,
                reasoning='Job posting requests upfront payment from applicant.',
            )
        ],
        missing_information=[],
    )
    result = RiskEngine.calculate_risk(extraction)
    assert result['risk_score'] == 30
    assert result['risk_level'] == 'MODERATE'
    assert len(result['signal_details']) == 1
    assert result['signal_details'][0]['signal_type'] == 'UPFRONT_PAYMENT'


def test_risk_engine_multiple_signals():
    '''Test that multiple signals add up.'''
    extraction = JobExtraction(
        job_title='Remote Operations Specialist',
        company='Apex Logistics',
        recruiter='Alex Mercer',
        recruiter_email='alex@apex-logistics.com',
        description='Pay  equipment fee. Contact on Telegram @hiring. Urgent hiring!',
        suspicious_signals=[
            SuspiciousSignal(
                signal_type='UPFRONT_PAYMENT',
                evidence='Pay  equipment fee',
                confidence=95,
                reasoning='Job posting requests upfront payment from applicant.',
            ),
            SuspiciousSignal(
                signal_type='OFF_PLATFORM_COMMUNICATION',
                evidence='Contact on Telegram @hiring',
                confidence=90,
                reasoning='Recruiter requests moving communication off-platform.',
            ),
            SuspiciousSignal(
                signal_type='HIGH_PRESSURE_LANGUAGE',
                evidence='Urgent hiring!',
                confidence=85,
                reasoning='High pressure urgency language detected.',
            ),
        ],
        missing_information=[],
    )
    result = RiskEngine.calculate_risk(extraction)
    # 30 + 20 + 10 = 60
    assert result['risk_score'] == 60
    assert result['risk_level'] == 'SUSPICIOUS'
    assert len(result['signal_details']) == 3


def test_risk_engine_positive_signals():
    '''Test that positive signals reduce risk score.'''
    extraction = JobExtraction(
        job_title='Software Engineer',
        company='Google',
        recruiter='Jane Doe',
        recruiter_email='jane@google.com',
        description='Standard software engineering role',
        suspicious_signals=[
            SuspiciousSignal(
                signal_type='VERIFIED_COMPANY_DOMAIN',
                evidence='google.com',
                confidence=100,
                reasoning='Company domain verified.',
            ),
            SuspiciousSignal(
                signal_type='VERIFIED_OFFICIAL_JOB',
                evidence='https://careers.google.com/jobs/123',
                confidence=100,
                reasoning='Official job posting verified.',
            ),
        ],
        missing_information=[],
    )
    result = RiskEngine.calculate_risk(extraction)
    # -15 + -25 = -40, clamped to 0
    assert result['risk_score'] == 0
    assert result['risk_level'] == 'LOW'
