from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class AnalyzeJobRequest(BaseModel):
    text: str = Field(..., min_length=10, description='The job opportunity text to analyze.')


class AnalyzeJobResponse(BaseModel):
    job_id: str


# New schemas for /api/analyze endpoints
class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., min_length=10, description='The job posting or recruitment message to analyze.')


class Indicator(BaseModel):
    type: str
    severity: str
    evidence: str
    explanation: str


class AnalyzeTextResponse(BaseModel):
    analysis_id: str
    risk_level: str
    risk_score: int
    summary: str
    indicators: List[Indicator]
    recommendations: List[str]


# History schemas
class AnalysisHistoryItem(BaseModel):
    analysis_id: str
    created_at: str
    input_type: str
    risk_score: int
    risk_level: str
    summary: str


class AnalysisHistoryResponse(BaseModel):
    analyses: List[AnalysisHistoryItem]


class AnalysisDetailResponse(BaseModel):
    analysis_id: str
    created_at: str
    input_type: str
    source_info: Optional[Dict[str, Any]] = None
    risk_score: int
    risk_level: str
    summary: str
    indicators: List[Indicator]
    recommendations: List[str]
    ai_findings: Optional[Dict[str, Any]] = None
    deterministic_findings: Optional[Dict[str, Any]] = None
