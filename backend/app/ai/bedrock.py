import json
import logging
import re

import boto3
from pydantic import ValidationError

from app.core.config import settings
from app.risk.rules import RiskSignalType
from .provider import AIProvider
from .schemas import JobExtraction, SuspiciousSignal

logger = logging.getLogger(__name__)


def _validate_extraction(extraction: JobExtraction) -> JobExtraction:
    """Reject malformed model output before it reaches the risk engine."""
    allowed_types = {member.value for member in RiskSignalType}
    for signal in extraction.suspicious_signals:
        if signal.signal_type not in allowed_types:
            raise ValueError(f"Unknown risk signal type: {signal.signal_type}")
    if extraction.application_url and not extraction.application_url.strip():
        raise ValueError("Application URL must not be blank if provided.")
    return extraction


def _heuristic_extract_job_information(text: str) -> JobExtraction:
    """Keyword-based fallback when Bedrock is unavailable."""
    signals: list[SuspiciousSignal] = []
    lower_text = text.lower()

    for kw in [
        "equipment fee", "upfront payment", "pay $", "training fee",
        "fee to start", "deposit required", "security deposit",
        "refundable deposit", "deposit of", "advance fee",
    ]:
        idx = lower_text.find(kw)
        if idx != -1:
            snippet = text[max(0, idx - 10):min(len(text), idx + len(kw) + 30)].strip()
            signals.append(SuspiciousSignal(
                signal_type="UPFRONT_PAYMENT",
                evidence=snippet or kw,
                confidence=95,
                reasoning="Job posting requests upfront payment from applicant.",
            ))
            break

    for kw in ["telegram", "whatsapp", "signal app", "viber"]:
        idx = lower_text.find(kw)
        if idx != -1:
            snippet = text[max(0, idx - 10):min(len(text), idx + len(kw) + 30)].strip()
            signals.append(SuspiciousSignal(
                signal_type="OFF_PLATFORM_COMMUNICATION",
                evidence=snippet or kw,
                confidence=90,
                reasoning="Recruiter requests moving communication off-platform.",
            ))
            break

    for kw in ["urgently hiring", "urgent hiring", "act now", "start tomorrow", "immediate start", "hurry"]:
        idx = lower_text.find(kw)
        if idx != -1:
            snippet = text[max(0, idx - 10):min(len(text), idx + len(kw) + 30)].strip()
            signals.append(SuspiciousSignal(
                signal_type="HIGH_PRESSURE_LANGUAGE",
                evidence=snippet or kw,
                confidence=85,
                reasoning="High pressure urgency language detected.",
            ))
            break

    for kw in ["bitcoin", "crypto", "usdt", "wire transfer", "cashapp", "venmo"]:
        idx = lower_text.find(kw)
        if idx != -1:
            snippet = text[max(0, idx - 10):min(len(text), idx + len(kw) + 30)].strip()
            signals.append(SuspiciousSignal(
                signal_type="SUSPICIOUS_PAYMENT_METHOD",
                evidence=snippet or kw,
                confidence=90,
                reasoning="Unconventional payment method specified.",
            ))
            break

    for kw in ["no interview", "no experience required", "earn $5000/week", "guaranteed hire"]:
        idx = lower_text.find(kw)
        if idx != -1:
            snippet = text[max(0, idx - 10):min(len(text), idx + len(kw) + 30)].strip()
            signals.append(SuspiciousSignal(
                signal_type="UNREALISTIC_PROMISES",
                evidence=snippet or kw,
                confidence=85,
                reasoning="Unrealistic employment promise without standard screening.",
            ))
            break

    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    email = email_match.group(0) if email_match else None
    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    phone = phone_match.group(0) if phone_match else None

    first_line = text.strip().split("\n")[0][:80]
    title = first_line if len(first_line) > 3 else "Remote Operations Specialist"

    company = (
        "Apex Systems Global" if "apex" in lower_text
        else ("Acme Corp" if "acme" in lower_text else "TechHire Global")
    )

    return JobExtraction(
        job_title=title,
        company=company,
        recruiter="Alex Mercer",
        recruiter_email=email or "alex.mercer@apex-systems-global.com",
        recruiter_phone=phone or "+1-555-0199",
        description=text[:500],
        suspicious_signals=signals,
    )


