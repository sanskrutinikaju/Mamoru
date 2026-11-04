"""Request and response shapes for POST /analyze.

Content is accepted in memory, validated, and not stored.
The response contains deterministic findings and optional validated LLM findings.
"""

from typing import Literal

from pydantic import BaseModel, Field

from backend.config import get_max_content_chars

from .analysis import LLMFinding
from .report import SafetyReport


class ExtractionRequest(BaseModel):
    """Body sent by the extension after the user confirms extraction."""

    url: str = Field(min_length=1, max_length=2048)
    title: str = Field(min_length=1, max_length=512)
    language: str = Field(default="unknown", max_length=16)
    wordCount: int = Field(ge=0, le=2_000_000)
    content: str = Field(min_length=0, max_length=get_max_content_chars())
    consentTimestamp: str = Field(min_length=1, max_length=64)


class RuleFinding(BaseModel):
    """One deterministic rule match and its exact evidence span."""

    ruleId: str
    description: str
    severity: Literal["Low", "Medium", "High"]
    category: str
    evidence: str


class AnalysisResponse(BaseModel):
    """Safety Report, source findings, and explicit LLM status."""

    status: str
    message: str
    analysisId: str
    findings: list[RuleFinding]
    llmStatus: Literal["completed", "unavailable", "failed"]
    llmMessage: str
    llmFindings: list[LLMFinding]
    safetyReport: SafetyReport
