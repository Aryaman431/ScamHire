from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class SuspiciousSignal(BaseModel):
    signal_type: str = Field(description="A predefined categorization of the risk signal (e.g. UPFRONT_PAYMENT, HIGH_PRESSURE_LANGUAGE, etc.).")
    evidence: str = Field(description="The exact text quote from the submitted job input that supports this signal. Do NOT invent text.")
    confidence: int = Field(description="AI's confidence that this signal is present, from 0 to 100.")
    reasoning: str = Field(description="Why this signal was flagged and how the evidence relates to it.")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, value: int) -> int:
        if not 0 <= value <= 100:
            raise ValueError("Confidence must be between 0 and 100.")
        return value

    @field_validator("evidence")
    @classmethod
    def validate_evidence(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Evidence must not be empty.")
        return value

class JobExtraction(BaseModel):
    company: Optional[str] = Field(default=None, description="The name of the company hiring.")
    recruiter: Optional[str] = Field(default=None, description="The name of the recruiter or contact person.")
    job_title: Optional[str] = Field(default=None, description="The job title.")
    description: Optional[str] = Field(default=None, description="A brief summary of the job description.")
    compensation: Optional[str] = Field(default=None, description="The offered compensation, salary, or pay rate.")
    location: Optional[str] = Field(default=None, description="The job location (remote or physical).")
    application_url: Optional[str] = Field(default=None, description="The URL where the applicant is supposed to apply or contact.")
    recruiter_email: Optional[str] = Field(default=None, description="The email address provided for contact.")
    recruiter_phone: Optional[str] = Field(default=None, description="The phone number provided for contact.")
    claims: List[str] = Field(default_factory=list, description="List of notable claims made in the posting (e.g., 'Guaranteed selection in 3 days').")
    suspicious_signals: List[SuspiciousSignal] = Field(default_factory=list, description="List of suspicious risk signals found in the text.")
    missing_information: List[str] = Field(default_factory=list, description="Critical information that is suspiciously absent (e.g., 'No company domain specified').")