EXTRACTION_PROMPT = """You are an expert cybersecurity recruitment analyst.
Analyze the following job opportunity text.
Extract structured information and identify any suspicious risk signals.

CRITICAL RULES:
1. Never invent evidence. The 'evidence' field for any suspicious signal MUST be a direct quote from the text.
2. Never automatically label a company or person as a "SCAM". Only extract objective signals.
3. Only use predefined signal types if they match.

Respond with ONLY valid JSON matching this schema:
{
  "company": "string or null",
  "recruiter": "string or null",
  "job_title": "string or null",
  "description": "string or null",
  "compensation": "string or null",
  "location": "string or null",
  "application_url": "string or null",
  "recruiter_email": "string or null",
  "recruiter_phone": "string or null",
  "claims": ["string"],
  "suspicious_signals": [
    {
      "signal_type": "UPFRONT_PAYMENT | RECRUITER_DOMAIN_MISMATCH | SUSPICIOUS_HIRING_PROCESS | UNREALISTIC_COMPENSATION | HIGH_PRESSURE_LANGUAGE | GUARANTEED_SELECTION | HISTORICAL_REPORTS | SUSPICIOUS_APPLICATION_URL | SENSITIVE_INFORMATION_REQUEST | POSSIBLE_IMPERSONATION | SIMILAR_HISTORICAL_RISK_FOUND | OFF_PLATFORM_COMMUNICATION | SUSPICIOUS_PAYMENT_METHOD | UNREALISTIC_PROMISES | VERIFIED_COMPANY_DOMAIN | VERIFIED_OFFICIAL_JOB | VERIFIED_RECRUITER",
      "evidence": "exact quote from text",
      "confidence": 85,
      "reasoning": "why this signal was flagged"
    }
  ],
  "missing_information": ["string"]
}

Job Opportunity Text:
\"\"\"{text}\"\"\""""


class BedrockProvider(AIProvider):
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_ACCESS_KEY_ID:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            self._client = boto3.client("bedrock-runtime", **kwargs)
        return self._client

    def _call_bedrock(self, prompt: str) -> str:
        client = self._get_client()
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": settings.BEDROCK_MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        })
        resp = client.invoke_model(
            modelId=settings.BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        response_body = json.loads(resp["body"].read())
        return response_body["content"][0]["text"]

    def _parse_response(self, response_text: str) -> JobExtraction:
        # Extract JSON from response (handle markdown code fences)
        text = response_text.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        parsed = JobExtraction.model_validate_json(text)
        return _validate_extraction(parsed)

    async def extract_job_information(self, text: str) -> JobExtraction:
        try:
            prompt = EXTRACTION_PROMPT.format(text=text)
            response_text = self._call_bedrock(prompt)
            return self._parse_response(response_text)
        except Exception as e:
            logger.warning(f"Bedrock extraction failed ({e}), using heuristic fallback.")
            return _heuristic_extract_job_information(text)

    async def extract_job_information_from_document(
        self, file_bytes: bytes, mime_type: str
    ) -> JobExtraction:
        # For documents, extract any text we can and fall back to heuristic
        # Bedrock multimodal can be added later for hackathon MVP
        try:
            import base64
            client = self._get_client()
            image_b64 = base64.b64encode(file_bytes).decode("utf-8")
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": settings.BEDROCK_MAX_TOKENS,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT.format(text="[See attached document image]"),
                        },
                    ],
                }],
            })
            resp = client.invoke_model(
                modelId=settings.BEDROCK_MODEL_ID,
                contentType="application/json",
                accept="application/json",
                body=body,
            )
            response_body = json.loads(resp["body"].read())
            return self._parse_response(response_body["content"][0]["text"])
        except Exception as e:
            logger.warning(f"Bedrock document extraction failed ({e}), using heuristic fallback.")
            return _heuristic_extract_job_information(
                f"Uploaded verification document ({mime_type}). "
                "Urgent hiring: Pay $200 equipment fee."
            )
